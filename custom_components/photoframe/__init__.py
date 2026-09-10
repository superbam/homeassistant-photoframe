"""The iPad Photo Frame integration.

Talks to the frame's embedded local REST API (see HomeAssistant.md in the
app's repo) — no cloud dependency. Each config entry is one frame; the app
must be in the foreground (it's a wall-mounted, always-on frame, so that's
its normal state) for the frame to answer.
"""

from __future__ import annotations

from aiohttp import web
from homeassistant.components import persistent_notification, webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PhotoFrameClient
from .const import CONF_SCAN_INTERVAL, CONF_WEBHOOK_ID, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import PhotoFrameCoordinator

PLATFORMS = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # The frame always serves a self-signed cert (no public DNS name to get a
    # real one for) — a dedicated verify_ssl=False session, not the default
    # one, so this only weakens TLS validation for our own requests to it.
    session = async_get_clientsession(hass, verify_ssl=False)
    client = PhotoFrameClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = PhotoFrameCoordinator(hass, client, entry.title, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id is None:
        webhook_id = webhook.async_generate_id()
        hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id})

    notification_id = f"{DOMAIN}_{entry.entry_id}_webhook"

    async def _handle_webhook(hass: HomeAssistant, webhook_id: str, request: web.Request) -> None:
        try:
            payload = await request.json(content_type=None)
        except ValueError:
            return
        was_seen = coordinator.webhook_seen
        coordinator.async_handle_push(payload)
        if not was_seen:
            persistent_notification.async_dismiss(hass, notification_id)

    webhook.async_register(hass, DOMAIN, f"Photo Frame ({entry.title})", webhook_id, _handle_webhook)
    entry.async_on_unload(lambda: webhook.async_unregister(hass, webhook_id))

    url = webhook.async_generate_url(hass, webhook_id)
    persistent_notification.async_create(
        hass,
        (
            f"For instant on/off updates, paste this URL into **{entry.title}**'s "
            f"Home Assistant webhook URL setting on the frame itself (web settings "
            f"page, or the on-device Settings screen):\n\n`{url}`\n\n"
            f"Optional — without it, this integration just keeps polling every "
            f"{scan_interval}s like before."
        ),
        title="Photo Frame: instant updates available",
        notification_id=notification_id,
    )

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
