

from enum import StrEnum
from typing import Final


DOMAIN: Final = "wgi_openvfd_x96max"

ENTRY_NAME: Final = "vfd control"

FILE_STATE_INTERVAL = 60

class LedCommandName(StrEnum):
    """Led命令名称."""

    APPS  = "apps"
    SETUP = "setup"
    USB   = "usb"
    SD    = "sd"
    HDMI  = "hdmi"
    CVBS  = "cvbs"

LED_COMMAND_PATH = "/sys/class/leds/openvfd"

LED_COMMAND_FILE_ON = f"{LED_COMMAND_PATH}/led_on"

LED_COMMAND_FILE_OFF = f"{LED_COMMAND_PATH}/led_off"

LED_COMMAND_STATE = f"cat {LED_COMMAND_PATH}led_on"

BASE_DEVICE_CONFIG = {
    "manufacturer": "冬瓜电子",
    "model": "wg_x96max_openvfd",
    "id": "openvfd-control-100",
    "name": "Openvfd Control",
}

ENTITY_CONFIG = [
    {
        "platform": "switch",
        "id": "switch.led_button_apps",
        "field_type": "apps",
        "name": "apps灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },
    {
        "platform": "switch",
        "id": "switch.led_button_setup",
        "field_type": "setup",
        "name": "setup灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },
    {
        "platform": "switch",
        "id": "switch.led_button_usb",
        "field_type": "usb",
        "name": "usb灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },
    {
        "platform": "switch",
        "id": "switch.led_button_sd",
        "field_type": "sd",
        "name": "SD灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },
    {
        "platform": "switch",
        "id": "switch.led_button_hdmi",
        "field_type": "hdmi",
        "name": "HDMI灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },
    {
        "platform": "switch",
        "id": "switch.led_button_cvbs",
        "field_type": "cvbs",
        "name": "CVBS灯",
        "state": "on",
        "allow_config": "off",
        "icon": "mdi:lightbulb",
        "unit_of_measurement": ""
    },

]