"""Switch platform for Wgi Openvfd."""
from __future__ import annotations

import logging
from abc import ABC
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, SERVICE_TURN_ON, SERVICE_TURN_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OPENVFD_SERVER_STATE_ACTION, OPENVFD_SERVER_CONTROL
from .common import WgiEntity, EntityManage, send_state
from .entity_factory import EntityFactory

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switch platform."""
    if 'device_info' not in hass.data[DOMAIN]:
        return

    factory = EntityFactory(
        hass=hass,
        entry=entry,
        async_add_entities=async_add_entities,
        entity_class=WgiSwitch,
        description_class=SwitchEntityDescription,
        platform=Platform.SWITCH,
        logger=_LOGGER
    )
    await factory.create_entities(hass.data[DOMAIN]['device_info'])

class WgiSwitch(WgiEntity, SwitchEntity, ABC):
    """Wgi Switch Entity."""

    _platform = Platform.SWITCH

    def __init__(self, **kwargs) -> None:
        """Initialize the switch."""
        super().__init__(**kwargs)
        self._attr_entity_registry_visible_default = False
        if (old_state := kwargs.get("old_state")) is not None:
            self._attr_capability_attributes = old_state.attributes
            self._attr_is_on = old_state.state == STATE_ON

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self._attr_is_on = False
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('openvfd_server_'):
            _openvfd_switch = OpenvfdSwitch(self.hass)
            await _openvfd_switch.turn_off(self.entity_id, entity_id_list[1])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        self._attr_is_on = True
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('openvfd_'):
            _openvfd_switch = OpenvfdSwitch(self.hass)
            await _openvfd_switch.turn_on(self.entity_id, entity_id_list[1])

class OpenvfdSwitch:
    """Openvfd Switch handler."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the switch handler."""
        self._hass = hass

    async def turn_off(self, entity_id: str, name: str) -> None:
        """Turn off the switch."""
        _entity_manage = EntityManage(self._hass)
        if name == OPENVFD_SERVER_CONTROL:
            await _entity_manage.update_server_state(0)
            send_state(self._hass, entity_id, 'off')
        elif name == OPENVFD_SERVER_STATE_ACTION:
            data = await _entity_manage.update_server_action_cmd(-1)
            is_enable = data.get('status_code', -1)
            if is_enable == -1:
                await _entity_manage.update_server_action_state(-1)
                send_state(self._hass, entity_id, 'off')

    async def turn_on(self, entity_id: str, name: str) -> None:
        """Turn on the switch."""
        _entity_manage = EntityManage(self._hass)
        if name == OPENVFD_SERVER_CONTROL:
            await _entity_manage.update_server_state(1)
            send_state(self._hass, entity_id, 'on')
        elif name == OPENVFD_SERVER_STATE_ACTION:
            data = await _entity_manage.update_server_action_cmd(0)
            is_enable = data.get('status_code', -1)
            if str(is_enable) != '-1':
                await _entity_manage.update_server_action_state(0)
                send_state(self._hass, entity_id, 'on')

