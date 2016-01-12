# ScanMan

ScanMan is a [ScanSnap iX500](http://scanners.fcpa.fujitsu.com/scansnap11/features_iX500.html) manager optimized [Raspberry Pi](https://www.raspberrypi.org) connected to a [Raspberry 7" touch display](https://www.raspberrypi.org/blog/the-eagerly-awaited-raspberry-pi-display/).

This project use [Python SANE](https://github.com/python-pillow/Sane) to connect to the scanner so it can be made compatible with any supported scanner with proper options set. Feel free to send pull requests to add support for more scanners.

The GUI is created using [Python Kivy](https://kivy.org/#home), so it should work with any platform / touch screen supported by this framework (with [SANE]( support). Again, feel free to send pull request for screen size / ratio or pixel density adaptations.

## Features

- Handle ultra-fast Automatic Document Feeder (ADF) scanners like [ScanSnap iX500](http://scanners.fcpa.fujitsu.com/scansnap11/features_iX500.html)
- Generates an optimized multi-page / multi-size PDF
- Send PDFs by email
- Multi profiles selector
- Touchscreen UI
- On screen preview of scanned documents
- Works on Linux and any platform supported by both [Python Kivy](https://kivy.org/#home) and [SANE]( support)

## Install

This project has been developed and tested on [Raspberry Pi](https://www.raspberrypi.org) attached to a [Raspberry 7" touchscreen](https://www.raspberrypi.org/blog/the-eagerly-awaited-raspberry-pi-display/) using [Raspbian](https://www.raspberrypi.org/downloads/raspbian/).

This document assumes you have a Raspberry Pi already attached to a touch display with Raspbian Jessi installed:

- Follow [Kivy installation instruction](https://kivy.org/docs/installation/installation-rpi.html)
- Install `libksane-dev` package
- Install `scanman` with its dependencies with `sudo pip install scanman`
- Customize the `sample-settings.yaml` file with your settings

You can launch `scanman` using the pi user or as root as follow:

    scanman /path/to/settings.yaml

To add scanman as a systemd service on Rasbian, create the following file in `/etc/systemd/system/scanman.service`:

    [Unit]
    Description=ScanMan

    [Service]
    User=pi
    Group=pi
    Restart=on-failure
    ExecStart=/usr/local/bin/scanman /etc/scanman.yaml

    [Install]
    WantedBy=multi-user.target

## Licenses

All source code is licensed under the [MIT License](https://raw.github.com/rs/scanman/master/LICENSE).
