"""Coordinator for the Megalion API integration."""

from datetime import timedelta
import logging
from typing import override

from megalion_http import Battery, MegalionHubAPI, MegalionHubError, User

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type MegalionConfigEntry = ConfigEntry[MegalionHubAPI]


class MegalionStatus:
    def __init__(self, user: User, batteries: [Battery]):
        self.user = user
        self.batteries = {b.sn: b for b in batteries}


class MegalionCoordinator(DataUpdateCoordinator[MegalionStatus]):
    """Fetch data from the Megalion API."""

    config_entry: MegalionConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MegalionConfigEntry,
        hub: MegaLionHubAPI,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.hub = hub

    @override
    async def _async_update_data(self) -> MegalionStatus:
        """Fetch the latest data from the Megalion API."""
        try:
            batteries = await self.hub.async_get_batteries()
            user = await self.hub.async_get_user()
            return MegalionStatus(user, batteries)

        except MegalionHubError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
            ) from err
