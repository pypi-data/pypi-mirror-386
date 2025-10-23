# AutoCamLight

    ╔═══╗    ╖      ╔═══╕         ╖         ╖   ╖   
    ║   ║    ║      ║             ║    °    ║   ║   
    ╠═══╣╖  ╓╠═╛╔══╗║    ╒══╗╔═╦═╗║    ╖╔══╗╠══╗╠═╛ 
    ║   ║║  ║║  ║  ║║    ╔══╣║ ║ ║║    ║║  ║║  ║║   
    ╜   ╙╚══╝╚═╛╚══╝╚═══╛╚══╝╜ ╙ ╙╚═══╛╙╚══╣╜  ╙╚═╛ 
                                        ╓  ║        
    AutoCamLight                        ╚══╝        

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/autocamlight.svg)](https://badge.fury.io/py/autocamlight)


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

Only a single toml file is loaded.

Example configuration:

```toml
log_level = "DEBUG"

[mqtt]
host = "homeassistant.local"
username = "mqtt"
password = "Correct Horse Battery Staple"

[entity]
name = "Webcam"
unique_id = "fe4bd497-7c2f-4f35-899f-f147f9f84738-capturing"

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
