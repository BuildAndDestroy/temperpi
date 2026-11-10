#!/usr/bin/env bash
# Install or upgrade TemperPi on Raspberry Pi OS (Bookworm or newer).
# Safe to re-run. Usage: sudo ./deploy/install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX=/opt/temperpi
SERVICE_USER=temperpi
LEGACY_INIT_SCRIPTS=(LCD_Welcome momentary_shutdown momentary_start_stop)

info() { echo "[*] $*"; }
warn() { echo "[!] $*" >&2; }

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo $0" >&2
    exit 1
fi

boot_config() {
    # Bookworm moved config.txt into /boot/firmware.
    for f in /boot/firmware/config.txt /boot/config.txt; do
        [[ -f $f ]] && { echo "$f"; return; }
    done
    return 1
}

remove_legacy_install() {
    # TemperPi 1.x used SysV init scripts and /opt/thermometer_box.
    local name
    for name in "${LEGACY_INIT_SCRIPTS[@]}"; do
        if [[ -e /etc/init.d/$name ]]; then
            info "Removing legacy init script $name"
            systemctl disable --now "$name" 2>/dev/null || true
            update-rc.d -f "$name" remove >/dev/null 2>&1 || true
            rm -f "/etc/init.d/$name"
        fi
    done
    if [[ -d /opt/thermometer_box ]]; then
        info "Removing legacy /opt/thermometer_box"
        rm -rf /opt/thermometer_box
    fi
}

install_packages() {
    info "Installing system packages"
    apt-get update
    # gpiozero/lgpio come from apt so they match the Pi's kernel and hardware.
    apt-get install -y python3-venv python3-gpiozero python3-lgpio polkitd
}

enable_one_wire() {
    local cfg
    if ! cfg=$(boot_config); then
        warn "config.txt not found; add 'dtoverlay=w1-gpio' manually"
        return
    fi
    if grep -Eq '^\s*dtoverlay=w1-gpio' "$cfg"; then
        info "1-Wire already enabled in $cfg"
    else
        info "Enabling 1-Wire (GPIO4) in $cfg"
        # Drop the broken line 1.x wrote (it used an en dash, so never worked).
        sed -i '/^dtoverlay=w1–gpio$/d' "$cfg"
        echo "dtoverlay=w1-gpio" >>"$cfg"
        NEEDS_REBOOT=1
    fi
}

create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        info "Creating system user $SERVICE_USER"
        useradd --system --no-create-home --home-dir /nonexistent \
            --shell /usr/sbin/nologin --groups gpio "$SERVICE_USER"
    else
        usermod -aG gpio "$SERVICE_USER"
    fi
}

install_app() {
    info "Installing TemperPi into $PREFIX/venv"
    # System site packages give the venv apt's gpiozero + lgpio.
    python3 -m venv --system-site-packages "$PREFIX/venv"
    "$PREFIX/venv/bin/pip" install --quiet --upgrade pip
    "$PREFIX/venv/bin/pip" install --quiet --upgrade "$REPO_DIR"
    ln -sf "$PREFIX/venv/bin/temperpi" /usr/local/bin/temperpi
}

install_config() {
    install -d -m 755 /etc/temperpi
    if [[ -f /etc/temperpi/config.toml ]]; then
        info "Keeping existing /etc/temperpi/config.toml"
    else
        install -m 644 "$REPO_DIR/deploy/config.toml" /etc/temperpi/config.toml
    fi
}

install_service() {
    info "Installing systemd service"
    install -m 644 "$REPO_DIR/deploy/temperpi.service" /etc/systemd/system/temperpi.service
    install -d -m 755 /etc/polkit-1/rules.d
    install -m 644 "$REPO_DIR/deploy/50-temperpi.rules" /etc/polkit-1/rules.d/50-temperpi.rules
    systemctl daemon-reload
    systemctl enable temperpi.service
    systemctl restart temperpi.service
}

NEEDS_REBOOT=0
remove_legacy_install
install_packages
enable_one_wire
create_user
install_app
install_config
install_service

info "Done. Status: systemctl status temperpi | Logs: journalctl -u temperpi -f"
if [[ $NEEDS_REBOOT -eq 1 ]]; then
    warn "Reboot required for the thermometers (1-Wire) to appear: sudo reboot"
fi
