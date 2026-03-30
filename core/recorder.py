"""
Screen recorder functionality
"""

import subprocess
import threading
import time
import os
from typing import Optional, Callable
from datetime import datetime
from utils.logger import get_logger

class ScreenRecorder:
    """Record Android screen"""
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.logger = get_logger(__name__)
        self.is_recording = False
        self.recording_thread = None
        self.output_path = None
        self.device_path = None
        self._process = None
        
    def _build_adb_command(self, *args) -> list:
        """Build ADB command with device serial"""
        cmd = ['adb']
        if self.device_serial:
            cmd.extend(['-s', self.device_serial])
        cmd.extend(args)
        return cmd
    
    def start_recording(self, output_path: str = None, max_time: int = 180, bit_rate: str = '4M') -> bool:
        """
        Start screen recording
        
        Args:
            output_path: Path to save recording
            max_time: Maximum recording time in seconds
            bit_rate: Video bit rate (e.g., '4M', '8M')
        """
        try:
            if self.is_recording:
                self.logger.warning("Recording already in progress")
                return False
            
            # Set output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"screenrecord_{timestamp}.mp4"
            
            self.output_path = output_path
            
            # Device temp path - gunakan timestamp yang sama dengan output_path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.device_path = f"/sdcard/screenrecord_{timestamp}.mp4"
            
            # Build recording command
            cmd = self._build_adb_command(
                'shell', 'screenrecord',
                '--time-limit', str(max_time),
                '--bit-rate', bit_rate,
                self.device_path
            )
            
            # Start recording process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.is_recording = True
            
            # Start monitoring thread
            self.recording_thread = threading.Thread(target=self._monitor_recording)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            self.logger.info(f"Recording started, will save to {self.output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def _monitor_recording(self):
        """Monitor recording process and pull file when done"""
        try:
            # Wait for process to complete
            if self._process:
                self._process.wait(timeout=180)  # Wait up to 3 minutes
            
            # Pull recording from device
            if self.device_path and self.output_path:
                pull_cmd = self._build_adb_command('pull', self.device_path, self.output_path)
                result = subprocess.run(pull_cmd, timeout=30, capture_output=True)
                
                if result.returncode == 0:
                    self.logger.info(f"Recording saved to {self.output_path}")
                else:
                    self.logger.error(f"Failed to pull recording: {result.stderr}")
                
                # Clean up device
                rm_cmd = self._build_adb_command('shell', 'rm', self.device_path)
                subprocess.run(rm_cmd, timeout=5)
            
        except Exception as e:
            self.logger.error(f"Failed to pull recording: {e}")
        finally:
            self.is_recording = False
            self._process = None
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and return file path"""
        if not self.is_recording:
            self.logger.warning("No recording in progress")
            return None
        
        try:
            # Stop the recording process
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            
            # Wait for monitoring thread to finish pulling file
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=30)
            
            self.logger.info(f"Recording stopped, file: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return None
        finally:
            self.is_recording = False
            self._process = None
    
    def get_recording_status(self) -> dict:
        """Get current recording status"""
        return {
            'is_recording': self.is_recording,
            'output_path': self.output_path,
            'device_serial': self.device_serial
        }