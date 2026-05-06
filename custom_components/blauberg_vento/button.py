"""Number platform for Blauberg Vento V.2 – writable numeric parameters."""
from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    P_HUMIDITY_THRESHOLD, P_VOLTAGE_THRESHOLD, P_BOOST_DELAY, P_MANUAL_SPEED,
    P_FILTER_TIMER_SETUP,
    P_SUPPLY_SPEED_1, P_EXHAUST_SPEED_1,
    P_SUPPLY_SPEED_2, P_EXHAUST_SPEED_2,
    P_SUPPLY_SPEED_3, P_EXHAUST_SPEED_3,
    P_NIGHT_TIMER_SETPOINT, P_PARTY_TIMER_SETPOINT,
)
from .coordinator import VentoCoordinator
from .entity_base import VentoEntity


@dataclass(frozen=True, kw_only=True)
class VentoNumberDescription(NumberEntityDescription):
    param_id: int
    # value_size > 1 triggers explicit size encoding in write packets
    value_size: int = 1
    # Timer params: HA value in minutes; encoded as LE 2-byte (min | hr<<8)
    is_min_hr_timer: bool = False


NUMBER_TYPES: tuple[VentoNumberDescription, ...] = (
    # ── Fan speed calibration (V.3 only; no-op on V.2) ───────────────────────
    VentoNumberDescription(
        key="supply_speed_1",
        param_id=P_SUPPLY_SPEED_1,
        name="Supply Fan Speed – Mode 1",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="exhaust_speed_1",
        param_id=P_EXHAUST_SPEED_1,
        name="Exhaust Fan Speed – Mode 1",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="supply_speed_2",
        param_id=P_SUPPLY_SPEED_2,
        name="Supply Fan Speed – Mode 2",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="exhaust_speed_2",
        param_id=P_EXHAUST_SPEED_2,
        name="Exhaust Fan Speed – Mode 2",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="supply_speed_3",
        param_id=P_SUPPLY_SPEED_3,
        name="Supply Fan Speed – Mode 3",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="exhaust_speed_3",
        param_id=P_EXHAUST_SPEED_3,
        name="Exhaust Fan Speed – Mode 3",
        icon="mdi:fan",
        native_min_value=10, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="manual_speed",
        param_id=P_MANUAL_SPEED,
        name="Manual Fan Speed",
        icon="mdi:speedometer",
        native_min_value=0, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    # ── Sensor thresholds ─────────────────────────────────────────────────────
    VentoNumberDescription(
        key="humidity_threshold",
        param_id=P_HUMIDITY_THRESHOLD,
        name="Humidity Trigger Threshold",
        icon="mdi:water-percent",
        native_min_value=40, native_max_value=80, native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    VentoNumberDescription(
        key="voltage_threshold",
        param_id=P_VOLTAGE_THRESHOLD,
        name="0-10V Trigger Threshold",
        icon="mdi:sine-wave",
        native_min_value=5, native_max_value=100, native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    # ── Timers ────────────────────────────────────────────────────────────────
    # Night/Party timer setpoints: spec says B1=min(0-59) B2=hr(0-23)
    # HA value is in TOTAL MINUTES (0-1439); we encode/decode accordingly.
    VentoNumberDescription(
        key="night_timer",
        param_id=P_NIGHT_TIMER_SETPOINT,
        name="Night Mode Timer",
        icon="mdi:weather-night",
        native_min_value=0, native_max_value=1439, native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_size=2,
        is_min_hr_timer=True,
    ),
    VentoNumberDescription(
        key="party_timer",
        param_id=P_PARTY_TIMER_SETPOINT,
        name="Party Mode Timer",
        icon="mdi:party-popper",
        native_min_value=0, native_max_value=1439, native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_size=2,
        is_min_hr_timer=True,
    ),
    VentoNumberDescription(
        key="boost_delay",
        param_id=P_BOOST_DELAY,
        name="Boost Deactivation Delay",
        icon="mdi:timer-off-outline",
        native_min_value=0, native_max_value=60, native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    # Filter timer: 2-byte LE integer, value in days (no min/hr encoding)
    VentoNumberDescription(
        key="filter_timer_setup",
        param_id=P_FILTER_TIMER_SETUP,
        name="Filter Replacement Interval",
        icon="mdi:air-filter",
        native_min_value=70, native_max_value=365, native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_size=2,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VentoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VentoNumber(coordinator, entry, desc) for desc in NUMBER_TYPES
    )


class VentoNumber(VentoEntity, NumberEntity):
    """Writable numeric entity."""

    entity_description: VentoNumberDescription

    def __init__(
        self,
        coordinator: VentoCoordinator,
        entry: ConfigEntry,
        description: VentoNumberDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self.entity_description.param_id)
        if raw is None:
            return None
        if self.entity_description.is_min_hr_timer:
            # Stored as LE 2-byte: B1=min(0-59), B2=hr(0-23)
            mn = raw & 0xFF
            hr = (raw >> 8) & 0xFF
            return float(hr * 60 + mn)
        return float(raw)

    async def async_set_native_value(self, value: float) -> None:
        desc    = self.entity_description
        int_val = int(value)
        if desc.is_min_hr_timer:
            # Encode total minutes back to B1=min, B2=hr (LE 2-byte int)
            hr      = int_val // 60
            mn      = int_val % 60
            encoded = mn | (hr << 8)          # little-endian: mn at byte 0
            await self.coordinator.async_write_param(
                desc.param_id, encoded, value_size=2
            )
        elif desc.value_size > 1:
            await self.coordinator.async_write_param(
                desc.param_id, int_val, value_size=desc.value_size
            )
        else:
            await self.coordinator.async_write_param(desc.param_id, int_val)
