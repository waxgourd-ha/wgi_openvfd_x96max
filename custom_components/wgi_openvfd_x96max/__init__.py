"""set up Wgi-openvfd"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigType, ConfigEntry, SOURCE_IMPORT
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE, Platform, STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant, callback, Event, State
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import (
    entity_registry as er,
    device_registry as dr,
)

from .const import (
    DOMAIN,
    BASE_DEVICE_CONFIG,
    OPENVFD_SERVER_STATE_ENABLE,
    OPENVFD_SERVER_STATE_DISABLE,
    OPENVFD_TIME_ZONE_UTC_NAME,
    OPENVFD_SERVER_CONTROL,
    OPENVFD_SERVER_STATE_ACTION,
    MANIFEST_FILE,
)
from .common import (
    EntityManage,
    read_yaml_async,
    read_json_async,
    get_version_last_from_gitcode,
    YAML_FILE,
)
from .coordinator import WgiOpenvfdDataUpdateCoordinator
from .zone_manager import ZoneManage

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.UPDATE,
]

def new_entry_device(hass: HomeAssistant, device_info: dict[str, Any], entry_id: str) -> dr.DeviceEntry:
    """Create a new device entry."""
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
    hass.data[DOMAIN]['manifest_version'] = "1.0.0"
    hass.data[DOMAIN]['manifest_last_version'] = "1.0.0"
    hass.data[DOMAIN]['manifest_update_last_version'] = "1.0.0"
    hass.data[DOMAIN]['device'] = []
    hass.data[DOMAIN]['device_info'] = []
    hass.data[DOMAIN]['entity_init_state'] = {}
    
    manifest_json = await read_json_async(MANIFEST_FILE)
    if manifest_json is not None:
        hass.data[DOMAIN]['manifest_version'] = manifest_json.get("version")
    
    cache = await read_yaml_async(YAML_FILE)
    if cache is not None:
        hass.data[DOMAIN]['yaml_config'] = cache
    else:
        hass.data[DOMAIN]['yaml_config'] = {}
    
    register_entry = hass.config_entries.async_entries(DOMAIN)
    if len(register_entry) == 0:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=BASE_DEVICE_CONFIG
            )
        )
    
    hass.data[DOMAIN]['coordinator'] = WgiOpenvfdDataUpdateCoordinator(hass)
    ZoneManage(hass)
    _entity_manage = EntityManage(hass)
    await _entity_manage.update_default_utc(hass.config.time_zone)
    await _entity_manage.update_default_utc_yaml(hass.config.time_zone)
    await _entity_manage.update_server_action()
    
    if 'openvfd_server' in hass.data[DOMAIN]['yaml_config']:
        server_state = hass.data[DOMAIN]['yaml_config'].get('openvfd_server')
    else:
        _state = _entity_manage.openvfd_server_state()
        server_state = OPENVFD_SERVER_STATE_ENABLE if int(_state) == 1 else OPENVFD_SERVER_STATE_DISABLE
    
    is_server_enable = 1 if server_state == OPENVFD_SERVER_STATE_ENABLE else 0
    hass.data[DOMAIN]['entity_init_state']['openvfd_server'] = STATE_ON if is_server_enable else STATE_OFF
    await _entity_manage.update_server_state(is_server_enable)

    is_enable = _entity_manage.action_state()
    hass.data[DOMAIN]['entity_init_state']['action_enable'] = STATE_ON if int(is_enable) != -1 else STATE_OFF
    hass.data[DOMAIN]['entity_init_state']['time_zone_name'] = hass.data[DOMAIN]['yaml_config'].get('time_zone_name', '')

    manifest_version = await get_version_last_from_gitcode()
    if manifest_version is not None:
        hass.data[DOMAIN]['manifest_update_last_version'] = hass.data[DOMAIN]['manifest_last_version'] = manifest_version
    else:
        hass.data[DOMAIN]['manifest_update_last_version'] = hass.data[DOMAIN]['manifest_last_version'] = hass.data[DOMAIN]['manifest_version']

    return True

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
) -> bool:
    """Set up Wgi Openvfd from a config entry."""
    if 'device' in BASE_DEVICE_CONFIG:
        if 'device' not in hass.data[DOMAIN]:
            hass.data[DOMAIN]['device'] = []
        devices = hass.data[DOMAIN]['device_info'] = BASE_DEVICE_CONFIG.get('device')

        for device in devices:
            entities = device.get('entities', [])
            for entity in entities:
                _entity_id = entity.get('id')
                if _entity_id == OPENVFD_TIME_ZONE_UTC_NAME:
                    entity['state'] = hass.data[DOMAIN]['entity_init_state']['time_zone_name']
                elif _entity_id == f"switch.{OPENVFD_SERVER_STATE_ACTION}":
                    entity['state'] = hass.data[DOMAIN]['entity_init_state']['action_enable']
                elif _entity_id == f"switch.{OPENVFD_SERVER_CONTROL}":
                    entity['state'] = hass.data[DOMAIN]['entity_init_state']['openvfd_server']

        for device_info in BASE_DEVICE_CONFIG.get('device'):
            dev = new_entry_device(hass, device_info, entry.entry_id)
            device_info['device_id'] = dev.id
            hass.data[DOMAIN]['device'].append(dev)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.setdefault(DOMAIN, {})
    return unload_ok
