from pathlib import Path

import pytest

from temperpi import thermometer
from temperpi.config import Sensor

GOOD = "72 01 4b 46 7f ff 0e 10 57 : crc=57 YES\n72 01 4b 46 7f ff 0e 10 57 t=23125\n"
BAD_CRC = "72 01 4b 46 7f ff 0e 10 57 : crc=57 NO\n72 01 4b 46 7f ff 0e 10 57 t=23125\n"
NEGATIVE = "5e ff 4b 46 7f ff 0c 10 1c : crc=1c YES\n5e ff 4b 46 7f ff 0c 10 1c t=-10125\n"


def make_sensor(root: Path, sensor_id: str, contents: str) -> None:
    (root / sensor_id).mkdir()
    (root / sensor_id / "w1_slave").write_text(contents)


def test_parse_good():
    assert thermometer.parse_w1_slave(GOOD) == pytest.approx(23.125)


def test_parse_negative():
    assert thermometer.parse_w1_slave(NEGATIVE) == pytest.approx(-10.125)


@pytest.mark.parametrize("text", [BAD_CRC, "", "garbage", "x YES\nno temp here"])
def test_parse_rejects_bad_input(text):
    with pytest.raises(thermometer.SensorError):
        thermometer.parse_w1_slave(text)


def test_fahrenheit():
    assert thermometer.Reading("S-1", 100.0).fahrenheit == pytest.approx(212.0)
    assert thermometer.Reading("S-1", -40.0).fahrenheit == pytest.approx(-40.0)


def test_discover_only_ds18b20_sorted(tmp_path):
    for name in ("28-80000007b187", "28-80000003f3f5", "w1_bus_master1", "10-000801b5"):
        (tmp_path / name).mkdir()
    assert thermometer.discover(tmp_path) == [
        Sensor("28-80000003f3f5", "S-1"),
        Sensor("28-80000007b187", "S-2"),
    ]


def test_read_all_reports_failures_in_place(tmp_path, monkeypatch):
    monkeypatch.setattr(thermometer.time, "sleep", lambda _s: None)
    make_sensor(tmp_path, "28-aaa", GOOD)
    make_sensor(tmp_path, "28-bbb", BAD_CRC)
    sensors = [Sensor("28-aaa", "A"), Sensor("28-bbb", "B"), Sensor("28-missing", "C")]

    good, bad_crc, missing = thermometer.read_all(sensors, tmp_path)

    assert isinstance(good, thermometer.Reading)
    assert good.celsius == pytest.approx(23.125)
    assert isinstance(bad_crc, thermometer.SensorError) and bad_crc.label == "B"
    assert isinstance(missing, thermometer.SensorError) and missing.label == "C"


def test_read_recovers_after_bad_crc(tmp_path, monkeypatch):
    make_sensor(tmp_path, "28-aaa", BAD_CRC)
    path = tmp_path / "28-aaa" / "w1_slave"
    monkeypatch.setattr(thermometer.time, "sleep", lambda _s: path.write_text(GOOD))
    assert thermometer.read(Sensor("28-aaa", "A"), tmp_path).celsius == pytest.approx(23.125)
