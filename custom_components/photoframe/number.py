"""Numeric settings from the web settings page, editable via POST /api/settings.

The frame's JSON settings API casts each of these to a specific Swift type
(`Int` or `Double`) rather than accepting either loosely, so `int_value`
tracks which one to send back — sending a float where an `Int` cast is
expected (or vice versa) is the kind of thing that works on some JSON
decoders and silently drops the write on others.

Excludes the on/off schedule times (`onTimeMinutes`/`offTimeMinutes`): the
JSON API doesn't accept writes to them at all (only the HTML form does),
so they're exposed read-only in sensor.py instead.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity


@dataclass(frozen=True, kw_only=True)
class PhotoFrameNumberDescription(NumberEntityDescription):
    int_value: bool = False


NUMBERS: tuple[PhotoFrameNumberDescription, ...] = (
    PhotoFrameNumberDescription(
        key="slideDuration",
        translation_key="slide_duration",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=1,
        native_max_value=300,
        native_step=1,
    ),
    PhotoFrameNumberDescription(
        key="transitionDuration",
        translation_key="transition_duration",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0.1,
        native_max_value=5,
        native_step=0.1,
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameNumberDescription(
        key="blurAmount",
        translation_key="blur_amount",
        icon="mdi:blur",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameNumberDescription(
        key="motionBlankTimeoutMinutes",
        translation_key="motion_blank_timeout",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=1,
        native_max_value=60,
        native_step=1,
        int_value=True,
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameNumberDescription(
        key="downloadCapMB",
        translation_key="download_cap",
        icon="mdi:harddisk",
        native_unit_of_measurement="MB",
        native_min_value=0,
        native_max_value=102400,
        native_step=256,
        int_value=True,
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameNumberDescription(
        key="liveTrimStart",
        translation_key="live_trim_start",
        icon="mdi:content-cut",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0,
        native_max_value=2,
        native_step=0.05,
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameNumberDescription(
        key="liveTrimEnd",
        translation_key="live_trim_end",
        icon="mdi:content-cut",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0,
        native_max_value=2,
        native_step=0.05,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameNumber(coordinator, entry, description) for description in NUMBERS)


class PhotoFrameNumber(PhotoFrameEntity, NumberEntity):
    entity_description: PhotoFrameNumberDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: PhotoFrameNumberDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data["settings"].get(self.entity_description.key)
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        sent = int(value) if self.entity_description.int_value else value
        await self.coordinator.client.async_set_settings({self.entity_description.key: sent})
        await self.coordinator.async_request_refresh()
