# WEMO Home Automation Control System

A comprehensive Python application to discover and control WEMO smart devices on your home network without relying on WEMO's cloud service or Google Home integration.

## Overview

Since WEMO disabled their cloud service, this project uses the `pywemo` library to provide direct local control of WEMO devices on your home network. Features include:

- **Device Discovery**: Automatically detects all WEMO devices on your network
- **Power Control**: Turn devices on/off, toggle, and get real-time status
- **Timer Management**: Set timers for automatic device shutdown
- **REST API**: HTTP endpoints for remote control via any application
- **Interactive CLI**: User-friendly command-line interface for manual control

## Project Structure

```
wemo_project/
├── main.py                 # Main CLI application
├── api.py                  # Flask REST API server
├── device_discovery.py     # Device discovery module
├── device_controller.py    # Device control and timer management
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

### Prerequisites

- Python 3.7+
- WEMO devices on the same local network
- Network access to control devices locally

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify Network Connection**:
Ensure your computer is on the same network as your WEMO devices.

## Usage

### Option 1: Interactive CLI Application

Run the interactive menu-driven application:

```bash
python main.py
```

**Menu Options:**
- List all devices
- Turn device ON
- Turn device OFF
- Toggle device
- Get device status
- Set timer for device (auto-shutdown)
- View active timers
- Cancel timer
- Refresh device list

**Example Usage:**
```bash
$ python main.py

============================================================
WEMO Home Automation System
============================================================

Discovering WEMO devices on the network...

Found 3 WEMO device(s):

1. Living Room Lamp
   Type: Switch
   Model: Wemo Smart Plug
   Firmware: 1.2.3
   Serial: 94103E2P50A5A7
   Host: 192.168.1.100:49154

2. Kitchen Outlet
   Type: Switch
   Model: Wemo Smart Plug
   Firmware: 1.2.3
   Serial: 94103E2P50A5B8
   Host: 192.168.1.101:49154

3. Outdoor Light
   Type: Switch
   Model: Wemo Smart Plug
   Firmware: 1.2.3
   Serial: 94103E2P50A5C9
   Host: 192.168.1.102:49154
```

### Option 2: REST API Server

Start the Flask REST API for programmatic control:

```bash
python api.py
```

Server runs on `http://localhost:5000`

#### API Endpoints

**Health Check:**
```
GET /api/health
```

**List All Devices:**
```
GET /api/devices
Response:
{
  "success": true,
  "data": {
    "total_devices": 3,
    "devices": [
      {
        "name": "Living Room Lamp",
        "model": "Wemo Smart Plug",
        "device_type": "Switch",
        "host": "192.168.1.100",
        "port": 49154,
        "serial_number": "94103E2P50A5A7",
        "firmware_version": "1.2.3",
        "id": "94103E2P50A5A7"
      }
    ]
  }
}
```

**Get Device Status:**
```
GET /api/devices/{device_id}/status

Example:
GET /api/devices/94103E2P50A5A7/status

Response:
{
  "success": true,
  "status": {
    "device_id": "94103E2P50A5A7",
    "device_name": "Living Room Lamp",
    "online": true,
    "state": true,
    "power": 15.5,
    "brightness": null
  }
}
```

**Turn Device On:**
```
POST /api/devices/{device_id}/on

Example:
POST /api/devices/94103E2P50A5A7/on

Response:
{
  "success": true,
  "message": "Living Room Lamp turned on"
}
```

**Turn Device Off:**
```
POST /api/devices/{device_id}/off

Example:
POST /api/devices/94103E2P50A5A7/off

Response:
{
  "success": true,
  "message": "Living Room Lamp turned off"
}
```

**Toggle Device:**
```
POST /api/devices/{device_id}/toggle

Example:
POST /api/devices/94103E2P50A5A7/toggle

Response:
{
  "success": true,
  "message": "Living Room Lamp toggled",
  "state": true
}
```

**Set Timer (Auto-Shutdown):**
```
POST /api/devices/{device_id}/timer
Content-Type: application/json

{
  "duration_seconds": 3600
}

Example:
POST /api/devices/94103E2P50A5A7/timer
{
  "duration_seconds": 1800
}

Response:
{
  "success": true,
  "timer": {
    "device_id": "94103E2P50A5A7",
    "device_name": "Living Room Lamp",
    "timer_id": "94103E2P50A5A7_1234567890",
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T11:00:00",
    "duration_seconds": 1800,
    "remaining_seconds": 1800,
    "status": "active"
  }
}
```

