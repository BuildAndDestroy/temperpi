#!/usr/bin/env python3
"""Initilize the thermometers.

Thermometers are pulled from static files for now.
Both thermometers are read then converted to celsius and fahrenheit,
then printed out.
"""
import os
import time


class Thermometer(object):
    """docstring for thermometer"""

    def __init__(self):
        self.w1_devices = self.list_of_thermometers()

    def list_of_thermometers(self) -> list:
        """Grab a list of thermometers"""
        all_w1_devices = [device for device in os.listdir('/sys/bus/w1/devices/') if os.path.isdir(
            os.path.join('/sys/bus/w1/devices/', device)) and '28-8' in device]

        if not all_w1_devices:
            raise ValueError('No Devices Found!')

        return all_w1_devices

    def full_w1_device_directory(self) -> list:
        """Returns the full device directory to the w1 device."""
        full_path_device = []

        for device in self.w1_devices:
            full_path_device.append(f'/sys/bus/w1/devices/{device}')

        return full_path_device

    def thermometer_slave_file(self):
        """Returns the full device directory and slave file name."""
        device_slave_file = []

        for device in self.w1_devices:
            device_slave_file.append(f'/sys/bus/w1/devices/{device}/w1_slave')

        return device_slave_file


def temp_raw(therm) -> list:
    """Raw output for thermometer"""
    read_thermometer = open(therm, 'r')
    lines = read_thermometer.readlines()
    read_thermometer.close()
    return lines


def read_temp(temp_raw) -> tuple:
    """Strip down to tempurature and calculate C and F"""
    lines = temp_raw
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = temp_raw
    temp_output = lines[1].find('t=')
    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temperature_celsius = float(temp_string) / 1000.0
        temperature_fahrenheit = temperature_celsius * 9.0 / 5.0 + 32.0
        return temperature_celsius, temperature_fahrenheit


def main() -> None:
    """Load drives and print output."""
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    initilize_thermometer = Thermometer()
    for one_thermometer in initilize_thermometer.thermometer_slave_file():
        print(read_temp(temp_raw(one_thermometer)))


if __name__ == '__main__':
    main()
