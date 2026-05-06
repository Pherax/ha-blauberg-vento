{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Blauberg Vento V.2",
        "description": "Enter the connection details for your Vento master device.\n\n**Device ID** – the 16-character code printed on the PCB label (e.g. `002D6E1B34565815`). Leave as `DEFAULT_DEVICEID` when connecting in access-point mode without a router.",
        "data": {
          "host":           "IP Address",
          "port":           "UDP Port",
          "device_id":      "Device ID",
          "password":       "Device Password",
          "scan_interval":  "Poll Interval (seconds)"
        },
        "data_description": {
          "host":           "Static IP of the master device. Default 192.168.4.1 in built-in AP mode.",
          "device_id":      "16-character alphanumeric ID from the control board label.",
          "password":       "Default is 1111. Change via the mobile app → Connection → At home → Settings."
        }
      }
    },
    "error": {
      "cannot_connect": "Could not reach the device. Check IP address, port, Device ID and password.",
      "unknown":        "Unexpected error – check Home Assistant logs."
    },
    "abort": {
      "already_configured": "This Vento device is already configured."
    }
  }
}
