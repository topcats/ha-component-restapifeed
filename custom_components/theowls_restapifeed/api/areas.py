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
from .floors import SENSOR_LABEL_DOMAINS

_LOGGER = logging.getLogger(__name__)


def _area_indexes(area_ids, devices, entities):
    """Index enabled entities and sensor IDs by area in linear passes."""
    entities_by_area = {area_id: [] for area_id in area_ids}
    sensors_by_area = {
        area_id: {label: None for label in SENSOR_LABEL_DOMAINS}
        for area_id in area_ids
    }
    selected_sensor_labels = {area_id: set() for area_id in area_ids}
    entities_by_device = {}

    enabled_entities = (
        entry
        for entry in entities.entities.values()
        if entry.disabled_by is None
    )
    for entry in sorted(enabled_entities, key=lambda item: item.entity_id):
        if entry.device_id:
            entities_by_device.setdefault(entry.device_id, []).append(entry)

        device = (
            devices.devices.get(entry.device_id)
            if entry.device_id
            else None
        )
        entity_area_id = getattr(entry, "area_id", None)
        if not entity_area_id and device:
            entity_area_id = device.area_id
        if entity_area_id in entities_by_area:
            entities_by_area[entity_area_id].append(entry)

    for device in sorted(devices.devices.values(), key=lambda item: item.id):
        area_id = device.area_id
        if area_id not in sensors_by_area:
            continue

        for label, domain in SENSOR_LABEL_DOMAINS.items():
            if (
                label not in device.labels
                or label in selected_sensor_labels[area_id]
            ):
                continue

            selected_sensor_labels[area_id].add(label)
            matching_entity = next(
                (
                    entry
                    for entry in entities_by_device.get(device.id, ())
                    if entry.domain == domain
                ),
                None,
            )
            if matching_entity is not None:
                sensors_by_area[area_id][label] = matching_entity.entity_id

    return entities_by_area, sensors_by_area


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

        area_ids = set(areas.areas)
        entities_by_area, sensors_by_area = _area_indexes(
            area_ids, devices, entities
        )
        result = []
        for area in sorted(
            areas.areas.values(), key=lambda item: item.name.casefold()
        ):
            area_data = _area_data(area, floors)
            area_data["sensors"] = sensors_by_area[area.id]
            area_data["entity_ids"] = [
                entry.entity_id for entry in entities_by_area[area.id]
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

        entities_by_area, sensors_by_area = _area_indexes(
            {area.id}, devices, entities
        )
        area_data = _area_data(area, floors)
        area_data["sensors"] = sensors_by_area[area.id]
        area_data["entities"] = [
            _entity_data(hass, entry, devices, areas, labels)
            for entry in entities_by_area[area.id]
        ]
        return self.json(area_data)
