"""
Updated Flask REST API with web interface
Serves both API and web UI
"""

from flask import Flask, jsonify, request, g, render_template_string
import logging
import threading
import json
import time
from datetime import datetime
from pathlib import Path
from device_discovery import get_discovery
from device_controller import get_controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SCHEDULE_FILE = Path(__file__).resolve().parent / 'schedules.json'
DEVICE_NAMES_FILE = Path(__file__).resolve().parent / 'device_names.json'
schedule_lock = threading.Lock()
triggered_schedule_cache = {}
schedule_thread_started = False


def load_schedules():
    if not SCHEDULE_FILE.exists():
        return {}
    try:
        with schedule_lock, SCHEDULE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Could not load schedules: {e}')
        return {}


def save_schedules(schedules):
    try:
        with schedule_lock:
            SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with SCHEDULE_FILE.open('w', encoding='utf-8') as f:
                json.dump(schedules, f, indent=2)
        return schedules
    except Exception as e:
        logger.error(f'Could not save schedules: {e}')
        raise


def load_device_names():
    if not DEVICE_NAMES_FILE.exists():
        return {}
    try:
        with schedule_lock, DEVICE_NAMES_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Could not load device names: {e}')
        return {}


def save_device_names(names):
    try:
        with schedule_lock:
            DEVICE_NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with DEVICE_NAMES_FILE.open('w', encoding='utf-8') as f:
                json.dump(names, f, indent=2)
        return names
    except Exception as e:
        logger.error(f'Could not save device names: {e}')
        raise


def _schedule_key(device_id, action, time_key):
    return f'{device_id}:{action}:{time_key}'


def should_trigger_schedule(device_id, action, time_key):
    key = _schedule_key(device_id, action, time_key)
    now = time.time()
    if key in triggered_schedule_cache and now - triggered_schedule_cache[key] < 90:
        return False
    triggered_schedule_cache[key] = now
    return True


def schedule_runner():
    while True:
        schedules = load_schedules()
        current = datetime.now()
        day_index = (current.weekday() + 1) % 7
        current_time = current.strftime('%H:%M')

        for device_id, schedule in schedules.items():
            if not isinstance(schedule, dict):
                continue
            days = schedule.get('days')
            if not isinstance(days, list) or len(days) != 7:
                continue
            day_schedule = days[day_index]
            if not day_schedule or not day_schedule.get('enabled'):
                continue

            on_time = day_schedule.get('onTime')
            off_time = day_schedule.get('offTime')

            if on_time == current_time and should_trigger_schedule(device_id, 'on', current_time):
                try:
                    controller = get_controller()
                    controller.turn_on(device_id, device_id)
                    logger.info(f'Scheduled ON triggered for {device_id} at {current_time}')
                except Exception as e:
                    logger.error(f'Error triggering scheduled ON for {device_id}: {e}')

            if off_time == current_time and should_trigger_schedule(device_id, 'off', current_time):
                try:
                    controller = get_controller()
                    controller.turn_off(device_id, device_id)
                    logger.info(f'Scheduled OFF triggered for {device_id} at {current_time}')
                except Exception as e:
                    logger.error(f'Error triggering scheduled OFF for {device_id}: {e}')

        time.sleep(30)


@app.before_request
def start_schedule_thread():
    global schedule_thread_started
    if not schedule_thread_started:
        schedule_thread_started = True
        thread = threading.Thread(target=schedule_runner, daemon=True)
        thread.start()

