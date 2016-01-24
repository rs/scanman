from setuptools import setup
setup(
    name='scanman',
    packages=['scanman'],
    version='0.8',
    description='A ScanSnap manager for Raspbery Pi',
    author='Olivier Poitrey',
    author_email='rs@rhapsodyk.net',
    url='https://github.com/rs/scanman',
    download_url='https://github.com/rs/scanman/tarball/0.8',
    install_requires=['kivy', 'python-sane', 'img2pdf', 'pyyaml'],
    package_data={'scanman': ['*.kv']},
    entry_points={'console_scripts': [
        'scanman = scanman.main:main',
    ]},
    keywords=['scan', 'scansnap', 'sane', 'raspberry', 'kivy', 'paperless', 'office'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console :: Framebuffer',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business',
    ]
)
