import logging
import os
import signal
from pathlib import Path
from threading import Timer
from typing import Literal

from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import BinarySensor, BinarySensorInfo
from inotify.adapters import Inotify
from inotify.constants import IN_CLOSE_WRITE, IN_OPEN
from pydantic import ValidationError
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

LOGO = r"""
╔═══╗    ╖      ╔═══╕         ╖         ╖   ╖
║   ║    ║      ║             ║    °    ║   ║
╠═══╣╖  ╓╠═╛╔══╗║    ╒══╗╔═╦═╗║    ╖╔══╗╠══╗╠═╛
║   ║║  ║║  ║  ║║    ╔══╣║ ║ ║║    ║║  ║║  ║║
╜   ╙╚══╝╚═╛╚══╝╚═══╛╚══╝╜ ╙ ╙╚═══╛╙╚══╣╜  ╙╚═╛
                                    ╓  ║
                                    ╚══╝
"""


def possible_config_files():
    for folder in (
        os.environ.get("XDG_CONFIG_HOME", os.environ["HOME"] + "/.config"),
        *os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":"),
        ".",
    ):
        yield Path(folder, "autocamlight.toml").resolve()


class Config(BaseSettings):
    model_config = SettingsConfigDict(toml_file=list(possible_config_files()))

    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    mqtt: Settings.MQTT
    entity: BinarySensorInfo

    @classmethod
    def settings_customise_sources(cls, settings_cls: type[BaseSettings], *args, **kwargs) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

    @classmethod
    def load(cls):
        try:
            # noinspection PyArgumentList
            return cls()
        except ValidationError as e:
            print("Tried to load these files:", ", ".join(map(os.fspath, cls.model_config.get("toml_file"))))
            print("Could not load config, please check your config file. Pydantic error:")
            print(e)
            exit(1)


class AutoCamLight:
    def __init__(self, cfg: Config):
        self._state = None
        self._cfg = cfg
        self.sensor = BinarySensor(Settings(mqtt=cfg.mqtt, entity=cfg.entity, manual_availability=True))

    def run(self):
        logger = logging.getLogger("autocamlight")

        try:
            self.sensor.set_availability(True)
            inotify = Inotify()

            inotify.add_watch("/dev", mask=IN_OPEN | IN_CLOSE_WRITE)

            debounce = Timer(0, lambda: None)

            for header, _, _, filename in inotify.event_gen(yield_nones=False):
                if not filename.startswith("video"):
                    continue

                state = bool(header.mask & IN_OPEN)

                logger.debug("Received event: device: %s, state %s", filename, state)

                debounce.cancel()
                debounce = Timer(0.1, self.set_state, (state,))
                debounce.start()
        except KeyboardInterrupt:
            pass
        finally:
            logger = logging.getLogger("autocamlight")
            logger.info("Exiting...")
            # noinspection PyBroadException
            try:
                self.sensor.set_availability(False)
            except Exception:
                logger.exception("Failed to set availability")
            # noinspection PyBroadException
            try:
                self.sensor.mqtt_client.disconnect()
            except Exception:
                logger.exception("Failed to disconnect MQTT client")

    def set_state(self, state: bool):
        if state == self._state:
            return
        self._state = state
        self.sensor.set_availability(True)
        self.sensor.update_state(state)


def main():
    signal.signal(signal.SIGTERM, lambda signal, frame: exit(0))

    cfg = Config.load()

    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)5s [%(name)s] %(message)s")
    if cfg.log_level == "DEBUG":
        # Too much noise from inotify, since it's not filtered by file name yet
        logging.getLogger("inotify.adapters").setLevel(logging.INFO)
    logger = logging.getLogger("autocamlight")
    logger.info(LOGO)
    logger.info("Loaded config:\n%s", cfg.model_dump_json(indent=2, exclude_defaults=True))

    acl = AutoCamLight(cfg)
    acl.run()
