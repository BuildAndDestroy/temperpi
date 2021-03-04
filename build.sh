#!/bin/bash

function check_root() { #  Best To Run This As Root
    if [ $(id -u) != 0 ];
       then echo "Please run as root"
       exit
    fi
}

function check_working_directory() { #  Deploy in /opt/, or else!
    if [ $(pwd) != '/opt' ]; then
        echo '[*] Please git clone or unzip in the /opt/ directory. Then run again.'
        exit
    fi
}

function build_directories_scripts() { #  Build Directories / Move Scripts
    mv /opt/temperpi/All_init_Files/* /etc/init.d/
    rm -rf /opt/temperpi/All_init_Files
}

function init_thermometer_hardware() { #  init gpio pins on boot
    echo "dtoverlay=w1-gpio" >> /boot/config.txt
}

function services_enabled() { #  Enable the TemperPi services
    systemctl start LCD_Welcome
    systemctl enable LCD_Welcome

    systemctl start momentary_shutdown
    systemctl enable momentary_shutdown

    systemctl start momentary_start_stop
    systemctl enable momentary_start_stop
}

function permissions_aliases() { #  Set File Permissions

    chmod 755 /opt/temperpi/*
    chmod 755 /opt/temperpi/thermometer/*
    chmod 755 /opt/temperpi/setup.py
    chmod 755 /etc/init.d/LCD_Welcome
    chmod 755 /etc/init.d/momentary_shutdown
    chmod 755 /etc/init.d/momentary_start_stop
    chown -R root:root /etc/init.d/LCD_Welcome
    chown -R root:root /etc/init.d/momentary_shutdown
    chown -R root:root /etc/init.d/momentary_start_stop
    chown -R heateduser:heateduser /opt/temperpi
}

function update_apt() { #  Update apt repo for up to date packaging
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt-get dist-upgrade -y
    sudo apt-get autoclean -y
    sudo apt-get autoremove -y
}

function install_modules() { #  Install Python modules required for TemperPi
    sudo apt-get install python3-pip -y
    sudo apt-get install python3-dev -y
    sudo apt-get install python3-rpi.gpio -y
    sudo apt-get install rpi.gpio -y
    sudo apt-get install iptables-persistent -y
    cd /opt/temperpi/ && pip3 install -r requirements.txt
}

function update_firewall_thermometer() { #  Update the firewall rules to secure Debian.
    # sudo ufw allow in on eth0 to 224.0.0.1
    # sudo ufw allow in on eth0 to 224.0.0.251
    # sudo ufw allow out proto udp to 224.0.0.0/24
    # sudo ufw allow in proto udp to 224.0.0.0/24
    sudo iptables -A INPUT -p icmp -m icmp --icmp-type 8 -j REJECT
    sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT
    sudo iptables -A FORWARD -i eth0 -m conntrack --ctstate NEW -j ACCEPT
    sudo iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j LOG  --log-prefix "INPUT_REL_EST " --log-level 7
    sudo iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    # -A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    sed -i 's/-A\ ufw-before-input\ -m\ conntrack\ --ctstate\ RELATED,ESTABLISHED\ -j\ ACCEPT/#\ -A\ ufw-before-input\ -m\ conntrack\ --ctstate\ RELATED,ESTABLISHED\ -j\ ACCEPT/g' /etc/iptables/rules.v4
    sed -i 's/-A\ ufw-before-input\ -m\ conntrack\ --ctstate\ INVALID\ -j\ DROP/#\ -A\ ufw-before-input\ -m\ conntrack\ --ctstate\ INVALID\ -j\ DROP/g' /etc/iptables/rules.v4
    sudo iptables -P OUTPUT ACCEPT
    sudo ufw reload
}

function install_temperpi() { #  Install The Python Module for TemperPi
    echo '[*] Installing temperpi into Python3.'
    cd /opt/temperpi/ && pip3 install .
}

function reboot_pi() { #  Reboot the Pi
    echo '[*] Rebooting the pi.'
    sleep 3
    reboot
}

###############################
# Functions to run on execute #
###############################


check_root
check_working_directory
build_directories_scripts
permissions_aliases
install_modules
update_apt
init_thermometer_hardware
install_temperpi
services_enabled
update_firewall_thermometer
reboot_pi
