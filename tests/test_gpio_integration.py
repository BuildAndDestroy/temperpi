"""Run the real daemon wiring (gpiozero Buttons + LCD pins) on gpiozero's mock pins.

Skipped where gpiozero isn't installed. In CI this also runs on Raspberry Pi OS
userland with the gpiozero/lgpio packages from the Raspberry Pi apt archive.
"""

import threading
import time
import types

import pytest

gpiozero = pytest.importorskip("gpiozero")
from gpiozero.pins.mock import MockFactory  # noqa: E402

from temperpi import config, daemon, screens  # noqa: E402


@pytest.fixture
def mock_pins(monkeypatch):
    factory = MockFactory()
    monkeypatch.setattr(gpiozero.Device, "pin_factory", factory)
    yield factory
    factory.reset()


@pytest.fixture
def running(mock_pins, monkeypatch, tmp_path):
    # signal.signal only works on the main thread; capture the handlers instead.
    handlers = {}
    monkeypatch.setattr(daemon.signal, "signal", handlers.__setitem__)
    # Skip screen hold delays without touching the global time module.
    monkeypatch.setattr(screens, "time", types.SimpleNamespace(sleep=lambda _s: None))
    monkeypatch.setattr(daemon.network, "primary_ipv4", lambda _p: "10.0.0.2")

    shown, powered_off = [], []
    real_show = daemon.LCD.show
    monkeypatch.setattr(
        daemon.LCD, "show", lambda self, t="", b="": (shown.append((t, b)), real_show(self, t, b))
    )
    monkeypatch.setattr(daemon, "power_off", lambda: powered_off.append(True))

    cfg = config.Config(
        buttons=config.Buttons(shutdown_hold_seconds=0.3),
        w1_devices_dir=tmp_path,
        show_welcome=False,
    )
    thread = threading.Thread(target=daemon.run, args=(cfg,), daemon=True)
    thread.start()
    assert _wait_for(lambda: screens.idle("HarvestRangeLabs", "10.0.0.2") in shown)
    yield types.SimpleNamespace(pins=mock_pins, shown=shown, powered_off=powered_off, thread=thread)

    if thread.is_alive():  # stop it the way systemd would
        handlers[daemon.signal.SIGTERM](daemon.signal.SIGTERM, None)
        thread.join(5)
        assert not thread.is_alive()
        assert shown[-1] == screens.STOPPED


def _wait_for(cond, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(0.02)
    return False


def _tap(pin, hold=0.1):
    pin.drive_high()
    time.sleep(hold)
    pin.drive_low()


def test_read_button_shows_temperatures_then_idle(running):
    _tap(running.pins.pin(16))
    assert _wait_for(lambda: screens.temperature_frames([])[-1][0] in running.shown)
    assert _wait_for(lambda: running.shown[-1] == screens.idle("HarvestRangeLabs", "10.0.0.2"))
    assert not running.powered_off


def test_shutdown_needs_a_hold(running):
    _tap(running.pins.pin(20), hold=0.05)
    time.sleep(0.6)
    assert not running.powered_off

    running.pins.pin(20).drive_high()
    assert _wait_for(lambda: running.powered_off)
    running.thread.join(5)
    assert not running.thread.is_alive()
    assert running.shown[-1] == screens.SHUTDOWN
