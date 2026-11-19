# ![Logo](https://raw.githubusercontent.com/topcats/ha-component-restapifeed/main/readicon.png) TheOwls RESTAPI Feed (Home Assistant Integration)

A Home Assistant custom integration that exposes registered devices, their labels, and their assigned areas (rooms) through a read-only REST endpoint.

## Installation

In HACS, add `https://github.com/topcats/ha-component-restapifeed` as a custom repository with the **Integration** category, then install **TheOwls RESTAPI Feed**. Alternatively, copy `custom_components/theowls_restapifeed` into the `custom_components` directory in your Home Assistant configuration directory and add this to `configuration.yaml`:

```yaml
theowls_restapifeed:
```

Restart Home Assistant to load the integration.

## Usage

### Devices Endpoint

`GET /api/restapifeed/devices`

The endpoint requires a Home Assistant access token. Include it as a bearer token in the `Authorization` header:

```http
Authorization: Bearer YOUR_LONG_LIVED_ACCESS_TOKEN
```

Example response:

```json
{
 "devices": [
  {
   "entity_id": "binary_sensor.hallway_motion",
   "type": "binary_sensor",
   "name": "Hallway motion",
   "friendly_name": "Hallway motion",
   "state": "on",
   "icon": "mdi:motion-sensor",
   "parent_device": {
    "id": "0123456789abcdef0123456789abcdef",
    "name": "Hallway motion sensor"
   },
   "area": {
    "id": "abcdef0123456789abcdef0123456789",
    "name": "Hallway"
   },
   "labels": [
    {
     "id": "1234567890abcdef1234567890abcdef",
     "name": "Battery powered"
    }
   ]
  },
  {
   "entity_id": "light.living_room",
   "type": "light",
   "name": "Living Room",
   "friendly_name": "Living Room",
   "state": "on",
   "icon": "mdi:lightbulb",
   "parent_device": {
    "id": "fedcba0987654321fedcba0987654321",
    "name": "Living Room Light"
   },
   "area": {
    "id": "abcdef0123456789abcdef0123456789",
    "name": "Living Room"
   },
   "labels": [],
   "brightness": 204,
   "rgb_color": [255, 180, 90],
   "hs_color": [32, 65],
   "xy_color": [0.51, 0.41],
   "color_temp_kelvin": null
  }
 ]
}
```

Entities without an assigned area return `"area": null`; entities without labels return an empty `labels` array. Labels include both registry ID and display name.
The `devices` array contains enabled Home Assistant entities rather than device registry entries. Each entity includes its entity ID, domain type, display name, friendly name, current state, icon, parent device ID and name, area, and labels. `friendly_name` is the value of the entity's Home Assistant state attribute, or `null` when no state or friendly name is available. The icon is the effective state icon when available, falling back to the entity registry icon; it is `null` when neither is set. `parent_device` and `area` are `null` when unavailable. Area and labels inherited from a parent device are included; entity-specific labels are included too. The `state` field is `null` when unavailable.

Light entities include `color_temp_kelvin` (which is `null` when unavailable) and may include `brightness`, `rgb_color`, `hs_color`, and `xy_color` when Home Assistant provides those state attributes.

### Single Entity Endpoint

`GET /api/restapifeed/devices/{entity_id}`

Returns the same entity object as an item in the devices list. For example:

```http
GET /api/restapifeed/devices/light.living_room
```

An unknown or disabled entity returns `404`.

`PUT /api/restapifeed/devices/{entity_id}` calls the entity domain's `turn_on` or `turn_off` service. The required `state` must be `"on"` or `"off"`. Light entities may also receive `brightness`, `color_temp_kelvin`, `effect`, `hs_color`, `rgb_color`, or `xy_color` service attributes when turning on:

```json
{
 "state": "on",
 "attributes": {
  "brightness": 180
 }
}
```

The response contains the entity's latest state after the service call. Unsupported domains or attributes return `400`; unknown or disabled entities return `404`. These service calls control the entity through its Home Assistant integration, unlike direct state-machine updates.

### Areas Endpoint

`GET /api/restapifeed/areas`

Returns all areas, including their ID, name, icon, picture, assigned floor (or `null`), sensor IDs, and IDs of enabled entities assigned to each area. Entity-specific area assignments take precedence over the parent device's area.

```json
{
 "areas": [
  {
   "id": "abcdef0123456789abcdef0123456789",
   "name": "Hallway",
   "icon": "mdi:door",
   "picture": null,
   "floor": {
    "id": "ground_floor",
    "name": "Ground floor",
    "level": 0
   },
   "sensors": {
    "temp": "sensor.hallway_temperature",
    "lux": null,
    "humid": null,
    "pir": "binary_sensor.hallway_motion",
    "door": null
   },
   "entity_ids": [
    "binary_sensor.hallway_motion",
    "sensor.hallway_temperature"
   ]
  }
 ]
}
```

`GET /api/restapifeed/areas/{area_id}`

Returns one area with the same area information, plus an `entities` array containing full entity objects for each enabled entity in that area. Each object matches the devices endpoint response format. An unknown `area_id` returns `404`.

### Floors Endpoint

`GET /api/restapifeed/floors`

Returns each floor's registry ID, name, level, icon, and assigned areas. Area entries include their registry ID, name, icon, picture, and matching sensor entity IDs. `level` and `icon` are `null` when they are not set. Areas without a floor are returned in `unassigned_areas`.

```json
{
 "floors": [
  {
   "id": "ground_floor",
   "name": "Ground floor",
   "level": 0,
   "icon": "mdi:home",
   "areas": [
    {
     "id": "abcdef0123456789abcdef0123456789",
     "name": "Hallway",
     "icon": "mdi:door",
     "picture": null,
     "sensors": {
      "temp": "sensor.hallway_temperature",
      "lux": "sensor.hallway_illuminance",
      "humid": "sensor.hallway_humidity",
      "pir": "binary_sensor.hallway_motion",
      "door": "binary_sensor.hallway_door"
     }
    }
   ]
  }
 ],
 "unassigned_areas": [
  {
   "id": "1234567890abcdef1234567890abcdef",
   "name": "Garage",
   "icon": "mdi:garage",
   "picture": null,
   "sensors": {
    "temp": null,
    "lux": null,
    "humid": null,
    "pir": "binary_sensor.garage_motion",
    "door": null
   }
  }
 ]
}
```

### Single Floor Endpoint

`GET /api/restapifeed/floors/{floor_id}`

Returns the same fields as one floor in the floors list. The response is the
floor object directly; an unknown `floor_id` returns `404`.

```json
{
 "id": "ground_floor",
 "name": "Ground floor",
 "level": 0,
 "icon": "mdi:home",
 "areas": [
  {
   "id": "abcdef0123456789abcdef0123456789",
   "name": "Hallway",
   "icon": "mdi:door",
   "picture": null,
   "sensors": {
    "temp": "sensor.hallway_temperature",
    "lux": "sensor.hallway_illuminance",
    "humid": "sensor.hallway_humidity",
    "pir": "binary_sensor.hallway_motion",
    "door": "binary_sensor.hallway_door"
   }
  }
 ]
}
```

## Versions

### V0.1.2 (November 2026)

- Working Readonly version
- Can grab:
  - Floors List
  - Flour Item
  - Devices List
- Floors also includes the required sensors for each Area (room)

### V0.1.1 (November 2026)

- Initial Version
