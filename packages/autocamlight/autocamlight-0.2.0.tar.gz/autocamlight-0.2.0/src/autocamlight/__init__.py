import errno
import importlib.metadata
import logging
import os
import signal
import time
from collections.abc import Generator
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from threading import Timer
from typing import Literal

from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import BinarySensor, BinarySensorInfo
from inotify.adapters import Inotify
from inotify.calls import InotifyError
from inotify.constants import IN_CLOSE, IN_CREATE, IN_IGNORED, IN_OPEN
from pydantic import ValidationError
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

try:
    __version__ = importlib.metadata.version("autocamlight")
except PackageNotFoundError:
    __version__ = "???"

LOGO = rf"""
╔═══╗    ╖      ╔═══╕         ╖         ╖   ╖
║   ║    ║      ║             ║    °    ║   ║
╠═══╣╖  ╓╠═╛╔══╗║    ╒══╗╔═╦═╗║    ╖╔══╗╠══╗╠═╛
║   ║║  ║║  ║  ║║    ╔══╣║ ║ ║║    ║║  ║║  ║║
╜   ╙╚══╝╚═╛╚══╝╚═══╛╚══╝╜ ╙ ╙╚═══╛╙╚══╣╜  ╙╚═╛
© 2025 Dries007 - MIT License       ╓  ║
v{__version__:<17}                  ╚══╝
"""


def possible_config_files() -> Generator[Path]:
    for folder in reversed(
        (
            os.environ.get("XDG_CONFIG_HOME", "~/.config"),
            *os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":"),
            ".",
        )
    ):
        yield Path(folder, "autocamlight.toml")


class Config(BaseSettings):
    """
    autocamlight.toml model
    """

    model_config = SettingsConfigDict(toml_file=list(possible_config_files()))

    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"
    inotify_block_duration: float = 0.1
    debounce_duration: float = 0.5

    mqtt: Settings.MQTT
    entity: BinarySensorInfo

    @classmethod
    def settings_customise_sources(cls, settings_cls: type[BaseSettings], *args, **kwargs) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

    @classmethod
    def load(cls):
        """
        Load the config from the possible config files or exit(1) with some help text on stdout if that fails.
        """
        try:
            # noinspection PyArgumentList
            return cls()
        except ValidationError as e:
            print("Tried to load these files:", ", ".join(map(os.fspath, cls.model_config.get("toml_file"))))
            print(e)
            exit(1)


def dev_video_watcher(inotify_block_duration: float) -> Generator[bool]:
    """
    Generate bool values based on video device open/close events.
    Automatically adds new video devices to watch and removes them when they disappear.
    """
    logger = logging.getLogger("autocamlight.watcher")

    inotify = Inotify(block_duration_s=inotify_block_duration)
    try:
        # Detect new device events
        inotify.add_watch("/dev", mask=IN_CREATE)
        # Listen to all pre-existing video devices
        for path in Path("/dev").rglob("video*"):
            logger.info("Adding device %s", path)
            inotify.add_watch(os.fspath(path), mask=IN_OPEN | IN_CLOSE)

        for header, type_names, path, filename in inotify.event_gen(yield_nones=False):
            logger.debug("Received inotify: path: %s, file: %s, events %s", path, filename, type_names)

            # This is an event for a video device.
            if path != "/dev":
                # IGNORED fires when the device is removed.
                if bool(header.mask & IN_IGNORED):
                    logger.info("Removed device %s", path)
                    # Remove only from the internal data structures, as it was already removed by the kernel from the inotify fd.
                    inotify.remove_watch(path, superficial=True)
                    continue

                # Only other case is OPEN or CLOSE, which is a state update.
                yield bool(header.mask & IN_OPEN)
                continue

            # This is an event for the /dev folder, for which we only care about new video devices.
            if not filename.startswith("video"):
                continue
            if bool(header.mask & IN_CREATE):
                logger.info("Adding device /dev/%s", filename)
                # 5 attempts, since udev takes time to register the device and change the permissions
                for _ in range(5):
                    try:
                        inotify.add_watch(f"/dev/{filename}", mask=IN_OPEN | IN_CLOSE)
                        break
                    except InotifyError as e:
                        # Only ignore "Permission Denied" errors.
                        if e.errno == errno.EACCES:
                            time.sleep(0.1)
                            continue

                        logger.exception("Failed to add watch for /dev/%s", filename)
                        exit(2)
                else:
                    logger.error("Failed to add watch for /dev/%s", filename)
                    exit(2)

    finally:
        del inotify


class AutoCamLight:
    def __init__(self, cfg: Config):
        self._state = None
        self._cfg = cfg
        self.sensor = BinarySensor(Settings(mqtt=cfg.mqtt, entity=cfg.entity, manual_availability=True))

    @contextmanager
    def _sensor_available(self) -> Generator[BinarySensor]:
        """
        Resource manager for availability of sensor, so it is turned off and marked as unavailable when exiting.
        """
        try:
            self.sensor.set_availability(True)
            yield self.sensor
        finally:
            self.sensor.off()
            self.sensor.set_availability(False)
            self.sensor.mqtt_client.disconnect()

    def run(self):
        """
        Loops forever handling events.
        """
        logger = logging.getLogger("autocamlight.debouncer")
        # Keeping a tally of opened handles is required, since we monitor all video devices in /dev, and also multiple opens can be called.
        count = 0
        # Only call set_state after debounce_duration has passed to avoid spamming short on/off events.
        # Avoid None handling later with this fake timer.
        debounce = Timer(0, lambda: None)

        with self._sensor_available():
            for state in dev_video_watcher(self._cfg.inotify_block_duration):
                logger.debug("Update: state %s, count: %d", state, count)

                if state:
                    count += 1
                # Avoid negative count from devices already opened before monitoring started closing.
                elif count > 0:
                    count -= 1

                debounce.cancel()
                debounce = Timer(self._cfg.debounce_duration, self.set_state, (count != 0,))
                debounce.start()

    def set_state(self, state: bool):
        """
        Set the state of the sensor, which triggers an update in HA if that state is different from the current state.
        """
        if state == self._state:
            return
        self._state = state
        self.sensor.set_availability(True)
        self.sensor.update_state(state)


def main():
    # Handle SIGTERM gracefully
    signal.signal(signal.SIGTERM, lambda signal, frame: exit(0))

    cfg = Config.load()

    # Set up logging
    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)5s [%(name)s] %(message)s")
    if cfg.log_level == "DEBUG":
        # Too much noise from inotify, since it's not filtered by file name yet
        logging.getLogger("inotify.adapters").setLevel(logging.INFO)
    logger = logging.getLogger("autocamlight")
    # Welcome info
    logger.info(LOGO.rstrip())
    logger.debug("Loaded config:\n%s", cfg.model_dump_json(indent=2, exclude_defaults=True))

    # Go to work
    try:
        AutoCamLight(cfg).run()
    except KeyboardInterrupt:
        # Handle SIGINT (Ctrl+C) gracefully
        exit(0)
