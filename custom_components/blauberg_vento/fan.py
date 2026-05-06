"""Constants for the Blauberg Vento V.2/V.3 Smart Home integration.

Protocol reference: VENTO Expert (Duo) A30/50/85/100 W V.2/V.3 Connection Guide
                    (Blauberg document B133-4-1EN-02)

Packet layout:
  0xFD 0xFD  TYPE  SIZE_ID  ID(16)  SIZE_PWD  PWD  FUNC  DATA  ChksumL  ChksumH

- TYPE       always 0x02
- SIZE_ID    always 0x10 (16)
- ID         16-byte device ID (ASCII from PCB label) or "DEFAULT_DEVICEID"
- SIZE_PWD   0-8 bytes
- PWD        device password (default "1111")
- FUNC       see FUNC_* constants below
- DATA       parameter numbers + values; special bytes 0xFC-0xFF
- Checksum   uint16 LE: sum of all bytes from TYPE through last DATA byte
"""
from __future__ import annotations

DOMAIN = "blauberg_vento"

# ── Network / config ──────────────────────────────────────────────────────────
DEFAULT_HOST          = "192.168.4.1"   # built-in AP (connection pattern 1)
DEFAULT_PORT          = 4000
DEFAULT_DEVICE_ID     = "DEFAULT_DEVICEID"  # exactly 16 chars
DEFAULT_PASSWORD      = "1111"
DEFAULT_SCAN_INTERVAL = 30             # seconds
DEFAULT_TIMEOUT       = 5.0            # seconds

CONF_DEVICE_ID    = "device_id"
CONF_PASSWORD     = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# ── Protocol framing ──────────────────────────────────────────────────────────
PACKET_START  = bytes([0xFD, 0xFD])
PROTOCOL_TYPE = 0x02
ID_BLOCK_SIZE = 16

# ── Function codes (FUNC byte) ────────────────────────────────────────────────
FUNC_READ       = 0x01   # read parameters; DATA = list of param low-bytes
FUNC_WRITE      = 0x02   # write, no response
FUNC_WRITE_RESP = 0x03   # write + request status response
FUNC_INC        = 0x04   # increment + response
FUNC_DEC        = 0x05   # decrement + response
FUNC_RESP       = 0x06   # controller response

# ── Special DATA-block commands ───────────────────────────────────────────────
CMD_FUNC_CHANGE   = 0xFC  # change FUNC; next byte = new FUNC code
CMD_NOT_SUPPORTED = 0xFD  # (response only) param not supported; next byte = low byte
CMD_SIZE_CHANGE   = 0xFE  # override value size; next byte = size, then param low byte
CMD_PAGE_CHANGE   = 0xFF  # change high byte; next byte = new high byte

