"""
WEMO Device Controller Module
Controls WEMO devices and manages timers
"""

import pywemo
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimerManager:
    """Manages timers for WEMO devices"""

    def __init__(self):
        self.active_timers: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def set_timer(self, device_id: str, device: Any, duration_seconds: int, device_name: str = "Device") -> Dict[str, Any]:
        """
        Set a timer for a WEMO device
        
        Args:
            device_id: Unique device identifier
            device: The device object
            duration_seconds: Duration in seconds
            device_name: Friendly device name
            
        Returns:
            Dictionary with timer information
        """
        with self.lock:
            try:
                # Check if device supports on/off using helper method
                controller = WEMOController()
                if not controller._supports_power_control(device):
                    return {'success': False, 'error': 'Device does not support power control'}

                # Turn on the device
                if not controller._turn_on_device(device, device_name):
                    return {'success': False, 'error': 'Failed to turn on device'}
                
                logger.info(f"Turned on {device_name}")

                # Create timer info
                start_time = datetime.now()
                end_time = start_time + timedelta(seconds=duration_seconds)
                timer_id = f"{device_id}_{int(start_time.timestamp())}"

                timer_info = {
                    'device_id': device_id,
                    'device_name': device_name,
                    'timer_id': timer_id,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration_seconds,
                    'remaining_seconds': duration_seconds,
                    'status': 'active'
                }

                self.active_timers[timer_id] = {
                    'device': device,
                    'device_id': device_id,
                    'device_name': device_name,
                    'end_time': end_time,
                    'started_at': start_time
                }

                # Start timer thread
                timer_thread = threading.Thread(
                    target=self._run_timer,
                    args=(timer_id, duration_seconds),
                    daemon=True
                )
                timer_thread.start()

                logger.info(f"Timer set for {device_name}: {duration_seconds} seconds")
                return {'success': True, 'timer': timer_info}

            except Exception as e:
                logger.error(f"Error setting timer for {device_name}: {e}")
                return {'success': False, 'error': str(e)}

    def _run_timer(self, timer_id: str, duration_seconds: int):
        """
        Internal method to run a timer in background
        
        Args:
            timer_id: Timer identifier
            duration_seconds: Duration in seconds
        """
        try:
            time.sleep(duration_seconds)

            with self.lock:
                if timer_id in self.active_timers:
                    timer_info = self.active_timers[timer_id]
                    device = timer_info['device']
                    device_name = timer_info['device_name']

                    # Turn off the device using helper method
                    controller = WEMOController()
                    controller._turn_off_device(device, device_name)
                    logger.info(f"Timer expired and turned off {device_name}")

                    # Remove from active timers
                    del self.active_timers[timer_id]
        except Exception as e:
            logger.error(f"Error in timer execution: {e}")

    def cancel_timer(self, timer_id: str) -> Dict[str, Any]:
        """
        Cancel an active timer
        
        Args:
            timer_id: Timer identifier
            
        Returns:
            Status dictionary
        """
        with self.lock:
            if timer_id in self.active_timers:
                timer_info = self.active_timers[timer_id]
                device = timer_info['device']
                device_name = timer_info['device_name']

                # Turn off the device using helper method
                controller = WEMOController()
                controller._turn_off_device(device, device_name)
                logger.info(f"Timer cancelled for {device_name}")

                # Remove from active timers
                del self.active_timers[timer_id]

                return {'success': True, 'message': f'Timer cancelled for {device_name}'}
            else:
                return {'success': False, 'error': 'Timer not found'}

    def get_active_timers(self) -> Dict[str, Any]:
        """
        Get all active timers
        
        Returns:
            Dictionary of active timers with remaining time
        """
        with self.lock:
            timers = {}
            now = datetime.now()

            for timer_id, timer_info in self.active_timers.items():
                remaining = (timer_info['end_time'] - now).total_seconds()
                timers[timer_id] = {
                    'device_id': timer_info['device_id'],
                    'device_name': timer_info['device_name'],
                    'remaining_seconds': max(0, int(remaining)),
                    'end_time': timer_info['end_time'].isoformat()
                }

            return timers


