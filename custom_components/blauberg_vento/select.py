"""Config flow for Blauberg Vento V.2 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_ID,
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
            int, vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=5, max=3600)
        ),
    }
)


class BlaubergVentoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Blauberg Vento V.2 config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host      = user_input[CONF_HOST].strip()
            port      = user_input[CONF_PORT]
            device_id = user_input[CONF_DEVICE_ID].strip()
            password  = user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)
            interval  = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            await self.async_set_unique_id(f"{host}:{port}:{device_id}")
            self._abort_if_unique_id_configured()

            try:
                ok = await self._probe(host, port, device_id, password)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error probing Vento device")
                errors["base"] = "unknown"
            else:
                if not ok:
                    errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Blauberg Vento ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_DEVICE_ID: device_id,
                        CONF_PASSWORD: password,
                        CONF_SCAN_INTERVAL: interval,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def _probe(
        self, host: str, port: int, device_id: str, password: str
    ) -> bool:
        """Send a minimal read packet and check for a valid response."""
        from .const import P_POWER
        from .coordinator import _udp_exchange
        from .protocol import build_read_packet, parse_response

        pkt = build_read_packet(device_id, password, [P_POWER])
        raw = await _udp_exchange(host, port, pkt, timeout=5.0)
        if raw is None:
            return False
        return bool(parse_response(raw))
