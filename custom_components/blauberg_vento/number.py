"""Blauberg Vento V.2/V.3 BGCP protocol implementation.

Packet structure (bytes):
  [0-1]  0xFD 0xFD           – start
  [2]    0x02                 – protocol type (TYPE)
  [3]    0x10                 – SIZE_ID (always 16)
  [4-19] <device_id>          – 16-byte ASCII ID
  [20]   <pwd_len>            – SIZE_PWD (0-8)
  [..]   <password>           – ASCII password bytes
  [+0]   FUNC                 – function code
  [+1..] DATA                 – parameter data
  [-2]   ChksumL              – checksum low byte
  [-1]   ChksumH              – checksum high byte

Checksum = uint16 sum of all bytes from TYPE (index 2) through the last DATA byte.
Byte order for multi-byte values: little-endian (LSB first).

DATA special commands:
  0xFF <page>         change high byte for following param numbers
  0xFE <size> <low>   override value size for the following parameter
  0xFC <func>         change function code mid-packet
  0xFD <low>          (response) parameter not supported
"""
from __future__ import annotations

import logging
from typing import Any

from .const import (
    PACKET_START, PROTOCOL_TYPE, ID_BLOCK_SIZE,
    FUNC_READ, FUNC_WRITE, FUNC_WRITE_RESP, FUNC_INC, FUNC_DEC, FUNC_RESP,
    CMD_PAGE_CHANGE, CMD_SIZE_CHANGE, CMD_FUNC_CHANGE, CMD_NOT_SUPPORTED,
    PARAM_SIZES, TEXT_PARAMS, IP_PARAMS,
    P_FIRMWARE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _encode_id(device_id: str) -> bytes:
    """Encode device ID to exactly ID_BLOCK_SIZE (16) ASCII bytes, zero-padded."""
    raw = device_id.encode("ascii")[:ID_BLOCK_SIZE]
    return raw.ljust(ID_BLOCK_SIZE, b"\x00")


def _encode_pwd(password: str) -> bytes:
    """Encode password as ASCII bytes (max 8)."""
    return password.encode("ascii")[:8]


def _checksum(payload: bytes) -> bytes:
    """Return 2-byte LE checksum over *payload* (which starts at TYPE byte).

    Per spec: sum of bytes from TYPE through last DATA byte, as uint16 LE.
    """
    total = sum(payload) & 0xFFFF
    return bytes([total & 0xFF, (total >> 8) & 0xFF])


def _build_frame(device_id: str, password: str, func: int, data: bytes) -> bytes:
    """Assemble a complete framed BGCP packet."""
    id_bytes  = _encode_id(device_id)
    pwd_bytes = _encode_pwd(password)
    # Payload = everything from TYPE byte onward (before checksum)
    payload = (
        bytes([PROTOCOL_TYPE, ID_BLOCK_SIZE])
        + id_bytes
        + bytes([len(pwd_bytes)])
        + pwd_bytes
        + bytes([func])
        + data
    )
    return PACKET_START + payload + _checksum(payload)


def _data_read(params: list[int]) -> bytes:
    """Build a DATA block for a FUNC_READ request.

    Inserts 0xFF page-change commands when the high byte of a parameter number
    changes.  The read DATA block contains only param IDs (no values).
    """
    data = bytearray()
    current_page = 0x00
    for p in params:
        high = (p >> 8) & 0xFF
        low  =  p       & 0xFF
        if high != current_page:
            data += bytes([CMD_PAGE_CHANGE, high])
            current_page = high
        data.append(low)
    return bytes(data)


def _data_write_single(param: int, value: int, value_size: int | None = None) -> bytes:
    """Build a DATA block to write one parameter.

    value_size, if provided, overrides PARAM_SIZES lookup.
    Uses 0xFE when size != 1, and 0xFF when high byte != 0x00.
    """
    size  = value_size if value_size is not None else PARAM_SIZES.get(param, 1)
    high  = (param >> 8) & 0xFF
    low   =  param       & 0xFF
    data  = bytearray()
    if high != 0x00:
        data += bytes([CMD_PAGE_CHANGE, high])
    if size > 1:
        # 0xFE <size> <param_low> <value LE bytes>
        data += bytes([CMD_SIZE_CHANGE, size, low])
        data += value.to_bytes(size, "little")
    else:
        data += bytes([low, value & 0xFF])
    return bytes(data)


# ── Public packet builders ────────────────────────────────────────────────────

def build_read_packet(device_id: str, password: str, params: list[int]) -> bytes:
    """Build FUNC_READ packet for a list of parameter numbers."""
    return _build_frame(device_id, password, FUNC_READ, _data_read(params))


def build_write_packet(
    device_id: str,
    password: str,
    param: int,
    value: int,
    value_size: int | None = None,
) -> bytes:
    """Build FUNC_WRITE_RESP packet (write + request echo response)."""
    data = _data_write_single(param, value, value_size)
    return _build_frame(device_id, password, FUNC_WRITE_RESP, data)


def build_trigger_packet(device_id: str, password: str, param: int) -> bytes:
    """Build FUNC_WRITE (no response) packet for write-only trigger parameters
    such as filter reset, alarm reset, and factory reset.
    Any non-zero byte is accepted; we use 0x01.
    """
    data = _data_write_single(param, 0x01, value_size=1)
    return _build_frame(device_id, password, FUNC_WRITE, data)


def build_inc_packet(device_id: str, password: str, param: int) -> bytes:
    """Build FUNC_INC packet (increment + response)."""
    return _build_frame(device_id, password, FUNC_INC, _data_read([param]))


def build_dec_packet(device_id: str, password: str, param: int) -> bytes:
    """Build FUNC_DEC packet (decrement + response)."""
    return _build_frame(device_id, password, FUNC_DEC, _data_read([param]))


# ── Packet verification ────────────────────────────────────────────────────────

def verify_packet(data: bytes) -> bool:
    """Return True if *data* has a valid start marker and correct checksum.

    Per the C example in the spec:
        for(i = 2; i <= size-3; i++) chksum1 += data[i];
        chksum2 = (data[size-1] << 8) | data[size-2];
    i.e. checksum covers indices [2 .. len-3] (inclusive).
    Checksum stored as LE at [len-2], [len-1].
    """
    if len(data) < 6:
        return False
    if data[0] != 0xFD or data[1] != 0xFD:
        return False
    expected = sum(data[2 : len(data) - 2]) & 0xFFFF
    received = data[-2] | (data[-1] << 8)
    if expected != received:
        _LOGGER.debug(
            "Checksum mismatch – expected 0x%04X got 0x%04X", expected, received
        )
        return False
    return True


# ── Response parser ───────────────────────────────────────────────────────────

def parse_response(raw: bytes) -> dict[int, Any]:
    """Parse a FUNC_RESP controller packet into {param_id: decoded_value}.

    Returns an empty dict on framing errors.

    Multi-byte integer values are decoded as Python int (LE).
    IP parameters are decoded as "a.b.c.d" strings.
    Text parameters are decoded as str (ASCII, null-stripped).
    Firmware version is decoded as a human-readable string.
    """
    if not verify_packet(raw):
        return {}
    if raw[2] != PROTOCOL_TYPE:
        _LOGGER.debug("Unexpected protocol type 0x%02X", raw[2])
        return {}

    # Locate FUNC byte
    # Layout: [0-1]=start [2]=TYPE [3]=SIZE_ID [4..4+SIZE_ID-1]=ID
    #         [4+SIZE_ID]=SIZE_PWD [4+SIZE_ID+1..]=PWD [FUNC][DATA...]
    pos     = 3                          # at SIZE_ID
    id_size = raw[pos];  pos += 1        # skip SIZE_ID, now at ID[0]
    pos    += id_size                    # skip ID, now at SIZE_PWD
    pwd_size= raw[pos];  pos += 1        # skip SIZE_PWD, now at PWD[0]
    pos    += pwd_size                   # skip PWD, now at FUNC

    func = raw[pos];  pos += 1
    if func != FUNC_RESP:
        _LOGGER.debug("Response FUNC=0x%02X is not FUNC_RESP (0x06)", func)
        return {}

    result: dict[int, Any] = {}
    page = 0x00
    end  = len(raw) - 2                  # exclude 2 checksum bytes

    while pos < end:
        b = raw[pos]

        # ── 0xFF: change page (high byte) ────────────────────────────────────
        if b == CMD_PAGE_CHANGE:
            pos += 1
            if pos >= end:
                break
            page = raw[pos]
            pos += 1
            continue

        # ── 0xFC: change function (skip new func byte) ────────────────────────
        if b == CMD_FUNC_CHANGE:
            pos += 2
            continue

        # ── 0xFD: parameter not supported ─────────────────────────────────────
        if b == CMD_NOT_SUPPORTED:
            pos += 1          # skip the unsupported param low byte
            if pos < end:
                pos += 1
            continue

        # ── 0xFE: size override — format is: 0xFE <size> <param_low> <value…> ─
        if b == CMD_SIZE_CHANGE:
            pos += 1
            if pos + 1 >= end:
                break
            size    = raw[pos];  pos += 1
            p_low   = raw[pos];  pos += 1
            param   = (page << 8) | p_low
            if pos + size > end:
                break
            result[param] = _decode_value(param, raw[pos : pos + size])
            pos += size
            continue

        # ── Regular parameter (default 1-byte value, or PARAM_SIZES override) ─
        p_low = b
        param = (page << 8) | p_low
        pos  += 1

        # Use PARAM_SIZES as a safety net for controllers that omit 0xFE.
        # Normally the controller uses 0xFE for all non-1-byte params, so
        # this branch handles them only as a fallback.
        size = PARAM_SIZES.get(param, 1)
        if pos + size > end:
            break
        result[param] = _decode_value(param, raw[pos : pos + size])
        pos += size

    return result


def _decode_value(param: int, raw: bytes) -> Any:
    """Decode raw bytes to a typed Python value."""
    if not raw:
        return None

    # IPv4 address
    if param in IP_PARAMS:
        if len(raw) >= 4:
            return ".".join(str(b) for b in raw[:4])
        return raw.hex()

    # Text (ASCII, null-stripped)
    if param in TEXT_PARAMS:
        try:
            return raw.rstrip(b"\x00").decode("ascii")
        except UnicodeDecodeError:
            return raw.hex()

    # Firmware version — 6 bytes: major, minor, day, month, year_lo, year_hi
    if param == P_FIRMWARE_VERSION:
        if len(raw) >= 6:
            major = raw[0]
            minor = raw[1]
            day   = raw[2]
            month = raw[3]
            year  = raw[4] | (raw[5] << 8)
            return f"{major}.{minor} ({day:02d}.{month:02d}.{year})"
        return raw.hex()

    # Everything else → integer, little-endian
    return int.from_bytes(raw, "little")
