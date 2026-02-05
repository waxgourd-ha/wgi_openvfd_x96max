"""Zone manager for Wgi Openvfd."""
from __future__ import annotations

from typing import Any
from homeassistant.core import HomeAssistant, Event, State
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from .const import DOMAIN
from .common import EntityManage

class ZoneManage:
    """Manage timezone updates for Wgi Openvfd."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the zone manager."""
        self._hass = hass
        self.listen()

    async def _handle_event(self, event: Event) -> None:
        """Handle core config update events."""
        await self.zone_update(event.data)

    async def zone_update(self, data: dict[str, Any]) -> None:
        """Update timezone when it changes in Home Assistant."""
        if not data or "time_zone" not in data:
            return

        zone = data.get('time_zone')
        _entity_manage = EntityManage(self._hass)
        _configs = self._hass.data[DOMAIN]
        _utc_val = _configs.get('yaml_config', {}).get('time_zone_name', '')

        if zone != _utc_val:
            await _entity_manage.update_default_utc(zone)

            devices = _configs.get('device_info', [])
            for device in devices:
                entities = device.get('entities', [])
                for entity in entities:
                    if entity.get('field_type') == 'zone_name':
                        eid = entity.get('id')
                        if eid:
                            new_state = State(eid, zone)
                            self._hass.states.async_set(eid, new_state.state, new_state.attributes)
                            return

    def listen(self) -> None:
        """Listen for timezone changes."""
        self._hass.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE,
            self._handle_event
        ) 