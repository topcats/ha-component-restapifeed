"""TheOwls RESTAPI feed integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import RestApiFeedDevicesView, RestApiFeedFloorsView

_LOGGER = logging.getLogger(__name__)

DOMAIN = "theowls_restapifeed"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the REST API feed integration."""
    _LOGGER.info("TheOwls RESTAPI feed: integration starting")

    hass.http.register_view(RestApiFeedDevicesView)
    hass.http.register_view(RestApiFeedFloorsView)
    return True

