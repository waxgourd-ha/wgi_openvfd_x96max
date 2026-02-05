"""Button platform for Wgi Openvfd."""
from __future__ import annotations

import logging
from abc import ABC

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import WgiEntity, EntityManage
from .const import DOMAIN, OPENVFD_SERVER_RESTART
from .entity_factory import EntityFactory

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the button platform."""
    if 'device_info' not in hass.data[DOMAIN]:
        return

    factory = EntityFactory(
        hass=hass,
        entry=entry,
        async_add_entities=async_add_entities,
        entity_class=M2Button,
        description_class=ButtonEntityDescription,
        platform=Platform.BUTTON,
        logger=_LOGGER
    )
    await factory.create_entities(hass.data[DOMAIN]['device_info'])

class M2Button(WgiEntity, ButtonEntity, ABC):
    """M2 Button Entity."""

    _platform = Platform.BUTTON

    def __init__(self, **kwargs) -> None:
        """Initialize the button."""
        super().__init__(**kwargs)
        self._attr_entity_registry_visible_default = False

    async def async_press(self) -> None:
        """Press the button."""
        entity_id_list = self.entity_id.split('.')
        if entity_id_list[1].startswith('openvfd_'):
            openvfd = OpenvfdButton(self.hass)
            await openvfd.press(self.entity_id, entity_id_list[1])

class OpenvfdButton:
    """Openvfd Button handler."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the button handler."""
        self._hass = hass

    async def press(self, entity_id: str, name: str) -> None:
        """Press the button."""
        _entity_manage = EntityManage(self._hass)
        if name == OPENVFD_SERVER_RESTART:
            await _entity_manage.update_server_restart()
