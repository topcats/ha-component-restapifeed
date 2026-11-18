"""Device lookup API view."""

from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.helpers import (
    area_registry,
    device_registry,
    label_registry,
)
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView

_LOGGER = logging.getLogger(__name__)


class RestApiFeedDevicesView(HomeAssistantView):
    """Return registered devices with their labels and area information."""

    url = "/api/restapifeed/devices"
    name = "api:restapifeed:devices"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Return device registry data as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Devices API called")

        hass = request.app[KEY_HASS]
        devices = device_registry.async_get(hass)
        areas = area_registry.async_get(hass)
        labels = label_registry.async_get(hass)

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
