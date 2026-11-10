from temperpi import screens
from temperpi.lcd import WIDTH
from temperpi.thermometer import Reading, SensorError


def test_all_frames_fit_display():
    frames = [f for f, _ in screens.welcome_frames()]
    frames += [f for f, _ in screens.temperature_frames([Reading("S-1", -12.34)])]
    frames += [
        screens.SHUTDOWN,
        screens.STOPPED,
        screens.idle("HarvestRangeLabs", "192.168.100.200"),
    ]
    for top, bottom in frames:
        assert len(top) <= WIDTH, top
        assert len(bottom) <= WIDTH, bottom


def test_animation_endpoints():
    assert screens._diverge(0).strip() == "<>"
    assert screens._diverge(7) == "<" + " " * 14 + ">"
    assert screens._converge(0) == ">" + " " * 14 + "<"
    assert screens._converge(7).strip() == "><"


def test_format_reading():
    top, bottom = screens.format_reading(Reading("S-1", 23.125))
    assert top == "S-1"
    assert bottom == " 23.1°C   73.6°F"


def test_format_error():
    assert screens.format_reading(SensorError("boom", "S-2")) == ("S-2 error", "Check sensor")


def test_no_sensors_message():
    texts = [f for f, _ in screens.temperature_frames([])]
    assert any("No sensors" in top for top, _ in texts)
