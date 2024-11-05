"""openvfd update entities."""

from __future__ import annotations

import logging
import asyncio
from typing import Any


from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    TEMP_PATH,
    INSTALL_PATH,
    FILE_DOWNLOAD_URL,
)

from .common import (
    compare_version,
    down_zip_file,
    unzip_file,
    remove_file,
    remove_dir,
    copytree,
)

from .coordinator import WgiOpenvfdDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

FAKE_INSTALL_SLEEP_TIME = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up demo update platform."""
    async_add_entities(
        [
            OpenvfdUpdate(
                hass.data[DOMAIN]['coordinator'],
                unique_id="update",
                title="Openvfd Update.",
                installed_version= hass.data[DOMAIN]['manifest_version'],
                latest_version= hass.data[DOMAIN]['manifest_last_version'],
                support_progress=True,
                release_summary="Openvdf update async file.",
                release_url="https://gitcode.com/wgihaos/wgi_openvfd_x96max",
                support_install=True,
            ),
        ]
    )


async def _fake_install() -> None:
    """Fake install an update."""
    await asyncio.sleep(FAKE_INSTALL_SLEEP_TIME)


class OpenvfdUpdate(UpdateEntity,CoordinatorEntity[WgiOpenvfdDataUpdateCoordinator]):
    """Representation of a OpenvfdUpdate update entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        coordinator:WgiOpenvfdDataUpdateCoordinator,
        unique_id: str,
        title: str | None,
        installed_version: str | None,
        latest_version: str | None,
        release_summary: str | None = None,
        release_url: str | None = None,
        support_progress: bool = False,
        support_install: bool = True,
        support_release_notes: bool = False,
        device_class: UpdateDeviceClass | None = None,
    ) -> None:
        """Initialize the Demo select entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_installed_version = installed_version
        self._attr_device_class = device_class
        self._attr_latest_version = latest_version
        self._attr_release_summary = release_summary
        self._attr_release_url = release_url
        self._attr_title = title
        self._attr_unique_id = unique_id

        if support_install:
            self._attr_supported_features |= (
                UpdateEntityFeature.INSTALL
                | UpdateEntityFeature.BACKUP
                | UpdateEntityFeature.SPECIFIC_VERSION
            )
        if support_progress:
            self._attr_supported_features |= UpdateEntityFeature.PROGRESS
        if support_release_notes:
            self._attr_supported_features |= UpdateEntityFeature.RELEASE_NOTES

    @property
    def latest_version(self) -> str:
        """Return latest version of the entity."""
        return self._attr_latest_version


    @property
    def installed_version(self) -> str:
        """Return downloaded version of the entity."""
        return self._attr_installed_version

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        self._attr_in_progress=0
        name=f"{DOMAIN}-{version}.zip"
        url = f"{FILE_DOWNLOAD_URL}/{name}"
        filename = f"{TEMP_PATH}/{name}"
        backup_path = f"{TEMP_PATH}/{DOMAIN}"
        source_path = f"{TEMP_PATH}/{DOMAIN}-{version}/custom_components/{DOMAIN}"

        self._attr_in_progress = 10
        self.async_write_ha_state()
        #await asyncio.gather(down_zip_file(url,filename))
        await down_zip_file(self.hass, url, filename)
        self._attr_in_progress =50
        self.async_write_ha_state()
        ## 解压缩
        # unzip_file(filename,{TEMP_PATH})
        await self.hass.async_add_executor_job(unzip_file, filename,TEMP_PATH)
        self._attr_in_progress =80
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(copytree, INSTALL_PATH,backup_path)
        await self.hass.async_add_executor_job(copytree, source_path,INSTALL_PATH)
        self._attr_in_progress =90
        self.async_write_ha_state()
        await _fake_install()

        await self.hass.async_add_executor_job(remove_file, filename)
        await self.hass.async_add_executor_job(remove_dir, backup_path)
        await self.hass.async_add_executor_job(remove_dir, f"{TEMP_PATH}/{DOMAIN}-{version}")
        self._attr_in_progress =100
        self.async_write_ha_state()

        self._attr_installed_version = (
            version if version is not None else self._attr_latest_version
        )
        self._attr_in_progress = False
        self.async_write_ha_state()
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        g_v = self.hass.data[DOMAIN]['manifest_update_last_version']
        l_v = self.hass.data[DOMAIN]['manifest_last_version']
        if compare_version(g_v, l_v) > 0:
            self._attr_latest_version = g_v
            self.async_write_ha_state()


