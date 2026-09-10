"""Config flow for the iPad Photo Frame integration.

Frames advertise themselves over Bonjour as `_photoframe._tcp` (see
HTTPServer.swift), so most installs are a zeroconf discovery card; manual
entry (host/port) covers the case where mDNS doesn't reach across VLANs.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import PhotoFrameAuthError, PhotoFrameClient, PhotoFrameConnectionError
from .const import CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _validate(hass: HomeAssistant, host: str, port: int, username: str, password: str) -> str:
    """Confirm the frame answers and return its display name."""
    session = async_get_clientsession(hass, verify_ssl=False)
    client = PhotoFrameClient(session, host, port, username, password)
    status = await client.async_get_status()
    return str(status.get("frame_name") or host)


class PhotoFrameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single photo frame."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                frame_name = await _validate(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except PhotoFrameAuthError:
                errors["base"] = "invalid_auth"
            except PhotoFrameConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating photo frame")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=frame_name, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        # Instance name is "<FrameName>._photoframe._tcp.local." — the part
        # before the service type is exactly the frame's configured name.
        frame_name = discovery_info.name.split(".")[0]

        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovered = {CONF_HOST: host, CONF_PORT: port, "frame_name": frame_name}
        self.context["title_placeholders"] = {"name": frame_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = self._discovered[CONF_HOST]
            port = self._discovered[CONF_PORT]
            try:
                frame_name = await _validate(
                    self.hass, host, port, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except PhotoFrameAuthError:
                errors["base"] = "invalid_auth"
            except PhotoFrameConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating discovered photo frame")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=frame_name,
                    data={CONF_HOST: host, CONF_PORT: port, **user_input},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"name": self._discovered.get("frame_name", "")},
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return PhotoFrameOptionsFlow()


class PhotoFrameOptionsFlow(config_entries.OptionsFlow):
    """Lets a user tune the polling interval per frame."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=5, max=300)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
