"""Runtime configuration, loaded from a TOML file with sane defaults.

Every key is optional. See ``deploy/config.toml`` for a documented example.
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("/etc/temperpi/config.toml")


@dataclass(frozen=True)
class LCDPins:
    """BCM GPIO numbers wired to the HD44780 LCD (4-bit mode)."""

    rs: int = 25
    e: int = 24
    d4: int = 23
    d5: int = 17
    d6: int = 21
    d7: int = 22


@dataclass(frozen=True)
class Buttons:
    """BCM GPIO numbers for the momentary switches (wired to 3V3, pulled down)."""

    read_temperature: int = 16
    shutdown: int = 20
    # Hold the shutdown button this long before the Pi powers off.
    shutdown_hold_seconds: float = 2.0
    bounce_seconds: float = 0.05


@dataclass(frozen=True)
class Sensor:
    id: str
    label: str


@dataclass(frozen=True)
class Config:
    lcd: LCDPins = field(default_factory=LCDPins)
    buttons: Buttons = field(default_factory=Buttons)
    # Explicit sensors (in display order). Empty = auto-discover all DS18B20s.
    sensors: tuple[Sensor, ...] = ()
    w1_devices_dir: Path = Path("/sys/bus/w1/devices")
    # Shown on the top line of the idle screen; the bottom line is the IPv4 address.
    idle_title: str = "Reaper-UT.com"
    preferred_interfaces: tuple[str, ...] = ("eth0", "end0", "wlan0")
    # How often the idle screen refreshes the IP address (it may change, or
    # not exist yet right after boot).
    idle_refresh_seconds: float = 30.0
    show_welcome: bool = True


def _build(cls: type, data: dict[str, Any], section: str) -> Any:
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"Unknown key(s) in [{section}]: {', '.join(sorted(unknown))}")
    return cls(**data)


def load(path: Path | None = None) -> Config:
    """Load config from ``path``; a missing default file yields defaults."""
    explicit = path is not None
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        if explicit:
            raise FileNotFoundError(path)
        log.info("No config at %s, using defaults", path)
        return Config()

    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    kwargs: dict[str, Any] = {}
    if "lcd" in raw:
        kwargs["lcd"] = _build(LCDPins, raw.pop("lcd"), "lcd")
    if "buttons" in raw:
        kwargs["buttons"] = _build(Buttons, raw.pop("buttons"), "buttons")
    if "sensors" in raw:
        kwargs["sensors"] = tuple(_build(Sensor, s, "sensors") for s in raw.pop("sensors"))
    if "w1_devices_dir" in raw:
        kwargs["w1_devices_dir"] = Path(raw.pop("w1_devices_dir"))
    if "preferred_interfaces" in raw:
        kwargs["preferred_interfaces"] = tuple(raw.pop("preferred_interfaces"))

    return _build(Config, {**raw, **kwargs}, "top level")
