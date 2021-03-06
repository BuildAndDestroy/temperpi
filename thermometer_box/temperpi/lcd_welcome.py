#!/usr/bin/env python3
"""Start the LCD screen on boot.

--------------------------------------
    ___  ___  _ ____
   / _ \\/ _ \\(_) __/__  __ __
  / , _/ ___/ /\\ \\/ _ \\/ // /
 /_/|_/_/  /_/___/ .__/\\_, /
                /_/   /___/

  lcd_16x2.py
  16x2 LCD Test Script

 Author : Matt Hawkins
 Date   : 06/04/2015

 Modified by : Mitch O'Donnell
 Date        : 06/03/2017

 http://www.raspberrypi-spy.co.uk/

 Copyright 2015 Matt Hawkins

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.

--------------------------------------

 The wiring for the LCD is as follows:
 1 : GND
 2 : 5V
 3 : Contrast (0-5V)*
 4 : RS (Register Select)
 5 : R/W (Read Write)       - GROUND THIS PIN
 6 : Enable or Strobe
 7 : Data Bit 0             - NOT USED
 8 : Data Bit 1             - NOT USED
 9 : Data Bit 2             - NOT USED
 10: Data Bit 3             - NOT USED
 11: Data Bit 4
 12: Data Bit 5
 13: Data Bit 6
 14: Data Bit 7
 15: LCD Backlight +5V**
 16: LCD Backlight GND
"""

import subprocess
import time

import RPi.GPIO as gpio

# Define GPIO to LCD mapping
LCD_RS = 25
LCD_E = 24
LCD_D4 = 23
LCD_D5 = 17
LCD_D6 = 21
LCD_D7 = 22


# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


def lcd_init() -> None:
    """Initialise display"""
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode) -> None:
    """Send byte to data pins
    bits = data
    mode = True  for character
           False for command
    """

    gpio.output(LCD_RS, mode)  # RS

    # High bits
    gpio.output(LCD_D4, False)
    gpio.output(LCD_D5, False)
    gpio.output(LCD_D6, False)
    gpio.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        gpio.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        gpio.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        gpio.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        gpio.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    gpio.output(LCD_D4, False)
    gpio.output(LCD_D5, False)
    gpio.output(LCD_D6, False)
    gpio.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        gpio.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        gpio.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        gpio.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        gpio.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()


def lcd_toggle_enable() -> None:
    """Toggle enable"""
    time.sleep(E_DELAY)
    gpio.output(LCD_E, True)
    time.sleep(E_PULSE)
    gpio.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_string(message, line) -> None:
    """Send string to display"""
    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


def welcome_screen() -> None:
    """Print the welcome screen to LCD."""
    lcd_string("  Welcome To", LCD_LINE_1)
    lcd_string("   TemperPi!", LCD_LINE_2)

    time.sleep(3)  # 3 second delay

    lcd_string("  Initializing", LCD_LINE_1)
    lcd_string(" Please Wait...", LCD_LINE_2)

    time.sleep(3)  # 2 second delay

    lcd_string("       <>", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(">              <", LCD_LINE_1)
    lcd_string("      <  >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(" >            <", LCD_LINE_1)
    lcd_string("     <    >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("  >          <", LCD_LINE_1)
    lcd_string("    <      >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("   >        <", LCD_LINE_1)
    lcd_string("   <        >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("    >      <", LCD_LINE_1)
    lcd_string("  <          >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("     >    <", LCD_LINE_1)
    lcd_string(" <            >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("      >  <", LCD_LINE_1)
    lcd_string("<              >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("       ><", LCD_LINE_1)
    lcd_string("", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("       <>", LCD_LINE_1)
    lcd_string(">              <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("      <  >", LCD_LINE_1)
    lcd_string(" >            <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("     <    >", LCD_LINE_1)
    lcd_string("  >          <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("    <      >", LCD_LINE_1)
    lcd_string("   >        <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("   <        >", LCD_LINE_1)
    lcd_string("    >      <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("  <          >", LCD_LINE_1)
    lcd_string("     >    <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(" <            >", LCD_LINE_1)
    lcd_string("      >  <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("<              >", LCD_LINE_1)
    lcd_string("       ><", LCD_LINE_2)
    time.sleep(.1)

    lcd_string("", LCD_LINE_1)
    lcd_string("       <>", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(">              <", LCD_LINE_1)
    lcd_string("      <  >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(" >            <", LCD_LINE_1)
    lcd_string("     <    >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("  >          <", LCD_LINE_1)
    lcd_string("    <      >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("   >        <", LCD_LINE_1)
    lcd_string("   <        >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("    >      <", LCD_LINE_1)
    lcd_string("  <          >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("     >    <", LCD_LINE_1)
    lcd_string(" <            >", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("      >  <", LCD_LINE_1)
    lcd_string("<              >", LCD_LINE_2)
    time.sleep(.1)

    lcd_string("       ><", LCD_LINE_1)
    lcd_string("", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("       <>", LCD_LINE_1)
    lcd_string(">              <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("      <  >", LCD_LINE_1)
    lcd_string(" >            <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("     <    >", LCD_LINE_1)
    lcd_string("  >          <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("    <      >", LCD_LINE_1)
    lcd_string("   >        <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("   <        >", LCD_LINE_1)
    lcd_string("    >      <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("  <          >", LCD_LINE_1)
    lcd_string("     >    <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string(" <            >", LCD_LINE_1)
    lcd_string("      >  <", LCD_LINE_2)
    time.sleep(.1)
    lcd_string("<              >", LCD_LINE_1)
    lcd_string("       ><", LCD_LINE_2)
    time.sleep(.1)

    lcd_string("      Ready!", LCD_LINE_1)
    lcd_string("", LCD_LINE_2)


def display_website_ip():
    """Display website and ipv4."""
    lcd_byte(0x01, LCD_CMD)
    lcd_string(" Reaper-UT.com", LCD_LINE_1)
    lcd_string('  {}'.format(subprocess.getoutput(
        ['/usr/local/bin/rpi_reaper_ip'])), LCD_LINE_2)
    gpio.cleanup()


def main():
    """Main program block"""

    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)       # Use BCM GPIO numbers
    gpio.setup(LCD_E, gpio.OUT)  # E
    gpio.setup(LCD_RS, gpio.OUT)  # RS
    gpio.setup(LCD_D4, gpio.OUT)  # DB4
    gpio.setup(LCD_D5, gpio.OUT)  # DB5
    gpio.setup(LCD_D6, gpio.OUT)  # DB6
    gpio.setup(LCD_D7, gpio.OUT)  # DB7

    # Initialise display
    lcd_init()

    welcome_screen()

    time.sleep(.5)

    display_website_ip()


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
