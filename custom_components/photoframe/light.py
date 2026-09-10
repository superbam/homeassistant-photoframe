"""Represents the frame's display as a dimmable light.

Plain on/off maps onto `/api/display?action=blank|wake` — the same
persistent, non-destructive override the web settings page's "Blank now" /
"Wake now" buttons use. Explicitly setting a brightness level instead maps
onto `/api/brightness`, which *persists* the configured on-brightness (the
web page's brightness slider does the same). The two must stay separate:
earlier this entity used `/api/brightness` for on/off too (brightness 0/1),
which meant a plain "turn on" — sent with whatever brightness level the
frontend's slider happened to be at — silently overwrote the frame's
configured brightness instead of just waking it at whatever brightness was
already set, leaving it stuck dim after a blank/wake cycle.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([PhotoFrameDisplay(entry.runtime_data, entry)])


class PhotoFrameDisplay(PhotoFrameEntity, LightEntity):
    _attr_name = "Display"
    _attr_icon = "mdi:image-frame"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "display")

    @property
    def is_on(self) -> bool | None:
        return bool(self.coordinator.data["status"].get("on"))

    @property
    def brightness(self) -> int | None:
        value = self.coordinator.data["status"].get("brightness")
        return round(float(value) * 255) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        async with self.coordinator.async_writing():
            if ATTR_BRIGHTNESS in kwargs:
                await self.coordinator.client.async_set_brightness(kwargs[ATTR_BRIGHTNESS] / 255)
            else:
                await self.coordinator.client.async_set_display("wake")
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        async with self.coordinator.async_writing():
            await self.coordinator.client.async_set_display("blank")
            await self.coordinator.async_request_refresh()
