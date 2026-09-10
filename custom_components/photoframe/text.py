"""Free-text settings from the web settings page, editable via POST /api/settings.

Deliberately excludes `frameName` and `webUsername` — editing either from
here risks breaking the very identity/auth this config entry relies on.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity


@dataclass(frozen=True, kw_only=True)
class PhotoFrameTextDescription(TextEntityDescription):
    pass


TEXTS: tuple[PhotoFrameTextDescription, ...] = (
    PhotoFrameTextDescription(
        key="weatherManualLocation",
        translation_key="weather_manual_location",
        icon="mdi:map-marker-outline",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameText(coordinator, entry, description) for description in TEXTS)


class PhotoFrameText(PhotoFrameEntity, TextEntity):
    entity_description: PhotoFrameTextDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: PhotoFrameTextDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data["settings"].get(self.entity_description.key)

    async def async_set_value(self, value: str) -> None:
        async with self.coordinator.async_writing():
            await self.coordinator.client.async_set_settings({self.entity_description.key: value})
            await self.coordinator.async_request_refresh()
