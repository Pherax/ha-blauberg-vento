"""DataUpdateCoordinator for Blauberg Vento V.2 – async UDP transport."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_ID,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    POLL_PARAMS_DIAG,
    POLL_PARAMS_MAIN,
)
from .protocol import (
    build_dec_packet,
    build_inc_packet,
    build_read_packet,
    build_trigger_packet,
    build_write_packet,
    parse_response,
)

_LOGGER = logging.getLogger(__name__)


# ── Async UDP transport ───────────────────────────────────────────────────────

async def _udp_exchange(
    host: str,
    port: int,
    packet: bytes,
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes | None:
    """Send *packet* via UDP and return the first response datagram, or None."""
    loop = asyncio.get_running_loop()
    fut: asyncio.Future[bytes] = loop.create_future()

    class _Proto(asyncio.DatagramProtocol):
        def datagram_received(self, data: bytes, addr: tuple) -> None:
            if not fut.done():
                fut.set_result(data)

        def error_received(self, exc: Exception) -> None:
            if not fut.done():
                fut.set_exception(exc)

        def connection_lost(self, exc: Exception | None) -> None:
            if not fut.done():
                if exc:
                    fut.set_exception(exc)
                else:
                    fut.cancel()

    transport = None
    try:
        transport, _ = await loop.create_datagram_endpoint(
            _Proto, remote_addr=(host, port)
        )
        transport.sendto(packet)
        return await asyncio.wait_for(asyncio.shield(fut), timeout=timeout)
    except asyncio.TimeoutError:
        _LOGGER.debug("UDP timeout – %s:%d", host, port)
        return None
    except OSError as err:
        _LOGGER.debug("UDP error – %s:%d – %s", host, port, err)
        return None
    finally:
        if transport is not None:
            transport.close()


# ── Coordinator ───────────────────────────────────────────────────────────────

class VentoCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Poll a Vento V.2 master device and keep merged parameter state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        # CONF_HOST / CONF_PORT come from homeassistant.const ("host" / "port")
        self.host      = entry.data[CONF_HOST]
        self.port      = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.device_id = entry.data.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID)
        self.password  = entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
        interval       = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    # ── Polling ───────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[int, Any]:
        state: dict[int, Any] = {}

        # ── Main state (mandatory) ────────────────────────────────────────────
        pkt = build_read_packet(self.device_id, self.password, POLL_PARAMS_MAIN)
        raw = await _udp_exchange(self.host, self.port, pkt)
        if raw is None:
            raise UpdateFailed(
                f"No response from Blauberg Vento at {self.host}:{self.port}"
            )
        parsed = parse_response(raw)
        if not parsed:
            raise UpdateFailed(
                f"Invalid / empty response from {self.host}:{self.port}"
            )
        state.update(parsed)

        # ── Diagnostics (best-effort) ─────────────────────────────────────────
        pkt_diag = build_read_packet(self.device_id, self.password, POLL_PARAMS_DIAG)
        raw_diag = await _udp_exchange(self.host, self.port, pkt_diag)
        if raw_diag:
            state.update(parse_response(raw_diag))
        else:
            _LOGGER.debug("Diagnostic poll timed out – using cached values")

        return state

    # ── Write helpers ─────────────────────────────────────────────────────────

    async def async_write_param(
        self,
        param: int,
        value: int,
        value_size: int | None = None,
        refresh: bool = True,
    ) -> None:
        """Write a parameter (FUNC_WRITE_RESP) and optionally refresh state."""
        pkt = build_write_packet(self.device_id, self.password, param, value, value_size)
        await _udp_exchange(self.host, self.port, pkt)
        if refresh:
            await self.async_request_refresh()

    async def async_trigger(self, param: int) -> None:
        """Write-only trigger (FUNC_WRITE, no response): reset / factory reset."""
        pkt = build_trigger_packet(self.device_id, self.password, param)
        await _udp_exchange(self.host, self.port, pkt)
        await self.async_request_refresh()

    async def async_increment(self, param: int) -> None:
        pkt = build_inc_packet(self.device_id, self.password, param)
        await _udp_exchange(self.host, self.port, pkt)
        await self.async_request_refresh()

    async def async_decrement(self, param: int) -> None:
        pkt = build_dec_packet(self.device_id, self.password, param)
        await _udp_exchange(self.host, self.port, pkt)
        await self.async_request_refresh()

    # ── Probe (used by config flow) ───────────────────────────────────────────

    async def async_probe(self) -> bool:
        """Return True if the device responds with at least one valid parameter."""
        from .const import P_POWER
        pkt = build_read_packet(self.device_id, self.password, [P_POWER])
        raw = await _udp_exchange(self.host, self.port, pkt, timeout=5.0)
        if raw is None:
            return False
        return bool(parse_response(raw))
