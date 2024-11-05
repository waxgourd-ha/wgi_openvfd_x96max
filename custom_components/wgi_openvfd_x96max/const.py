
import os
from enum import StrEnum
from typing import Final

from datetime import timedelta


DOMAIN: Final = "wgi_openvfd_x96max"

DEFAULT_NAME: Final = "OpenVfd x96max"
YAML_FILE_BASE = os.path.dirname(__file__)
TEMP_PATH = "/tmp"
INSTALL_PATH = f"/config/custom_components/{DOMAIN}"
YAML_FILE = f"{YAML_FILE_BASE}/config.yaml"
MANIFEST_FILE = f"{YAML_FILE_BASE}/manifest.json"

VERSION_UPDATE_GITCODE_URL = f"https://raw.gitcode.com/wgihaos/{DOMAIN}/raw/main/custom_components/{DOMAIN}/manifest.json"
FILE_DOWNLOAD_URL= "http://ota.wghaos.com/wgi/openvfd"

#SCAN_INTERVAL = timedelta(seconds=30)
SCAN_INTERVAL = timedelta(minutes=180)

CONF_BASE_KEY = "openvfd"

OPENVFD_SERVER_STATE_SCAN_INTERVAL = timedelta(seconds=20)
OPENVFD_SERVER_STATE_ENABLE = 'enable'
OPENVFD_SERVER_STATE_DISABLE = 'disable'
OPENVFD_SERVER_SETTING_STATE = "openvfd_server_setting_state"
OPENVFD_SERVER_CONTROL    = "openvfd_server_control"
OPENVFD_SERVER_STATE_ACTION = "openvfd_server_state_action"
OPENVFD_SERVER_RESTART = "openvfd_server_restart"
OPENVFD_SERVER_STATE    = "openvfd_server_state"
OPENVFD_SERVER_DISABLE = "openvfd_server_disable"
OPENVFD_SERVER_ENABLE = "openvfd_server_enable"

OPENVFD_TIME_ZONE_UTC_NAME = "sensor.openvfd_time_zone_utc_name"
OPENVFD_TIME_ZONE_UTC = "sensor.openvfd_time_zone_utc"
OPENVFD_TIME_ZONE_CTS = "sensor.openvfd_time_zone_cst"
OPENVFD_TIME_ZONE_GMT = "sensor.openvfd_time_zone_gmt"

OPENVFD_TIME_DELAYED_TIME = 10

BASE_DEVICE_CONFIG = {
    "device": [
        {
            "manufacturer": "冬瓜电子",
            "model": "wg_x96max_openvfd",
            "id": "vfd-mf-100",
            "name": "Openvfd设备",
            "entities": [
                {
                    "platform": "sensor",
                    "id": OPENVFD_TIME_ZONE_UTC_NAME,
                    "field_type": "zone_name",
                    "name": "时区",
                    "state": "Asia/Shanghai",
                    "allow_config":"off",
                    "icon": "mdi:timeline-clock",
                    "unit_of_measurement": ""
                },

                {
                    "platform": "switch",
                    "id": f"switch.{OPENVFD_SERVER_CONTROL}",
                    "field_type": f"{OPENVFD_SERVER_CONTROL}",
                    "value_type": "",
                    "name": "开机OpenVFD启动",
                    "icon": "mdi:server",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
                {
                    "platform": "switch",
                    "id": f"switch.{OPENVFD_SERVER_STATE_ACTION}",
                    "field_type": f"{OPENVFD_SERVER_STATE_ACTION}",
                    "value_type": "",
                    "name": "服务状态切换",
                    "icon": "mdi:server",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
                {
                    "platform": "button",
                    "id": f"button.{OPENVFD_SERVER_RESTART}",
                    "field_type": f"{OPENVFD_SERVER_RESTART}",
                    "value_type": "",
                    "name": "服务重启",
                    "icon": "",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
            ]
        }
    ]
}
