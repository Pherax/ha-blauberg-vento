"""Button platform for Blauberg Vento V.2 – write-only trigger parameters."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, P_FILTER_RESET, P_RESET_ALARMS, P_FACTORY_RESET
from .coordinator import VentoCoordinator
from .entity_base import VentoEntity


@dataclass(frozen=True, kw_only=True)
class VentoButtonDescription(ButtonEntityDescription):
    param_id: int


BUTTON_TYPES: tuple[VentoButtonDescription, ...] = (
    VentoButtonDescription(
        key="filter_reset",
        param_id=P_FILTER_RESET,
        name="Reset Filter Timer",
        icon="mdi:air-filter",
        entity_category=EntityCategory.CONFIG,
    ),
    VentoButtonDescription(
        key="reset_alarms",
        param_id=P_RESET_ALARMS,
        name="Reset Alarms",
        icon="mdi:alarm-off",
        entity_category=EntityCategory.CONFIG,
    ),
    VentoButtonDescription(
        key="factory_reset",
        param_id=P_FACTORY_RESET,
        name="Factory Reset",
        icon="mdi:restore",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VentoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VentoButton(coordinator, entry, desc) for desc in BUTTON_TYPES
    )


class VentoButton(VentoEntity, ButtonEntity):
    """Button that sends a FUNC_WRITE (no-response) packet to trigger an action."""

    entity_description: VentoButtonDescription

    def __init__(
        self,
        coordinator: VentoCoordinator,
        entry: ConfigEntry,
        description: VentoButtonDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await self.coordinator.async_trigger(self.entity_description.param_id)
