# AutoCamLight

    ╔═══╗    ╖      ╔═══╕         ╖         ╖   ╖  
    ║   ║    ║      ║             ║    °    ║   ║  
    ╠═══╣╖  ╓╠═╛╔══╗║    ╒══╗╔═╦═╗║    ╖╔══╗╠══╗╠═╛
    ║   ║║  ║║  ║  ║║    ╔══╣║ ║ ║║    ║║  ║║  ║║  
    ╜   ╙╚══╝╚═╛╚══╝╚═══╛╚══╝╜ ╙ ╙╚═══╛╙╚══╣╜  ╙╚═╛
                                        ╓  ║  
    AutoCamLight                        ╚══╝  

[![PyPI version](https://badge.fury.io/py/autocamlight.svg)](https://badge.fury.io/py/autocamlight)
[![Python Versions](https://img.shields.io/pypi/pyversions/autocamlight)](https://pypi.org/project/autocamlight)
[![Downloads](https://static.pepy.tech/badge/autocamlight)](https://pepy.tech/project/autocamlight)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![GitHub issues](https://img.shields.io/github/issues/Dries007/AutoCamLight)](https://github.com/Dries007/AutoCamLight/issues)
[![GitHub stars](https://img.shields.io/github/stars/Dries007/AutoCamLight)](https://github.com/Dries007/AutoCamLight/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/Dries007/AutoCamLight)](https://github.com/Dries007/AutoCamLight/commits/main)[![PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/Dries007)


A small linux utility to automate your webcam light via Home Assistant.

Monitors /dev/video* and sends a state update to HA via MQTT when it detects that video is being captured.  

## Usage

Install, configure and run in the background.

After the first time the webcam is used, the device & entity will be created in Home Assistant, so you can set up your automations.

### Install

Use of [uv](https://docs.astral.sh/uv/) is highly recommended:

```shell
uv tool install autocamlight
```

### Configure

Create a `autocamlight.toml` file in one of the following locations:

1. $XDG_CONFIG_HOME (or ~/.config if unset), or
2. $XDG_CONFIG_DIRS (or /etc/xdg if unset), read as a list of folder split by :, as per the XDG specification, or
3. the current working directory.

The files are read in the order they are listed, so you can override settings. But only top level keys can be overridden in their entirety, no table merging is performed.

Example configuration with some comments:

```toml
# Log level, one of: CRITICAL, ERROR, WARNING, INFO, DEBUG
log_level = "DEBUG"

# Time to wait for inotify events, in seconds.
# Longer times will reduce CPU usage, but will increase the delay and jitter of the state updates.
inotify_block_duration = 0.1

# Time to wait after before sending the state update, in seconds.
# If another event is received before this time, the timer is reset.
debounce_duration = 0.5

# MQTT settings from https://github.com/unixorn/ha-mqtt-discoverable
[mqtt]
host = "homeassistant.local"
username = "mqtt"
password = "Correct Horse Battery Staple"

# Entity settings from https://github.com/unixorn/ha-mqtt-discoverable
[entity]
name = "Webcam"
unique_id = "fe4bd497-7c2f-4f35-899f-f147f9f84738-capturing"

# Device settings from https://github.com/unixorn/ha-mqtt-discoverable
[entity.device]
name = "Webcam"
identifiers = "fe4bd497-7c2f-4f35-899f-f147f9f84738"
```

The file structure is dictated mostly by [ha_mqtt_discoverable](https://github.com/unixorn/ha-mqtt-discoverable).


### Auto-run on login

Create a new (user) unit file:

```shell
systemctl --user --force --full edit autocamlight
```

Add the following to the file, assuming uv is installed in /usr/bin:

```ini
[Unit]
Description=AutoCamLight
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/uv tool run autocamlight
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

Now enable & start the unit:

```shell
systemctl --user enable autocamlight
systemctl --user start autocamlight
```

You can monitor the service status with:

```bash
systemctl --user status autocamlight
journalctl --user -u autocamlight -f
```

### Test

Open any program that uses the webcam, e.g. Cheese.

If you have the logs open, an INFO message should appear.
The entity should be created in Home Assistant.

## Support the Project

If you find this project useful, a tip is always welcome via PayPal:

[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.me/Dries007)
