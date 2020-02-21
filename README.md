# Installation

* Built for Raspberry Pi, Debian Buster build.

    1)  Install the hardware following the wire diagram, schematics.png
    2)  After a clean Raspbian install, turn on the Raspberry Pi and download git repo to /opt/.
    3)  Switch to root user and run ./secure_rpi.sh
    4)  After reboot, "sudo su" to root with your new password and change working directory to /opt/.
    5)  ./build.sh
    6)  After reboot, enjoy!

# Now GA! Install works!

*Known Issues*
* Circuits for this build are found in the images/ directory.
* Circuit for thermometer is wrong, these need to be plugged into 3.3v.
* Current diagram shows a feed off of the potentiomter. This is wrong.
