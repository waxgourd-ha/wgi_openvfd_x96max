"""显示状态"""

import logging
from datetime import timedelta,datetime

from homeassistant.core import (
    CALLBACK_TYPE,
    HomeAssistant,
)
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    LED_COMMAND_FILE_ON,
    LED_COMMAND_FILE_OFF,
    FILE_STATE_INTERVAL,
)

from .common import (
    file_exists,
    hex_to_bin,
)

_LOGGER = logging.getLogger(__name__)


class OpenVfd:

    is_listen: bool = True
    is_stop: bool = False
    is_file: bool = False
    is_off_file: bool = False
    state_info = ""

    led_state = {
        "apps":  "off",
        "setup": "off",
        "usb":   "off",
        "sd":    "off",
        "hdmi":  "off",
        "cvbs":  "off",
    }

    led_name = ["apps","setup","usb","sd","","hdmi","cvbs"]

    def __init__(self,hass: HomeAssistant, file_state_interval: int =FILE_STATE_INTERVAL, enable: bool = True) -> None:
        self.is_file = False
        self._cancel_unavailable_tracking: CALLBACK_TYPE | None = None
        self.call = None
        self.hass = hass
        self.file_state_interval = file_state_interval
        self.enable = enable


    def reg_call(self, call):
        self.call = call

    def check_on_file(self,):
        self.is_file = file_exists(LED_COMMAND_FILE_ON)
        return self.is_file

    def check_off_file(self,):
        self.is_off_file = file_exists(LED_COMMAND_FILE_OFF)
        return self.is_off_file

    def start(self):
        if self.enable:
            self.listen_start()

    def listen_stop(self):
        if self._cancel_unavailable_tracking:
            self._cancel_unavailable_tracking()
            self._cancel_unavailable_tracking = None


    def state(self,now: datetime):
        if self.check_on_file():
            self.state_info = self.get_state()
            self.parse_state()

    def states(self,is_call = False):
        if self.check_on_file():
            self.state_info = self.get_state()
            self.parse_state(is_call)


    def parse_state(self, is_call = True):
        if len(self.state_info) >0:
            bin_num = hex_to_bin(self.state_info)
            bin_list = list(bin_num)
            bin_list.reverse()
            bin_list_len = len(bin_list)
            for idx, x in enumerate(self.led_name):
                if idx <= (bin_list_len - 1):
                    state = bin_list[idx]
                else:
                    state = 0
                if idx != 4:
                    if int(state) == 1:
                        state_info = "on"
                    else:
                        state_info = "off"
                    st = self.led_state.get(x)
                    if st != state_info:
                        self.led_state[x] = state_info
                        if is_call:
                            if self.call is not None:
                                self.call(self.hass,x,state_info)


    def listen_start(self):
        self._cancel_unavailable_tracking = async_track_time_interval(self.hass,
            self.state, timedelta(seconds=self.file_state_interval)
        )

    def get_state(self) -> str:
        info = ''
        try:
            with open(LED_COMMAND_FILE_ON, "r+") as file:
                state_info = file.read()
                if state_info.startswith('led status is '):
                    info = state_info[14:].strip()
        except Exception as e:
            _LOGGER.error(e)
        return info


