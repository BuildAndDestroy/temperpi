#!/usr/bin/env python3
"""
-------------------------------------------------------------------------------
 Name:         Momentary Shutdown Switch

 Purpose:      This program gets installed in /etc/init.d to run as a daemon.
               It monitors the /INT signal coming from the start-stop device,
               an LTC2951-1 to start a new temperature reading procedure.
               If the LTC2951-1 asserts the /INT pin, we start a thermometer
               scan, by executing the correct python script.

               The power to the Pi will be cut when the timer of the LT2951
               runs out, or if the Pi has reached the poweroff state (Halt).
               To activate a gpio pin with the poweroff state, the
               /boot/config.txt file needs to have :
               dtoverlay=gpio-poweroff,gpiopin=27,active_low="y"

 Author:      Paul Versteeg

 Created:     15-06-2015, revised on 4-12-2015
 Copyright:   (c) Paul 2015
 Licence:     <Reaper-UT>
-------------------------------------------------------------------------------
"""

import subprocess

import lcd_16x2_shutdown
import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)  # use gpio numbering
gpio.setwarnings(False)

# I use the following two gpio pins because they are next to each other,
# and I can use a two pin header to connect the switch logic to the Pi.
INT = 20  # gpio-12 /INT interrupt to shutdown procedure

# use a weak pull_down to avoid noise issues
gpio.setup(INT, gpio.IN, pull_up_down=gpio.PUD_DOWN)


def main():
    """Execute the main function."""
    while True:
        # set an interrupt on a falling edge and wait for it to happen
        gpio.wait_for_edge(INT, gpio.FALLING)
        lcd_16x2_shutdown.main()

        subprocess.call(['/sbin/shutdown -H now'],
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
