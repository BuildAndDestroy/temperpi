#!/bin/bash

###########################
#        TemperPi         #
# Secure the Raspberry Pi #
###########################

function run_as_root() {
    if [[ $(id -u) != 0 ]]; then
        echo '[*] Must be ran as root.'
        exit
    fi
}

function create_pi_password () {
    echo '[*] Type in user "pi" password.'
    read -sp "Password: " password_pi_variable
}

function set_pi_password() { #  Set the new password for the pi user.
    echo -e '[*] Changing user "pi" password'
    echo -e "$password_pi_variable\n$password_pi_variable\n" | sudo passwd pi
}

function create_root_password() {
    echo '[*] Type in user "root" password.'
    read -sp "Password: " password_root_variable
}

function set_root_password() { #  Set the new password for the root user.
    echo -e '[*] Changing user "root" password'
    echo -e "$password_root_variable\n$password_root_variable\n" | sudo passwd root
}

function create_heateduser_password() {
    echo '[*] Type in user "heateduser" password.'
    read -sp "Password: " password_heateduser_variable
}

function creat_heateduser_user() {
    echo -e '[*] Creating user heateduser'
    sudo /usr/sbin/useradd heateduser -m -s /bin/bash -U
    echo -e "$password_heateduser_variable\n$password_heateduser_variable\n" | passwd heateduser
    sudo usermod -a -G adm,dialout,cdrom,sudo,audio,video,plugdev,games,users,input,netdev,gpio,i2c,spi heateduser
}

function set_keyboard_english() {
    echo -e '[*] Setting Keyboard to English (US)'
    sed -i 's/gb/us/g' /etc/default/keyboard
}

function secure_sudo() {
    sed -i 's/NOPASSWD/PASSWD/g' /etc/sudoers.d/010_pi-nopasswd
    mv /etc/sudoers.d/010_pi-nopasswd /etc/sudoers.d/010_pi-passwd
    touch /etc/sudoers.d/010_heateduser-passwd
    cat /etc/sudoers.d/010_pi-passwd > /etc/sudoers.d/010_heateduser-passwd
    sed -i 's/pi/heateduser/g' /etc/sudoers.d/010_heateduser-passwd
}

function configure_sshd() {
    echo "" > /etc/issue.net
    echo "               #####################################################" >> /etc/issue.net
    echo "               # Unauthorized access to this machine is prohibited #" >> /etc/issue.net
    echo "               #   Speak with the owner first to obtain Permission #" >> /etc/issue.net
    echo "               #####################################################" >> /etc/issue.net
    echo "" >> /etc/issue.net
    echo "" >> /etc/issue.net
    echo "" >> /etc/issue.net
    echo "" >> /etc/issue.net
    sed -i 's/#Banner\ none/Banner\ \/etc\/issue.net/g' /etc/ssh/sshd_config
    echo -e "AllowUsers heateduser" >> /etc/ssh/sshd_config
    echo -e "DenyUsers pi" >> /etc/ssh/sshd_config
    sudo systemctl enable ssh
    sudo systemctl restart ssh
}

function install_firewall() {
    sudo apt-get install ufw -y
    sudo ufw enable
    sudo ufw allow 22/tcp
    sudo ufw status
}

function install_iptables() {
    sudo apt-get install iptables-persistent -y
}

function reboot_pi() {
    echo '[*] Rebooting the pi in 5 seconds.'
    sleep 5
    reboot
}

################################
# Functions to run on execute. #
################################

run_as_root
create_pi_password
set_pi_password
set_keyboard_english
create_heateduser_password
creat_heateduser_user
create_root_password
set_root_password
configure_sshd
secure_sudo
install_iptables
install_firewall
reboot_pi