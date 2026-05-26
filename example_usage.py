"""
Example Usage Script
Demonstrates how to use the WEMO control system programmatically
"""

from device_discovery import get_discovery
from device_controller import get_controller
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_control():
    """Example: Basic device discovery and control"""
    print("\n=== Example 1: Basic Device Discovery and Control ===\n")

    # Initialize discovery
    discovery = get_discovery()
    controller = get_controller()

    # Discover devices
    devices = discovery.discover_devices()

    if not devices:
        print("No devices found. Please check your network connection.")
        return

    # Get first device
    first_device = devices[0]
    device = discovery.get_device_by_id(first_device.id)

    # Register device
    controller.register_device(first_device.id, device)

    # Turn on device
    print(f"\nTurning ON: {first_device.name}")
    result = controller.turn_on(first_device.id, first_device.name)
    print(f"Result: {result}")

    # Get status
    print(f"\nGetting status of: {first_device.name}")
    status = controller.get_status(first_device.id, first_device.name)
    print(f"Status: {status}")

    # Turn off device
    print(f"\nTurning OFF: {first_device.name}")
    result = controller.turn_off(first_device.id, first_device.name)
    print(f"Result: {result}")


def example_set_timer():
    """Example: Set timer for device"""
    print("\n=== Example 2: Set Timer for Device ===\n")

    discovery = get_discovery()
    controller = get_controller()

    # Discover devices
    devices = discovery.discover_devices()

    if not devices:
        print("No devices found.")
        return

    first_device = devices[0]
    device = discovery.get_device_by_id(first_device.id)
    controller.register_device(first_device.id, device)

    # Set 30-second timer (for testing; use 1800 for 30 minutes)
    print(f"\nSetting 30-second timer for: {first_device.name}")
    result = controller.set_timer(first_device.id, 30, first_device.name)

    if result['success']:
        print(f"Timer set successfully!")
        print(f"Timer will turn off device at: {result['timer']['end_time']}")
        print(f"Timer ID: {result['timer']['timer_id']}")

        # Check active timers
        import time
        time.sleep(2)
        print(f"\nActive timers after 2 seconds:")
        timers = controller.get_active_timers()
        for timer_id, timer_info in timers.items():
            print(f"  - {timer_info['device_name']}: {timer_info['remaining_seconds']}s remaining")
    else:
        print(f"Error: {result['error']}")


def example_list_all_devices():
    """Example: List all devices with details"""
    print("\n=== Example 3: List All Devices ===\n")

    discovery = get_discovery()

    # Discover devices
    devices = discovery.discover_devices()

    if not devices:
        print("No devices found.")
        return

    print(f"Found {len(devices)} device(s):\n")

    for i, device_info in enumerate(devices, 1):
        print(f"{i}. {device_info.name}")
        print(f"   ID: {device_info.id}")
        print(f"   Type: {device_info.device_type}")
        print(f"   Model: {device_info.model}")
        print(f"   Host: {device_info.host}:{device_info.port}")
        print(f"   Serial: {device_info.serial_number}")
        print(f"   Firmware: {device_info.firmware_version}\n")


def example_control_multiple_devices():
    """Example: Control multiple devices"""
    print("\n=== Example 4: Control Multiple Devices ===\n")

    discovery = get_discovery()
    controller = get_controller()

    # Discover devices
    devices = discovery.discover_devices()

    if len(devices) < 2:
        print("This example requires at least 2 devices.")
        return

    # Register all devices
    for device_info in devices:
        device = discovery.get_device_by_id(device_info.id)
        if device:
            controller.register_device(device_info.id, device)

    # Control different devices differently
    print(f"\nControlling {len(devices)} devices:\n")

    for i, device_info in enumerate(devices):
        if i == 0:
            # Turn on first device
            print(f"Turning ON: {device_info.name}")
            result = controller.turn_on(device_info.id, device_info.name)
            print(f"  Result: {result['message'] if result['success'] else result['error']}\n")
        elif i == 1:
            # Set timer for second device
            print(f"Setting 60-second timer for: {device_info.name}")
            result = controller.set_timer(device_info.id, 60, device_info.name)
            if result['success']:
                print(f"  Timer set until: {result['timer']['end_time']}\n")
            else:
                print(f"  Error: {result['error']}\n")
        else:
            # Turn off other devices
            print(f"Turning OFF: {device_info.name}")
            result = controller.turn_off(device_info.id, device_info.name)
            print(f"  Result: {result['message'] if result['success'] else result['error']}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("WEMO Control System - Example Usage")
    print("=" * 60)

    # Choose which example to run
    print("\nAvailable examples:")
    print("1. Basic device discovery and control")
    print("2. Set timer for device")
    print("3. List all devices")
    print("4. Control multiple devices")

    choice = input("\nEnter example number (1-4): ").strip()

    try:
        if choice == "1":
            example_basic_control()
        elif choice == "2":
            example_set_timer()
        elif choice == "3":
            example_list_all_devices()
        elif choice == "4":
            example_control_multiple_devices()
        else:
            print("Invalid choice.")
    except Exception as e:
        logger.error(f"Example error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