**Get Active Timers:**
```
GET /api/timers

Response:
{
  "success": true,
  "total_timers": 2,
  "timers": {
    "94103E2P50A5A7_1234567890": {
      "device_id": "94103E2P50A5A7",
      "device_name": "Living Room Lamp",
      "remaining_seconds": 1200,
      "end_time": "2024-01-15T11:00:00"
    }
  }
}
```

**Cancel Timer:**
```
DELETE /api/devices/{device_id}/timer/{timer_id}

Example:
DELETE /api/devices/94103E2P50A5A7/timer/94103E2P50A5A7_1234567890

Response:
{
  "success": true,
  "message": "Timer cancelled for Living Room Lamp"
}
```

## Common Use Cases

### Set Timer for Device (30 minutes)
```bash
# Using API
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/timer \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 1800}'

# Device will automatically turn off after 30 minutes
```

### Control Multiple Devices
```bash
# Turn on living room lamp
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/on

# Turn off kitchen outlet
curl -X POST http://localhost:5000/api/devices/94103E2P50A5B8/off

# Set 1-hour timer for outdoor light
curl -X POST http://localhost:5000/api/devices/94103E2P50A5C9/timer \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 3600}'
```

### Integration with Home Assistant

You can integrate this API with Home Assistant or other automation platforms by creating HTTP switches:

```yaml
# Example Home Assistant configuration
switch:
  - platform: http
    name: "Living Room Lamp"
    resource: "http://localhost:5000/api/devices/94103E2P50A5A7"
    body_on: '{"state": "on"}'
    body_off: '{"state": "off"}'
    is_on_template: "{{ value_json.state }}"
```

## Troubleshooting

### No Devices Found

1. **Check Network Connection:**
   - Ensure your computer and WEMO devices are on the same WiFi network
   - Some networks separate IoT devices to a guest network

2. **Check Device Status:**
   - Ensure WEMO devices are powered on
   - Check if devices have the latest firmware

3. **Check Network Permissions:**
   - Look for firewall rules that might block device discovery
   - Try disabling Windows firewall temporarily for testing

4. **Enable Detailed Logging:**
   - Logs show discovery attempts and errors
   - Check the console output for diagnostics

### API Returns "Device Not Found"

- Verify the device_id is correct from `/api/devices`
- Device may have disconnected from network
- Try refreshing the device list

### Timer Not Working

- Ensure device is registered and responsive
- Check if device supports power control
- Review logs for error messages

## Technical Details

### Device Discovery

The discovery module uses UPNP (Universal Plug and Play) to find WEMO devices:
- Sends multicast discovery requests on the network
- Collects device information and network addresses
- Creates a local registry for quick access

### Timer Management

- Timers run in background threads (non-blocking)
- Accurate to within 1 second
- Device automatically turns off when timer expires
- Multiple timers can run simultaneously

### Network Communication

- Direct local communication with devices (no cloud connection)
- SOAP protocol for device control
- No internet dependency for operation

## Security Considerations

- **Local Network Only**: Devices are controlled locally without internet access
- **No Authentication**: This setup assumes a trusted local network
- **For Remote Access**: Add authentication/HTTPS in production deployment

## Future Enhancements

- [ ] Brightness control for dimmable devices
- [ ] Energy monitoring and logging
- [ ] Scheduling/automation rules
- [ ] Mobile app integration
- [ ] Scene management (multiple device control)
- [ ] REST API authentication
- [ ] Database persistence for statistics

## Dependencies

- `pywemo`: WEMO device control library
- `flask`: REST API framework
- `requests`: HTTP library
- `python-dotenv`: Environment configuration

## License

This project is provided as-is for personal use with WEMO devices.

## Support

For issues with:
- **pywemo library**: https://github.com/pywemo/pywemo
- **WEMO devices**: Check device manual or WEMO support
- **Python/Flask**: Refer to respective documentation

## Author

Created for WEMO device owners looking to maintain home automation after cloud service discontinuation.
