"""Device lookup API view."""

from __future__ import annotations

import json
import logging

from aiohttp import web

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry,
    device_registry,
    entity_registry,
    label_registry,
)
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView

_LOGGER = logging.getLogger(__name__)


def _entity_data(
    hass: HomeAssistant, entry, devices, areas, labels
) -> dict[str, object]:
    """Return one entity's registry and state data."""
    device = devices.devices.get(entry.device_id) if entry.device_id else None
    entity_area_id = getattr(entry, "area_id", None)
    if not entity_area_id and device:
        entity_area_id = device.area_id
    entity_area = (
        areas.async_get_area(entity_area_id) if entity_area_id else None
    )

    label_ids = set(getattr(entry, "labels", ()) or ())
    if device:
        label_ids.update(device.labels)
    entity_labels = []
    for label_id in sorted(label_ids):
        label = labels.labels.get(label_id)
        entity_labels.append(
            {
                "id": label_id,
                "name": label.name if label else label_id,
            }
        )

    state = hass.states.get(entry.entity_id)
    entity_data = {
        "entity_id": entry.entity_id,
        "type": entry.domain,
        "name": (
            entry.name
            or getattr(entry, "original_name", None)
            or (state.name if state else None)
            or entry.entity_id
        ),
        "friendly_name": (
            state.attributes.get("friendly_name") if state else None
        ),
        "state": state.state if state else None,
        "icon": (
            (state.attributes.get("icon") if state else None)
            or entry.icon
            or getattr(entry, "original_icon", None)
        ),
        "parent_device": (
            {
                "id": device.id,
                "name": device.name_by_user or device.name or device.id,
            }
            if device
            else None
        ),
        "area": (
            {"id": entity_area.id, "name": entity_area.name}
            if entity_area
            else None
        ),
        "labels": entity_labels,
    }

    if state and state.attributes.get("device_class"):
        entity_data["device_class"] = state.attributes.get("device_class")

    if state and state.attributes.get("entity_picture"):
        entity_data["entity_picture"] = state.attributes.get("entity_picture")

    if state and state.attributes.get("unit_of_measurement"):
        entity_data["unit_of_measurement"] = state.attributes.get("unit_of_measurement")

    if entry.domain == "light" and state is not None:
        attributes = state.attributes
        if "effect" in attributes:
            entity_data["effect"] = attributes.get("effect")
        if "effect_list" in attributes:
            entity_data["effect_list"] = attributes.get("effect_list")
        if "brightness" in attributes:
            entity_data["brightness"] = attributes.get("brightness")
        if "rgb_color" in attributes:
            entity_data["rgb_color"] = attributes.get("rgb_color")
        if "hs_color" in attributes:
            entity_data["hs_color"] = attributes.get("hs_color")
        if "xy_color" in attributes:
            entity_data["xy_color"] = attributes.get("xy_color")
        if "color_temp_kelvin" in attributes:
            entity_data["color_temp_kelvin"] = attributes.get("color_temp_kelvin")

    return entity_data



class RestApiFeedDeviceList(HomeAssistantView):
    """Return registered entities with their state, labels, and area."""

    url = "/api/restapifeed/devices"
    name = "api:restapifeed:devices"
    requires_auth = True


    async def get(self, request: web.Request) -> web.Response:
        """Return entity registry data as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Devices API called")

        hass = request.app[KEY_HASS]
        devices = device_registry.async_get(hass)
        areas = area_registry.async_get(hass)
        entities = entity_registry.async_get(hass)
        labels = label_registry.async_get(hass)

        result = []
        entity_entries = sorted(
            (
                entry
                for entry in entities.entities.values()
                if entry.disabled_by is None
            ),
            key=lambda entry: entry.entity_id,
        )
        for entry in entity_entries:
            result.append(_entity_data(hass, entry, devices, areas, labels))

        result.sort(key=lambda entity: entity["name"].casefold())
        return self.json({"devices": result})



class RestApiFeedDeviceItem(HomeAssistantView):
    """Return one entity from the devices API."""

    url = "/api/restapifeed/devices/{entity_id}"
    name = "api:restapifeed:devices:item"
    requires_auth = True


    async def get(self, request: web.Request, entity_id: str) -> web.Response:
        """Return one entity's data as JSON."""
        _LOGGER.info("TheOwls RESTAPI feed: Device entity API called. Entity ID: %s", entity_id)

        hass = request.app[KEY_HASS]
        devices = device_registry.async_get(hass)
        areas = area_registry.async_get(hass)
        entities = entity_registry.async_get(hass)
        labels = label_registry.async_get(hass)

        entry = entities.entities.get(entity_id)
        if entry is None or entry.disabled_by is not None:
            raise web.HTTPNotFound()

        return self.json(_entity_data(hass, entry, devices, areas, labels))


    async def put(self, request: web.Request, entity_id: str) -> web.Response:
        """Set an entity's state and optionally its attributes."""
        _LOGGER.info("TheOwls RESTAPI feed: Device entity state update requested. Entity ID: %s", entity_id)

        hass = request.app[KEY_HASS]
        devices = device_registry.async_get(hass)
        areas = area_registry.async_get(hass)
        entities = entity_registry.async_get(hass)
        labels = label_registry.async_get(hass)

        entry = entities.entities.get(entity_id)
        if entry is None or entry.disabled_by is not None:
            raise web.HTTPNotFound()

        try:
            payload = await request.json()
        except json.JSONDecodeError as err:
            raise web.HTTPBadRequest(
                text="Request body must contain valid JSON."
            ) from err

        if not isinstance(payload, dict):
            raise web.HTTPBadRequest(
                text="Request body must be a JSON object."
            )
        if set(payload) - {"state", "attributes"}:
            raise web.HTTPBadRequest(
                text="Only 'state' and 'attributes' are supported."
            )

        new_state = payload.get("state")
        if not isinstance(new_state, str):
            raise web.HTTPBadRequest(
                text="'state' is required and must be a string."
            )

        current_state = hass.states.get(entity_id)
        if "attributes" in payload:
            attributes = payload["attributes"]
            if not isinstance(attributes, dict):
                raise web.HTTPBadRequest(
                    text="'attributes' must be a JSON object when provided."
                )
        else:
            attributes = (
                dict(current_state.attributes) if current_state else {}
            )

        hass.states.async_set(entity_id, new_state, attributes)
        return self.json(_entity_data(hass, entry, devices, areas, labels))
