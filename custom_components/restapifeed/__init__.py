"""TheOwls RESTAPI feed integration for Home Assistant."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import RestApiFeedDevicesView, RestApiFeedFloorsView


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the REST API feed integration."""
    hass.http.register_view(RestApiFeedDevicesView)
    hass.http.register_view(RestApiFeedFloorsView)
    return True
