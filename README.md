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
   "device_id": "0123456789abcdef0123456789abcdef",
   "name": "Hallway motion sensor",
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
  }
 ]
}
```

Devices without an assigned area return `"area": null`; devices without labels return an empty `labels` array. Labels include both registry ID and display name.

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
