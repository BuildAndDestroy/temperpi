import pytest

from temperpi import lcd as lcd_mod
from temperpi.lcd import LCD, encode


class FakePin:
    def __init__(self, name, log):
        self.name, self.log, self._value, self.closed = name, log, False, False

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = bool(v)
        if self.name == "e" and self._value:  # latch on rising edge of E
            self.log.append(self.log_snapshot())

    def close(self):
        self.closed = True


class Bus:
    """Records each (rs, nibble) latched on the E line."""

    def __init__(self):
        self.latched = []
        self.rs = FakePin("rs", self.latched)
        self.e = FakePin("e", self.latched)
        self.data = tuple(FakePin(f"d{i}", self.latched) for i in (4, 5, 6, 7))
        self.e.log_snapshot = lambda: (
            self.rs.value,
            sum(int(p.value) << i for i, p in enumerate(self.data)),
        )

    def bytes_written(self):
        pairs = zip(self.latched[::2], self.latched[1::2], strict=True)
        return [(hi[0], hi[1] << 4 | lo[1]) for hi, lo in pairs]


@pytest.fixture
def bus(monkeypatch):
    monkeypatch.setattr(lcd_mod.time, "sleep", lambda _s: None)
    return Bus()


def test_init_sequence(bus):
    LCD(bus.rs, bus.e, bus.data)
    assert bus.bytes_written() == [
        (False, 0x33),
        (False, 0x32),
        (False, 0x28),
        (False, 0x0C),
        (False, 0x06),
        (False, 0x01),
    ]


def test_write_line_sets_address_then_padded_chars(bus):
    display = LCD(bus.rs, bus.e, bus.data)
    bus.latched.clear()
    display.write_line(1, "Hi")

    written = bus.bytes_written()
    assert written[0] == (False, 0xC0)
    assert written[1:] == [(True, b) for b in b"Hi" + b" " * 14]


def test_encode_truncates_pads_and_maps_degree():
    assert encode("x" * 20) == b"x" * 16
    assert encode("23°C") == b"23\xdfC" + b" " * 12
    assert encode("é")[0] == ord("?")


def test_close_releases_all_pins(bus):
    LCD(bus.rs, bus.e, bus.data).close()
    assert all(p.closed for p in (bus.rs, bus.e, *bus.data))
