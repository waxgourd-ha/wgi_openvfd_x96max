from __future__ import annotations

import logging


from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import  (
    WgiEntity,
    async_common_setup_entry,
)


from .const import (
    DOMAIN,
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
            SensorEntityDescription,
            M2Sensor,
            Platform.SENSOR,
            _LOGGER
        )

class M2Sensor(WgiEntity, SensorEntity):
    """M2 Sensor Entity"""
