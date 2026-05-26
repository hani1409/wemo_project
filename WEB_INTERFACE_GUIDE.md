# WEMO Web Interface Guide

## Overview

The WEMO Web Interface is a modern, user-friendly dashboard for discovering and controlling your WEMO devices from any web browser. It's built into the REST API server and accessed directly through your browser.

## Getting Started

### 1. Start the API Server

```bash
python api.py
```

You should see output like:
```
Starting WEMO Control API with Web Interface...
Open http://localhost:5000 in your browser
```

### 2. Open in Browser

Open your web browser and navigate to:
```
http://localhost:5000
```

The web interface will load with a modern, responsive dashboard.

## Features

### 🏠 Header Section
- **WEMO Home Control** title with emoji
- **🔍 Discover Devices** button - Manually trigger device discovery
- **🔄 Refresh** button - Update all device statuses and timers

### 🔌 My Devices Section

Displays all discovered WEMO devices in a responsive grid.

#### Device Card Features:
- **Device Name** - Your device's friendly name
- **Device Type** - Type of WEMO device (Switch, Plug, etc.)
- **Model** - Device model name
- **Host** - IP address and port
- **Status Indicator** - Shows if device is ON/OFF with real-time power consumption
- **Color Coding**:
  - 🟢 Green gradient = Device is ON
  - 🔴 Red/Orange gradient = Device is OFF

#### Device Controls:
- **Turn ON** - Power on the device immediately
- **Turn OFF** - Power off the device immediately
- **Toggle** - Switch device state

#### Timer Section (per device):
- **Input Field** - Enter duration in seconds (default: 1800 = 30 minutes)
- **Set Timer** - Activate auto-shutdown timer
  - Device turns ON when timer starts
  - Device automatically turns OFF after specified duration
  - Common durations:
    - 60 = 1 minute
    - 300 = 5 minutes
    - 900 = 15 minutes
    - 1800 = 30 minutes (default)
    - 3600 = 1 hour
    - 7200 = 2 hours

### ⏱️ Active Timers Section

Displays all currently active timers with real-time countdown.

#### Timer Card Shows:
- **Device Name** - Which device the timer is for
- **Remaining Time** - Time left in seconds
- **End Time** - When the timer will expire (local time)
- **Live Countdown** - Large countdown display that updates every second
- **Cancel Timer** - Red button to stop the timer and turn off the device

### 🎯 Alert System

Alerts appear at the top of the page and auto-dismiss after 4 seconds:
- **Blue (Info)** - General information (e.g., "Refreshing...")
- **Green (Success)** - Operation succeeded (e.g., "Device turned on")
- **Red (Error)** - Operation failed with error message

## How It Works

### Device Discovery
1. Click the **🔍 Discover Devices** button
2. Web interface queries the API for connected WEMO devices
3. Each device appears as a card in the grid
4. Status is automatically loaded for each device

### Controlling a Device
1. Find the device card
2. Click **Turn ON** to power on, **Turn OFF** to power off, or **Toggle** to switch
3. The device status updates immediately
4. Success/error message appears at top

### Setting a Timer
1. Find the device
2. Enter the duration in seconds in the timer input
3. Click **Set Timer**
4. Device turns ON and will auto-shutdown after the duration
5. Timer appears in the **Active Timers** section with countdown

### Canceling a Timer
1. Find the timer in the **Active Timers** section
2. Click the **Cancel Timer** button
3. Device immediately turns OFF
4. Timer disappears from the list

### Refreshing Data
1. Click the **🔄 Refresh** button
2. All device statuses and timers are updated
3. **Auto-refresh happens every 30 seconds automatically**

## User Interface Details

### Responsive Design
- Desktop: Multi-column grid layout
- Tablet: 2-column layout
- Mobile: Single column (full-width)

### Color Scheme
- **Purple gradient** - Page background
- **White cards** - Content containers
- **Green buttons** - Success/positive actions (Turn ON)
- **Red buttons** - Danger actions (Turn OFF, Cancel)
- **Orange buttons** - Warning actions (Set Timer)
- **Blue buttons** - Primary actions (Discover, Refresh)

