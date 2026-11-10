#!/usr/bin/env bash
# Install TemperPi into a Raspberry Pi OS-like userland and verify the result.
#
# Runs as root inside a debian:<suite> container (arm64 natively, armhf under
# QEMU in CI). Adds the Raspberry Pi apt archive, which is what Raspberry Pi OS
# layers on Debian and where gpiozero/lgpio come from on a real Pi, then runs
# deploy/install.sh exactly as a user would.
#
# Usage: pi-os-smoke.sh <repo-dir> [wheel]
#   Installs from source and runs every check; if a wheel is given, it is then
#   installed fresh as well (the "install a release" path).
set -euo pipefail

REPO=$(cd "$1" && pwd)
WHEEL=${2:-}
# shellcheck source=/dev/null
SUITE=$(. /etc/os-release && echo "$VERSION_CODENAME")
export DEBIAN_FRONTEND=noninteractive
KEYRING_DEB=raspberrypi-archive-keyring_2025.1+rpt1_all.deb
KEYRING_SHA256=2e727149d7acb8cc7f604e66d0049161039c8aa1eaf1175e54f9e69d963d60e4

step() { echo "::group::$*"; }
end() { echo "::endgroup::"; }
fail() { echo "::error::$*"; exit 1; }

step "Raspberry Pi OS userland ($SUITE, $(dpkg --print-architecture))"
apt-get update -qq
apt-get install -y -qq ca-certificates curl systemd >/dev/null
# Bootstrap trust the way Pi OS images do: the raspberrypi-archive-keyring
# package (pinned by hash). The legacy raspberrypi.gpg.key download has a SHA-1
# binding signature, which trixie's apt verifier (sqv) rejects.
curl -fsSLo /tmp/keyring.deb "https://archive.raspberrypi.com/debian/pool/main/r/raspberrypi-archive-keyring/$KEYRING_DEB"
echo "$KEYRING_SHA256  /tmp/keyring.deb" | sha256sum -c --quiet
dpkg -i /tmp/keyring.deb >/dev/null
echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.pgp]" \
    "http://archive.raspberrypi.com/debian $SUITE main" >/etc/apt/sources.list.d/raspi.list
# What Raspberry Pi OS provides on a fresh image.
mkdir -p /boot/firmware
printf '[all]\ndtparam=audio=on\n' >/boot/firmware/config.txt
getent group gpio >/dev/null || groupadd --system gpio
end

step "deploy/install.sh (from source)"
"$REPO/deploy/install.sh"
end

step "Verify install"
VENV=/usr/local/lib/temperpi/venv
temperpi --version
"$VENV/bin/python" - <<'EOF'
from importlib.metadata import version
import gpiozero, lgpio, temperpi
print(f"gpiozero {version('gpiozero')} from {gpiozero.__file__}")
print(f"lgpio from {lgpio.__file__}")
assert gpiozero.__file__.startswith("/usr/lib/python3/"), "gpiozero should come from apt"
print(f"temperpi {temperpi.__version__} from {temperpi.__file__}")
EOF
[[ $(grep -c '^dtoverlay=w1-gpio$' /boot/firmware/config.txt) -eq 1 ]] || fail "w1-gpio overlay missing"
id -nG temperpi | grep -qw gpio || fail "temperpi user not in gpio group"
[[ -L /etc/systemd/system/multi-user.target.wants/temperpi.service ]] || fail "service not enabled"
[[ -f /etc/polkit-1/rules.d/50-temperpi.rules ]] || fail "polkit rule missing"
[[ -f /etc/temperpi/config.toml ]] || fail "config missing"
systemd-analyze verify /etc/systemd/system/temperpi.service
end

step "Re-run install.sh (idempotent, keeps config)"
echo '# local edit' >>/etc/temperpi/config.toml
"$REPO/deploy/install.sh"
[[ $(grep -c '^dtoverlay=w1-gpio$' /boot/firmware/config.txt) -eq 1 ]] || fail "overlay duplicated"
grep -q '# local edit' /etc/temperpi/config.toml || fail "config was overwritten"
end

step "Read fake DS18B20 sensors as the service user"
W1=$(mktemp -d)
for id in 28-80000007b187 28-80000003f3f5; do
    mkdir "$W1/$id"
    printf '72 01 4b 46 7f ff 0e 10 57 : crc=57 YES\n72 01 4b 46 7f ff 0e 10 57 t=23125\n' \
        >"$W1/$id/w1_slave"
done
chmod -R a+rX "$W1"
sed "s|^# w1_devices_dir = .*|w1_devices_dir = \"$W1\"|" /etc/temperpi/config.toml >"$W1/config.toml"
out=$(runuser -u temperpi -- temperpi -c "$W1/config.toml" temps)
echo "$out"
[[ $(grep -c '23.12 C' <<<"$out") -eq 2 ]] || fail "unexpected sensor output"
end

step "Test suite against the installed package and apt gpiozero"
"$VENV/bin/pip" install --quiet pytest
# Copy the tests away from src/ so they import the installed package.
SUITE_DIR=$(mktemp -d)
mkdir "$SUITE_DIR/deploy"
cp -r "$REPO/tests" "$SUITE_DIR/"
cp "$REPO/deploy/config.toml" "$SUITE_DIR/deploy/" # read by test_config
(cd "$SUITE_DIR" && "$VENV/bin/python" -m pytest -q -p no:cacheprovider tests)
end

step "deploy/uninstall.sh"
"$REPO/deploy/uninstall.sh"
[[ ! -e $VENV && ! -e /etc/systemd/system/temperpi.service ]] || fail "uninstall left files"
! id temperpi &>/dev/null || fail "user not removed"
end

if [[ -n $WHEEL ]]; then
    step "Fresh install from wheel $(basename "$WHEEL")"
    TEMPERPI_PACKAGE=$(realpath "$WHEEL") "$REPO/deploy/install.sh"
    runuser -u temperpi -- temperpi --version
    "$VENV/bin/pip" show temperpi >"$W1/show.txt"
    grep -q "^Location: $VENV/" "$W1/show.txt" || fail "wheel not installed into venv"
    "$REPO/deploy/uninstall.sh"
    end
fi

echo "Pi OS smoke test passed ($SUITE, $(dpkg --print-architecture))"
