"""Shared base class for all Blauberg Vento entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VentoCoordinator


class VentoEntity(CoordinatorEntity[VentoCoordinator]):
    """Mixin that wires up unique_id and device_info for every Vento entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VentoCoordinator,
        entry: ConfigEntry,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Blauberg Vento ({coordinator.host})",
            "manufacturer": "Blauberg",
            "model": "Vento Expert W V.2/V.3",
            "configuration_url": f"udp://{coordinator.host}:{coordinator.port}",
        }
