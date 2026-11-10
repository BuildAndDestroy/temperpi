#!/usr/bin/env bash
# Optional baseline hardening for a Raspberry Pi OS box. Safe to re-run.
#
#   sudo ./deploy/harden.sh [ADMIN_USER]
#
# ADMIN_USER (default: the user who ran sudo) is the only account allowed to
# SSH in. Make sure you can log in as that user before running this.
#
# What it does:
#   - requires a password for sudo (removes the NOPASSWD rule)
#   - SSH: banner, no root login, only ADMIN_USER may log in
#   - ufw firewall: deny incoming except SSH and mDNS (<hostname>.local)
#   - unattended security upgrades
#   - locks the legacy default 'pi' account if it exists and is not ADMIN_USER
set -euo pipefail

info() { echo "[*] $*"; }

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo $0 [ADMIN_USER]" >&2
    exit 1
fi

ADMIN_USER="${1:-${SUDO_USER:-}}"
if [[ -z $ADMIN_USER || $ADMIN_USER == root ]] || ! id "$ADMIN_USER" &>/dev/null; then
    echo "Pass an existing non-root admin user: sudo $0 <user>" >&2
    exit 1
fi
if [[ -z $(getent shadow "$ADMIN_USER" | cut -d: -f2 | tr -d '!*') ]]; then
    echo "$ADMIN_USER has no password; set one first (passwd $ADMIN_USER), or sudo will lock you out." >&2
    exit 1
fi

info "Installing packages"
apt-get update
apt-get install -y ufw unattended-upgrades

info "Requiring a password for sudo"
for f in /etc/sudoers.d/010_pi-nopasswd /etc/sudoers.d/010_*-nopasswd; do
    [[ -e $f ]] && rm -f "$f"
done
usermod -aG sudo "$ADMIN_USER"

info "Configuring SSH (only $ADMIN_USER may log in)"
cat >/etc/issue.net <<'EOF'

    #####################################################
    # Unauthorized access to this machine is prohibited #
    #  Speak with the owner first to obtain permission  #
    #####################################################

EOF
install -d -m 755 /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/10-temperpi-hardening.conf <<EOF
# Managed by temperpi/deploy/harden.sh
Banner /etc/issue.net
PermitRootLogin no
AllowUsers $ADMIN_USER
EOF
sshd -t
systemctl enable ssh
systemctl reload ssh

if id pi &>/dev/null && [[ $ADMIN_USER != pi ]]; then
    info "Locking legacy 'pi' account"
    usermod --lock --expiredate 1 pi
fi

info "Configuring firewall"
ufw default deny incoming
ufw default allow outgoing
ufw limit 22/tcp comment 'SSH'
ufw allow 5353/udp comment 'mDNS'
ufw --force enable
ufw status verbose

info "Enabling unattended security upgrades"
echo 'unattended-upgrades unattended-upgrades/enable_auto_updates boolean true' |
    debconf-set-selections
dpkg-reconfigure -f noninteractive unattended-upgrades

info "Hardening complete. Keep this session open and test SSH as $ADMIN_USER in a new one."