# HTML Template for web interface
WEB_INTERFACE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WEMO Home Automation Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            color: #333;
            font-size: 28px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #666;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ccc;
            animation: pulse 2s infinite;
        }

        .status-dot.connected {
            background: #4caf50;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .controls {
            display: flex;
            gap: 10px;
        }

        button {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5568d3;
        }

        .btn-danger {
            background: #f44336;
            color: white;
        }

        .btn-danger:hover {
            background: #da190b;
        }

        .btn-warning {
            background: #ff9800;
            color: white;
        }

        .btn-warning:hover {
            background: #e68900;
        }

        .btn-success {
            background: #4caf50;
            color: white;
        }

        .btn-success:hover {
            background: #45a049;
        }

        .section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 22px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .devices-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 50px;
            grid-auto-rows: auto;
        }

        .device-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .device-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.22);
        }

        .device-card.powered-on {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        }

        .device-card.powered-off {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }

        .device-name {
            font-size: 18px;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
        }

        .device-info {
            font-size: 12px;
            color: #666;
            margin-bottom: 15px;
            line-height: 1.6;
        }

        .device-info-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }

        .device-status {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 15px;
            padding: 8px 12px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.7);
        }

        .device-status.on {
            color: #4caf50;
        }

        .device-status.off {
            color: #f44336;
        }

        .device-controls {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }

        .device-controls button {
            flex: 1;
            min-width: 60px;
            padding: 8px 12px;
            font-size: 12px;
        }

        .timer-section {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 6px;
            padding: 12px;
            margin-top: 15px;
        }

        .timer-form {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }

        .timer-form input {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
        }

        .timer-form input::placeholder {
            color: #999;
        }

        .timer-form button {
            padding: 6px 12px;
            min-width: 80px;
        }

        .brightness-section {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 6px;
            padding: 12px;
            margin: 15px 0;
        }

        .brightness-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: 600;
            color: #333;
        }

        .brightness-value {
            font-weight: 700;
            color: #667eea;
        }

        .brightness-slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: linear-gradient(to right, #ccc, #667eea);
            outline: none;
            -webkit-appearance: none;
            appearance: none;
            cursor: pointer;
        }

        .brightness-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
        }

        .brightness-slider::-webkit-slider-thumb:hover {
            transform: scale(1.2);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .brightness-slider::-moz-range-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
        }

        .brightness-slider::-moz-range-thumb:hover {
            transform: scale(1.2);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .schedule-section {
            background: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            box-shadow: inset 0 0 0 1px rgba(102, 126, 234, 0.15);
        }

        .schedule-title {
            font-size: 14px;
            font-weight: 700;
            color: #333;
            margin-bottom: 12px;
        }

        .schedule-grid {
            display: grid;
            grid-template-columns: max-content minmax(120px, 1fr) minmax(120px, 1fr) minmax(70px, 70px);
            gap: 8px;
            align-items: center;
            margin-bottom: 12px;
            min-width: 0;
        }

        .schedule-row {
            display: contents;
        }

        .schedule-cell {
            padding: 4px 6px;
            font-size: 12px;
            color: #444;
            min-width: 0;
        }

        .schedule-input {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            color: #333;
            box-sizing: border-box;
            min-width: 0;
        }

        .schedule-header {
            font-weight: 700;
            color: #222;
        }

        .schedule-input {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            color: #333;
        }

        .schedule-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .schedule-actions button {
            flex: 1;
            min-width: 100px;
            padding: 8px 10px;
        }

        .timers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }

        .timer-card {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .timer-card h4 {
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }

        .timer-info {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.5;
        }

        .timer-countdown {
            font-size: 18px;
            font-weight: 700;
            color: #f44336;
            margin-bottom: 10px;
            text-align: center;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .empty-state svg {
            width: 60px;
            height: 60px;
            margin-bottom: 15px;
            opacity: 0.5;
        }

        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            font-size: 14px;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        @media (max-width: 768px) {
            .devices-grid {
                grid-template-columns: 1fr;
            }

            .timers-grid {
                grid-template-columns: 1fr;
            }

            header {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }

            h1 {
                font-size: 22px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🏠 Zion Home Control</h1>
            </div>
            <div class="controls">
                <button class="btn-primary" onclick="discoverDevices()">🔍 Discover Devices</button>
                <button class="btn-warning" onclick="refreshData()">🔄 Refresh</button>
            </div>
        </header>

        <div id="alerts"></div>

        <!-- Devices Section -->
        <div class="section">
            <h2>🔌 My Devices</h2>
            <div id="devices-container">
                <div class="loading">
                    <div class="spinner"></div>
                </div>
            </div>
        </div>

        <!-- Timers Section -->
        <div class="section">
            <h2>⏱️ Active Timers</h2>
            <div id="timers-container">
                <div class="empty-state">
                    <p>No active timers</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';

        // Alert system
        function showAlert(message, type = 'info') {
            const alertDiv = document.getElementById('alerts');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.innerHTML = message;
            alertDiv.appendChild(alert);

            setTimeout(() => alert.remove(), 4000);
        }

        // Discover devices
        async function discoverDevices() {
            try {
                showAlert('Discovering devices...', 'info');
                await loadDevices(true);
            } catch (error) {
                showAlert(`Error discovering devices: ${error.message}`, 'error');
            }
        }

        // Load devices from API
        async function loadDevices(refresh = false) {
            try {
                const response = await fetch(`${API_BASE}/devices`);
                const data = await response.json();

                if (!data.success) {
                    showAlert('Failed to load devices', 'error');
                    return;
                }

                const devices = data.data.devices;
                devices.sort((a, b) => a.name.localeCompare(b.name));
                const container = document.getElementById('devices-container');

                if (devices.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No WEMO devices found. Make sure they are on the same network.</p></div>';
                    if (refresh) {
                        showAlert('No devices found. Ensure WEMO devices are powered on and on your network.', 'error');
                    }
                    return;
                }

                let html = '<div class="devices-grid">';
                for (const device of devices) {
                            html += buildDeviceCard(device);
                }
                html += '</div>';
                container.innerHTML = html;

                if (refresh) {
                    showAlert(`Found ${devices.length} device(s)!`, 'success');
                }

                // Load status and schedule for each device
                for (const device of devices) {
                    updateDeviceStatus(device.id);
                    checkBrightnessSupport(device.id);
                    loadDeviceSchedule(device.id);
                }
            } catch (error) {
                document.getElementById('devices-container').innerHTML = `
                    <div class="empty-state">
                        <p>Error loading devices: ${error.message}</p>
                    </div>
                `;
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        function buildDeviceCard(device) {
            return `
                <div class="device-card" id="device-${device.id}">
                    <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="device-name" id="name-${device.id}">${device.name}</span>
                            <input id="edit-input-${device.id}" class="name-edit" style="display:none;padding:6px;border-radius:4px;border:1px solid #ddd;min-width:160px;" value="${device.name}" onkeydown="handleEditKey(event, '${device.id}')">
                        </div>
                        <div>
                            <button class="btn-primary" id="edit-btn-${device.id}" style="padding:6px 8px;font-size:12px;" onclick="startEdit('${device.id}')">✏️</button>
                            <button class="btn-success" id="save-btn-${device.id}" style="display:none;padding:6px 8px;font-size:12px;" onclick="saveEdit('${device.id}')">Save</button>
                            <button class="btn-danger" id="cancel-btn-${device.id}" style="display:none;padding:6px 8px;font-size:12px;" onclick="cancelEdit('${device.id}')">Cancel</button>
                        </div>
                    </div>
                    <div class="device-info">
                        <div class="device-info-row">
                            <span>Type:</span>
                            <span>${device.device_type}</span>
                        </div>
                        <div class="device-info-row">
                            <span>Model:</span>
                            <span>${device.model}</span>
                        </div>
                        <div class="device-info-row">
                            <span>Host:</span>
                            <span>${device.host}</span>
                        </div>
                    </div>
                    <div class="device-status" id="status-${device.id}">
                        Loading...
                    </div>
                    <div class="device-controls">
                        <button class="btn-success" onclick="turnOn('${device.id}')">Turn ON</button>
                        <button class="btn-danger" onclick="turnOff('${device.id}')">Turn OFF</button>
                        <button class="btn-primary" onclick="toggleDevice('${device.id}')">Toggle</button>
                    </div>
                    <div class="brightness-section" id="brightness-section-${device.id}" data-supports-brightness="false" style="display: none;">
                        <div class="brightness-label">
                            <span>Brightness:</span>
                            <span class="brightness-value" id="brightness-value-${device.id}">50%</span>
                        </div>
                        <input type="range" id="brightness-slider-${device.id}" class="brightness-slider" min="0" max="100" value="50" 
                               oninput="updateBrightness('${device.id}', this.value)">
                    </div>
                    <div class="timer-section">
                        <div class="timer-form">
                            <input type="number" id="timer-input-${device.id}" placeholder="Seconds" min="1" value="1800">
                            <button class="btn-warning" onclick="setTimer('${device.id}')">Set Timer</button>
                        </div>
                    </div>
                    <div class="schedule-section" id="schedule-section-${device.id}">
                        <div class="schedule-title">🗓️ Weekly Schedule</div>
                        <div class="schedule-grid">
                            <div class="schedule-cell schedule-header">Day</div>
                            <div class="schedule-cell schedule-header">On Time</div>
                            <div class="schedule-cell schedule-header">Off Time</div>
                            <div class="schedule-cell schedule-header">Enabled</div>
                            ${['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'].map((day, index) => `
                                <div class="schedule-cell">${day}</div>
                                <div class="schedule-cell"><input type="time" id="schedule-${device.id}-${index}-on" class="schedule-input" value=""></div>
                                <div class="schedule-cell"><input type="time" id="schedule-${device.id}-${index}-off" class="schedule-input" value=""></div>
                                <div class="schedule-cell"><input type="checkbox" id="schedule-${device.id}-${index}-enabled"></div>
                            `).join('')}
                        </div>
                        <div class="schedule-actions">
                            <button class="btn-success" onclick="saveSchedule('${device.id}')">Save Schedule</button>
                            <button class="btn-danger" onclick="clearSchedule('${device.id}')">Clear Schedule</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // Inline edit helpers for device renaming
        function startEdit(deviceId) {
            const nameSpan = document.getElementById(`name-${deviceId}`);
            const input = document.getElementById(`edit-input-${deviceId}`);
            const editBtn = document.getElementById(`edit-btn-${deviceId}`);
            const saveBtn = document.getElementById(`save-btn-${device.id || deviceId}`);
            const cancelBtn = document.getElementById(`cancel-btn-${device.id || deviceId}`);

            if (editBtn) editBtn.style.display = 'none';
            if (saveBtn) saveBtn.style.display = 'inline-block';
            if (cancelBtn) cancelBtn.style.display = 'inline-block';
            if (input) { input.style.display = 'inline-block'; input.focus(); input.select(); }
        }

        function cancelEdit(deviceId) {
            const nameSpan = document.getElementById(`name-${deviceId}`);
            const input = document.getElementById(`edit-input-${deviceId}`);
            const editBtn = document.getElementById(`edit-btn-${deviceId}`);
            const saveBtn = document.getElementById(`save-btn-${deviceId}`);
            const cancelBtn = document.getElementById(`cancel-btn-${deviceId}`);

            if (editBtn) editBtn.style.display = 'inline-block';
            if (saveBtn) saveBtn.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (input && nameSpan) { input.value = nameSpan.textContent; input.style.display = 'none'; }
        }

        async function saveEdit(deviceId) {
            const input = document.getElementById(`edit-input-${deviceId}`);
            if (!input) return;
            const newName = input.value.trim();
            if (!newName) { showAlert('Name cannot be empty', 'error'); return; }
            await renameDevice(deviceId, newName);
            cancelEdit(deviceId);
        }

        function handleEditKey(e, deviceId) {
            if (!e) return;
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit(deviceId);
            } else if (e.key === 'Escape' || e.key === 'Esc') {
                e.preventDefault();
                cancelEdit(deviceId);
            }
        }

        async function renameDevice(deviceId, newName) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/name`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                const data = await response.json();
                if (data.success) {
                    const nameEl = document.querySelector(`#device-${deviceId} .device-name`);
                    if (nameEl) nameEl.textContent = newName;
                    showAlert('Device renamed', 'success');
                } else {
                    showAlert(`Rename failed: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        function setDeviceCardState(deviceId, isOn) {
            const statusDiv = document.getElementById(`status-${deviceId}`);
            const card = document.getElementById(`device-${deviceId}`);
            if (!statusDiv || !card) return;

            statusDiv.textContent = isOn ? '✓ ON' : '✗ OFF';
            statusDiv.className = `device-status ${isOn ? 'on' : 'off'}`;
            card.classList.remove('powered-on', 'powered-off');
            card.classList.add(isOn ? 'powered-on' : 'powered-off');
        }

        // Update device status
        async function updateDeviceStatus(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/status`);
                const data = await response.json();

                const statusDiv = document.getElementById(`status-${deviceId}`);
                const card = document.getElementById(`device-${deviceId}`);
                const brightnessSection = document.getElementById(`brightness-section-${deviceId}`);

                if (data.success) {
                    const status = data.status;
                    const isOn = status.state;
                    const power = status.power ? ` (${status.power.toFixed(1)}W)` : '';
                    const brightness = status.brightness;

                    statusDiv.textContent = isOn ? `✓ ON${power}` : '✗ OFF';
                    statusDiv.className = `device-status ${isOn ? 'on' : 'off'}`;

                    // Update card styling
                    card.classList.remove('powered-on', 'powered-off');
                    card.classList.add(isOn ? 'powered-on' : 'powered-off');

                    // Handle brightness
                    if (brightness !== null && brightness !== undefined) {
                        brightnessSection.style.display = 'block';
                        brightnessSection.dataset.supportsBrightness = 'true';
                        const slider = document.getElementById(`brightness-slider-${deviceId}`);
                        const value = document.getElementById(`brightness-value-${deviceId}`);
                        if (slider) slider.value = brightness;
                        if (value) value.textContent = `${brightness}%`;
                    } else if (brightnessSection.dataset.supportsBrightness === 'true') {
                        brightnessSection.style.display = 'block';
                    } else {
                        brightnessSection.style.display = 'none';
                    }
                } else {
                    statusDiv.textContent = 'Error loading status';
                    statusDiv.className = 'device-status';
                    brightnessSection.style.display = 'none';
                }
            } catch (error) {
                const statusDiv = document.getElementById(`status-${deviceId}`);
                if (statusDiv) statusDiv.textContent = 'Error';
            }
        }

        // Device control functions
        async function turnOn(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/on`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    setDeviceCardState(deviceId, true);
                    setTimeout(() => updateDeviceStatus(deviceId), 1000);
                } else {
                    showAlert(data.error, 'error');
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        async function turnOff(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/off`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    setDeviceCardState(deviceId, false);
                    setTimeout(() => updateDeviceStatus(deviceId), 1000);
                } else {
                    showAlert(data.error, 'error');
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        async function toggleDevice(deviceId) {
            try {
                const statusDiv = document.getElementById(`status-${deviceId}`);
                if (statusDiv) statusDiv.textContent = 'Updating...';

                const response = await fetch(`${API_BASE}/devices/${deviceId}/toggle`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    setTimeout(() => updateDeviceStatus(deviceId), 1000);
                } else {
                    showAlert(data.error, 'error');
                    updateDeviceStatus(deviceId);
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        async function updateBrightness(deviceId, brightness) {
            try {
                // Update the display value
                document.getElementById(`brightness-value-${deviceId}`).textContent = `${brightness}%`;

                // Send to API
                const response = await fetch(`${API_BASE}/devices/${deviceId}/brightness`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ brightness: parseInt(brightness) })
                });
                const data = await response.json();
                if (!data.success) {
                    showAlert(`Brightness control failed: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert(`Error setting brightness: ${error.message}`, 'error');
            }
        }

        async function checkBrightnessSupport(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/supports-brightness`);
                const data = await response.json();
                const brightnessSection = document.getElementById(`brightness-section-${deviceId}`);

                if (data.success && data.supports_brightness && brightnessSection) {
                    brightnessSection.style.display = 'block';
                    brightnessSection.dataset.supportsBrightness = 'true';
                }
            } catch (error) {
                console.debug(`Brightness support check failed for ${deviceId}: ${error}`);
            }
        }

        async function loadDeviceSchedule(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/schedule`);
                const data = await response.json();
                if (!data.success || !data.schedule || !data.schedule.days) {
                    return;
                }

                for (let i = 0; i < 7; i++) {
                    const day = data.schedule.days[i] || {};
                    const onInput = document.getElementById(`schedule-${deviceId}-${i}-on`);
                    const offInput = document.getElementById(`schedule-${deviceId}-${i}-off`);
                    const enabledInput = document.getElementById(`schedule-${deviceId}-${i}-enabled`);

                    if (onInput) onInput.value = day.onTime || '';
                    if (offInput) offInput.value = day.offTime || '';
                    if (enabledInput) enabledInput.checked = !!day.enabled;
                }
            } catch (error) {
                console.debug(`Unable to load schedule for ${deviceId}: ${error}`);
            }
        }

        async function saveSchedule(deviceId) {
            const days = [];
            for (let i = 0; i < 7; i++) {
                const onInput = document.getElementById(`schedule-${deviceId}-${i}-on`);
                const offInput = document.getElementById(`schedule-${deviceId}-${i}-off`);
                const enabledInput = document.getElementById(`schedule-${deviceId}-${i}-enabled`);
                days.push({
                    enabled: enabledInput ? enabledInput.checked : false,
                    onTime: onInput ? onInput.value : '',
                    offTime: offInput ? offInput.value : ''
                });
            }

            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/schedule`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ days })
                });
                const data = await response.json();
                if (data.success) {
                    showAlert('Schedule saved to local machine', 'success');
                } else {
                    showAlert(`Schedule save failed: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert(`Error saving schedule: ${error.message}`, 'error');
            }
        }

        async function clearSchedule(deviceId) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/schedule`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                if (data.success) {
                    for (let i = 0; i < 7; i++) {
                        const onInput = document.getElementById(`schedule-${deviceId}-${i}-on`);
                        const offInput = document.getElementById(`schedule-${deviceId}-${i}-off`);
                        const enabledInput = document.getElementById(`schedule-${deviceId}-${i}-enabled`);
                        if (onInput) onInput.value = '';
                        if (offInput) offInput.value = '';
                        if (enabledInput) enabledInput.checked = false;
                    }
                    showAlert('Schedule cleared from local machine', 'info');
                } else {
                    showAlert(`Unable to clear schedule: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert(`Error clearing schedule: ${error.message}`, 'error');
            }
        }

        async function setTimer(deviceId) {
            const input = document.getElementById(`timer-input-${deviceId}`);
            const duration = parseInt(input.value);

            if (!duration || duration <= 0) {
                showAlert('Please enter a valid duration in seconds', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}/timer`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ duration_seconds: duration })
                });
                const data = await response.json();
                if (data.success) {
                    showAlert(`Timer set for ${duration} seconds!`, 'success');
                    input.value = '1800';
                    loadTimers();
                } else {
                    showAlert(data.error, 'error');
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        // Load active timers
        async function loadTimers() {
            try {
                const response = await fetch(`${API_BASE}/timers`);
                const data = await response.json();
                const container = document.getElementById('timers-container');

                if (!data.timers || Object.keys(data.timers).length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No active timers</p></div>';
                    return;
                }

                let html = '<div class="timers-grid">';
                for (const [timerId, timer] of Object.entries(data.timers)) {
                    html += buildTimerCard(timerId, timer);
                }
                html += '</div>';
                container.innerHTML = html;

                // Update countdowns
                updateCountdowns();
            } catch (error) {
                showAlert(`Error loading timers: ${error.message}`, 'error');
            }
        }

        function buildTimerCard(timerId, timer) {
            return `
                <div class="timer-card" id="timer-${timerId}">
                    <h4>${timer.device_name}</h4>
                    <div class="timer-info">
                        <div>Remaining: <span id="countdown-${timerId}">${timer.remaining_seconds}s</span></div>
                        <div>Ends: ${new Date(timer.end_time).toLocaleTimeString()}</div>
                    </div>
                    <div class="timer-countdown" id="countdown-display-${timerId}">
                        ${formatTime(timer.remaining_seconds)}
                    </div>
                    <button class="btn-danger" style="width: 100%;" onclick="cancelTimer('${timerId}')">Cancel Timer</button>
                </div>
            `;
        }

        async function cancelTimer(timerId) {
            try {
                const response = await fetch(`${API_BASE}/devices/dummy/timer/${timerId}`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    loadTimers();
                } else {
                    showAlert(data.error, 'error');
                }
            } catch (error) {
                showAlert(`Error: ${error.message}`, 'error');
            }
        }

        function formatTime(seconds) {
            const hrs = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;

            if (hrs > 0) {
                return `${hrs}h ${mins}m ${secs}s`;
            } else if (mins > 0) {
                return `${mins}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        }

        function updateCountdowns() {
            setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE}/timers`);
                    const data = await response.json();

                    if (data.timers) {
                        for (const [timerId, timer] of Object.entries(data.timers)) {
                            const countdownEl = document.getElementById(`countdown-${timerId}`);
                            const displayEl = document.getElementById(`countdown-display-${timerId}`);

                            if (countdownEl) {
                                countdownEl.textContent = `${timer.remaining_seconds}s`;
                                displayEl.textContent = formatTime(timer.remaining_seconds);
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error updating countdowns:', error);
                }
            }, 1000);
        }

        async function updateAllStatuses() {
            const deviceCards = document.querySelectorAll('.device-card');
            const updatePromises = [];
            deviceCards.forEach(card => {
                const deviceId = card.id.replace('device-', '');
                updatePromises.push(updateDeviceStatus(deviceId));
            });
            await Promise.all(updatePromises);
        }

        // Refresh all data
        async function refreshData() {
            showAlert('Refreshing...', 'info');
            await updateAllStatuses();
            await loadTimers();
        }

        // Initial load
        window.addEventListener('load', () => {
            loadDevices();
            loadTimers();
            setInterval(refreshData, 30000); // Auto-refresh every 30 seconds
        });
    </script>
</body>
</html>
'''


@app.before_request
def initialize_devices():
    """Initialize devices on first request"""
    if not hasattr(g, 'initialized'):
        discovery = get_discovery()
        controller = get_controller()
        
        # Discover devices
        devices = discovery.discover_devices()
        
        # Register devices with controller
        for device_info in devices:
            device = discovery.get_device_by_id(device_info.id)
            if device:
                controller.register_device(device_info.id, device)
        
        g.initialized = True
        g.discovery = discovery
        g.controller = controller


@app.route('/')
def index():
    """Serve web interface"""
    return render_template_string(WEB_INTERFACE)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'WEMO API is running'})


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """
    Get list of all discovered WEMO devices
    
    Returns:
        JSON list of discovered devices
    """
    try:
        discovery = g.discovery
        devices_info = discovery.get_all_devices_info()

        # Override names from local store if present
        try:
            names = load_device_names()
            # support both {'devices':[...]} and list
            if isinstance(devices_info, dict) and 'devices' in devices_info:
                for d in devices_info['devices']:
                    if d.get('id') in names:
                        d['name'] = names[d.get('id')]
            elif isinstance(devices_info, list):
                for d in devices_info:
                    if d.get('id') in names:
                        d['name'] = names[d.get('id')]
        except Exception:
            logger.debug('No device names to override')

        return jsonify({
            'success': True,
            'data': devices_info
        })
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/status', methods=['GET'])
def get_device_status(device_id):
    """
    Get status of a specific device
    
    Args:
        device_id: Device ID (serial number)
        
    Returns:
        JSON with device status
    """
    try:
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break
        
        result = controller.get_status(device_id, device_name)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/on', methods=['POST'])
def turn_on_device(device_id):
    """
    Turn on a device
    
    Args:
        device_id: Device ID (serial number)
        
    Returns:
        JSON with operation result
    """
    try:
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break

        if not controller.supports_power_control(device_id):
            return jsonify({'success': False, 'error': 'Device does not support power control'}), 404

        threading.Thread(target=controller.turn_on, args=(device_id, device_name), daemon=True).start()
        return jsonify({'success': True, 'message': f'{device_name} turn-on queued'}), 202
    except Exception as e:
        logger.error(f"Error turning on device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/off', methods=['POST'])
def turn_off_device(device_id):
    """
    Turn off a device
    
    Args:
        device_id: Device ID (serial number)
        
    Returns:
        JSON with operation result
    """
    try:
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break

        if not controller.supports_power_control(device_id):
            return jsonify({'success': False, 'error': 'Device does not support power control'}), 404

        threading.Thread(target=controller.turn_off, args=(device_id, device_name), daemon=True).start()
        return jsonify({'success': True, 'message': f'{device_name} turn-off queued'}), 202
    except Exception as e:
        logger.error(f"Error turning off device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/toggle', methods=['POST'])
def toggle_device(device_id):
    """
    Toggle a device on/off
    
    Args:
        device_id: Device ID (serial number)
        
    Returns:
        JSON with operation result
    """
    try:
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break

        if not controller.supports_power_control(device_id):
            return jsonify({'success': False, 'error': 'Device does not support power control'}), 404

        threading.Thread(target=controller.toggle, args=(device_id, device_name), daemon=True).start()
        return jsonify({'success': True, 'message': f'{device_name} toggle queued'}), 202
    except Exception as e:
        logger.error(f"Error toggling device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/brightness', methods=['POST'])
def set_device_brightness(device_id):
    """
    Set brightness level for a device
    
    Args:
        device_id: Device ID (serial number)
        
    JSON body:
        {
            "brightness": 75  # Brightness level 0-100
        }
        
    Returns:
        JSON with operation result
    """
    try:
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break
        
        # Get brightness from request
        data = request.get_json()
        if not data or 'brightness' not in data:
            return jsonify({'success': False, 'error': 'Missing brightness value'}), 400
        
        brightness = int(data['brightness'])
        if not controller.supports_brightness(device_id):
            return jsonify({'success': False, 'error': 'Device does not support brightness control'}), 404

        threading.Thread(target=controller.set_brightness, args=(device_id, brightness, device_name), daemon=True).start()
        return jsonify({'success': True, 'message': f'{device_name} brightness update queued', 'brightness': brightness}), 202
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid brightness value'}), 400
    except Exception as e:
        logger.error(f"Error setting brightness: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/supports-brightness', methods=['GET'])
def check_brightness_support(device_id):
    """
    Check if device supports brightness control
    
    Args:
        device_id: Device ID (serial number)
        
    Returns:
        JSON with brightness support status
    """
    try:
        controller = g.controller
        supports = controller.supports_brightness(device_id)
        return jsonify({
            'success': True,
            'device_id': device_id,
            'supports_brightness': supports
        })
    except Exception as e:
        logger.error(f"Error checking brightness support: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/name', methods=['GET'])
def get_device_name(device_id):
    try:
        # prefer locally stored name
        names = load_device_names()
        if device_id in names:
            return jsonify({'success': True, 'device_id': device_id, 'name': names[device_id]})

        # fallback to discovery
        discovery = g.discovery
        for device_info in getattr(discovery, 'device_list', []):
            if device_info.id == device_id:
                return jsonify({'success': True, 'device_id': device_id, 'name': device_info.name})

        return jsonify({'success': False, 'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f'Error getting device name: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/name', methods=['POST'])
def set_device_name(device_id):
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'success': False, 'error': 'Missing name'}), 400

        new_name = str(data['name']).strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'Empty name'}), 400

        # try to update controller if supported
        try:
            controller = g.controller
            if hasattr(controller, 'set_device_name'):
                controller.set_device_name(device_id, new_name)
        except Exception:
            # non-fatal
            logger.debug('Controller does not support remote rename or rename failed')

        names = load_device_names()
        names[device_id] = new_name
        save_device_names(names)

        return jsonify({'success': True, 'device_id': device_id, 'name': new_name}), 200
    except Exception as e:
        logger.error(f'Error setting device name: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    """
    Get all saved schedules
    """
    try:
        schedules = load_schedules()
        return jsonify({'success': True, 'schedules': schedules})
    except Exception as e:
        logger.error(f'Error getting schedules: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/schedule', methods=['GET'])
def get_device_schedule(device_id):
    """
    Get saved schedule for a specific device
    """
    try:
        schedules = load_schedules()
        schedule = schedules.get(device_id, {'days': [{'enabled': False, 'onTime': '', 'offTime': ''} for _ in range(7)]})
        return jsonify({'success': True, 'device_id': device_id, 'schedule': schedule})
    except Exception as e:
        logger.error(f'Error getting device schedule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/schedule', methods=['POST'])
def save_device_schedule(device_id):
    """
    Save or update a schedule for a device
    """
    try:
        data = request.get_json()
        if not data or 'days' not in data:
            return jsonify({'success': False, 'error': 'Request must include days array'}), 400

        days = data['days']
        if not isinstance(days, list) or len(days) != 7:
            return jsonify({'success': False, 'error': 'days must be an array of 7 entries'}), 400

        for item in days:
            if not isinstance(item, dict):
                return jsonify({'success': False, 'error': 'Each day entry must be an object'}), 400
            if 'enabled' not in item or 'onTime' not in item or 'offTime' not in item:
                return jsonify({'success': False, 'error': 'Each day entry must include enabled, onTime, and offTime'}), 400

        schedules = load_schedules()
        schedules[device_id] = {'days': days}
        save_schedules(schedules)

        return jsonify({'success': True, 'message': 'Schedule saved', 'schedule': schedules[device_id]}), 201
    except Exception as e:
        logger.error(f'Error saving device schedule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/schedule', methods=['DELETE'])
def delete_device_schedule(device_id):
    """
    Delete a saved schedule for a device
    """
    try:
        schedules = load_schedules()
        if device_id in schedules:
            del schedules[device_id]
            save_schedules(schedules)
        return jsonify({'success': True, 'message': 'Schedule deleted'})
    except Exception as e:
        logger.error(f'Error deleting device schedule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/timer', methods=['POST'])
def set_device_timer(device_id):
    """
    Set a timer for a device
    
    Args:
        device_id: Device ID (serial number)
        
    JSON body:
        {
            "duration_seconds": 3600  # Duration in seconds
        }
        
    Returns:
        JSON with timer information
    """
    try:
        data = request.get_json()
        
        if not data or 'duration_seconds' not in data:
            return jsonify({'success': False, 'error': 'duration_seconds is required'}), 400
        
        duration_seconds = data['duration_seconds']
        
        if not isinstance(duration_seconds, int) or duration_seconds <= 0:
            return jsonify({'success': False, 'error': 'duration_seconds must be a positive integer'}), 400
        
        controller = g.controller
        discovery = g.discovery
        
        # Find device name
        device_name = "Device"
        for device_info in discovery.device_list:
            if device_info.id == device_id:
                device_name = device_info.name
                break
        
        result = controller.set_timer(device_id, duration_seconds, device_name)
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error setting device timer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<device_id>/timer/<timer_id>', methods=['DELETE'])
def cancel_device_timer(device_id, timer_id):
    """
    Cancel a device timer
    
    Args:
        device_id: Device ID (serial number)
        timer_id: Timer ID
        
    Returns:
        JSON with operation result
    """
    try:
        controller = g.controller
        result = controller.cancel_timer(timer_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error cancelling device timer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/timers', methods=['GET'])
def get_active_timers():
    """
    Get all active timers
    
    Returns:
        JSON list of active timers
    """
    try:
        controller = g.controller
        timers = controller.get_active_timers()
        
        return jsonify({
            'success': True,
            'total_timers': len(timers),
            'timers': timers
        })
    except Exception as e:
        logger.error(f"Error getting active timers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Starting WEMO Control API with Web Interface...")
    logger.info("Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)
