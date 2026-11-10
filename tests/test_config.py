from pathlib import Path

import pytest

from temperpi import config


def test_missing_default_file_gives_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DEFAULT_CONFIG_PATH", tmp_path / "nope.toml")
    assert config.load() == config.Config()


def test_missing_explicit_file_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        config.load(tmp_path / "nope.toml")


def test_example_config_loads():
    example = Path(__file__).parent.parent / "deploy" / "config.toml"
    cfg = config.load(example)
    assert cfg.buttons.read_temperature == 16
    assert [s.label for s in cfg.sensors] == ["S-1", "S-2"]


def test_overrides(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text(
        'idle_title = "Hello"\n'
        'preferred_interfaces = ["wlan0"]\n'
        "[lcd]\nrs = 5\n"
        "[buttons]\nshutdown_hold_seconds = 0.5\n"
        '[[sensors]]\nid = "28-abc"\nlabel = "Oven"\n'
    )
    cfg = config.load(path)
    assert cfg.idle_title == "Hello"
    assert cfg.preferred_interfaces == ("wlan0",)
    assert cfg.lcd.rs == 5 and cfg.lcd.e == 24
    assert cfg.buttons.shutdown_hold_seconds == 0.5
    assert cfg.sensors == (config.Sensor("28-abc", "Oven"),)


def test_unknown_key_is_an_error(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text("[lcd]\nrss = 5\n")
    with pytest.raises(ValueError, match="rss"):
        config.load(path)
