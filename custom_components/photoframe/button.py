"""One-shot playback/presence actions the frame's REST API exposes."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PhotoFrameEntity

_PLAYBACK_ACTIONS = {"next", "prev", "play", "pause"}

BUTTONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(key="next", translation_key="next_slide", icon="mdi:skip-next"),
    ButtonEntityDescription(key="prev", translation_key="previous_slide", icon="mdi:skip-previous"),
    ButtonEntityDescription(key="play", translation_key="play", icon="mdi:play"),
    ButtonEntityDescription(key="pause", translation_key="pause", icon="mdi:pause"),
    ButtonEntityDescription(
        key="presence",
        translation_key="ping_presence",
        icon="mdi:motion-sensor",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PhotoFrameButton(coordinator, entry, description) for description in BUTTONS)


class PhotoFrameButton(PhotoFrameEntity, ButtonEntity):
    def __init__(self, coordinator, entry: ConfigEntry, description: ButtonEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        key = self.entity_description.key
        if key in _PLAYBACK_ACTIONS:
            await self.coordinator.client.async_set_playback(key)
        elif key == "presence":
            await self.coordinator.client.async_ping_presence()
        await self.coordinator.async_request_refresh()
