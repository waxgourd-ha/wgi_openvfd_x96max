"""Entity factory for Wgi Openvfd."""
from __future__ import annotations

import logging
from typing import Any, Type, TypeVar, Generic, Optional, Callable, Awaitable, Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .common import get_device_entity_info

T = TypeVar('T', bound=Entity)
E = TypeVar('E', bound=EntityDescription)
EntityInfo = Dict[str, Any]
DeviceInfo = Dict[str, Any]

class EntityFactory(Generic[T, E]):
    """Factory for creating entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        entity_class: Type[T],
        description_class: Type[E],
        platform: Platform,
        logger: logging.Logger,
        entity_validator: Optional[Callable[[EntityInfo], bool]] = None,
        entity_processor: Optional[Callable[[EntityInfo], EntityInfo]] = None,
        post_create_hook: Optional[Callable[[T], Awaitable[None]]] = None
    ) -> None:
        """Initialize the factory."""
        self._hass = hass
        self._entry = entry
        self._async_add_entities = async_add_entities
        self._entity_class = entity_class
        self._description_class = description_class
        self._platform = platform
        self._logger = logger
        self._entities: List[T] = []
        self._entity_validator = entity_validator
        self._entity_processor = entity_processor
        self._post_create_hook = post_create_hook

    async def create_entities(self, devices: List[DeviceInfo]) -> None:
        """Create entities from device info."""
        try:
            for device_info in devices:
                await self._create_device_entities(device_info)

            if self._entities:
                self._async_add_entities(self._entities, True)
                self._logger.info(
                    "Successfully created %d entities for platform %s",
                    len(self._entities),
                    self._platform
                )
        except Exception as e:
            self._logger.error(
                "Failed to create entities: %s",
                str(e),
                exc_info=True
            )

    async def _create_device_entities(self, device_info: DeviceInfo) -> None:
        """Create entities for a single device."""
        try:
            device_id = device_info.get('device_id')
            if not device_id:
                self._logger.warning("Device ID not found in device info")
                return

            device_entry = await get_device_entity_info(self._hass, device_id)
            if not device_entry:
                self._logger.warning("Device entry not found for device %s", device_id)
                return

            device_entities = device_info.get('entities', [])
            for entity_info in device_entities:
                if entity_info.get('platform') != self._platform:
                    continue

                if self._entity_validator and not self._entity_validator(entity_info):
                    self._logger.warning(
                        "Entity validation failed for %s",
                        entity_info.get('id')
                    )
                    continue

                try:
                    entity = await self._create_entity(entity_info, device_entry)

                    if self._entity_processor:
                        entity_info = self._entity_processor(entity_info)

                    if self._post_create_hook:
                        await self._post_create_hook(entity)

                    self._entities.append(entity)
                    self._logger.debug(
                        "Created entity %s for device %s",
                        entity_info.get('id'),
                        device_id
                    )
                except Exception as e:
                    self._logger.error(
                        "Error creating entity %s: %s",
                        entity_info.get('id'),
                        str(e),
                        exc_info=True
                    )
        except Exception as e:
            self._logger.error(
                "Error processing device %s: %s",
                device_info.get('device_id'),
                str(e),
                exc_info=True
            )

    def _create_entity_description(self, entity_info: EntityInfo) -> E:
        """Create entity description from entity info."""
        try:
            return self._description_class(
                key=entity_info.get('id'),
                force_update=True,
                icon=entity_info.get('icon'),
                has_entity_name=True,
                name=entity_info.get('name'),
                unit_of_measurement=entity_info.get('unit_of_measurement'),
            )
        except Exception as e:
            self._logger.error(
                "Failed to create entity description: %s",
                str(e),
                exc_info=True
            )
            raise

    def _create_device_info(self, device_entry: dr.DeviceEntry) -> dr.DeviceInfo:
        """Create device info from device entry."""
        try:
            return dr.DeviceInfo(
                identifiers=device_entry.identifiers,
                name=device_entry.name,
                entry_type=device_entry.entry_type,
                manufacturer=device_entry.manufacturer,
                model=device_entry.model,
                sw_version=device_entry.sw_version,
                hw_version=device_entry.hw_version,
                via_device=device_entry.via_device_id,
                configuration_url=device_entry.configuration_url,
            )
        except Exception as e:
            self._logger.error(
                "Failed to create device info: %s",
                str(e),
                exc_info=True
            )
            raise

    def _get_entity_attributes(self, entity_info: EntityInfo) -> EntityInfo:
        """Get entity attributes from entity info."""
        try:
            attrs = {
                'unique_id': entity_info.get('id'),
                'entity_id': entity_info.get('id'),
                'icon': entity_info.get('icon'),
                'name': entity_info.get('name'),
                'has_entity_name': True,
                'unit_of_measurement': entity_info.get('unit_of_measurement'),
                'should_poll': False,
                'state': entity_info.get('state'),
            }

            if self._entity_processor:
                attrs = self._entity_processor(attrs)

            return attrs
        except Exception as e:
            self._logger.error(
                "Failed to get entity attributes: %s",
                str(e),
                exc_info=True
            )
            raise

    async def _create_entity(
        self,
        entity_info: EntityInfo,
        device_entry: dr.DeviceEntry
    ) -> T:
        """Create a single entity."""
        entity_id = entity_info.get('id')
        if not entity_id:
            self._logger.warning("Entity ID not found in entity info")
            raise ValueError("Entity ID not found in entity info")

        try:
            description = self._create_entity_description(entity_info)
            device_info = self._create_device_info(device_entry)
            entity_attrs = self._get_entity_attributes(entity_info)
            
            entity = self._entity_class(
                registry_entry=None,  # 让 Home Assistant 自动处理注册
                device_entry=device_entry,
                entity_description=description,
                device_info=device_info,
                **entity_attrs  # 使用 entity_attrs 中的属性
            )

            if self._post_create_hook:
                await self._post_create_hook(entity)

            return entity
            
        except Exception as e:
            self._logger.error(
                "Error creating entity %s: %s",
                entity_id,
                str(e),
                exc_info=True
            )
            raise 