class WEMOController:
    """Controls WEMO devices"""

    def __init__(self):
        self.timer_manager = TimerManager()
        self.devices: Dict[str, Any] = {}

    def _supports_power_control(self, device: Any) -> bool:
        """
        Check if device supports power control via multiple methods
        
        Args:
            device: The device object
            
        Returns:
            True if device can be turned on/off
        """
        # Check for standard methods
        if hasattr(device, 'turn_on') and hasattr(device, 'turn_off'):
            return True
        
        # Check for state-based control (lights, dimmers)
        if hasattr(device, 'set_state') or (hasattr(device, 'state') and hasattr(device, '__setattr__')):
            return True
        
        # Check for switch-like methods
        if hasattr(device, 'switch_on') or hasattr(device, 'switch_off'):
            return True
        
        return False

    def supports_power_control(self, device_id: str) -> bool:
        """
        Check whether a registered device supports power control
        
        Args:
            device_id: Device ID
            
        Returns:
            True if the device supports on/off operations
        """
        device = self.devices.get(device_id)
        if not device:
            return False
        return self._supports_power_control(device)

    def _turn_on_device(self, device: Any, device_name: str) -> bool:
        """
        Turn on a device using available methods
        
        Args:
            device: The device object
            device_name: Friendly device name
            
        Returns:
            True if successful
        """
        try:
            # Try standard turn_on method
            if hasattr(device, 'turn_on'):
                device.turn_on()
                logger.info(f"Turned on {device_name} using turn_on()")
                return True
            
            # Try set_state method (for lights)
            if hasattr(device, 'set_state'):
                device.set_state(1)
                logger.info(f"Turned on {device_name} using set_state()")
                return True
            
            # Try switch_on method
            if hasattr(device, 'switch_on'):
                device.switch_on()
                logger.info(f"Turned on {device_name} using switch_on()")
                return True
            
            # Try setting state attribute directly
            if hasattr(device, 'state'):
                try:
                    device.state = 1
                    logger.info(f"Turned on {device_name} by setting state attribute")
                    return True
                except:
                    pass
            
            return False
        except Exception as e:
            logger.error(f"Error turning on {device_name}: {e}")
            return False

    def _turn_off_device(self, device: Any, device_name: str) -> bool:
        """
        Turn off a device using available methods
        
        Args:
            device: The device object
            device_name: Friendly device name
            
        Returns:
            True if successful
        """
        try:
            # Try standard turn_off method
            if hasattr(device, 'turn_off'):
                device.turn_off()
                logger.info(f"Turned off {device_name} using turn_off()")
                return True
            
            # Try set_state method (for lights)
            if hasattr(device, 'set_state'):
                device.set_state(0)
                logger.info(f"Turned off {device_name} using set_state()")
                return True
            
            # Try switch_off method
            if hasattr(device, 'switch_off'):
                device.switch_off()
                logger.info(f"Turned off {device_name} using switch_off()")
                return True
            
            # Try setting state attribute directly
            if hasattr(device, 'state'):
                try:
                    device.state = 0
                    logger.info(f"Turned off {device_name} by setting state attribute")
                    return True
                except:
                    pass
            
            return False
        except Exception as e:
            logger.error(f"Error turning off {device_name}: {e}")
            return False

    def register_device(self, device_id: str, device: Any) -> None:
        """
        Register a device for control
        
        Args:
            device_id: Unique device identifier
            device: The device object
        """
        self.devices[device_id] = device
        logger.info(f"Registered device: {device_id}")

    def turn_on(self, device_id: str, device_name: str = "Device") -> Dict[str, Any]:
        """
        Turn on a device
        
        Args:
            device_id: Device ID
            device_name: Friendly device name
            
        Returns:
            Status dictionary
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return {'success': False, 'error': 'Device not found'}

            if not self._supports_power_control(device):
                return {'success': False, 'error': 'Device does not support power control'}
            
            if self._turn_on_device(device, device_name):
                return {'success': True, 'message': f'{device_name} turned on'}
            else:
                return {'success': False, 'error': 'Failed to turn on device'}
        except Exception as e:
            logger.error(f"Error turning on {device_name}: {e}")
            return {'success': False, 'error': str(e)}

    def turn_off(self, device_id: str, device_name: str = "Device") -> Dict[str, Any]:
        """
        Turn off a device
        
        Args:
            device_id: Device ID
            device_name: Friendly device name
            
        Returns:
            Status dictionary
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return {'success': False, 'error': 'Device not found'}

            if not self._supports_power_control(device):
                return {'success': False, 'error': 'Device does not support power control'}
            
            if self._turn_off_device(device, device_name):
                return {'success': True, 'message': f'{device_name} turned off'}
            else:
                return {'success': False, 'error': 'Failed to turn off device'}
        except Exception as e:
            logger.error(f"Error turning off {device_name}: {e}")
            return {'success': False, 'error': str(e)}

    def toggle(self, device_id: str, device_name: str = "Device") -> Dict[str, Any]:
        """
        Toggle a device on/off
        
        Args:
            device_id: Device ID
            device_name: Friendly device name
            
        Returns:
            Status dictionary
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return {'success': False, 'error': 'Device not found'}

            if not self._supports_power_control(device):
                return {'success': False, 'error': 'Device does not support power control'}
            
            # Get current state
            current_state = None
            if hasattr(device, 'state'):
                current_state = device.state
            
            # Toggle based on current state
            if current_state:
                if self._turn_off_device(device, device_name):
                    logger.info(f"Toggled {device_name} to OFF")
                    return {'success': True, 'message': f'{device_name} toggled to OFF', 'state': 0}
                else:
                    return {'success': False, 'error': 'Failed to toggle device'}
            else:
                if self._turn_on_device(device, device_name):
                    logger.info(f"Toggled {device_name} to ON")
                    return {'success': True, 'message': f'{device_name} toggled to ON', 'state': 1}
                else:
                    return {'success': False, 'error': 'Failed to toggle device'}
        except Exception as e:
            logger.error(f"Error toggling {device_name}: {e}")
            return {'success': False, 'error': str(e)}

    def get_status(self, device_id: str, device_name: str = "Device") -> Dict[str, Any]:
        """
        Get device status
        
        Args:
            device_id: Device ID
            device_name: Friendly device name
            
        Returns:
            Status dictionary
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return {'success': False, 'error': 'Device not found'}

            status = {
                'device_id': device_id,
                'device_name': device_name,
                'online': True,
                'state': None,
                'power': None,
                'brightness': None
            }

            # Get power state
            if hasattr(device, 'get_state'):
                try:
                    status['state'] = device.get_state()
                except Exception:
                    status['state'] = None
            elif hasattr(device, 'state'):
                status['state'] = device.state

            # Get brightness if available (for dimmers/lights)
            if hasattr(device, 'get_brightness'):
                try:
                    status['brightness'] = device.get_brightness()
                except Exception:
                    status['brightness'] = None
            elif hasattr(device, 'brightness'):
                status['brightness'] = device.brightness

            # Get power in watts if available
            if hasattr(device, 'current_power'):
                status['power'] = device.current_power

            logger.info(f"Status check for {device_name}: {status}")
            return {'success': True, 'status': status}

        except Exception as e:
            logger.error(f"Error getting status for {device_name}: {e}")
            return {'success': False, 'error': str(e), 'online': False}

    def set_timer(self, device_id: str, duration_seconds: int, device_name: str = "Device") -> Dict[str, Any]:
        """
        Set a timer for a device (turns on and schedules turn off)
        
        Args:
            device_id: Device ID
            duration_seconds: Duration in seconds
            device_name: Friendly device name
            
        Returns:
            Timer information
        """
        device = self.devices.get(device_id)
        if not device:
            return {'success': False, 'error': 'Device not found'}

        return self.timer_manager.set_timer(device_id, device, duration_seconds, device_name)

    def cancel_timer(self, timer_id: str) -> Dict[str, Any]:
        """
        Cancel an active timer
        
        Args:
            timer_id: Timer identifier
            
        Returns:
            Status dictionary
        """
        return self.timer_manager.cancel_timer(timer_id)

    def set_brightness(self, device_id: str, brightness: int, device_name: str = "Device") -> Dict[str, Any]:
        """
        Set brightness level for a dimmable device
        
        Args:
            device_id: Device ID
            brightness: Brightness level (0-100 or 0-255 depending on device)
            device_name: Friendly device name
            
        Returns:
            Status dictionary
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return {'success': False, 'error': 'Device not found'}

            # Validate brightness range
            if brightness < 0:
                brightness = 0
            elif brightness > 100:
                brightness = 100

            # Try different brightness control methods
            success = False
            
            # Method 1: Direct brightness attribute
            if hasattr(device, 'brightness'):
                try:
                    # Check if brightness is on 0-255 scale or 0-100 scale
                    if hasattr(device, 'max_brightness'):
                        max_brightness = device.max_brightness
                        scaled_brightness = int((brightness / 100) * max_brightness)
                    else:
                        scaled_brightness = brightness
                    
                    device.brightness = scaled_brightness
                    logger.info(f"Set {device_name} brightness to {brightness}% using brightness attribute")
                    success = True
                except Exception as e:
                    logger.debug(f"Failed to set brightness via attribute: {e}")

            # Method 2: set_brightness method
            if not success and hasattr(device, 'set_brightness'):
                try:
                    device.set_brightness(brightness)
                    logger.info(f"Set {device_name} brightness to {brightness}% using set_brightness()")
                    success = True
                except Exception as e:
                    logger.debug(f"Failed to set brightness via method: {e}")

            # Method 3: set_state with brightness
            if not success and hasattr(device, 'set_state'):
                try:
                    # Some devices use set_state with a brightness value
                    device.set_state(brightness)
                    logger.info(f"Set {device_name} brightness to {brightness}% using set_state()")
                    success = True
                except Exception as e:
                    logger.debug(f"Failed to set brightness via set_state: {e}")

            if success:
                return {'success': True, 'message': f'{device_name} brightness set to {brightness}%', 'brightness': brightness}
            else:
                return {'success': False, 'error': 'Device does not support brightness control'}

        except Exception as e:
            logger.error(f"Error setting brightness for {device_name}: {e}")
            return {'success': False, 'error': str(e)}

    def supports_brightness(self, device_id: str) -> bool:
        """
        Check if device supports brightness control
        
        Args:
            device_id: Device ID
            
        Returns:
            True if device supports brightness control
        """
        device = self.devices.get(device_id)
        if not device:
            return False
        
        return (
            hasattr(device, 'brightness') or
            hasattr(device, 'set_brightness') or
            hasattr(device, 'set_state') or
            hasattr(device, 'dim') or
            hasattr(device, 'dim_level') or
            hasattr(device, 'dimming')
        )

    def get_active_timers(self) -> Dict[str, Any]:
        """
        Get all active timers
        
        Returns:
            Dictionary of active timers
        """
        return self.timer_manager.get_active_timers()


# Global controller instance
_controller_instance = None


def get_controller() -> WEMOController:
    """Get or create the global controller instance"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = WEMOController()
    return _controller_instance
