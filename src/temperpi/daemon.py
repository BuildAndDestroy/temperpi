"""The TemperPi service: one process that owns the LCD and both buttons.

Button presses only enqueue events; the main loop is the only thing that
touches the display, so screens never interleave.
"""

from __future__ import annotations

import logging
import queue
import signal

# Only used for the fixed poweroff command in power_off().
import subprocess  # nosec B404
from enum import Enum, auto
from types import FrameType

from temperpi import network, screens, thermometer
from temperpi.config import Config
from temperpi.lcd import LCD

log = logging.getLogger(__name__)


class Event(Enum):
    READ = auto()
    SHUTDOWN = auto()
    STOP = auto()


def power_off() -> None:
    # Authorised for the service user by deploy/50-temperpi.rules (polkit).
    # Fixed argv with an absolute path, no shell, no external input.
    subprocess.run(["/usr/bin/systemctl", "poweroff"], check=True)  # nosec B603


class Daemon:
    def __init__(self, config: Config, lcd: LCD) -> None:
        self.config = config
        self.lcd = lcd
        self.events: queue.Queue[Event] = queue.Queue()
        self.sensors = list(config.sensors) or thermometer.discover(config.w1_devices_dir)

    def show_idle(self) -> None:
        ip = network.primary_ipv4(self.config.preferred_interfaces)
        self.lcd.show(*screens.idle(self.config.idle_title, ip))

    def show_temperatures(self) -> None:
        if not self.config.sensors:  # rediscover in case sensors were hot-plugged
            self.sensors = thermometer.discover(self.config.w1_devices_dir)
        results = thermometer.read_all(self.sensors, self.config.w1_devices_dir)
        for r in results:
            if isinstance(r, thermometer.SensorError):
                log.warning("Sensor read failed: %s", r)
            else:
                log.info("%s: %.2f C / %.2f F", r.label, r.celsius, r.fahrenheit)
        screens.play(self.lcd, screens.temperature_frames(results))

    def run(self) -> None:
        log.info("Sensors: %s", ", ".join(f"{s.label}={s.id}" for s in self.sensors) or "none")
        if self.config.show_welcome:
            screens.play(self.lcd, screens.welcome_frames())
        self.show_idle()

        while True:
            try:
                event = self.events.get(timeout=self.config.idle_refresh_seconds)
            except queue.Empty:
                self.show_idle()
                continue

            if event is Event.READ:
                self.show_temperatures()
                self._drain(Event.READ)  # ignore presses made while displaying
                self.show_idle()
            elif event is Event.SHUTDOWN:
                log.info("Shutdown button held, powering off")
                self.lcd.show(*screens.SHUTDOWN)
                power_off()
                return
            elif event is Event.STOP:
                self.lcd.show(*screens.STOPPED)
                return

    def _drain(self, kind: Event) -> None:
        """Drop queued events of ``kind``, keeping anything else."""
        keep = []
        while True:
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                break
            if ev is not kind:
                keep.append(ev)
        for ev in keep:
            self.events.put(ev)


def run(config: Config) -> None:
    from gpiozero import Button

    lcd = LCD.from_gpio(**vars(config.lcd))
    daemon = Daemon(config, lcd)

    b = config.buttons
    read_btn = Button(b.read_temperature, pull_up=False, bounce_time=b.bounce_seconds)
    stop_btn = Button(
        b.shutdown, pull_up=False, bounce_time=b.bounce_seconds, hold_time=b.shutdown_hold_seconds
    )
    read_btn.when_pressed = lambda: daemon.events.put(Event.READ)
    stop_btn.when_held = lambda: daemon.events.put(Event.SHUTDOWN)

    def on_signal(signum: int, _frame: FrameType | None) -> None:
        log.info("Received %s", signal.Signals(signum).name)
        daemon.events.put(Event.STOP)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    try:
        daemon.run()
    finally:
        read_btn.close()
        stop_btn.close()
        lcd.close()
