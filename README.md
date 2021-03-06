# Installation

* Built for Raspberry Pi, Debian Buster build.

    1)  Install the hardware following the wire diagram, schematics.png
    2)  After a clean Raspbian install, turn on the Raspberry pi and login as default "pi" user.
    3)  sudo apt install git -y
    4)  sudo su 
    5)  cd /opt/ && git clone https://github.com/BuildAndDestroy/temperpi.git
    6)  cd temperpi && ./secure.sh # Your keyboard will change and reboot pi. Just cd back into temperpi as root.
    7)  ./build.sh
    8)  After reboot, enjoy!

# Now GA! Install works!

*Known Issues*
* Circuits for this build are found in the images/ directory.
* Circuit for thermometer is wrong, these need to be plugged into 3.3v.
* Current diagram shows a feed off of the potentiomter. This is wrong.
