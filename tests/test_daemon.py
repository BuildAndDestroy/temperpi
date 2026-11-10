import pytest

from temperpi import daemon as daemon_mod
from temperpi import screens
from temperpi.config import Config
from temperpi.daemon import Daemon, Event


class FakeLCD:
    def __init__(self):
        self.shown = []

    def show(self, top="", bottom=""):
        self.shown.append((top, bottom))


@pytest.fixture
def d(tmp_path, monkeypatch):
    monkeypatch.setattr(screens.time, "sleep", lambda _s: None)
    monkeypatch.setattr(daemon_mod.network, "primary_ipv4", lambda _p: "10.1.2.3")
    cfg = Config(w1_devices_dir=tmp_path, show_welcome=False)
    return Daemon(cfg, FakeLCD())


def test_starts_on_idle_and_stops(d):
    d.events.put(Event.STOP)
    d.run()
    assert d.lcd.shown[0] == screens.idle("HarvestRangeLabs", "10.1.2.3")
    assert d.lcd.shown[-1] == screens.STOPPED


def test_read_then_back_to_idle_and_drops_repeat_presses(d, monkeypatch):
    calls = []
    monkeypatch.setattr(d, "show_temperatures", lambda: calls.append(1))
    for ev in (Event.READ, Event.READ, Event.READ, Event.STOP):
        d.events.put(ev)
    d.run()
    assert calls == [1]
    assert d.lcd.shown[-2] == screens.idle("HarvestRangeLabs", "10.1.2.3")


def test_shutdown_shows_message_and_powers_off(d, monkeypatch):
    powered_off = []
    monkeypatch.setattr(daemon_mod, "power_off", lambda: powered_off.append(True))
    d.events.put(Event.SHUTDOWN)
    d.run()
    assert d.lcd.shown[-1] == screens.SHUTDOWN
    assert powered_off == [True]
