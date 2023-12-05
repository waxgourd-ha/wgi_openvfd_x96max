"""公共函数"""

import os
import subprocess

from homeassistant.core import HomeAssistant, State


def send_cmd(name, file):
    return subprocess.run(f"echo '{name}' > {file}", shell=True)

def hex_to_bin(hex_string):
    decimal = int(hex_string, 16)
    binary = bin(decimal)
    return binary[2:]

def send_state(hass:HomeAssistant, entity_id,state="on"):
    new_state = State(entity_id,state)
    hass.states.async_set(entity_id, new_state.state, new_state.attributes)

def file_exists(file:str) -> bool:
    return os.path.isfile(file)

def path_exists(path:str) -> bool:
    return os.path.exists(path)

