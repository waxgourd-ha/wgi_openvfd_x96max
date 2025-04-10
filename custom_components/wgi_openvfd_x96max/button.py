from __future__ import annotations

import logging
from abc import ABC

from homeassistant.components.button import (
    ButtonEntityDescription,
    ButtonEntity,
)

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant,State
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import  (
    WgiEntity,
    async_common_setup_entry,
    EntityManage,

)
from .const import (
    DOMAIN,
    OPENVFD_SERVER_RESTART,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
):
    """async setup entry"""
    if 'device_info' in hass.data[DOMAIN]:
        await async_common_setup_entry(
            hass,
            hass.data[DOMAIN]['device_info'],
            entry,
            async_add_entities,
            ButtonEntityDescription,
            M2Button,
            Platform.BUTTON,
            _LOGGER
        )


class M2Button(WgiEntity, ButtonEntity, ABC):
    """M2 Button Entity"""

    _platform = Platform.BUTTON

    def __init__(self, **kwargs):
        super(M2Button, self).__init__(**kwargs)
        self._attr_entity_registry_visible_default = False

    async def async_press(self) -> None:
        """Press the button."""
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('openvfd_'):
            openvfd = OpenvfdButton(self.hass)
            await openvfd.press(self.entity_id, entity_id_list[1])


class OpenvfdButton:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def press(self,entity_id, name):
        _entity_manage = EntityManage(self._hass)
        if name == OPENVFD_SERVER_RESTART:
            await _entity_manage.update_server_restart()
