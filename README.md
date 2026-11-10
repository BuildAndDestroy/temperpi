# TemperPi

A Raspberry Pi thermometer box. DS18B20 probes are read over 1-Wire and shown on
a 16x2 HD44780 LCD. Two momentary buttons control it:

| Button  | GPIO (BCM) | Action                                           |
|---------|-----------:|--------------------------------------------------|
| Read    | 16         | Show each sensor in °C and °F, then return to idle |
| Power   | 20         | **Hold 2 s** to show "Shutting down!" and power off |

When idle, the LCD shows a title line and the Pi's IPv4 address.

## Hardware

Wiring diagrams are in [`docs/circuits/`](docs/circuits/) (full schematic:
[`thermopi.png`](docs/circuits/thermopi.png)).

| Part                | Connection                                                       |
|---------------------|------------------------------------------------------------------|
| DS18B20 probes (×N) | Data → GPIO4, 4.7 kΩ pull-up to 3V3                              |
| 16x2 LCD            | RS 25, E 24, D4 23, D5 17, D6 21, D7 22; R/W → GND; contrast via pot |
| Buttons             | Between 3V3 and GPIO16 / GPIO20 (internal pull-downs are used)   |

All pins are configurable in `/etc/temperpi/config.toml`.

## Install

Requires Raspberry Pi OS **Bookworm or newer** (any Pi, including the Pi 5).

```bash
git clone https://github.com/BuildAndDestroy/temperpi.git
cd temperpi
sudo ./deploy/install.sh
sudo reboot            # first install only, so the 1-Wire overlay loads
```

`install.sh` is safe to re-run; it's also how you upgrade (`git pull && sudo ./deploy/install.sh`). It:

- installs `python3-gpiozero`, `python3-lgpio` and `polkitd` from apt
- adds `dtoverlay=w1-gpio` to `config.txt`
- creates an unprivileged `temperpi` system user (in the `gpio` group)
- installs the app into a venv at `/opt/temperpi/venv`
- writes `/etc/temperpi/config.toml` (never overwrites an existing one)
- installs and starts the `temperpi` systemd service, plus a polkit rule
  that only lets that user power off the Pi
- removes a TemperPi 1.x install (SysV init scripts, `/opt/thermometer_box`) if one exists

To remove it: `sudo ./deploy/uninstall.sh`.

### Optional: harden the Pi

```bash
sudo ./deploy/harden.sh <your-admin-user>
```

This requires a password for sudo and limits SSH to `<your-admin-user>` (no root,
with a login banner). It also turns on a `ufw` firewall that allows only SSH
(rate-limited) and mDNS, turns on unattended security upgrades, and locks the
legacy `pi` account. Before you close your current session, check that you can
still SSH in from a new one.

## Configuration

Edit `/etc/temperpi/config.toml`, then run `sudo systemctl restart temperpi`. The
[annotated example](deploy/config.toml) lists every option. If you remove the
`[[sensors]]` entries, every probe on the bus is found and labelled automatically.

## Commands

```bash
temperpi temps                 # print every sensor reading
temperpi ip                    # print the IP shown on the LCD
sudo systemctl stop temperpi   # free the GPIOs before using the wiring tests:
temperpi buttons               #   print button presses/releases
temperpi lcd "Hello" "World"   #   write text to the LCD

systemctl status temperpi
journalctl -u temperpi -f
```

## Troubleshooting

- **`No DS18B20 sensors found`**: check that `dtoverlay=w1-gpio` is in
  `/boot/firmware/config.txt` and that you've rebooted. Also check the 4.7 kΩ
  pull-up. `ls /sys/bus/w1/devices/` should list `28-…` entries.
- **The LCD shows blocks or nothing**: adjust the contrast potentiometer.
- **A sensor shows "error"**: the sensor ID in `config.toml` doesn't match
  `temperpi temps`, or the probe is disconnected.

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format .
```

The hardware is behind small interfaces, so the tests run on any Linux machine
without a Pi.

## License

GPL-3.0-or-later. The LCD driver is based on Matt Hawkins' raspberrypi-spy.co.uk
script (GPL-3.0).
