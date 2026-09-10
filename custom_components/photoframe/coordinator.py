"""Polling coordinator for a single photo frame.

Fetches two endpoints per cycle: `/api/status` (runtime state — on/off,
current slide, memory) and `/api/settings` (the full persisted settings
blob — everything the web settings page can edit). Kept separate in
``coordinator.data`` under ``"status"``/``"settings"`` rather than merged,
since they use different key-naming conventions (status is a hand-picked
snake_case-ish summary; settings is the app's `AppSettings` struct encoded
verbatim, camelCase) and partially overlap (e.g. both carry `brightness`).

Polling is a fallback, not the primary path. Frames new enough to push
(see `__init__.py`'s webhook registration) call `async_handle_push()` on
every on/off or brightness change; that calls `async_set_updated_data()`,
which — same as a normal successful poll — reschedules the coordinator's
own timer `update_interval` out from *now*. So as long as pushes keep
arriving, a real poll (an actual round trip to the device) never happens;
one only fires if nothing, push or poll, has been heard in `update_interval`
seconds. Older frames that don't know how to push yet never call it, so
they transparently keep getting today's pure-polling behavior.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
import logging
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PhotoFrameAuthError, PhotoFrameClient, PhotoFrameConnectionError

_LOGGER = logging.getLogger(__name__)

# Keys a webhook push is trusted to update. The webhook has no auth beyond
# the id being unguessable, so pushes are merged onto the last-known status
# rather than replacing it, and only for the couple of fields the frame
# actually reports on a display change — not arbitrary attacker-controlled
# state for every entity that reads `status`.
_PUSHABLE_STATUS_KEYS = {"on", "brightness"}


class PhotoFrameData(TypedDict):
    status: dict[str, Any]
    settings: dict[str, Any]


class PhotoFrameCoordinator(DataUpdateCoordinator[PhotoFrameData]):
    """Fetches /api/status + /api/settings on an interval, as a fallback for push."""

    def __init__(self, hass: HomeAssistant, client: PhotoFrameClient, name: str, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Photo Frame ({name})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        # In-memory only (not persisted to the config entry) — __init__.py
        # reads this to decide whether to show/dismiss the "go configure the
        # webhook" notification. Persisting it would mean writing entry.data
        # from inside the webhook handler, which would fire this integration's
        # own update listener and reload the whole entry on the very first
        # push, tearing down the coordinator mid-flight.
        self.webhook_seen = False
        # Counts entity writes currently between their POST and the refresh
        # that confirms it (see `async_writing()`) — while >0, a webhook push
        # is deferred rather than published. A push's payload only reports
        # `status`, but publishing it still means re-broadcasting whatever
        # `self.data["settings"]` currently is, and mid-write that's the
        # *pre*-write snapshot: the on-device change that triggered this
        # very push already landed there before the push fired, but the
        # matching GET this entity is about to make hasn't come back yet, so
        # every entity reading `settings` would flash back to the old value
        # for one tick before the pending refresh corrects it moments later.
        # Skipping the push here costs nothing — that refresh fetches fresh
        # status too, so no information is actually lost, only deferred.
        self._pending_writes = 0

    @asynccontextmanager
    async def async_writing(self) -> AsyncIterator[None]:
        """Wrap an entity's own POST-then-refresh so pushes defer to it instead of racing it."""
        self._pending_writes += 1
        try:
            yield
        finally:
            self._pending_writes -= 1

    async def _async_update_data(self) -> PhotoFrameData:
        try:
            status = await self.client.async_get_status()
            settings = await self.client.async_get_settings()
        except PhotoFrameAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PhotoFrameConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return {"status": status, "settings": settings}

    def async_handle_push(self, payload: dict[str, Any]) -> None:
        """Merge an instant webhook push and defer the next fallback poll."""
        self.webhook_seen = True
        if not self.data or self._pending_writes:
            return
        changes = {k: v for k, v in payload.items() if k in _PUSHABLE_STATUS_KEYS}
        if not changes:
            return
        self.async_set_updated_data(
            {"status": {**self.data["status"], **changes}, "settings": self.data["settings"]}
        )
