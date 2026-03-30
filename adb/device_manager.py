"""
Device manager for ADB operations
"""

import subprocess
import re
import socket
import threading
import time
from typing import List, Dict, Optional, Tuple
from utils.logger import get_logger

class DeviceManager:
    """Manage Android devices"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger(__name__)
        self.devices = []
        self.wifi_devices = []
        self.scan_thread = None
        self.scanning = False
        
    def list_devices(self) -> List[Dict]:
        """List all connected devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]
            
            for line in lines:
                if line.strip() and 'device' in line:
                    device_info = self._parse_device_line(line)
                    devices.append(device_info)
            
            self.devices = devices
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to list devices: {e}")
            return []
    
    def _parse_device_line(self, line: str) -> Dict:
        """Parse ADB device line"""
        parts = line.split()
        serial = parts[0]
        
        info = {'serial': serial}
        
        # Parse additional info
        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                info[key] = value
        
        # Determine connection type
        if ':' in serial:
            info['connection_type'] = 'WiFi'
            info['ip'] = serial.split(':')[0]
            info['port'] = serial.split(':')[1] if ':' in serial else '5555'
        else:
            info['connection_type'] = 'USB'
            info['ip'] = None
            info['port'] = None
        
        return info
    
    def connect_wireless(self, ip_address: str, port: int = 5555) -> bool:
        """
        Connect to device via WiFi
        
        Args:
            ip_address: Device IP address
            port: ADB port (default 5555)
        """
        try:
            # First, ensure ADB server is running
            subprocess.run(['adb', 'start-server'], capture_output=True, timeout=5)
            
            # Try to connect
            full_address = f"{ip_address}:{port}"
            self.logger.info(f"Connecting to {full_address}...")
            
            result = subprocess.run(
                ['adb', 'connect', full_address],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            
            if 'connected' in output.lower():
                self.logger.info(f"✅ Connected to {full_address}")
                # Refresh device list
                self.list_devices()
                return True
            elif 'already connected' in output.lower():
                self.logger.info(f"Already connected to {full_address}")
                self.list_devices()
                return True
            else:
                self.logger.error(f"Failed to connect: {output}")
                return False
                
        except Exception as e:
            self.logger.error(f"Wireless connection failed: {e}")
            return False
    
    def disconnect_wireless(self, ip_address: str, port: int = 5555) -> bool:
        """Disconnect wireless device"""
        try:
            full_address = f"{ip_address}:{port}"
            result = subprocess.run(
                ['adb', 'disconnect', full_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'disconnected' in result.stdout:
                self.logger.info(f"✅ Disconnected from {full_address}")
                self.list_devices()
                return True
            else:
                self.logger.warning(f"Failed to disconnect: {result.stdout}")
                return False
                
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False
    
    def scan_network_for_devices(self, network_prefix: str = "192.168.1.", start: int = 1, end: int = 254) -> List[str]:
        """
        Scan local network for Android devices with ADB enabled
        
        Args:
            network_prefix: Network prefix (e.g., "192.168.1.")
            start: Start IP range
            end: End IP range
            
        Returns:
            List of found IP addresses
        """
        found_devices = []
        self.scanning = True
        
        def scan_ip(ip):
            try:
                # Quick ping test
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '1000', ip],
                    capture_output=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    # Try ADB connection
                    test_connect = subprocess.run(
                        ['adb', 'connect', f"{ip}:5555"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    
                    if 'connected' in test_connect.stdout.lower():
                        found_devices.append(ip)
                        self.logger.info(f"Found Android device at {ip}")
                    
                    # Disconnect after test
                    subprocess.run(['adb', 'disconnect', f"{ip}:5555"], capture_output=True)
                    
            except Exception:
                pass
        
        self.logger.info(f"Scanning network {network_prefix}* for Android devices...")
        
        # Create threads for scanning
        threads = []
        for i in range(start, end + 1):
            if not self.scanning:
                break
            ip = f"{network_prefix}{i}"
            thread = threading.Thread(target=scan_ip, args=(ip,))
            thread.start()
            threads.append(thread)
            
            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join(timeout=2)
                threads = []
        
        # Wait for remaining threads
        for t in threads:
            t.join(timeout=2)
        
        self.scanning = False
        self.logger.info(f"Scan completed. Found {len(found_devices)} device(s)")
        return found_devices
    
    def enable_wifi_debugging(self, usb_serial: str) -> bool:
        """
        Enable WiFi debugging on USB-connected device
        
        Args:
            usb_serial: USB device serial
        """
        try:
            # Set ADB to TCP/IP mode on port 5555
            result = subprocess.run(
                ['adb', '-s', usb_serial, 'tcpip', '5555'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'restarting in TCP mode' in result.stdout:
                self.logger.info(f"WiFi debugging enabled on {usb_serial}")
                
                # Get device IP
                ip_result = subprocess.run(
                    ['adb', '-s', usb_serial, 'shell', 'ip', 'route'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Parse IP address
                match = re.search(r'src (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                if match:
                    ip = match.group(1)
                    self.logger.info(f"Device IP: {ip}")
                    return True
                else:
                    self.logger.warning("Could not determine device IP")
                    return True
            else:
                self.logger.error(f"Failed to enable WiFi debugging: {result.stdout}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to enable WiFi debugging: {e}")
            return False
    
    def get_device_ip(self, serial: str) -> Optional[str]:
        """Get IP address of connected device"""
        try:
            # Try via ADB
            result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'ip', 'route'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            match = re.search(r'src (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
            
            # Alternative method
            result2 = subprocess.run(
                ['adb', '-s', serial, 'shell', 'ifconfig', 'wlan0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            match2 = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', result2.stdout)
            if match2:
                return match2.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get device IP: {e}")
            return None
    
    def is_connected(self, serial: Optional[str] = None) -> bool:
        """Check if device is connected"""
        devices = self.list_devices()
        if serial:
            return any(d['serial'] == serial for d in devices)
        return len(devices) > 0
    
    def get_connection_info(self, serial: str) -> Dict:
        """Get detailed connection information for a device"""
        info = {
            'serial': serial,
            'is_connected': False,
            'connection_type': None,
            'ip': None,
            'port': None,
            'adb_version': None,
            'device_model': None
        }
        
        devices = self.list_devices()
        for device in devices:
            if device['serial'] == serial:
                info['is_connected'] = True
                info['connection_type'] = device.get('connection_type', 'Unknown')
                info['ip'] = device.get('ip')
                info['port'] = device.get('port')
                break
        
        # Get ADB version
        try:
            version_result = subprocess.run(
                ['adb', 'version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            info['adb_version'] = version_result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # Get device model
        try:
            model_result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True,
                text=True,
                timeout=3
            )
            info['device_model'] = model_result.stdout.strip()
        except:
            pass
        
        return info
    
    def capture_screenshot(self, serial: Optional[str] = None) -> bytes:
        """Capture screenshot from device"""
        try:
            cmd = ['adb']
            if serial:
                cmd.extend(['-s', serial])
            cmd.extend(['exec-out', 'screencap', '-p'])
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.stdout
            
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            return b''
    
    def get_device_info(self, serial: Optional[str] = None) -> Dict:
        """Get device information"""
        info = {}
        
        # Get device model
        info['model'] = self._get_property('ro.product.model', serial)
        info['manufacturer'] = self._get_property('ro.product.manufacturer', serial)
        info['android_version'] = self._get_property('ro.build.version.release', serial)
        info['resolution'] = self._get_resolution(serial)
        
        # Get IP if connected via WiFi
        if serial and ':' in str(serial):
            info['ip'] = serial.split(':')[0]
        else:
            info['ip'] = self.get_device_ip(serial) if serial else None
        
        return info
    
    def _get_property(self, prop: str, serial: Optional[str]) -> str:
        """Get system property"""
        try:
            cmd = ['adb']
            if serial:
                cmd.extend(['-s', serial])
            cmd.extend(['shell', 'getprop', prop])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
            
        except Exception:
            return 'Unknown'
    
    def _get_resolution(self, serial: Optional[str]) -> str:
        """Get device resolution"""
        try:
            cmd = ['adb']
            if serial:
                cmd.extend(['-s', serial])
            cmd.extend(['shell', 'wm', 'size'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            match = re.search(r'(\d+x\d+)', result.stdout)
            return match.group(1) if match else 'Unknown'
            
        except Exception:
            return 'Unknown'