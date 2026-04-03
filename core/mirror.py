"""
Core mirroring functionality
"""

import os
import subprocess
import threading
import time
from typing import Optional, Callable
from adb.device_manager import DeviceManager
from utils.logger import get_logger

class AndroidMirror:
    """Main mirroring controller"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger(__name__)
        self.device_manager = DeviceManager(config)
        self.scrcpy_process = None
        self.is_mirroring = False
        
        # Tentukan path scrcpy
        self.scrcpy_path = self._find_scrcpy()
        self.logger.info(f"Using scrcpy at: {self.scrcpy_path}")
        
    def _find_scrcpy(self) -> str:
        """Find scrcpy executable"""
        # Cek di folder proyek terlebih dahulu (prioritas utama)
        project_dir = os.path.dirname(os.path.dirname(__file__))
        local_scrcpy = os.path.join(project_dir, 'scrcpy', 'scrcpy.exe')
        if os.path.exists(local_scrcpy):
            self.logger.info(f"Found scrcpy in project folder: {local_scrcpy}")
            return local_scrcpy
        
        # Cek di folder Downloads (backup)
        downloads_scrcpy = r"C:\Users\Administrator\Downloads\scrcpy-win64-v3.3.4\scrcpy.exe"
        if os.path.exists(downloads_scrcpy):
            self.logger.info(f"Found scrcpy in downloads: {downloads_scrcpy}")
            return downloads_scrcpy
        
        # Cek di system PATH
        import shutil
        system_scrcpy = shutil.which('scrcpy')
        if system_scrcpy:
            self.logger.info(f"Found scrcpy in PATH: {system_scrcpy}")
            return system_scrcpy
        
        self.logger.error("scrcpy not found!")
        return 'scrcpy'
    
    def start_mirroring(self, device_serial: Optional[str] = None, 
                        optimization: str = 'balanced') -> bool:
        """
        Start screen mirroring
        
        Args:
            device_serial: Device serial number
            optimization: 'latency', 'balanced', or 'quality'
        """
        try:
            # Check device connection
            if not self.device_manager.is_connected(device_serial):
                self.logger.error("No device connected")
                return False
            
            # Build scrcpy command with optimization
            cmd = self._build_scrcpy_command(device_serial, optimization)
            self.logger.info(f"Running command: {' '.join(cmd)}")
            
            # Test if scrcpy exists and is executable
            if not os.path.exists(self.scrcpy_path):
                self.logger.error(f"scrcpy not found at: {self.scrcpy_path}")
                return False
            
            # Set working directory to scrcpy folder so DLLs can be found
            scrcpy_dir = os.path.dirname(self.scrcpy_path)
            
            # Start scrcpy with its own window
            self.scrcpy_process = subprocess.Popen(
                cmd,
                cwd=scrcpy_dir,
                shell=False
            )
            
            # Check if process started successfully
            time.sleep(2)
            
            if self.scrcpy_process.poll() is not None:
                self.logger.error("scrcpy process exited immediately")
                return False
            
            self.is_mirroring = True
            self.logger.info(f"Mirroring started with {optimization} optimization")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start mirroring: {e}")
            return False
    
    def _build_scrcpy_command(self, device_serial: Optional[str], 
                              optimization: str = 'balanced') -> list:
        """Build scrcpy command with options"""
        cmd = [self.scrcpy_path]
        
        if device_serial:
            cmd.extend(['--serial', device_serial])
        
        # ============ OPTIMIZATION SETTINGS ============
        
        if optimization == 'latency':
            self.logger.info("Using LOW LATENCY mode")
            cmd.extend([
                '--max-fps', '30',
                '--max-size', '720',
                '--video-bit-rate', '2M',
                '--video-codec', 'h264',
                '--no-audio',  # Audio disabled for latency
                '--video-buffer', '50',
            ])
            
        elif optimization == 'balanced':
            self.logger.info("Using BALANCED mode")
            cmd.extend([
                '--max-fps', '45',
                '--max-size', '1024',
                '--video-bit-rate', '4M',
                '--video-codec', 'h264',
                '--video-buffer', '100',
            ])
            # Audio ENABLED by default (no --no-audio flag)
            
        elif optimization == 'quality':
            self.logger.info("Using HIGH QUALITY mode")
            cmd.extend([
                '--max-fps', '60',
                '--max-size', '1920',
                '--video-bit-rate', '16M',
                '--video-codec', 'h265',
                '--video-buffer', '200',
            ])
            # Audio ENABLED by default
        
        # ============ COMMON OPTIONS ============
        
        # Stay awake
        if self.config.get('stay_awake', True):
            cmd.append('--stay-awake')
        
        # Audio codec (for better compatibility)
        cmd.extend(['--audio-codec', 'opus'])
        
        # Window title
        cmd.extend(['--window-title', f'Android Mirror ({optimization})'])
        
        # Window position and size
        cmd.extend(['--window-x', '100', '--window-y', '100'])
        
        if optimization == 'latency':
            cmd.extend(['--window-width', '800', '--window-height', '600'])
        elif optimization == 'balanced':
            cmd.extend(['--window-width', '1024', '--window-height', '768'])
        else:
            cmd.extend(['--window-width', '1280', '--window-height', '960'])
        
        return cmd
    
    def stop_mirroring(self):
        """Stop screen mirroring"""
        if self.scrcpy_process:
            self.logger.info("Stopping mirroring...")
            try:
                self.scrcpy_process.terminate()
                self.scrcpy_process.wait(timeout=5)
            except:
                self.scrcpy_process.kill()
            self.is_mirroring = False
            self.logger.info("Mirroring stopped")
    
    def capture_screenshot(self) -> bytes:
        """Capture screenshot from device"""
        return self.device_manager.capture_screenshot()
    
    def get_device_info(self) -> dict:
        """Get device information"""
        return self.device_manager.get_device_info()
    
    def set_optimization(self, mode: str):
        """Change optimization mode on the fly"""
        if self.is_mirroring:
            self.logger.warning("Cannot change optimization while mirroring")
            return False
        return True