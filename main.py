"""
WEMO Home Automation Control System
Main application for discovering and controlling WEMO devices
"""

import logging
import sys
from device_discovery import get_discovery
from device_controller import get_controller
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WEMOHomeAutomation:
    """Main application class for WEMO home automation"""

    def __init__(self):
        self.discovery = get_discovery()
        self.controller = get_controller()
        self.devices_info = {}

    def initialize(self) -> bool:
        """
        Initialize the WEMO system
        
        Returns:
            True if initialization successful
        """
        logger.info("=" * 60)
        logger.info("WEMO Home Automation System")
        logger.info("=" * 60)

        logger.info("\nDiscovering WEMO devices on the network...")
        devices = self.discovery.discover_devices()

        if not devices:
            logger.warning("No WEMO devices found on the network")
            logger.info("Please ensure:")
            logger.info("  1. You are connected to the same network as your WEMO devices")
            logger.info("  2. WEMO devices are powered on")
            logger.info("  3. The pywemo library can access your network")
            return False

        logger.info(f"\nFound {len(devices)} WEMO device(s):\n")

        # Register devices and display info
        for i, device_info in enumerate(devices, 1):
            logger.info(f"{i}. {device_info.name}")
            logger.info(f"   Type: {device_info.device_type}")
            logger.info(f"   Model: {device_info.model}")
            logger.info(f"   Firmware: {device_info.firmware_version}")
            logger.info(f"   Serial: {device_info.serial_number}")
            logger.info(f"   Host: {device_info.host}:{device_info.port}\n")

            # Register with controller
            device = self.discovery.get_device_by_id(device_info.id)
            if device:
                self.controller.register_device(device_info.id, device)
                self.devices_info[device_info.id] = device_info

        return True

    def display_menu(self):
        """Display the interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("WEMO Home Automation Control Menu")
            print("=" * 60)
            print("\n1. List all devices")
            print("2. Turn device ON")
            print("3. Turn device OFF")
            print("4. Toggle device")
            print("5. Get device status")
            print("6. Set timer for device")
            print("7. View active timers")
            print("8. Cancel timer")
            print("9. Refresh device list")
            print("0. Exit")
            print("\n" + "-" * 60)

            choice = input("Enter your choice (0-9): ").strip()

            if choice == "1":
                self.list_devices()
            elif choice == "2":
                self.turn_on_device()
            elif choice == "3":
                self.turn_off_device()
            elif choice == "4":
                self.toggle_device()
            elif choice == "5":
                self.check_device_status()
            elif choice == "6":
                self.set_timer()
            elif choice == "7":
                self.view_timers()
            elif choice == "8":
                self.cancel_timer()
            elif choice == "9":
                self.refresh_devices()
            elif choice == "0":
                logger.info("\nShutting down WEMO Home Automation System")
                break
            else:
                print("Invalid choice. Please try again.")

    def list_devices(self):
        """List all devices"""
        print("\n" + "-" * 60)
        print("Available WEMO Devices:")
        print("-" * 60)

        if not self.devices_info:
            print("No devices found")
            return

        for i, (device_id, device_info) in enumerate(self.devices_info.items(), 1):
            print(f"\n{i}. {device_info.name}")
            print(f"   ID: {device_id}")
            print(f"   Type: {device_info.device_type}")
            print(f"   Model: {device_info.model}")

    def _get_device_choice(self) -> str:
        """Helper method to get device selection from user"""
        self.list_devices()

        if not self.devices_info:
            return None

        device_num = input("\nEnter device number (or name): ").strip()

        # Try to parse as number
        try:
            device_index = int(device_num) - 1
            device_id = list(self.devices_info.keys())[device_index]
            return device_id
        except (ValueError, IndexError):
            # Try to match by name
            for device_id, device_info in self.devices_info.items():
                if device_info.name.lower() == device_num.lower():
                    return device_id

        print("Invalid device selection")
        return None

    def turn_on_device(self):
        """Turn on a device"""
        device_id = self._get_device_choice()
        if not device_id:
            return

        device_info = self.devices_info[device_id]
        result = self.controller.turn_on(device_id, device_info.name)

        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")

    def turn_off_device(self):
        """Turn off a device"""
        device_id = self._get_device_choice()
        if not device_id:
            return

        device_info = self.devices_info[device_id]
        result = self.controller.turn_off(device_id, device_info.name)

        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")

    def toggle_device(self):
        """Toggle a device on/off"""
        device_id = self._get_device_choice()
        if not device_id:
            return

        device_info = self.devices_info[device_id]
        result = self.controller.toggle(device_id, device_info.name)

        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")

    def check_device_status(self):
        """Check device status"""
        device_id = self._get_device_choice()
        if not device_id:
            return

        device_info = self.devices_info[device_id]
        result = self.controller.get_status(device_id, device_info.name)

        if result['success']:
            status = result['status']
            print("\n" + "-" * 60)
            print(f"Status for {status['device_name']}:")
            print("-" * 60)
            print(f"Online: {status['online']}")
            print(f"State: {status['state']}")
            if status['power'] is not None:
                print(f"Power: {status['power']}W")
            if status['brightness'] is not None:
                print(f"Brightness: {status['brightness']}%")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")

    def set_timer(self):
        """Set a timer for a device"""
        device_id = self._get_device_choice()
        if not device_id:
            return

        try:
            duration_str = input("\nEnter timer duration:\n  (e.g., 3600 for 1 hour, 1800 for 30 mins): ").strip()
            duration_seconds = int(duration_str)

            if duration_seconds <= 0:
                print("Duration must be positive")
                return

            device_info = self.devices_info[device_id]
            result = self.controller.set_timer(device_id, duration_seconds, device_info.name)

            if result['success']:
                timer = result['timer']
                print(f"\n✓ Timer set for {timer['device_name']}")
                print(f"  Duration: {timer['duration_seconds']} seconds")
                print(f"  End time: {timer['end_time']}")
                print(f"  Timer ID: {timer['timer_id']}")
            else:
                print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
        except ValueError:
            print("Invalid duration. Please enter a number (seconds)")

    def view_timers(self):
        """View active timers"""
        timers = self.controller.get_active_timers()

        print("\n" + "-" * 60)
        print("Active Timers:")
        print("-" * 60)

        if not timers:
            print("No active timers")
            return

        for timer_id, timer_info in timers.items():
            print(f"\nDevice: {timer_info['device_name']}")
            print(f"Time remaining: {timer_info['remaining_seconds']} seconds")
            print(f"End time: {timer_info['end_time']}")
            print(f"Timer ID: {timer_id}")

    def cancel_timer(self):
        """Cancel an active timer"""
        timers = self.controller.get_active_timers()

        if not timers:
            print("\nNo active timers to cancel")
            return

        print("\n" + "-" * 60)
        print("Active Timers:")
        print("-" * 60)

        timer_list = list(timers.items())
        for i, (timer_id, timer_info) in enumerate(timer_list, 1):
            print(f"\n{i}. {timer_info['device_name']}")
            print(f"   Time remaining: {timer_info['remaining_seconds']} seconds")

        try:
            choice = int(input("\nEnter timer number to cancel: ").strip()) - 1
            timer_id = timer_list[choice][0]
            result = self.controller.cancel_timer(timer_id)

            if result['success']:
                print(f"\n✓ {result['message']}")
            else:
                print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
        except (ValueError, IndexError):
            print("Invalid selection")

    def refresh_devices(self):
        """Refresh the device list"""
        logger.info("\nRefreshing device list...")
        devices = self.discovery.refresh_devices()

        self.devices_info.clear()
        for device_info in devices:
            device = self.discovery.get_device_by_id(device_info.id)
            if device:
                self.controller.register_device(device_info.id, device)
                self.devices_info[device_info.id] = device_info

        logger.info(f"Refresh complete. Found {len(devices)} device(s)")


def main():
    """Main entry point"""
    app = WEMOHomeAutomation()

    if not app.initialize():
        sys.exit(1)

    app.display_menu()


if __name__ == "__main__":
    main()
