"""Polling coordinator for a single photo frame."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PhotoFrameAuthError, PhotoFrameClient, PhotoFrameConnectionError

_LOGGER = logging.getLogger(__name__)


class PhotoFrameCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches /api/status on an interval and hands entities the parsed JSON."""

    def __init__(self, hass: HomeAssistant, client: PhotoFrameClient, name: str, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Photo Frame ({name})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_status()
        except PhotoFrameAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PhotoFrameConnectionError as err:
            raise UpdateFailed(str(err)) from err