# ── Parameter numbers (dec/hex as in spec) ────────────────────────────────────
P_POWER               = 0x0001  # R/W/RW      Unit On/Off  0=Off 1=On 2=Invert
P_SPEED               = 0x0002  # R/W/RW/I/D  Speed 1/2/3/255=manual
P_BOOST_STATUS        = 0x0006  # R           Boost 0=Off 1=On
P_TIMER_MODE          = 0x0007  # R/W/RW/I/D  0=Off 1=Night 2=Party
P_TIMER_COUNTDOWN     = 0x000B  # R   3 bytes  B1=sec B2=min B3=hr
P_HUMIDITY_SENSOR_EN  = 0x000F  # R/W/RW      0=Off 1=On 2=Invert
P_RELAY_SENSOR_EN     = 0x0014  # R/W/RW      0=Off 1=On 2=Invert
P_VOLTAGE_SENSOR_EN   = 0x0016  # R/W/RW      0=Off 1=On 2=Invert
P_HUMIDITY_THRESHOLD  = 0x0019  # R/W/RW/I/D  40-80 %RH
P_RTC_BATTERY_VOLTAGE = 0x0024  # R   2 bytes  0-5000 mV
P_CURRENT_HUMIDITY    = 0x0025  # R           0-100 %RH
P_VOLTAGE_SENSOR_VAL  = 0x002D  # R           0-100 %
P_RELAY_STATE         = 0x0032  # R           0=Off 1=On
P_SUPPLY_SPEED_1      = 0x003A  # R/W/RW/I/D  10-255 (V.3 only)
P_EXHAUST_SPEED_1     = 0x003B  # R/W/RW/I/D  10-255 (V.3 only)
P_SUPPLY_SPEED_2      = 0x003C  # R/W/RW/I/D  10-255 (V.3 only)
P_EXHAUST_SPEED_2     = 0x003D  # R/W/RW/I/D  10-255 (V.3 only)
P_SUPPLY_SPEED_3      = 0x003E  # R/W/RW/I/D  10-255 (V.3 only)
P_EXHAUST_SPEED_3     = 0x003F  # R/W/RW/I/D  10-255 (V.3 only)
P_MANUAL_SPEED        = 0x0044  # R/W/RW/I/D  0-255
P_FAN1_RPM            = 0x004A  # R   2 bytes  0-5000 rpm
P_FAN2_RPM            = 0x004B  # R   2 bytes  0-5000 rpm
P_FILTER_TIMER_SETUP  = 0x0063  # R/W/RW/I/D  70-365 days  2 bytes
P_FILTER_COUNTDOWN    = 0x0064  # R   3 bytes  B1=min B2=hr B3=days
P_FILTER_RESET        = 0x0065  # W           reset filter countdown
P_BOOST_DELAY         = 0x0066  # R/W/RW/I/D  0-60 min
P_RTC_TIME            = 0x006F  # R/W/RW  3 bytes  B1=sec B2=min B3=hr
P_RTC_CALENDAR        = 0x0070  # R/W/RW  4 bytes  B1=day B2=weekday B3=month B4=year
P_SCHEDULE_MODE       = 0x0072  # R/W/RW  0=Off 1=On 2=Invert
P_SCHEDULE_SETUP      = 0x0077  # R/W/RW  6 bytes  (complex – see spec)
P_DEVICE_SEARCH       = 0x007C  # R       16 bytes  ID text
P_DEVICE_PASSWORD     = 0x007D  # R/W/RW  0-8 bytes  text
P_MACHINE_HOURS       = 0x007E  # R   4 bytes  B1=min B2=hr B3-4=days
P_RESET_ALARMS        = 0x0080  # W           reset alarms
P_ALARM_STATUS        = 0x0083  # R   0=No 1=Alarm 2=Warning
P_CLOUD_CONTROL       = 0x0085  # R/W/RW  0=Off 1=On 2=Invert
P_FIRMWARE_VERSION    = 0x0086  # R   6 bytes  B1=major B2=minor B3=day B4=month B5-6=year
P_FACTORY_RESET       = 0x0087  # W           restore factory settings
P_FILTER_INDICATOR    = 0x0088  # R   0=OK 1=Replace
P_WIFI_MODE           = 0x0094  # R/W/RW/I/D  1=Client 2=AP
P_WIFI_SSID           = 0x0095  # R/W/RW  1-32 bytes  text
P_WIFI_PASSWORD       = 0x0096  # R/W/RW  8-64 bytes  text
P_WIFI_ENCRYPTION     = 0x0099  # R/W/RW  48=OPEN 50=WPA 51=WPA2 52=WPA/WPA2
P_WIFI_CHANNEL        = 0x009A  # R/W/RW/I/D  1-13
P_WIFI_DHCP           = 0x009B  # R/W/RW  0=STATIC 1=DHCP 2=Invert
P_WIFI_IP             = 0x009C  # R/W/RW  4 bytes  IP address
P_WIFI_SUBNET         = 0x009D  # R/W/RW  4 bytes  subnet mask
P_WIFI_GATEWAY        = 0x009E  # R/W/RW  4 bytes  gateway
P_WIFI_APPLY          = 0x00A0  # W           apply new WiFi params
P_WIFI_DISCARD        = 0x00A2  # W           discard new WiFi params
P_CURRENT_IP          = 0x00A3  # R   4 bytes  current IP
P_OPERATION_MODE      = 0x00B7  # R/W/RW/I/D  0=Ventilation 1=HeatRecovery 2=Supply
P_VOLTAGE_THRESHOLD   = 0x00B8  # R/W/RW/I/D  5-100 %
P_UNIT_TYPE           = 0x00B9  # R   2 bytes  unit type code
P_NIGHT_TIMER_SETPOINT= 0x0302  # R/W/RW  2 bytes  B1=min B2=hr
P_PARTY_TIMER_SETPOINT= 0x0303  # R/W/RW  2 bytes  B1=min B2=hr
P_HUMIDITY_SNS_STATUS = 0x0304  # R   0=below setpoint 1=over setpoint
P_VOLTAGE_SNS_STATUS  = 0x0305  # R   0=below setpoint 1=over setpoint

# ── Non-default parameter sizes (bytes) ───────────────────────────────────────
# The controller always uses 0xFE in responses for these.
# Also used as a fallback during parsing and when building write packets.
PARAM_SIZES: dict[int, int] = {
    P_TIMER_COUNTDOWN:     3,
    P_RTC_BATTERY_VOLTAGE: 2,
    P_FAN1_RPM:            2,
    P_FAN2_RPM:            2,
    P_FILTER_TIMER_SETUP:  2,
    P_FILTER_COUNTDOWN:    3,
    P_RTC_TIME:            3,
    P_RTC_CALENDAR:        4,
    P_SCHEDULE_SETUP:      6,
    P_DEVICE_SEARCH:       16,
    P_MACHINE_HOURS:       4,
    P_FIRMWARE_VERSION:    6,
    P_WIFI_IP:             4,
    P_WIFI_SUBNET:         4,
    P_WIFI_GATEWAY:        4,
    P_CURRENT_IP:          4,
    P_UNIT_TYPE:           2,
    P_NIGHT_TIMER_SETPOINT:2,
    P_PARTY_TIMER_SETPOINT:2,
}

