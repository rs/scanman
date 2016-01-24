import sane
import threading
import time

try:
    from Queue import Queue, Empty
except:
    from queue import Queue, Empty


class Scanner(object):
    PAGE_LOADED = 82
    COVER_OPEN = 84
    SCAN_BUTTON_PRESSED = 88

    def __init__(self):
        self.version = sane.init()
        self.scanning = False
        self.cancelled = False
        self.dev = None
        self._open_first_device()

    def _open_first_device(self):
        devices = sane.get_devices()
        try:
            self.dev = sane.open(devices[0][0])
        except:
            self.dev = None
            return
        # Selects the scan source (ADF Front/ADF Back/ADF Duplex).
        self.dev.source = 'ADF Duplex'
        # Specifies the height of the media.
        self._set_option(7, 320.0)
        self._set_option(11, 320.0)
        # Selects the scan mode (e.g., lineart, monochrome, or color).
        self.dev.mode = 'color'
        # Sets the resolution of the scanned image (50..600dpi in steps of 1)).
        self.dev.resolution = 192
        # Controls the brightness of the acquired image. -127..127 (in steps of 1) [0]
        self.dev.brightness = 15
        # Controls the contrast of the acquired image. 0..255 (in steps of 1) [0]
        self.dev.contrast = 20
        # Set SDTC variance rate (sensitivity), 0 equals 127. 0..255 (in steps of 1) [0]
        self.dev.variance = 0
        # Collect a few mm of background on top side of scan, before paper
        # enters ADF, and increase maximum scan area beyond paper size, to allow
        # collection on remaining sides. May conflict with bgcolor option
        self.dev.overscan = 'Off'
        # Scanner detects paper lower edge. May confuse some frontends (bool).
        self.dev.ald = True
        # Request scanner to read pages quickly from ADF into internal memory (On/Off/Default).
        self.dev.buffermode = 'On'
        # Request scanner to grab next page from ADF (On/Off/Default).
        self.dev.prepick = 'On'
        # Request driver to rotate skewed pages digitally.
        self.dev.swdeskew = False
        # Maximum diameter of lone dots to remove from scan ([0..9] in steps of 1).
        self.dev.swdespeck = 0
        # Request driver to remove border from pages digitally.
        self.dev.swcrop = True
        # Request driver to discard pages with low percentage of dark pixels
        self.dev.swskip = 5

    def _get_option(self, code):
        try:
            return self.dev.__dict__['dev'].get_option(code)
        except AttributeError:
            return None
        except Exception as e:
            if str(e) == 'Error during device I/O':
                self._open_first_device()
            else:
                raise

    def _set_option(self, code, value):
        try:
            return self.dev.__dict__['dev'].set_option(code, value)
        except AttributeError:
            return None
        except Exception as e:
            if str(e) == 'Error during device I/O':
                self._open_first_device()
            else:
                raise

    def _is_scan_button_pressed(self):
        """
        Returns true if the scan button on the scanner has been pressed.
        """
        return self._get_option(self.SCAN_BUTTON_PRESSED) == 1

    def _is_cover_open(self):
        """
        Returns true if the scan cover is opened.
        """
        return self._get_option(self.COVER_OPENED) == 1

    def _is_page_loaded(self):
        """
        Returns true if a page is loaded in the automatic document feeder
        """
        return self._get_option(self.PAGE_LOADED) == 1

    def scan(self, processor, done, cancelled):
        if not self.dev or self.scanning:
            done()
            return
        self.scanning = True
        self.cancelled = False
        self.iterator = self.dev.multi_scan()
        q = Queue()

        def scan():
            i = 0
            while True:
                try:
                    self.dev.start()
                except Exception as e:
                    if str(e) == 'Document feeder out of documents':
                        q.join()
                        done()
                    else:
                        cancelled()
                    self.scanning = False
                    return
                if self.cancelled:
                    cancelled()
                    self.scanning = False
                    return
                image = self.dev.snap(True)
                q.put((i, image))
                i += 1
                if self.cancelled:
                    cancelled()
                    self.scanning = False
                    return

        def process_queue():
            while True:
                try:
                    processor(*q.get())
                    q.task_done()
                except Empty:
                    return

        threading.Thread(target=scan).start()
        threading.Thread(target=process_queue).start()

    def cancel(self):
        self.cancelled = True
        self.dev.cancel()

    def connected(self, callback):
        def check_connection():
            while True:
                if self.dev is None:
                    # Try to reconnect
                    self._open_first_device()
                callback(self.dev is not None)
                time.sleep(1)
        return threading.Thread(target=check_connection).start()

    def scan_button(self, callback):
        def monitor_scan_button():
            while True:
                try:
                    if not self.scanning and self._is_scan_button_pressed():
                        callback()
                except:
                    pass
                time.sleep(1)
        return threading.Thread(target=monitor_scan_button).start()

    def page_loaded(self, callback):
        def monitor_page_loaded():
            while True:
                if not self.scanning:
                    try:
                        state = self._is_page_loaded()
                        if state is None:
                            state = False
                        callback(state)
                    except:
                        pass
                time.sleep(1)
        return threading.Thread(target=monitor_page_loaded).start()
