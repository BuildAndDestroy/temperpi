"""Minimal HD44780 16x2 character LCD driver, 4-bit mode, write-only.

Based on the raspberrypi-spy.co.uk script by Matt Hawkins (2015, GPL-3.0).

LCD wiring:
     1 GND              9  D2 (unused)
     2 5V              10  D3 (unused)
     3 Contrast (pot)  11  D4
     4 RS              12  D5
     5 R/W -> GND      13  D6
     6 E               14  D7
     7 D0 (unused)     15  Backlight +5V
     8 D1 (unused)     16  Backlight GND
"""

from __future__ import annotations

import threading
import time
from typing import Protocol

WIDTH = 16
LINE_ADDRESSES = (0x80, 0xC0)

_CLEAR = 0x01
_PULSE = 0.0005
_DELAY = 0.0005
_CLEAR_DELAY = 0.002  # clear/home take ~1.5 ms

# Characters that exist in the HD44780 A00 ROM at a non-ASCII code.
_CHARMAP = {"°": 0xDF}


class OutputPin(Protocol):
    value: bool | int

    def close(self) -> None: ...


def encode(text: str) -> bytes:
    """Pad/truncate to the display width and map to the LCD's character ROM."""
    text = text[:WIDTH].ljust(WIDTH)
    return bytes(_CHARMAP.get(ch, ord(ch) if ord(ch) < 0x80 else ord("?")) for ch in text)


def center(text: str) -> str:
    return text[:WIDTH].center(WIDTH).rstrip()


class LCD:
    """HD44780 display. Thread-safe: each call holds an internal lock."""

    def __init__(
        self,
        rs: OutputPin,
        e: OutputPin,
        data: tuple[OutputPin, OutputPin, OutputPin, OutputPin],
    ) -> None:
        self._rs = rs
        self._e = e
        self._data = data
        self._lock = threading.Lock()
        self._init_display()

    @classmethod
    def from_gpio(cls, rs: int, e: int, d4: int, d5: int, d6: int, d7: int) -> LCD:
        from gpiozero import DigitalOutputDevice

        def pin(n: int) -> DigitalOutputDevice:
            return DigitalOutputDevice(n)

        return cls(pin(rs), pin(e), (pin(d4), pin(d5), pin(d6), pin(d7)))

    def _init_display(self) -> None:
        with self._lock:
            for cmd in (0x33, 0x32, 0x28, 0x0C, 0x06):
                # 0x33/0x32: force 4-bit mode; 0x28: 2 lines 5x8;
                # 0x0C: display on, no cursor; 0x06: increment, no shift.
                self._write(cmd, char=False)
            self._write(_CLEAR, char=False)
            time.sleep(_CLEAR_DELAY)

    def _nibble(self, value: int) -> None:
        for bit, pin in enumerate(self._data):
            pin.value = bool(value >> bit & 1)
        time.sleep(_DELAY)
        self._e.value = True
        time.sleep(_PULSE)
        self._e.value = False
        time.sleep(_DELAY)

    def _write(self, byte: int, *, char: bool) -> None:
        self._rs.value = char
        self._nibble(byte >> 4)
        self._nibble(byte & 0x0F)

    def clear(self) -> None:
        with self._lock:
            self._write(_CLEAR, char=False)
            time.sleep(_CLEAR_DELAY)

    def write_line(self, line: int, text: str) -> None:
        with self._lock:
            self._write(LINE_ADDRESSES[line], char=False)
            for byte in encode(text):
                self._write(byte, char=True)

    def show(self, top: str = "", bottom: str = "") -> None:
        """Replace both lines."""
        self.write_line(0, top)
        self.write_line(1, bottom)

    def close(self) -> None:
        for pin in (self._rs, self._e, *self._data):
            pin.close()
