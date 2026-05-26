"""
API Testing Script
Test the WEMO REST API with example requests
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5000/api"


class WEMOAPITester:
    """Test client for WEMO REST API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def test_health(self):
        """Test health endpoint"""
        print("\n=== Testing Health Endpoint ===")
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

    def test_list_devices(self) -> list:
        """Test device listing"""
        print("\n=== Testing List Devices ===")
        try:
            response = requests.get(f"{self.base_url}/devices")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            if data['success'] and data['data']['devices']:
                return data['data']['devices']
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def test_device_status(self, device_id: str):
        """Test device status"""
        print(f"\n=== Testing Device Status for {device_id} ===")
        try:
            response = requests.get(f"{self.base_url}/devices/{device_id}/status")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def test_turn_on(self, device_id: str):
        """Test turn on"""
        print(f"\n=== Testing Turn On {device_id} ===")
        try:
            response = requests.post(f"{self.base_url}/devices/{device_id}/on")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def test_turn_off(self, device_id: str):
        """Test turn off"""
        print(f"\n=== Testing Turn Off {device_id} ===")
        try:
            response = requests.post(f"{self.base_url}/devices/{device_id}/off")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def test_toggle(self, device_id: str):
        """Test toggle"""
        print(f"\n=== Testing Toggle {device_id} ===")
        try:
            response = requests.post(f"{self.base_url}/devices/{device_id}/toggle")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def test_set_timer(self, device_id: str, duration_seconds: int = 30):
        """Test set timer"""
        print(f"\n=== Testing Set Timer {device_id} ===")
        try:
            payload = {"duration_seconds": duration_seconds}
            response = requests.post(
                f"{self.base_url}/devices/{device_id}/timer",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")

            if response.status_code == 201:
                return response.json()['timer']['timer_id']
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def test_view_timers(self):
        """Test view active timers"""
        print(f"\n=== Testing View Active Timers ===")
        try:
            response = requests.get(f"{self.base_url}/timers")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def test_cancel_timer(self, device_id: str, timer_id: str):
        """Test cancel timer"""
        print(f"\n=== Testing Cancel Timer {timer_id} ===")
        try:
            response = requests.delete(f"{self.base_url}/devices/{device_id}/timer/{timer_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    def run_full_test(self):
        """Run a full test suite"""
        print("=" * 60)
        print("WEMO API Full Test Suite")
        print("=" * 60)

        # Test health
        if not self.test_health():
            print("\n✗ API is not running. Start it with: python api.py")
            return

        # List devices
        devices = self.test_list_devices()

        if not devices:
            print("\n✗ No devices found. Make sure WEMO devices are on network.")
            return

        # Get first device ID
        device_id = devices[0]['id']
        print(f"\n✓ Using device: {devices[0]['name']} ({device_id})")

        # Test device status
        self.test_device_status(device_id)

        # Test turn on
        self.test_turn_on(device_id)
        time.sleep(1)

        # Test get status after turn on
        self.test_device_status(device_id)
        time.sleep(1)

        # Test toggle
        self.test_toggle(device_id)
        time.sleep(1)

        # Test set timer
        timer_id = self.test_set_timer(device_id, duration_seconds=10)
        time.sleep(2)

        # Test view active timers
        self.test_view_timers()

        # Test cancel timer
        if timer_id:
            self.test_cancel_timer(device_id, timer_id)
            time.sleep(1)

        # Test turn off
        self.test_turn_off(device_id)
        time.sleep(1)

        # Final status check
        self.test_device_status(device_id)

        print("\n" + "=" * 60)
        print("Test suite completed!")
        print("=" * 60)


if __name__ == "__main__":
    print("WEMO API Tester")
    print("\nNote: Make sure the API is running first:")
    print("  python api.py")
    print("\nWaiting for API to be ready...")

    # Try to connect
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print("✓ API is running!\n")
                break
        except:
            if i < max_retries - 1:
                print(f"  Attempt {i+1}/{max_retries}: Waiting for API...")
                time.sleep(1)

    # Run full test
    tester = WEMOAPITester()
    tester.run_full_test()
