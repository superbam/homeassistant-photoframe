"""Boolean settings from the web settings page, editable via POST /api/settings.

Deliberately excludes a few boolean settings that exist in the web form:
`webServerEnabled` (turning it off via HA would cut the connection HA uses
to control it — the one setting that can brick this integration from
inside itself) and the frame-sync toggle (`syncFrames`, a multi-field
onboarding flow with an album picker that doesn't map cleanly onto a
single switch).
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity


@dataclass(frozen=True, kw_only=True)
class PhotoFrameSwitchDescription(SwitchEntityDescription):
    pass


SWITCHES: tuple[PhotoFrameSwitchDescription, ...] = (
    PhotoFrameSwitchDescription(key="muteVideo", translation_key="mute_video", icon="mdi:volume-off"),
    PhotoFrameSwitchDescription(key="shuffle", translation_key="shuffle", icon="mdi:shuffle"),
    PhotoFrameSwitchDescription(
        key="scheduleEnabled", translation_key="schedule_enabled", icon="mdi:clock-outline"
    ),
    PhotoFrameSwitchDescription(
        key="motionBlankingEnabled", translation_key="motion_blanking", icon="mdi:motion-sensor"
    ),
    PhotoFrameSwitchDescription(
        key="externalPresenceEnabled", translation_key="external_presence", icon="mdi:account-check"
    ),
    PhotoFrameSwitchDescription(key="collageMode", translation_key="collage_mode", icon="mdi:view-grid"),
    PhotoFrameSwitchDescription(
        key="randomizeTransitions", translation_key="randomize_transitions", icon="mdi:shuffle-variant",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="blurEdges", translation_key="blur_edges", icon="mdi:blur",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="showClock", translation_key="show_clock", icon="mdi:clock-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="clockUse24Hour", translation_key="clock_24_hour", icon="mdi:clock-time-four-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="showCaption", translation_key="show_caption", icon="mdi:closed-caption-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="showLocation", translation_key="show_location", icon="mdi:map-marker-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="showWeather", translation_key="show_weather", icon="mdi:weather-partly-cloudy",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="weatherUseDeviceLocation", translation_key="weather_use_device_location", icon="mdi:crosshairs-gps",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="showCalendar", translation_key="show_calendar", icon="mdi:calendar",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="videoPlaysToCompletion", translation_key="video_plays_to_completion", icon="mdi:play-speed",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="playLivePhotos", translation_key="play_live_photos", icon="mdi:motion-play-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="repeatLivePhotos", translation_key="repeat_live_photos", icon="mdi:repeat",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="loopLivePhotos", translation_key="loop_live_photos", icon="mdi:repeat-variant",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="usePerPhotoLiveSettings", translation_key="use_per_photo_live_settings", icon="mdi:image-edit-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    PhotoFrameSwitchDescription(
        key="downloadEnabled", translation_key="download_cache", icon="mdi:download-circle-outline",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameSwitch(coordinator, entry, description) for description in SWITCHES)


class PhotoFrameSwitch(PhotoFrameEntity, SwitchEntity):
    entity_description: PhotoFrameSwitchDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: PhotoFrameSwitchDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data["settings"].get(self.entity_description.key)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs) -> None:
        async with self.coordinator.async_writing():
            await self.coordinator.client.async_set_settings({self.entity_description.key: True})
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        async with self.coordinator.async_writing():
            await self.coordinator.client.async_set_settings({self.entity_description.key: False})
            await self.coordinator.async_request_refresh()
