"""What gets drawn on the LCD. Pure functions/sequences of (top, bottom) frames."""

from __future__ import annotations

import time
from collections.abc import Iterator, Sequence

from temperpi.lcd import LCD, WIDTH, center
from temperpi.thermometer import Reading, SensorError

Frame = tuple[str, str]


def _diverge(step: int) -> str:
    """``<>`` in the middle moving apart to the edges (step 0..7)."""
    mid = WIDTH // 2
    return " " * (mid - 1 - step) + "<" + " " * (2 * step) + ">"


def _converge(step: int) -> str:
    """``>`` and ``<`` at the edges moving together (step 0..7)."""
    return " " * step + ">" + " " * (WIDTH - 2 - 2 * step) + "<"


def welcome_frames() -> Iterator[tuple[Frame, float]]:
    yield (center("Welcome To"), center("TemperPi!")), 3.0
    yield (center("Initializing"), center("Please Wait...")), 3.0
    steps = WIDTH // 2
    for cycle in range(3):
        for i in range(steps):
            a, b = _converge(i), _diverge(i)
            yield ((a, b) if cycle % 2 == 0 else (b, a)), 0.1
    yield (center("Ready!"), ""), 0.5


def format_reading(result: Reading | SensorError) -> Frame:
    if isinstance(result, SensorError):
        return f"{result.label} error", "Check sensor"
    return result.label, f"{result.celsius:5.1f}°C {result.fahrenheit:6.1f}°F"


def play(lcd: LCD, frames: Iterator[tuple[Frame, float]] | Sequence[tuple[Frame, float]]) -> None:
    for (top, bottom), hold in frames:
        lcd.show(top, bottom)
        time.sleep(hold)


def temperature_frames(results: Sequence[Reading | SensorError]) -> list[tuple[Frame, float]]:
    frames: list[tuple[Frame, float]] = [((center("Temperature"), center("C and F")), 2.0)]
    if not results:
        frames.append(((center("No sensors"), center("found")), 3.0))
    frames += [(format_reading(r), 3.0) for r in results]
    frames.append(((center("Done, son!"), center("t(-_-t)")), 2.0))
    return frames


def idle(title: str, ip: str) -> Frame:
    return center(title), center(ip)


SHUTDOWN: Frame = (center("Shutting down!"), center("Good Bye!"))
STOPPED: Frame = (center("TemperPi"), center("stopped"))
