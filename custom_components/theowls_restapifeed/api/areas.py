"""Area lookup API views."""

from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.helpers import (
    area_registry,
    device_registry,
    entity_registry,
    floor_registry,
    label_registry,
)
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView

from .devices import _entity_data
from .floors import lookup_sensors

_LOGGER = logging.getLogger(__name__)


def _area_entities(area_id, devices, entities):
    """Return enabled entity registry entries assigned to an area."""
    result = []
    for entry in entities.entities.values():
        if entry.disabled_by is not None:
            continue

        device = (
            devices.devices.get(entry.device_id)
            if entry.device_id
            else None
        )
        entity_area_id = getattr(entry, "area_id", None)
        if not entity_area_id and device:
            entity_area_id = device.area_id
        if entity_area_id == area_id:
            result.append(entry)

    return sorted(result, key=lambda entry: entry.entity_id)


def _area_data(area, floors) -> dict[str, object]:
    """Return area registry details, including its floor when assigned."""
    floor = floors.floors.get(area.floor_id) if area.floor_id else None
    return {
        "id": area.id,
        "name": area.name,
        "icon": area.icon,
        "picture": area.picture,
        "floor": (
            {
                "id": floor.floor_id,
                "name": floor.name,
                "level": floor.level,
            }
            if floor
            else None
        ),
    }



class RestApiFeedAreaList(HomeAssistantView):
    """Return all areas with their entity IDs."""

    url = "/api/restapifeed/areas"
    name = "api:restapifeed:areas"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Return area registry data and entity IDs as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Areas API called")

        hass = request.app[KEY_HASS]
        areas = area_registry.async_get(hass)
        devices = device_registry.async_get(hass)
        entities = entity_registry.async_get(hass)
        floors = floor_registry.async_get(hass)

        result = []
        for area in sorted(
            areas.areas.values(), key=lambda item: item.name.casefold()
        ):
            area_data = _area_data(area, floors)
            area_data["sensors"] = lookup_sensors(hass, area.id)
            area_data["entity_ids"] = [
                entry.entity_id
                for entry in _area_entities(area.id, devices, entities)
            ]
            result.append(area_data)

        return self.json({"areas": result})



class RestApiFeedAreaItem(HomeAssistantView):
    """Return one area with full data for its entities."""

    url = "/api/restapifeed/areas/{area_id}"
    name = "api:restapifeed:areas:item"
    requires_auth = True

    async def get(self, request: web.Request, area_id: str) -> web.Response:
        """Return one area and its entities as JSON."""
        _LOGGER.info(
            "TheOwls RESTAPI feed: Area API called. Area ID: %s", area_id
        )

        hass = request.app[KEY_HASS]
        areas = area_registry.async_get(hass)
        area = areas.areas.get(area_id)
        if area is None:
            raise web.HTTPNotFound()

        devices = device_registry.async_get(hass)
        entities = entity_registry.async_get(hass)
        floors = floor_registry.async_get(hass)
        labels = label_registry.async_get(hass)

        area_data = _area_data(area, floors)
        area_data["sensors"] = lookup_sensors(hass, area.id)
        area_data["entities"] = [
            _entity_data(hass, entry, devices, areas, labels)
            for entry in _area_entities(area.id, devices, entities)
        ]
        return self.json(area_data)
