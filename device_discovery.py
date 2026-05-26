"""
WEMO Device Discovery Module
Discovers all WEMO devices on the home network
"""

import pywemo
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Data class to store WEMO device information"""
    name: str
    model: str
    device_type: str
    host: str
    port: int
    serial_number: str
    firmware_version: str
    id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert device info to dictionary"""
        return {
            'name': self.name,
            'model': self.model,
            'device_type': self.device_type,
            'host': self.host,
            'port': self.port,
            'serial_number': self.serial_number,
            'firmware_version': self.firmware_version,
            'id': self.id
        }


class WEMODiscovery:
    """Discovers and manages WEMO devices on the network"""

    def __init__(self):
        self.devices: Dict[str, Any] = {}
        self.device_list: List[DeviceInfo] = []

    def discover_devices(self) -> List[DeviceInfo]:
        """
        Discover all WEMO devices on the home network
        
        Returns:
            List of DeviceInfo objects for discovered devices
        """
        logger.info("Starting WEMO device discovery...")
        discovered_devices = []

        try:
            # Discover devices on the network
            wemo_devices = pywemo.discover_devices()
            logger.info(f"Found {len(wemo_devices)} WEMO devices")

            for device in wemo_devices:
                try:
                    device_info = self._extract_device_info(device)
                    discovered_devices.append(device_info)
                    self.devices[device_info.id] = device
                    logger.info(f"Discovered: {device_info.name} ({device_info.model})")
                except Exception as e:
                    logger.error(f"Error processing device: {e}")
                    continue

            # Keep device ordering stable by sorting alphabetically by name
            discovered_devices.sort(key=lambda d: d.name.lower())
            self.device_list = discovered_devices
            return discovered_devices

        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            return []

    def _extract_device_info(self, device) -> DeviceInfo:
        """
        Extract information from a WEMO device object
        
        Args:
            device: pywemo device object
            
        Returns:
            DeviceInfo object with device details
        """
        device_id = device.serialnumber if hasattr(device, 'serialnumber') else device.name

        device_info = DeviceInfo(
            name=device.name,
            model=device.model if hasattr(device, 'model') else "Unknown",
            device_type=device.__class__.__name__,
            host=device.host if hasattr(device, 'host') else "Unknown",
            port=device.port if hasattr(device, 'port') else 49154,
            serial_number=device.serialnumber if hasattr(device, 'serialnumber') else "Unknown",
            firmware_version=device.firmware if hasattr(device, 'firmware') else "Unknown",
            id=device_id
        )
        return device_info

    def get_device_by_name(self, name: str) -> Any:
        """
        Get a device by its name
        
        Args:
            name: Device name
            
        Returns:
            The device object or None if not found
        """
        for device_info in self.device_list:
            if device_info.name.lower() == name.lower():
                return self.devices.get(device_info.id)
        return None

    def get_device_by_id(self, device_id: str) -> Any:
        """
        Get a device by its ID
        
        Args:
            device_id: Device ID (serial number)
            
        Returns:
            The device object or None if not found
        """
        return self.devices.get(device_id)

    def get_all_devices_info(self) -> Dict[str, Any]:
        """
        Get information about all discovered devices
        
        Returns:
            Dictionary with device information
        """
        devices = sorted(self.device_list, key=lambda d: d.name.lower())
        return {
            'total_devices': len(devices),
            'devices': [device.to_dict() for device in devices]
        }

    def refresh_devices(self) -> List[DeviceInfo]:
        """
        Refresh the device list
        
        Returns:
            Updated list of devices
        """
        self.devices.clear()
        self.device_list.clear()
        return self.discover_devices()


# Global discovery instance
_discovery_instance = None


def get_discovery() -> WEMODiscovery:
    """Get or create the global discovery instance"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = WEMODiscovery()
    return _discovery_instance
