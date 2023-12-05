from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigEntry, ConfigFlow,FlowResult,OptionsFlow

from homeassistant.data_entry_flow import FlowHandler, FlowResult
from homeassistant.core import callback


from homeassistant.helpers.typing import Any

from .const import (
    DOMAIN,
    ENTRY_NAME,
    FILE_STATE_INTERVAL,
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
                return self.async_create_entry(title=ENTRY_NAME, data=user_input)

        except Exception as e:
            errors["base"] = "error: " + str(e)
            _LOGGER.error(errors)

        return self.async_show_form(step_id=step_id, data_schema=None, errors=errors)


    async def async_step_import(self, import_config):
        """Import wgi openvfd config from configuration.yaml"""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MgiOptionsFlow(config_entry)


class MgiOptionsFlow(ConfigFlow, config_entries.OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> data_entry_flow.FlowResult:
        return await self.async_show_user_form("init", user_input, self.config_entry)

    @callback
    async def async_show_user_form(
            self,
            step_id=None,
            user_input: dict[str, Any] | None = None,
            entry: ConfigEntry | None = None
    ):
        errors = {}
        if user_input is None:
            listen_enable = True
            state_interval = FILE_STATE_INTERVAL
            if 'state_interval' in entry.options:
                state_interval = int(entry.options.get('state_interval'))
            if 'listen_enable' in entry.options:
                listen_enable = bool(entry.options.get('listen_enable'))
            data_schema = vol.Schema(
                {
                    vol.Optional("listen_enable", default=listen_enable): bool,
                    vol.Optional("state_interval", default=state_interval): vol.All(
                        int, vol.Range(min=2)
                    ),
                }
            )
            return self.async_show_form(
                step_id="init",
                data_schema=data_schema,
            )
        try:
            state_interval = user_input.get('state_interval')
            op = {
                "state_interval": state_interval,
                "listen_enable": user_input.get('listen_enable')
            }
            self.hass.config_entries.async_update_entry(entry, options=op)
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(entry.entry_id)
            )
        except Exception as e:
            errors["base"] = "error: " + str(e)
            return self.async_show_form(
                    step_id=step_id,
                    data_schema=None,
                    errors=errors or {}
                )
        return self.async_abort(reason="setting success")