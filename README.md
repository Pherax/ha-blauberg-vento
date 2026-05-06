# Blauberg Vento – Home Assistant Integration

Custom integration for the Blauberg Vento Expert W series ventilation units (A30, A50, A85, A100, Duo A30). Communicates locally over UDP — no cloud required.

Tested on Home Assistant 2026.2.3.

---

## Requirements

- Home Assistant 2024.1 or newer
- Vento device on the same network as Home Assistant
- A static IP or DHCP reservation for the device

---

## Installation

1. Copy the `custom_components/blauberg_vento` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration → search for **Blauberg Vento**.

---

## Setup

| Field | Default | Notes |
|---|---|---|
| IP Address | `192.168.4.1` | Use `192.168.4.1` if connecting directly to the unit's hotspot. Otherwise use the IP assigned by your router. |
| UDP Port | `4000` | Don't change this. |
| Device ID | `DEFAULT_DEVICEID` | 16-character code printed on the PCB label inside the unit. `DEFAULT_DEVICEID` works in hotspot mode. |
| Password | `1111` | Changeable in the Blauberg mobile app. |
| Poll Interval | `30` | How often HA fetches state, in seconds. |

---

## Entities

**Fan**
- On/Off and three speed levels (Low / Medium / High)

**Select**
- Airflow mode — Ventilation, Heat Recovery, Air Supply
- Timer mode — Off, Night Mode, Party Mode
- Humidity sensor mode — Off, On, Inverted
- Relay sensor mode — Off, On, Inverted
- 0-10V sensor mode — Off, On, Inverted
- WiFi mode — Client, Access Point
- WiFi IP mode — Static, DHCP

**Sensor**
- Humidity, Fan 1 RPM, Fan 2 RPM
- Speed mode, Boost mode, Timer countdown
- Relay sensor state, 0-10V sensor value and status
- Alarm, Filter status, Filter replacement countdown
- Machine hours, RTC time and date, Firmware version
- RTC battery voltage, Unit type, Device IP address

**Number**
- Manual fan speed
- Supply and exhaust fan speed for each of the three modes
- Humidity and 0-10V trigger thresholds
- Night mode timer, Party mode timer, Boost delay
- Filter replacement interval

**Switch**
- Cloud control
- Weekly schedule

**Button**
- Reset filter timer
- Reset alarms
- Factory reset

---

## Protocol

Uses the Blauberg BGCP protocol (V.2/V.3) over UDP port 4000. Packet structure includes a 16-byte device ID, password, function code, and a 16-bit checksum. All communication is local — nothing is sent to external servers by this integration.

Reference: VENTO Expert (Duo) A30/50/85/100 W V.2/V.3 Connection Guide (Blauberg document B133-4-1EN-02).

---

## License

MIT
