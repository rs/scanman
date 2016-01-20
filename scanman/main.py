# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.core.image import ImageData
from kivy.graphics.texture import Texture
from kivy.clock import mainthread, Clock
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.graphics import Line, Color
from kivy.logger import Logger
from img2pdf import pdfdoc
from datetime import datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import sys
import yaml

from .scanner import Scanner

try:
    from StringIO import StringIO as BytesIO
except:
    from io import BytesIO


class ScanMan(BoxLayout):
    scan_button = ObjectProperty(None)
    default_scan_button_background = None
    status_label = ObjectProperty(None)
    preview_image = ObjectProperty(None)
    profiles_container = ObjectProperty(None)

    def on_scan_button(self, instance, value):
        self.default_scan_button_background = self.scan_button.background_color

    def active_profile(self):
        # Get the active profile
        for i, w in enumerate(ToggleButtonBehavior.get_widgets('profile')):
            if w.state == 'down':
                return i


class ImageButton(ToggleButtonBehavior, Image):
    border_width = NumericProperty(2)
    border_color = ObjectProperty((.196, .647, .812))

    def on_border_color(self, instance, value):
        self.update_state()

    def on_border_size(self, instance, value):
        self.update_state()

    def on_pos(self, instance, value):
        self.update_state()

    def on_state(self, instance, value):
        self.update_state()

    def update_state(self):
        self.canvas.after.clear()
        if self.state == 'down':
            self.draw_border()

    def draw_border(self):
        with self.canvas.after:
            Color(*self.border_color)
            w = self.border_width
            Line(width=w, rectangle=(self.x+w, self.y+w, self.width-w, self.height-w))


class ScanManApp(App):
    scanning = BooleanProperty(False)
    ready = BooleanProperty(False)
    connected = BooleanProperty(False)
    custom_status_text = StringProperty("")

    def __init__(self, settings, **kwargs):
        self.settings = settings
        super(ScanManApp, self).__init__(**kwargs)

    def build(self):
        self.ui = ScanMan()
        self.init_profiles()
        self.scanner = Scanner()
        return self.ui

    def init_profiles(self):
        state = 'down'
        for profile in self.settings.get('profiles', []):
            b = ImageButton()
            b.name = profile
            b.source = profile['icon']
            b.size_hint = (None, None)
            b.width = 120
            b.height = 120
            b.allow_stretch = True
            b.group = 'profile'
            b.state = state
            b.allow_no_selection = False
            self.ui.profiles_container.add_widget(b)
            state = 'normal'

    def on_start(self):
        # The UI is init
        self.scanner.scan_button(self.scan)
        self.ui.scan_button.on_release = self.scan

        def set_ready(state):
            self.ready = state
        self.scanner.page_loaded(set_ready)

        def set_connected(state):
            self.connected = state
        self.scanner.connected(set_connected)

    def on_connected(self, instance, value):
        Logger.info('Scanman: connected: %s', value)
        self.reset_custom_status()
        self._update_status()

    def on_ready(self, instance, value):
        Logger.info('Scanman: ready: %s', value)
        if not self.scanning:
            self.reset_custom_status()
        self._update_status()

    def on_scanning(self, instance, value):
        Logger.info('Scanman: scanning: %s', value)
        self._update_status()

    def on_custom_status_text(self, instance, value):
        self._update_status()

    def reset_custom_status(self, *args):
        self.custom_status_text = ""

    @mainthread
    def _update_status(self):
        self.ui.scan_button.text = "Scan"
        self.ui.scan_button.disabled = False
        self.ui.scan_button.background_color = self.ui.default_scan_button_background
        if not self.connected:
            self.ui.status_label.text = 'Scanner is not connected.'
            self.ui.scan_button.disabled = True
        elif self.scanning:
            self.ui.status_label.text = 'Scanning...'
            self.ui.scan_button.background_color = (1, 0, 0, 1)
            self.ui.scan_button.text = "Cancel"
        elif self.ready:
            self.ui.status_label.text = 'Ready.'
        else:
            self.ui.status_label.text = 'No scan in progress.'
            self.ui.scan_button.disabled = True
        if self.custom_status_text:
            self.ui.status_label.text = self.custom_status_text

    @mainthread
    def _update_preview(self, image):
        self.ui.preview_image.texture = Texture.create_from_data(ImageData(image.size[0], image.size[1], image.mode.lower(), image.tobytes()))

    def scan(self):
        if not self.ready:
            return
        if self.scanning:
            self.cancel()
        self.reset_custom_status()
        self.scanning = True
        profile = self.settings['profiles'][self.ui.active_profile()]
        Logger.info('Scanman: scanning with profile: %s', profile.get('name'))

        pdf = pdfdoc()
        dpi = self.scanner.dev.resolution

        def scan_processor(page_index, image):
            Logger.info('Scanman: processing page %d', page_index+1)
            self.custom_status_text = 'Processing page {}'.format(page_index+1)
            self._update_preview(image)
            buf = BytesIO()
            image.save(buf, format='JPEG', quality=75, optimize=True)
            width, height = image.size
            pdf_x, pdf_y = 72.0*width/float(dpi), 72.0*height/float(dpi)
            pdf.addimage(image.mode, width, height, 'JPEG', buf.getvalue(), pdf_x, pdf_y)
            buf.close()

        def done():
            Logger.info('Scanman: processing document')
            self.custom_status_text = 'Processing document…'
            self._update_status()
            filename = datetime.now().strftime(self.settings.get('filename', '%Y%m%d-%H%M%S'))
            msg = MIMEMultipart()
            msg['Subject'] = filename
            msg['From'] = profile['email_from']
            msg['To'] = profile['email_to']
            att = MIMEApplication(pdf.tostring(), _subtype='pdf')
            att.add_header('content-disposition', 'attachment', filename=('utf-8', '', filename + '.pdf'))
            msg.attach(att)
            Logger.info('Scanman: sending email: %s', profile)
            self.custom_status_text = 'Sending email…'
            s = smtplib.SMTP(profile.get('smtp_server', self.settings.get('smtp_server', 'localhost')))
            if profile.get('smtp_tls', self.settings.get('smtp_tls', False)):
                s.starttls()
            cred = profile.get('smtp_credentials', self.settings.get('smtp_credentials'))
            if cred:
                s.login(*cred)
            s.sendmail(profile['email_from'], [profile['email_to']], msg.as_string())
            s.quit()
            self.custom_status_text = 'Done.'
            Clock.schedule_once(self.reset_custom_status, 5)
            self.scanning = False

        def cancelled():
            self.ui.status_label.text = 'Cancelled.'
            Clock.schedule_once(self.reset_custom_status, 5)
            self.scanning = False

        self.scanner.scan(scan_processor, done, cancelled)

    def cancel(self):
        Logger.info('Scanman: cancelling')
        self.scanning = False
        self.scanner.cancel()


def main():
    try:
        settings = yaml.safe_load(open(sys.argv[1]))
    except:
        print('Syntax: scanman <path/to/config.yaml>')
        exit(1)
    ScanManApp(settings).run()

if __name__ == '__main__':
    main()
