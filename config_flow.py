from __future__ import annotations

import logging

import voluptuous as vol
from collections.abc import  Mapping
from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow,FlowResult

from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er
)
from homeassistant.helpers.typing import Any
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from .common import (
    StoreBase
)
from .const import (
    DOMAIN,
    DEFAULT_NAME,
    LedCommandName,
    PILOT_LAMP_ONE,
    BASE_DEVICE_CONFIG
)

_LOGGER = logging.getLogger(__name__)


class MgiConfigFlow(ConfigFlow, domain=DOMAIN):
    """handle a config flow"""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

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
                _store = StoreBase(self.hass)
                await _store.async_store_remove()
                await _store.update_data(BASE_DEVICE_CONFIG)
                await _store.async_store_save()
                # self.async_create_entry(title=DEFAULT_NAME, data={})
                entry = ConfigEntry(
                    version=1,
                    domain=DOMAIN,
                    title=DEFAULT_NAME,
                    data={},
                    source="user",
                )
                await self.hass.config_entries.async_add(entry)
                return self.async_abort(reason="setting success")

        except Exception as e:  # pylint: disable=broad-except
            errors["base"] = "error: " + str(e)
            _LOGGER.error(errors)

        return self.async_show_form(step_id=step_id, data_schema=None, errors=errors)


    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
    #     return MgiOptionsFlow(config_entry)

    # async def async_step_import(self, import_config) -> FlowResult:
    async def async_step_import(self, import_config):
        """Import wgi openvfd config from configuration.yaml"""
        return await self.async_step_user(import_config)

class MgiOptionsFlow(OptionsFlow):

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
            config_entry: ConfigEntry | None = None
    ):
        errors = {}

        try:
            if user_input is not None:
                return self.async_create_entry(title=DEFAULT_NAME, data={})

        except Exception as e:  # pylint: disable=broad-except
            errors["base"] = "error: " + str(e)
        da =   {
            "github": "github.com",
            "docker": "docker.com"
        }
        data_schemas = vol.Schema(
            {
                vol.Required(PILOT_LAMP_ONE, default="github", description="pilot",msg="pilot one"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in da.items()
                        ],
                        # options=[
                        #     "github.com",
                        #     "docker.com"
                        # ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }

        )
        return self.async_show_form(step_id=step_id, data_schema=data_schemas, errors=errors or {})
