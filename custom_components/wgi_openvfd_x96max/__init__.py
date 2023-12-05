"""set up Wgi-openvfd"""
from __future__ import annotations

import logging
from copy import deepcopy

from homeassistant.config_entries import ConfigType, ConfigEntry,SOURCE_IMPORT
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant


from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import (
    device_registry as dr,
)

from .const import (
    DOMAIN,
    BASE_DEVICE_CONFIG,
    ENTITY_CONFIG,
    FILE_STATE_INTERVAL,

)

from .openvfd import OpenVfd


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SWITCH
]

def new_entry_device(hass: HomeAssistant, device_info: dict, entry_id: str):

    device_registry = dr.async_get(hass)
    dev = device_registry.async_get_or_create(
        manufacturer=device_info.get('manufacturer'),
        identifiers={(DOMAIN, '{}'.format(device_info.get('id')))},
        config_entry_id=entry_id,
        model=device_info.get('model'),
        name=device_info.get('name'),
        entry_type=DeviceEntryType.SERVICE,
    )
    return dev

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wgi Openvfd."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]['device']  = None
    hass.data[DOMAIN]['entity_info']  = []
    hass.data[DOMAIN]['entities']  = []
    hass.data[DOMAIN]['openvfd'] = None
    register_entry = hass.config_entries.async_entries(DOMAIN)
    if len(register_entry) == 0:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data={}
            )
        )

    return True

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
) -> bool:
    """条目初始化"""
    hass.data[DOMAIN]['device']  = None
    hass.data[DOMAIN]['entity_info']  = []
    hass.data[DOMAIN]['entities']  = []
    if hass.data[DOMAIN]['openvfd'] is not None:
        hass.data[DOMAIN]['openvfd'].listen_stop()
        hass.data[DOMAIN]['openvfd'] = None

    state_interval = FILE_STATE_INTERVAL
    listen_enable = True
    if 'state_interval' in entry.options:
        state_interval = int(entry.options.get('state_interval'))
    if 'listen_enable' in entry.options:
        listen_enable = bool(entry.options.get('listen_enable'))
    openvfd = hass.data[DOMAIN]['openvfd'] = OpenVfd(hass, file_state_interval=state_interval, enable=listen_enable)

    if len(BASE_DEVICE_CONFIG) > 0:
        device_info = deepcopy(BASE_DEVICE_CONFIG)
        dev = new_entry_device(hass, device_info, entry.entry_id)
        device_info['device_id'] = dev.id
        hass.data[DOMAIN]['device'] = dev
        hass.data[DOMAIN]['entity_info'] = entities = deepcopy(ENTITY_CONFIG)
        openvfd.states()
        for entity in entities:
            field_type = entity.get('field_type')
            if field_type in openvfd.led_state:
                entity['state'] = openvfd.led_state.get(field_type)

    openvfd.start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载"""
    if hass.data[DOMAIN]['openvfd'] is not None:
        hass.data[DOMAIN]['openvfd'].listen_stop()
        hass.data[DOMAIN]['openvfd'] = None
    if unload_ok := await hass.config_entries.async_unload_platforms(entry,PLATFORMS):
        hass.data.setdefault(DOMAIN, {})
    return unload_ok

