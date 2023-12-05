from __future__ import annotations

import logging
from abc import ABC
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers import (
    entity,
    device_registry as dr,
    entity_registry as er,
)
from .const import (
    DOMAIN,
    ENTITY_CONFIG,
    LED_COMMAND_FILE_ON,
    LED_COMMAND_FILE_OFF
)

from .common import (
    send_state,
    send_cmd,
)

from .wgi_entity import WgiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
):
    """async setup entry"""

    m2 = []
    if len(ENTITY_CONFIG) >0:
        device_entry = hass.data[DOMAIN]['device']
        entities = hass.data[DOMAIN]['entity_info']

        if entities is not None and len(entities) >0:
            for entitys in entities:
                _platform = entitys.get('platform')
                if _platform != Platform.SWITCH:
                    continue

                _entity_id =  entitys.get('id')
                icon = entitys.get('icon')

                value = entitys.get('state')
                desc = SwitchEntityDescription(
                    key=_entity_id,
                    force_update = True,
                    icon= icon,
                    has_entity_name= True,
                    name= entitys.get('name'),
                    unit_of_measurement= entitys.get('unit_of_measurement'),
                )

                ent = er.RegistryEntry(
                    entity_id=_entity_id,
                    unique_id=_entity_id,
                    platform=_platform,
                    config_entry_id=entry.entry_id,
                    device_id=device_entry.id,
                    id=_entity_id,
                    has_entity_name=True,

                )

                deviceInfo = entity.DeviceInfo(
                    manufacturer=device_entry.manufacturer,
                    entry_type=device_entry.entry_type,
                    identifiers=device_entry.identifiers,
                    model=device_entry.model,
                    name=device_entry.name
                )

                ##注册
                sw = WgiSwitch(
                    registry_entry=ent,
                    device_entry=device_entry,
                    entity_description=desc,
                    device_info=deviceInfo,
                    unique_id=_entity_id,
                    entity_id=_entity_id,
                    icon= icon,
                    name=entitys.get('name'),
                    device_id=device_entry.id,
                    has_entity_name=True,
                    capability_attributes=ent.capabilities,
                    supported_features=ent.supported_features,
                    entity_category=ent.entity_category,
                    original_device_class=ent.original_device_class,
                    original_icon=ent.original_icon,
                    original_name=ent.original_name,
                    translation_key=ent.translation_key,
                    unit_of_measurement=entitys.get('unit_of_measurement'),
                    device_class=ent.device_class,
                    should_poll=False,
                    state = value
                )
                m2.append(sw)
                hass.data[DOMAIN]['entities'].append(sw)

    if len(m2) > 0:
        async_add_entities(m2, True)

    openvfd = hass.data[DOMAIN]['openvfd']
    if openvfd is not None:
        openvfd.reg_call(switch_update_state)

def switch_update_state(hass:HomeAssistant, name, state):
    entity_info = hass.data[DOMAIN]['entity_info']
    hass.data[DOMAIN]['entities']
    if len(entity_info)>0:
        for entity in entity_info:
            field_type = entity.get('field_type')
            if name == field_type:
                eid = entity.get('id')
                for entity_obj in hass.data[DOMAIN]['entities']:
                    if eid == entity_obj.entity_id:
                        send_state(hass, entity_obj.entity_id,state)
                        break
                break



class WgiSwitch(WgiEntity, SwitchEntity, ABC):
    """Wgi Switch Entity"""

    _platform = Platform.SWITCH

    def __init__(self, **kwargs):
        super(WgiSwitch, self).__init__(**kwargs)



    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off"""
        self._attr_is_on = False
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('led_'):
            _openvfd_seitch = OpenvfdSwitch(self.hass)
            await _openvfd_seitch.turn_off(self.entity_id,entity_id_list[1])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on"""
        self._attr_is_on = True
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('led_'):
            _openvfd_seitch = OpenvfdSwitch(self.hass)
            await _openvfd_seitch.turn_on(self.entity_id,entity_id_list[1])


class OpenvfdSwitch:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def turn_off(self, entity_id,name):
        name_list = name.split("_")
        file_type = name_list[2]
        send_cmd(file_type, LED_COMMAND_FILE_OFF)
        send_state(self._hass, entity_id, 'off')

    async def turn_on(self, entity_id,name):
        name_list = name.split("_")
        file_type = name_list[2]
        send_cmd(file_type, LED_COMMAND_FILE_ON)
        send_state(self._hass, entity_id, 'on')


