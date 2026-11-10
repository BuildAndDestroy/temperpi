"""DS18B20 1-Wire temperature sensors, read through the kernel's w1-therm driver.

Requires ``dtoverlay=w1-gpio`` in the Pi's config.txt (data line on GPIO4).
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from temperpi.config import Sensor

DS18B20_FAMILY = "28-"


class SensorError(RuntimeError):
    def __init__(self, message: str, label: str = "") -> None:
        super().__init__(message)
        self.label = label


@dataclass(frozen=True)
class Reading:
    label: str
    celsius: float

    @property
    def fahrenheit(self) -> float:
        return self.celsius * 9.0 / 5.0 + 32.0


def discover(devices_dir: Path) -> list[Sensor]:
    """Find every DS18B20 on the bus, labelled S-1, S-2, ... in ID order."""
    ids = sorted(p.name for p in devices_dir.glob(f"{DS18B20_FAMILY}*"))
    return [Sensor(id=sid, label=f"S-{n}") for n, sid in enumerate(ids, start=1)]


def parse_w1_slave(text: str) -> float:
    """Parse the contents of a ``w1_slave`` file into degrees Celsius.

    Example::

        72 01 4b 46 7f ff 0e 10 57 : crc=57 YES
        72 01 4b 46 7f ff 0e 10 57 t=23125
    """
    lines = text.strip().splitlines()
    if len(lines) < 2 or not lines[0].rstrip().endswith("YES"):
        raise SensorError("CRC check failed")
    _, sep, millis = lines[1].rpartition("t=")
    if not sep:
        raise SensorError("No temperature in sensor output")
    try:
        return int(millis) / 1000.0
    except ValueError as exc:
        raise SensorError(f"Bad temperature value {millis!r}") from exc


def read(sensor: Sensor, devices_dir: Path, retries: int = 5, delay: float = 0.2) -> Reading:
    path = devices_dir / sensor.id / "w1_slave"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return Reading(sensor.label, parse_w1_slave(path.read_text()))
        except (OSError, SensorError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay)
    raise SensorError(f"{sensor.label} ({sensor.id}): {last_error}", sensor.label) from last_error


def read_all(sensors: Iterable[Sensor], devices_dir: Path) -> list[Reading | SensorError]:
    """Read every sensor; failures are returned in place rather than raised."""
    results: list[Reading | SensorError] = []
    for sensor in sensors:
        try:
            results.append(read(sensor, devices_dir))
        except SensorError as exc:
            results.append(exc)
    return results
