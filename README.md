# ![Logo](https://raw.githubusercontent.com/topcats/ha-component-restapifeed/main/custom_components/theowls_restapifeed/brand/icon.png){height=24} TheOwls RESTAPI Feed (Home Assistant Integration)

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

Returns each floor's name, level, and assigned areas. Area entries include their registry ID and name; `level` is `null` when it is not set.

```json
{
 "floors": [
  {
   "name": "Ground floor",
   "level": 0,
   "areas": [
    {
     "id": "abcdef0123456789abcdef0123456789",
     "name": "Hallway"
    }
   ]
  }
 ]
}
```

## Versions

### V0.1.1 (November 2026)

- Initial Version
