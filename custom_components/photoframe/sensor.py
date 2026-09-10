"""Read-only diagnostics and slideshow status sensors.

Most come from GET /api/status (live/runtime); the two schedule-time
sensors come from GET /api/settings instead — the on/off clock times are
part of the persisted settings blob, but the JSON settings API (unlike the
HTML settings form) doesn't accept writes to them, so they're read-only
here rather than a `number`/`time` entity.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import PhotoFrameEntity


def _minutes_to_clock(value: Any) -> str | None:
    if value is None:
        return None
    hours, minutes = divmod(int(value), 60)
    return f"{hours:02d}:{minutes:02d}"


@dataclass(frozen=True, kw_only=True)
class PhotoFrameSensorDescription(SensorEntityDescription):
    source: Literal["status", "settings"] = "status"
    attributes_from: tuple[str, ...] = ()
    transform: Callable[[Any], Any] | None = None


SENSORS: tuple[PhotoFrameSensorDescription, ...] = (
    PhotoFrameSensorDescription(
        key="photo_count",
        translation_key="photo_count",
        icon="mdi:image-multiple",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PhotoFrameSensorDescription(
        key="current_index",
        translation_key="slide_position",
        icon="mdi:image",
        entity_category=EntityCategory.DIAGNOSTIC,
        attributes_from=("current_total", "current_kind", "current_id", "current_date"),
    ),
    PhotoFrameSensorDescription(
        key="slide_duration",
        translation_key="slide_duration",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PhotoFrameSensorDescription(
        key="transition",
        translation_key="transition",
        icon="mdi:image-multiple-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PhotoFrameSensorDescription(
        key="memory_mb",
        translation_key="memory_usage",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PhotoFrameSensorDescription(
        key="peak_memory_mb",
        translation_key="peak_memory_usage",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PhotoFrameSensorDescription(
        key="last_sync",
        translation_key="last_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PhotoFrameSensorDescription(
        key="onTimeMinutes",
        translation_key="schedule_on_time",
        icon="mdi:clock-start",
        source="settings",
        entity_category=EntityCategory.DIAGNOSTIC,
        transform=_minutes_to_clock,
    ),
    PhotoFrameSensorDescription(
        key="offTimeMinutes",
        translation_key="schedule_off_time",
        icon="mdi:clock-end",
        source="settings",
        entity_category=EntityCategory.DIAGNOSTIC,
        transform=_minutes_to_clock,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameSensor(coordinator, entry, description) for description in SENSORS)


class PhotoFrameSensor(PhotoFrameEntity, SensorEntity):
    entity_description: PhotoFrameSensorDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: PhotoFrameSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        value = self.coordinator.data[self.entity_description.source].get(self.entity_description.key)
        if self.entity_description.transform is not None:
            return self.entity_description.transform(value)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP and value:
            return dt_util.parse_datetime(value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.attributes_from:
            return None
        status = self.coordinator.data["status"]
        return {key: status.get(key) for key in self.entity_description.attributes_from}
