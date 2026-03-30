"""
Input controller for Android device
"""

import subprocess
import threading
import time
from typing import Optional, Tuple, List
from utils.logger import get_logger
from input.mapper import CoordinateMapper

class InputController:
    """Handle input events to Android device"""
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.logger = get_logger(__name__)
        self.coordinate_mapper = CoordinateMapper()
        self._lock = threading.Lock()
        
    def _build_adb_command(self, *args) -> List[str]:
        """Build ADB command with device serial"""
        cmd = ['adb']
        if self.device_serial:
            cmd.extend(['-s', self.device_serial])
        cmd.extend(args)
        return cmd
    
    def tap(self, x: int, y: int, duration: int = 50) -> bool:
        """Perform tap at coordinates"""
        try:
            with self._lock:
                cmd = self._build_adb_command('shell', 'input', 'tap', str(x), str(y))
                subprocess.run(cmd, timeout=2, check=True)
                return True
        except Exception as e:
            self.logger.error(f"Tap failed: {e}")
            return False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """Perform swipe gesture"""
        try:
            with self._lock:
                cmd = self._build_adb_command(
                    'shell', 'input', 'swipe',
                    str(x1), str(y1), str(x2), str(y2), str(duration)
                )
                subprocess.run(cmd, timeout=5, check=True)
                return True
        except Exception as e:
            self.logger.error(f"Swipe failed: {e}")
            return False
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """Perform long press gesture"""
        return self.tap(x, y, duration)
    
    def double_tap(self, x: int, y: int, interval: int = 100) -> bool:
        """Perform double tap gesture"""
        success = self.tap(x, y)
        if success:
            time.sleep(interval / 1000.0)
            success = self.tap(x, y)
        return success
    
    def input_text(self, text: str) -> bool:
        """Input text to device"""
        try:
            escaped_text = text.replace(' ', '%s').replace('&', '\\&')
            with self._lock:
                cmd = self._build_adb_command('shell', 'input', 'text', escaped_text)
                subprocess.run(cmd, timeout=2, check=True)
                return True
        except Exception as e:
            self.logger.error(f"Text input failed: {e}")
            return False
    
    def press_key(self, key_code: int) -> bool:
        """Press hardware key"""
        try:
            with self._lock:
                cmd = self._build_adb_command('shell', 'input', 'keyevent', str(key_code))
                subprocess.run(cmd, timeout=2, check=True)
                return True
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")
            return False
    
    def press_back(self) -> bool:
        """Press back button"""
        return self.press_key(4)
    
    def press_home(self) -> bool:
        """Press home button"""
        return self.press_key(3)
    
    def paste_from_clipboard(self) -> bool:
        """Paste clipboard content"""
        # Placeholder - implement if needed
        return self.input_text("")
    
    def get_clipboard(self) -> Optional[str]:
        """Get clipboard content"""
        return None
    
    def sync_clipboard_pc_to_android(self, text: str) -> bool:
        """Sync clipboard from PC to Android"""
        return self.input_text(text)
    
    def sync_clipboard_android_to_pc(self) -> Optional[str]:
        """Sync clipboard from Android to PC"""
        return None