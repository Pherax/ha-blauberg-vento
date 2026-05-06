"""Switch platform for Blauberg Vento V.2 – simple on/off parameters."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, P_CLOUD_CONTROL, P_SCHEDULE_MODE
from .coordinator import VentoCoordinator
from .entity_base import VentoEntity


@dataclass(frozen=True, kw_only=True)
class VentoSwitchDescription(SwitchEntityDescription):
    param_id: int


SWITCH_TYPES: tuple[VentoSwitchDescription, ...] = (
    VentoSwitchDescription(
        key="cloud_control",
        param_id=P_CLOUD_CONTROL,
        name="Cloud Control",
        icon="mdi:cloud",
        entity_category=EntityCategory.CONFIG,
    ),
    VentoSwitchDescription(
        key="schedule_mode",
        param_id=P_SCHEDULE_MODE,
        name="Weekly Schedule",
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VentoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VentoSwitch(coordinator, entry, desc) for desc in SWITCH_TYPES
    )


class VentoSwitch(VentoEntity, SwitchEntity):
    """Toggle switch for a Vento boolean parameter (0 = Off, 1 = On)."""

    entity_description: VentoSwitchDescription

    def __init__(
        self,
        coordinator: VentoCoordinator,
        entry: ConfigEntry,
        description: VentoSwitchDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get(self.entity_description.param_id, 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_param(self.entity_description.param_id, 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_param(self.entity_description.param_id, 0)
