"""Shared base entity — one Home Assistant device per frame."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PhotoFrameCoordinator


class PhotoFrameEntity(CoordinatorEntity[PhotoFrameCoordinator]):
    """Base for every entity belonging to one frame's config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PhotoFrameCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=entry.title,
            manufacturer="bammcm",
            model="iPad Photo Frame",
            configuration_url=f"https://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}/",
        )
