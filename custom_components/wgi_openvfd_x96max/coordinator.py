"""DataUpdateCoordinator for the Wgi Openvfd x96max integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, cast


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util


from .const import (
    DOMAIN,
    SCAN_INTERVAL,
)

from .common import (
    get_version_last_from_gitcode,
)
_LOGGER = logging.getLogger(__name__)




class WgiOpenvfdDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """The Openvfd Data Update Coordinator."""

    config_entry: ConfigEntry
    station_name: str
    last_measured: datetime | None = None

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.hass = hass

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest version from the gitcode wgi."""

        try:
            manifest_version = await get_version_last_from_gitcode()
            if manifest_version is not None:
                if self.hass.data[DOMAIN]['manifest_update_last_version'] != manifest_version:
                    self.hass.data[DOMAIN]['manifest_update_last_version'] = manifest_version
        except Exception:
            _LOGGER.error("Wgi Openvfd get version error.")


