#!/usr/bin/env bash
# Remove TemperPi. Leaves /etc/temperpi/config.toml and the 1-Wire overlay.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo $0" >&2
    exit 1
fi

systemctl disable --now temperpi.service 2>/dev/null || true
rm -f /etc/systemd/system/temperpi.service /etc/polkit-1/rules.d/50-temperpi.rules
if [[ -d /run/systemd/system ]]; then systemctl daemon-reload; fi
rm -rf /usr/local/lib/temperpi /var/lib/temperpi
rm -f /usr/local/bin/temperpi
if id temperpi &>/dev/null; then
    userdel temperpi
fi
echo "[*] TemperPi removed. Config left in /etc/temperpi/."
