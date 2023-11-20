"""set up Wgi-openvfd"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigType, ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE,Platform
from homeassistant.core import HomeAssistant, callback, Event, State


from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import (
    entity_registry as er,
    device_registry as dr,
)

from .const import (
    DOMAIN,
    OPENVFD_SERVER_STATE_ENABLE,
)
from .common import (
    StoreBase,
    EntityManage,
    yaml_read,
    YAML_FILE,
)


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON
]

def new_entry_device(hass: HomeAssistant, device_info: dict, entry_id: str):

    device_registry = dr.async_get(hass)
    dev = device_registry.async_get_or_create(
        # manufacturer=device_info.get('manufacturer'),
        # configuration_url=device_info.get('configuration_url'),
        identifiers={(DOMAIN, '{}'.format(device_info.get('id')))},
        config_entry_id=entry_id,
        # sw_version=device_info.get('sw_version'),
        # hw_version=device_info.get('hw_version'),
        # model=device_info.get('model'),
        name=device_info.get('name'),
        entry_type=DeviceEntryType.SERVICE,
    )
    return dev

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wgi Openvfd."""
    # _LOGGER.error('------------------ wgi_openvfd_v96max async_setup.')
    hass.data.setdefault(DOMAIN, {
        "store" : {}
    })

    store_obj = StoreBase(hass)
    cache = yaml_read(YAML_FILE)
    if cache is not None:
        hass.data[DOMAIN]['yaml_config'] = cache
    else:
        hass.data[DOMAIN]['yaml_config'] = {}
    hass.data[DOMAIN]['store'] = await store_obj.async_load()

    if len(hass.data[DOMAIN]['store']) >0:
        _Zone = ZoneManage(hass)
        _entity_manage = EntityManage(hass)
        await _entity_manage.update_default_utc(hass.config.time_zone)
        await _entity_manage.update_default_utc_yaml(hass.config.time_zone)
        # await _entity_manage.update_server()
        if 'openvfd_server' in hass.data[DOMAIN]['yaml_config']:
            server_state = hass.data[DOMAIN]['yaml_config'].get('openvfd_server')
        else:
            server_state = OPENVFD_SERVER_STATE_ENABLE
        if server_state == OPENVFD_SERVER_STATE_ENABLE:
            is_server_enable = 1
        else:
            is_server_enable = 0
        await _entity_manage.update_server_state(is_server_enable)
        await _entity_manage.update_server_action()




    return True

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
) -> bool:
    """条目初始化"""
    # _LOGGER.warning('----------------async_setup_entry')
    if 'device' in  hass.data[DOMAIN]['store']:
        devices =  hass.data[DOMAIN]['store']['device']
        if 'device' not in hass.data[DOMAIN]:
            hass.data[DOMAIN]['device']  = []
        for device_info in devices:
            dev = new_entry_device(hass, device_info, entry.entry_id)
            device_info['device_id'] = dev.id
            hass.data[DOMAIN]['device'].append(dev)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True



async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载"""
    # _LOGGER.warning("----------async_unload_entry")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry,PLATFORMS):
        store_obj = StoreBase(hass)
        hass.data.setdefault(DOMAIN, {})
        await store_obj.async_store_remove()
    return True

class ZoneManage:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self.listen()

    async def _handle_event(self, event: Event) -> None:
        await self.zone_update(event.data)

    async def zone_update(self, data) -> None:
        if data and "time_zone" in data:

            zone = data.get('time_zone')

            _store = self._hass.data[DOMAIN]['store']
            _utc_val = _store.get('utc')

            if zone != _utc_val:
                _entity_manage = EntityManage(self._hass)
                await _entity_manage.update_default_utc(zone)


                devices = _store.get('device')
                for device in devices:
                    entities = device.get('entities')
                    for entity in entities:
                        field_type = entity.get('field_type')
                        if field_type == 'zone_name':
                            eid = entity.get('id')
                            new_state = State(eid,zone)
                            self._hass.states.async_set(eid, new_state.state, new_state.attributes)
                            return None


    def listen(self) -> None:
        self._hass.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE,
            self._handle_event
        )