# Parameters whose values are ASCII text (decode as str)
TEXT_PARAMS: frozenset[int] = frozenset({
    P_DEVICE_SEARCH, P_DEVICE_PASSWORD, P_WIFI_SSID, P_WIFI_PASSWORD,
})

# Parameters that are 4-byte IPv4 addresses (decode as dotted-decimal string)
IP_PARAMS: frozenset[int] = frozenset({
    P_WIFI_IP, P_WIFI_SUBNET, P_WIFI_GATEWAY, P_CURRENT_IP,
})

# ── Value maps ────────────────────────────────────────────────────────────────
SPEED_MAP: dict[int, str] = {
    1: "Speed 1", 2: "Speed 2", 3: "Speed 3", 255: "Manual",
}
# Preset speed % for the fan entity (manual = 255 → not mapped here)
SPEED_PCT_MAP: dict[int, int] = {1: 33, 2: 66, 3: 100}

OPERATION_MODE_MAP: dict[int, str] = {
    0: "Ventilation", 1: "Heat Recovery", 2: "Air Supply",
}
OPERATION_MODE_BY_NAME: dict[str, int] = {v: k for k, v in OPERATION_MODE_MAP.items()}

TIMER_MODE_MAP: dict[int, str] = {0: "Off", 1: "Night Mode", 2: "Party Mode"}
TIMER_MODE_BY_NAME: dict[str, int] = {v: k for k, v in TIMER_MODE_MAP.items()}

ALARM_MAP: dict[int, str] = {0: "OK", 1: "Alarm", 2: "Warning"}

SENSOR_ENABLE_MAP: dict[int, str] = {0: "Off", 1: "On", 2: "Inverted"}
SENSOR_ENABLE_BY_NAME: dict[str, int] = {v: k for k, v in SENSOR_ENABLE_MAP.items()}

WIFI_MODE_MAP: dict[int, str] = {1: "Client", 2: "Access Point"}
WIFI_MODE_BY_NAME: dict[str, int] = {v: k for k, v in WIFI_MODE_MAP.items()}

WIFI_DHCP_MAP: dict[int, str] = {0: "Static", 1: "DHCP"}
WIFI_DHCP_BY_NAME: dict[str, int] = {v: k for k, v in WIFI_DHCP_MAP.items()}

UNIT_TYPE_MAP: dict[int, str] = {
    3: "A50-1/A85-1/A100-1 W V.2",
    4: "Duo A30-1 W V.2",
    5: "A30 W V.2",
}

# ── Poll groups (split to stay well under 256-byte packet limit) ───────────────
# Main state — polled every cycle; failure → UpdateFailed
POLL_PARAMS_MAIN: list[int] = [
    P_POWER, P_SPEED, P_BOOST_STATUS, P_TIMER_MODE, P_TIMER_COUNTDOWN,
    P_HUMIDITY_SENSOR_EN, P_RELAY_SENSOR_EN, P_VOLTAGE_SENSOR_EN,
    P_HUMIDITY_THRESHOLD, P_CURRENT_HUMIDITY, P_VOLTAGE_SENSOR_VAL,
    P_RELAY_STATE, P_MANUAL_SPEED, P_FAN1_RPM, P_FAN2_RPM,
    P_BOOST_DELAY, P_FILTER_INDICATOR, P_ALARM_STATUS, P_CLOUD_CONTROL,
    P_OPERATION_MODE, P_VOLTAGE_THRESHOLD,
    # Page 0x03 params (need 0xFF page command in packet)
    P_NIGHT_TIMER_SETPOINT, P_PARTY_TIMER_SETPOINT,
    P_HUMIDITY_SNS_STATUS, P_VOLTAGE_SNS_STATUS,
]

# Diagnostics — non-critical; polled every cycle but failure is non-fatal
POLL_PARAMS_DIAG: list[int] = [
    P_RTC_BATTERY_VOLTAGE,
    P_SUPPLY_SPEED_1, P_EXHAUST_SPEED_1,
    P_SUPPLY_SPEED_2, P_EXHAUST_SPEED_2,
    P_SUPPLY_SPEED_3, P_EXHAUST_SPEED_3,
    P_FILTER_TIMER_SETUP, P_FILTER_COUNTDOWN,
    P_RTC_TIME, P_RTC_CALENDAR, P_SCHEDULE_MODE,
    P_MACHINE_HOURS, P_FIRMWARE_VERSION,
    P_WIFI_MODE, P_WIFI_DHCP, P_CURRENT_IP,
    P_UNIT_TYPE,
]
