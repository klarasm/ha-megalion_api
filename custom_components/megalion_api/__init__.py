"""The Megalion API integration."""

from megalion_http import Auth, MegalionHubAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import MegalionConfigEntry, MegalionCoordinator

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: MegalionConfigEntry) -> bool:
    """Set up Megalion API from a config entry."""

    auth = Auth(async_get_clientsession(hass), entry.data[CONF_HOST], "")
    await auth.update_token(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = MegalionCoordinator(hass, entry, MegalionHubAPI(auth))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True

# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: MegalionConfigEntry) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, _PLATFORMS)
