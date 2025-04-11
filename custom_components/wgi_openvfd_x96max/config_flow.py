from __future__ import annotations

import logging


from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow,FlowResult

from homeassistant.core import callback


from homeassistant.helpers.typing import Any

from .const import (
    DOMAIN,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)


class MgiConfigFlow(ConfigFlow, domain=DOMAIN):
    """handle a config flow"""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    _hassio_discovery: dict[str, Any] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return await self.async_show_user_form("user", user_input)

    @callback
    async def async_show_user_form(
            self,
            step_id=None,
            user_input: dict[str, Any] | None = None,
            config_entry: ConfigEntry | None = None
    ):
        errors = {}
        try:
            if user_input is not None:
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)


        except Exception as e:  # pylint: disable=broad-except
            errors["base"] = "error: " + str(e)
            _LOGGER.error(errors)

        return self.async_show_form(step_id=step_id, data_schema=None, errors=errors)


    async def async_step_import(self, import_config):
        """Import wgi openvfd config from configuration.yaml"""
        return await self.async_step_user(import_config)


