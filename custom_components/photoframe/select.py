"""Enum-valued settings from the web settings page, editable via POST /api/settings.

`collageGridSize` is the one non-string case — the frame's settings model
stores it as an `Int` (2/4/6), but `select` options are always strings, so
values are stringified for display and parsed back to `int` on write.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity


@dataclass(frozen=True, kw_only=True)
class PhotoFrameSelectDescription(SelectEntityDescription):
    int_value: bool = False


SELECTS: tuple[PhotoFrameSelectDescription, ...] = (
    PhotoFrameSelectDescription(
        key="transitionStyle",
        translation_key="transition_style",
        icon="mdi:image-multiple-outline",
        options=[
            "crossfade", "slide", "slideVertical", "zoom", "kenBurns",
            "flip", "push", "cube", "blur", "swirl",
        ],
    ),
    PhotoFrameSelectDescription(
        key="scaleMode",
        translation_key="scale_mode",
        icon="mdi:fit-to-page-outline",
        options=["fit", "fill"],
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSelectDescription(
        key="clockSize",
        translation_key="clock_size",
        icon="mdi:format-size",
        options=["small", "medium", "large"],
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSelectDescription(
        key="collageGridSize",
        translation_key="collage_grid_size",
        icon="mdi:view-grid-outline",
        options=["2", "4", "6"],
        int_value=True,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameSelect(coordinator, entry, description) for description in SELECTS)


class PhotoFrameSelect(PhotoFrameEntity, SelectEntity):
    entity_description: PhotoFrameSelectDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: PhotoFrameSelectDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data["settings"].get(self.entity_description.key)
        return str(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        sent = int(option) if self.entity_description.int_value else option
        async with self.coordinator.async_writing():
            await self.coordinator.client.async_set_settings({self.entity_description.key: sent})
            await self.coordinator.async_request_refresh()
