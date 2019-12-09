# Installation

* Built for Raspberry Pi, Debian Buster build.

    1)  Install the hardware following the wire diagram, schematics.png
    2)  Turn on the Raspberry Pi and download the zip file to /home/pi/.
    3)  Switch to root user or use "sudo" for next command.
    4)  ./secure_rpi.sh
    5)  After reboot, move the repo to /home/heateduser/.
    6)  "sudo su" to root with your new password and change working directory to /home/heateduser/.
    7)  ./build.sh
    6)  After reboot, enjoy!

* Circuits for this build are found in the images/ directory.


###### Known Issue
    Thermometers do not work.
    Momentary switch for thermometers do not work.
    This is beta, testing continues.
