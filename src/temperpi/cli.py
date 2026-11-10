"""``temperpi`` command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from temperpi import __version__, config, network, thermometer


def _cmd_run(cfg: config.Config, _args: argparse.Namespace) -> int:
    from temperpi import daemon

    daemon.run(cfg)
    return 0


def _cmd_temps(cfg: config.Config, _args: argparse.Namespace) -> int:
    sensors = list(cfg.sensors) or thermometer.discover(cfg.w1_devices_dir)
    if not sensors:
        print(f"No DS18B20 sensors found in {cfg.w1_devices_dir}", file=sys.stderr)
        print("Is 'dtoverlay=w1-gpio' in config.txt, and have you rebooted?", file=sys.stderr)
        return 1
    ok = True
    for sensor, result in zip(
        sensors, thermometer.read_all(sensors, cfg.w1_devices_dir), strict=True
    ):
        if isinstance(result, thermometer.SensorError):
            print(f"{sensor.label}\t{sensor.id}\tERROR: {result}")
            ok = False
        else:
            print(f"{sensor.label}\t{sensor.id}\t{result.celsius:.2f} C\t{result.fahrenheit:.2f} F")
    return 0 if ok else 1


def _cmd_ip(cfg: config.Config, _args: argparse.Namespace) -> int:
    print(network.primary_ipv4(cfg.preferred_interfaces))
    return 0


def _cmd_buttons(cfg: config.Config, _args: argparse.Namespace) -> int:
    """Print button state changes; for checking the wiring."""
    from gpiozero import Button

    b = cfg.buttons
    pins = {"read_temperature": b.read_temperature, "shutdown": b.shutdown}
    buttons = []
    print("Press the buttons (Ctrl+C to quit). Stop the temperpi service first.")
    for name, gpio in pins.items():
        btn = Button(gpio, pull_up=False)
        label = f"{name} (GPIO{gpio})"
        btn.when_pressed = lambda label=label: print(f"{label}: pressed", flush=True)
        btn.when_released = lambda label=label: print(f"{label}: released", flush=True)
        buttons.append(btn)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


def _cmd_lcd(cfg: config.Config, args: argparse.Namespace) -> int:
    """Write text to the LCD; for checking the wiring and contrast."""
    from temperpi.lcd import LCD

    lcd = LCD.from_gpio(**vars(cfg.lcd))
    try:
        lcd.show(args.top, args.bottom)
    finally:
        lcd.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="temperpi", description="TemperPi thermometer box.")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("-c", "--config", type=Path, help=f"default: {config.DEFAULT_CONFIG_PATH}")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="run the LCD/button service").set_defaults(func=_cmd_run)
    sub.add_parser("temps", help="print sensor readings").set_defaults(func=_cmd_temps)
    sub.add_parser("ip", help="print the IPv4 address shown on the LCD").set_defaults(func=_cmd_ip)
    sub.add_parser("buttons", help="print button presses (wiring test)").set_defaults(
        func=_cmd_buttons
    )
    lcd = sub.add_parser("lcd", help="write text to the LCD (wiring test)")
    lcd.add_argument("top")
    lcd.add_argument("bottom", nargs="?", default="")
    lcd.set_defaults(func=_cmd_lcd)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    cfg = config.load(args.config)
    return args.func(cfg, args)
