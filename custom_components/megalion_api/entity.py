"""Bbase entity for the Megalion API integration"""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MegalionCoordinator


class MegalionEntity(CoordinatorEntity[MegalionCoordinator]):
    """Base class for Megalion entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: MegalionCoordinator, device_info: DeviceInfo
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        status = coordinator.data
        self._attr_device_info = device_info
