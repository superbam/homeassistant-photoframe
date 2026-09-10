"""Represents the frame's display as a dimmable light.

Maps directly onto /api/brightness: 0 blanks the screen, >0 wakes it. This
mirrors HomeAssistant.md's documented convention for manual power control.
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
        return bool(self.coordinator.data.get("on"))

    @property
    def brightness(self) -> int | None:
        value = self.coordinator.data.get("brightness")
        return round(float(value) * 255) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            fraction = kwargs[ATTR_BRIGHTNESS] / 255
        else:
            # No level requested — restore the last known brightness (or full
            # on if the frame was already at 0, e.g. previously blanked).
            fraction = self.coordinator.data.get("brightness") or 1.0
            if fraction <= 0:
                fraction = 1.0
        await self.coordinator.client.async_set_brightness(fraction)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_set_brightness(0.0)
        await self.coordinator.async_request_refresh()
