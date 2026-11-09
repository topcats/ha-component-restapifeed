"""TheOwls RESTAPI feed: HTTP API views for the integration."""

from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry,
    device_registry,
    floor_registry,
    label_registry,
)


class RestApiFeedDevicesView(HomeAssistantView):
    """Return registered devices with their labels and area information."""

    url = "/api/restapifeed/devices"
    name = "api:restapifeed:devices"
    requires_auth = True
    hass: HomeAssistant

    async def get(self, request: web.Request) -> web.Response:
        """Return device registry data as JSON."""
        devices = device_registry.async_get(self.hass)
        areas = area_registry.async_get(self.hass)
        labels = label_registry.async_get(self.hass)

        result = []
        for device in devices.devices.values():
            area = areas.async_get_area(device.area_id) if device.area_id else None
            device_labels = []
            for label_id in sorted(device.labels):
                label = labels.labels.get(label_id)
                device_labels.append(
                    {
                        "id": label_id,
                        "name": label.name if label else label_id,
                    }
                )

            result.append(
                {
                    "device_id": device.id,
                    "name": device.name_by_user or device.name or device.id,
                    "area": (
                        {"id": area.id, "name": area.name} if area else None
                    ),
                    "labels": device_labels,
                }
            )

        result.sort(key=lambda device: device["name"].casefold())
        return self.json({"devices": result})


class RestApiFeedFloorsView(HomeAssistantView):
    """Return floors with their assigned areas."""

    url = "/api/restapifeed/floors"
    name = "api:restapifeed:floors"
    requires_auth = True
    hass: HomeAssistant

    async def get(self, request: web.Request) -> web.Response:
        """Return floor names, levels, and areas as JSON."""
        floors = floor_registry.async_get(self.hass)
        areas = area_registry.async_get(self.hass)

        result = []
        for floor in floors.floors.values():
            floor_areas = area_registry.async_entries_for_floor(
                areas, floor.floor_id
            )
            result.append(
                {
                    "name": floor.name,
                    "level": floor.level,
                    "areas": [
                        {"id": area.id, "name": area.name}
                        for area in sorted(
                            floor_areas, key=lambda area: area.name.casefold()
                        )
                    ],
                }
            )

        result.sort(key=lambda floor: floor["name"].casefold())
        return self.json({"floors": result})
