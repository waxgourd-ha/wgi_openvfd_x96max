"""Sensor platform for Wgi Openvfd."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import WgiEntity
from .entity_factory import EntityFactory
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    if 'device_info' not in hass.data[DOMAIN]:
        return

    factory = EntityFactory(
        hass=hass,
        entry=entry,
        async_add_entities=async_add_entities,
        entity_class=M2Sensor,
        description_class=SensorEntityDescription,
        platform=Platform.SENSOR,
        logger=_LOGGER
    )
    await factory.create_entities(hass.data[DOMAIN]['device_info'])

class M2Sensor(WgiEntity, SensorEntity):
    """M2 Sensor Entity."""

    def __init__(self, **kwargs) -> None:
        """Initialize the sensor."""
        super().__init__(**kwargs)
        self._attr_entity_registry_visible_default = False