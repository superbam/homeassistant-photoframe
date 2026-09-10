"""Polling coordinator for a single photo frame.

Fetches two endpoints per cycle: `/api/status` (runtime state — on/off,
current slide, memory) and `/api/settings` (the full persisted settings
blob — everything the web settings page can edit). Kept separate in
``coordinator.data`` under ``"status"``/``"settings"`` rather than merged,
since they use different key-naming conventions (status is a hand-picked
snake_case-ish summary; settings is the app's `AppSettings` struct encoded
verbatim, camelCase) and partially overlap (e.g. both carry `brightness`).
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PhotoFrameAuthError, PhotoFrameClient, PhotoFrameConnectionError

_LOGGER = logging.getLogger(__name__)


class PhotoFrameData(TypedDict):
    status: dict[str, Any]
    settings: dict[str, Any]


class PhotoFrameCoordinator(DataUpdateCoordinator[PhotoFrameData]):
    """Fetches /api/status + /api/settings on an interval."""

    def __init__(self, hass: HomeAssistant, client: PhotoFrameClient, name: str, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Photo Frame ({name})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> PhotoFrameData:
        try:
            status = await self.client.async_get_status()
            settings = await self.client.async_get_settings()
        except PhotoFrameAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PhotoFrameConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return {"status": status, "settings": settings}
