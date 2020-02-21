#!/usr/bin/env python3

from setuptools import setup

__version__ = '1.2'
packages = ['temperpi', 'thermometer']
py_modules = [ 'thermometer',
                'thermometer.thermometer_f5_87',
                'thermometer.temp_reading_f5',
                'thermometer.temp_reading_87',
                'temperpi',
                'temperpi.lcd_16x2'
            ]
commands = ['rpi_shutdown = temperpi.shutdown:main',
            'rpi_reaper_ip = temperpi.reaper_ip:main',
            'rpi_lcd_16x2 = temperpi.lcd_16x2:main',
            'rpi_lcd_16x2_shutdown = temperpi.lcd_16x2_shutdown:main',
            'rpi_lcd_welcome = temperpi.lcd_welcome:main',
            'rpi_thermometer = thermometer.thermometer_f5_87:main'
            ]

setup(
    name                ='TemperPi',
    version             =__version__,
    description         = 'Python packaging for TemperPi.',
    author              = 'Mitch O\'Donnell',
    author_email        = 'devreap1@gmail.com',
    packages            = packages,
    py_modules          = py_modules,
    url                 = 'https://github.com/BuildAndDestroy/temperpi',
    license             = open('LICENSE').read(),
    install_requires    = ['netifaces'],
    entry_points        = {'console_scripts': commands},
    prefix              = '/opt/thermometer_box',
    long_description    = open('README.md').read()
)
