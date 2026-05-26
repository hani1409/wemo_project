# WEMO Home Automation - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd wemo_project
pip install -r requirements.txt
```

### Step 2: Run the Application

Choose one of two options:

#### Option A: Interactive Menu (Easiest)
```bash
python main.py
```

This gives you a user-friendly menu to discover devices and control them.

#### Option B: REST API Server
```bash
python api.py
```

Then in another terminal, use curl or another HTTP client:
```bash
# List devices
curl http://localhost:5000/api/devices

# Turn on a device
curl -X POST http://localhost:5000/api/devices/{device_id}/on

# Set a 30-minute timer
curl -X POST http://localhost:5000/api/devices/{device_id}/timer \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 1800}'
```

### Step 3: Test the API (Optional)

If running the API server, test it in another terminal:
```bash
python test_api.py
```

---

## 📋 Common Tasks

### Discover My WEMO Devices
```bash
python main.py
# Select option 1: "List all devices"
```

### Turn a Device On
```bash
python main.py
# Select option 2: "Turn device ON"
# Choose device by number or name
```

### Set a Timer (Auto-Shutdown)
```bash
python main.py
# Select option 6: "Set timer for device"
# Enter duration in seconds (e.g., 1800 for 30 minutes)
# Device will automatically turn off when timer expires
```

### Monitor Active Timers
```bash
python main.py
# Select option 7: "View active timers"
```

---

## 🔌 Network Requirements

Your computer must be on the same **local network** as your WEMO devices:

✓ Computer and WEMO devices on same WiFi network  
✓ All devices can reach each other  
✗ NOT through VPN or guest network (usually doesn't work)

### Test Network Connection
```python
python -c "
import pywemo
devices = pywemo.discover_devices()
print(f'Found {len(devices)} devices')
"
```

---

## 🌐 Using the REST API

Start the API server:
```bash
python api.py
```

### Get Full Device List
```bash
curl http://localhost:5000/api/devices
```

### Control Specific Device
```bash
# Replace 94103E2P50A5A7 with your device's ID

# Get current status
curl http://localhost:5000/api/devices/94103E2P50A5A7/status

# Turn on
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/on

# Turn off
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/off

# Toggle
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/toggle

# Set timer (30 minutes = 1800 seconds)
curl -X POST http://localhost:5000/api/devices/94103E2P50A5A7/timer \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 1800}'

# View all active timers
curl http://localhost:5000/api/timers

# Cancel a timer
curl -X DELETE http://localhost:5000/api/devices/94103E2P50A5A7/timer/{timer_id}
```

---

## 🐛 Troubleshooting

### "No WEMO devices found"

1. **Check network connection:**
   ```bash
   # Ping one of your WEMO devices to verify network access
   ping 192.168.1.100  # Replace with your device's IP
   ```

2. **Check device status:**
   - Ensure WEMO devices are powered on
   - Check if they're connected to WiFi (look for LED indicators)
   - Firmware should be up-to-date

3. **Check firewall:**
   - Try disabling Windows Firewall temporarily for testing
   - Look for network discovery permissions in firewall settings

4. **Try reinstalling pywemo:**
   ```bash
   pip uninstall pywemo -y
   pip install pywemo==1.2.14
   ```

### "Device doesn't support power control"

Not all WEMO devices support turning on/off. Some devices may be:
- Motion sensors (read-only)
- Outdated firmware
- Different device type

Check the device type in the discovery output.

### Timer not working

1. Verify device turned on:
   ```bash
   python main.py  # Check device status
   ```

2. Try a longer duration (test with 60 seconds first)

3. Check logs for errors

---

## 💡 Example Scenarios

### Scenario 1: Control Outdoor Lights
```bash
# Set 4-hour timer for outdoor light (14,400 seconds)
python main.py
# Option 6 → Select "Outdoor Light" → 14400
```

### Scenario 2: Turn Off All Devices
```bash
python main.py

# Option 2 → Turn all devices OFF
# Repeat for each device
```

### Scenario 3: Automate with Scheduler
```python
# Save as schedule_devices.py
import schedule
import time
from device_discovery import get_discovery
from device_controller import get_controller

discovery = get_discovery()
controller = get_controller()
devices = discovery.discover_devices()

for device_info in devices:
    device = discovery.get_device_by_id(device_info.id)
    controller.register_device(device_info.id, device)

def turn_off_all():
    """Turn off all devices"""
    for device_id, device_info in controller.devices.items():
        controller.turn_off(device_id, device_info.name)

# Schedule to run every day at 11 PM
schedule.every().day.at("23:00").do(turn_off_all)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Run with: `python schedule_devices.py`

### Scenario 4: Integration with Home Assistant
Add to Home Assistant `configuration.yaml`:
```yaml
rest_command:
  wemo_living_room_on:
    url: "http://localhost:5000/api/devices/{{ device_id }}/on"
    method: POST

switch:
  - platform: rest
    name: "WEMO Living Room"
    resource: "http://localhost:5000/api/devices/94103E2P50A5A7/status"
```

---

## 📚 Project Files

| File | Purpose |
|------|---------|
| `main.py` | Interactive CLI application |
| `api.py` | Flask REST API server |
| `device_discovery.py` | Device discovery module |
| `device_controller.py` | Device control & timer logic |
| `example_usage.py` | Usage examples |
| `test_api.py` | API test script |
| `README.md` | Full documentation |
| `requirements.txt` | Python dependencies |

---

## 🆘 Need Help?

1. **Check README.md** for detailed documentation
2. **Run example_usage.py** for code examples
3. **Check logs** for error messages (they're helpful!)
4. **Test network** to ensure devices are reachable

---

## ✅ Next Steps

1. ✓ Install dependencies
2. ✓ Discover your WEMO devices
3. ✓ Test basic control (turn on/off)
4. ✓ Set a timer
5. ✓ Consider using the API for advanced automation

Good luck with your home automation setup! 🏠
