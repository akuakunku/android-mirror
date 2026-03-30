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

# Hapus import yang menyebabkan circular:
# from video.streamer import VideoStreamer
# from input.mouse_handler import MouseHandler
# from core.mirror import AndroidMirror  <-- INI YANG HARUS DIHAPUS

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
            
            # Start scrcpy process
            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.scrcpy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=scrcpy_dir,
                creationflags=creation_flags,
                text=True
            )
            
            # Check if process started successfully
            time.sleep(1)
            
            if self.scrcpy_process.poll() is not None:
                stderr = self.scrcpy_process.stderr.read()
                self.logger.error(f"scrcpy failed to start: {stderr}")
                return False
            
            self.is_mirroring = True
            self.logger.info(f"Mirroring started with {optimization} optimization")
            
            # Start a thread to monitor stderr for errors
            self._monitor_stderr()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start mirroring: {e}")
            return False
    
    def _monitor_stderr(self):
        """Monitor stderr for error messages"""
        def monitor():
            if self.scrcpy_process and self.scrcpy_process.stderr:
                for line in self.scrcpy_process.stderr:
                    if line:
                        self.logger.info(f"scrcpy: {line.strip()}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
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
                '--no-audio',
                '--video-buffer', '50',
                '--window-x', '100',
                '--window-y', '100',
                '--window-width', '800',
                '--window-height', '600',
            ])
            
        elif optimization == 'balanced':
            self.logger.info("Using BALANCED mode")
            cmd.extend([
                '--max-fps', '45',
                '--max-size', '1024',
                '--video-bit-rate', '4M',
                '--video-codec', 'h264',
                '--video-buffer', '100',
                '--window-x', '100',
                '--window-y', '100',
                '--window-width', '1024',
                '--window-height', '800',
            ])
            
        elif optimization == 'quality':
            self.logger.info("Using HIGH QUALITY mode")
            cmd.extend([
                '--max-fps', '60',
                '--max-size', '1920',
                '--video-bit-rate', '16M',
                '--video-codec', 'h265',
                '--video-buffer', '200',
                '--window-x', '100',
                '--window-y', '100',
                '--window-width', '1280',
                '--window-height', '960',
            ])
        
        # Stay awake
        if self.config.get('stay_awake', True):
            cmd.append('--stay-awake')
        
        # Window title
        cmd.extend(['--window-title', f'Android Mirror ({optimization})'])
        
        # Force always on top
        cmd.append('--always-on-top')
        
        return cmd
    
    def stop_mirroring(self):
        """Stop screen mirroring"""
        if self.scrcpy_process:
            self.logger.info("Stopping mirroring...")
            self.scrcpy_process.terminate()
            try:
                self.scrcpy_process.wait(timeout=5)
                self.logger.info("Mirroring stopped")
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate, killing...")
                self.scrcpy_process.kill()
            self.is_mirroring = False
    
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