"""Floor and area lookup API view."""

from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry,
    device_registry,
    entity_registry,
    floor_registry,
)
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView

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


def _floor_data(hass: HomeAssistant, floor, areas) -> dict[str, object]:
    """Return one floor and its assigned areas."""
    floor_areas = area_registry.async_entries_for_floor(areas, floor.floor_id)
    return {
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
                "sensors": lookup_sensors(hass, area.id),
            }
            for area in sorted(floor_areas, key=lambda area: area.name.casefold())
        ],
    }



class RestApiFeedFloorsList(HomeAssistantView):
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

        sorted_floors = sorted(
            floors.floors.values(),
            key=lambda floor: (
                floor.level
                if floor.level is not None
                else float("inf")
            )
        )
        result_floors = [
            _floor_data(hass, floor, areas) for floor in sorted_floors
        ]

        unassigned_areas = [
            {
                "id": area.id,
                "name": area.name,
                "icon": area.icon,
                "picture": area.picture,
                "sensors": lookup_sensors(hass, area.id),
            }
            for area in areas.areas.values()
            if area.floor_id is None
        ]
        return self.json(
            {"floors": result_floors, "unassigned_areas": unassigned_areas}
        )



class RestApiFeedFloorsItem(HomeAssistantView):
    """Return one floor with its assigned areas."""

    url = "/api/restapifeed/floors/{floor_id}"
    name = "api:restapifeed:floors:item"
    requires_auth = True

    async def get(self, request: web.Request, floor_id: str) -> web.Response:
        """Return one floor and its areas as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Floor API called. Floor ID: %s", floor_id)

        hass = request.app[KEY_HASS]
        floors = floor_registry.async_get(hass)
        floor = floors.floors.get(floor_id)
        if floor is None:
            raise web.HTTPNotFound()

        areas = area_registry.async_get(hass)
        return self.json(_floor_data(hass, floor, areas))
