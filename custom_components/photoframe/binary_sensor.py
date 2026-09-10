"""Runtime status flags that aren't persisted settings (see switch.py for those)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="paused", translation_key="paused", icon="mdi:pause", entity_category=EntityCategory.DIAGNOSTIC
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameBinarySensor(coordinator, entry, description) for description in BINARY_SENSORS)


class PhotoFrameBinarySensor(PhotoFrameEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, description: BinarySensorEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data["status"].get(self.entity_description.key)
        return bool(value) if value is not None else None
