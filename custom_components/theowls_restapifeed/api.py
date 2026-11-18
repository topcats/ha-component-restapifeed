"""TheOwls RESTAPI feed: HTTP API views for the integration."""

from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView
# from homeassistant.exceptions import Unauthorized, UnknownUser
from homeassistant.helpers import (
    area_registry,
    device_registry,
    entity_registry,
    floor_registry,
    label_registry,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_LABEL_DOMAINS = {
    "temp": "sensor",
    "lux": "sensor",
    "humid": "sensor",
    "pir": "binary_sensor",
    "door": "binary_sensor",
}



def lookup_sensors(hass: HomeAssistant, area_id: str) -> dict[str, str | None]:
    """Return one matching sensor entity ID for each label in an area."""
    devices = device_registry.async_get(hass)
    entities = entity_registry.async_get(hass)
    result = {label: None for label in SENSOR_LABEL_DOMAINS}

    for label, domain in SENSOR_LABEL_DOMAINS.items():
        for device in sorted(devices.devices.values(), key=lambda item: item.id):
            if device.area_id != area_id or label not in device.labels:
                continue

            matching_entities = sorted(
                (
                    entry
                    for entry in entity_registry.async_entries_for_device(
                        entities, device.id
                    )
                    if entry.domain == domain and entry.disabled_by is None
                ),
                key=lambda entry: entry.entity_id,
            )
            if matching_entities:
                result[label] = matching_entities[0].entity_id
            break

    return result



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



class RestApiFeedFloorsView(HomeAssistantView):
    """Return floors with their assigned areas."""

    url = "/api/restapifeed/floors"
    name = "api:restapifeed:floors"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Return floor names, levels, and areas as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Floors API called")

        hass = request.app[KEY_HASS]
        floors = floor_registry.async_get(hass)
        areas = area_registry.async_get(hass)

        # Build a list of floors with their areas
        result_floors = []
        for floor in floors.floors.values():
            floor_areas = area_registry.async_entries_for_floor(
                areas, floor.floor_id
            )
            result_floors.append(
                {
                    "id": floor.floor_id,
                    "name": floor.name,
                    "level": floor.level,
                    "icon": floor.icon,
                    "areas": [
                        {
                            "id": area.id, 
                            "name": area.name,
                            "icon": area.icon,
                            "picture": area.picture,
                            "sensors": lookup_sensors(hass, area.id)
                        }
                        for area in sorted(
                            floor_areas, key=lambda area: area.name.casefold()
                        )
                    ],
                }
            )
        result_floors.sort(key=lambda floor: floor["level"] if floor["level"] is not None else float("inf"))

        # Build a list of areas that are not assigned to any floor
        unassigned_areas = [
            {
                "id": area.id, 
                "name": area.name,
                "icon": area.icon,
                "picture": area.picture,
                "sensors": lookup_sensors(hass, area.id)
            }
            for area in areas.areas.values()
            if area.floor_id is None
        ]
        # Return the result as JSON
        return self.json({"floors": result_floors, "unassigned_areas": unassigned_areas})