### Loading States
- When discovering or loading devices, a **spinning loader** appears
- Provides visual feedback that action is in progress

### Real-time Updates
- **Device status** updates after each control action
- **Timer countdown** updates every second
- **Auto-refresh** every 30 seconds keeps data current

## Common Scenarios

### Scenario 1: Turn On Outdoor Light for 2 Hours
1. Find "Outdoor Light" card
2. Click "Turn ON"
3. Enter 7200 in timer field (2 hours in seconds)
4. Click "Set Timer"
5. Light turns on and will auto-off after 2 hours

### Scenario 2: Quick Device Status Check
1. Click **🔄 Refresh**
2. All device statuses load instantly
3. See which devices are on/off and power usage

### Scenario 3: Emergency Turn Off All Devices
1. Find each device card
2. Click "Turn OFF" for each device
3. All devices immediately power off

### Scenario 4: Monitor Active Timers
1. Look at **Active Timers** section
2. See countdown for each active timer
3. Remaining time updates every second
4. Cancel any timer by clicking its button

## Network Access

### Local Network Only (Default)
```
http://192.168.1.YOUR_COMPUTER_IP:5000
```

### Access from Another Computer on Network
1. Find your computer's IP address
2. On other computer, open browser
3. Navigate to `http://YOUR_IP:5000`

### Important
- All devices must be on the **same local network**
- Does NOT require internet connection
- No cloud dependency

## Troubleshooting

### Devices Not Showing
1. Ensure WEMO devices are powered on
2. All on same WiFi network
3. Click **🔍 Discover Devices** button
4. Check browser console for errors (F12)

### Timer Not Working
1. Ensure device is responsive
2. Try shorter duration first (60 seconds)
3. Click **🔄 Refresh**
4. Check alert messages for errors

### Interface Not Loading
1. Ensure API server is running (`python api.py`)
2. Correct URL: `http://localhost:5000`
3. Try refreshing browser (F5)
4. Check for firewall blocking port 5000

### Slow Updates
1. Check network connection
2. Ensure devices are powered on
3. Click **🔄 Refresh** manually
4. Auto-refresh runs every 30 seconds

## Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome | ✓ Full |
| Firefox | ✓ Full |
| Safari | ✓ Full |
| Edge | ✓ Full |
| Opera | ✓ Full |
| Mobile Browsers | ✓ Full (Responsive) |

## API Integration

The web interface uses these API endpoints:
- `GET /api/devices` - List all devices
- `GET /api/devices/{id}/status` - Get device status
- `POST /api/devices/{id}/on` - Turn on
- `POST /api/devices/{id}/off` - Turn off
- `POST /api/devices/{id}/toggle` - Toggle
- `POST /api/devices/{id}/timer` - Set timer
- `DELETE /api/devices/{id}/timer/{timer_id}` - Cancel timer
- `GET /api/timers` - Get active timers

## Security Notes

- Web interface runs **locally only** by default
- No authentication required for local network (assumes trusted network)
- For external/remote access, consider:
  - Adding authentication/HTTPS
  - Using VPN
  - Firewall rules
  - Reverse proxy with auth

## Performance Tips

1. **Minimize timers** - Each active timer uses a server thread
2. **Batch operations** - Control multiple devices together
3. **Use 30-second auto-refresh** - Manual refresh available anytime
4. **Close unused tabs** - Reduces polling overhead

## Keyboard Shortcuts

- **F5** - Refresh browser
- **F12** - Open developer tools
- **Escape** - Close any modals

## Tips & Tricks

1. **Set Multiple Timers** - Can run timers for many devices simultaneously
2. **Power Monitoring** - Watch real-time power consumption in status
3. **Device Organization** - Devices appear in discovery order
4. **Mobile Control** - Fully responsive, control from phone/tablet
5. **Status Colors** - Green = ON, Red = OFF for quick visual reference

## Future Features (Potential Enhancements)

- Device grouping/scenes
- Custom device names
- Timer history/logging
- Energy consumption charts
- Automatic scheduling
- Mobile app
- Voice control integration
- Dark mode toggle

---

**Made for WEMO device owners who want local, reliable home automation without cloud dependency!** 🏠
