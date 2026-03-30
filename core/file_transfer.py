"""
File transfer operations for Android device
"""

import subprocess
import os
from typing import List, Optional, Dict
from pathlib import Path
from utils.logger import get_logger

class FileTransfer:
    """Handle file transfer between PC and Android device"""
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.logger = get_logger(__name__)
        
    def _build_adb_command(self, *args) -> list:
        """Build ADB command with device serial"""
        cmd = ['adb']
        if self.device_serial:
            cmd.extend(['-s', self.device_serial])
        cmd.extend(args)
        return cmd
    
    def push_file(self, local_path: str, remote_path: str, show_progress: bool = True) -> bool:
        """
        Push file to device
        
        Args:
            local_path: Local file path
            remote_path: Remote destination path
            show_progress: Show progress bar
        """
        try:
            if not os.path.exists(local_path):
                self.logger.error(f"Local file not found: {local_path}")
                return False
            
            cmd = self._build_adb_command('push')
            if show_progress:
                cmd.append('-p')
            cmd.extend([local_path, remote_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Pushed {local_path} to {remote_path}")
                return True
            else:
                self.logger.error(f"Push failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Push failed: {e}")
            return False
    
    def pull_file(self, remote_path: str, local_path: str, show_progress: bool = True) -> bool:
        """
        Pull file from device
        
        Args:
            remote_path: Remote file path
            local_path: Local destination path
            show_progress: Show progress bar
        """
        try:
            # Create local directory if not exists
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            cmd = self._build_adb_command('pull')
            if show_progress:
                cmd.append('-p')
            cmd.extend([remote_path, local_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Pulled {remote_path} to {local_path}")
                return True
            else:
                self.logger.error(f"Pull failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Pull failed: {e}")
            return False
    
    def list_directory(self, remote_path: str = '/sdcard') -> List[Dict]:
        """
        List directory contents on device
        
        Returns:
            List of dicts with file info: name, size, modified, is_dir
        """
        try:
            # Gunakan format yang lebih konsisten dengan ls -lA
            # -A: list all except . and ..
            # -l: long format
            cmd = self._build_adb_command('shell', 'ls', '-lA', remote_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Coba dengan ls biasa jika gagal
                cmd = self._build_adb_command('shell', 'ls', '-la', remote_path)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to list directory: {result.stderr}")
                    return []
            
            files = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Parse ls -l output format: drwxrwx--x 1 root root 4096 2024-01-01 12:00 folder_name
                parts = line.split()
                
                # Minimum parts: permissions, links, owner, group, size, date, time, name
                if len(parts) < 8:
                    continue
                
                # Check if it's a directory (starts with 'd')
                is_dir = parts[0].startswith('d')
                
                # Get file size
                try:
                    size = int(parts[4]) if not is_dir else 0
                except ValueError:
                    size = 0
                
                # Get date and time (parts 5,6,7)
                if len(parts) >= 8:
                    date = parts[5]
                    time = parts[6]
                    modified = f"{date} {time}"
                else:
                    modified = "Unknown"
                
                # Get filename (from index 7 onwards, because names can have spaces)
                name = ' '.join(parts[7:])
                
                # Skip current and parent directory
                if name in ['.', '..']:
                    continue
                
                files.append({
                    'name': name,
                    'size': size,
                    'modified': modified,
                    'is_dir': is_dir
                })
            
            # Sort: directories first, then files
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            self.logger.debug(f"Listed {len(files)} items in {remote_path}")
            return files
            
        except Exception as e:
            self.logger.error(f"List directory failed: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete file/directory on device"""
        try:
            # Use rm -rf for directories, rm for files
            cmd = self._build_adb_command('shell', 'rm', '-rf', remote_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info(f"Deleted {remote_path}")
                return True
            else:
                self.logger.error(f"Delete failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory on device"""
        try:
            cmd = self._build_adb_command('shell', 'mkdir', '-p', remote_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info(f"Created directory {remote_path}")
                return True
            else:
                self.logger.error(f"Create directory failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Create directory failed: {e}")
            return False
    
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get file information"""
        try:
            # Use stat command for more reliable info
            cmd = self._build_adb_command('shell', 'stat', remote_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return None
            
            # Parse stat output
            info = {'path': remote_path}
            
            # Extract size
            for line in result.stdout.split('\n'):
                if 'Size:' in line:
                    try:
                        info['size'] = int(line.split(':')[1].strip().split()[0])
                    except:
                        info['size'] = 0
                elif 'Modify:' in line:
                    info['modified'] = line.split(':')[1].strip()
            
            return info
            
        except Exception as e:
            self.logger.error(f"Get file info failed: {e}")
            return None
    
    def install_app(self, apk_path: str) -> bool:
        """Install APK on device"""
        try:
            if not os.path.exists(apk_path):
                self.logger.error(f"APK not found: {apk_path}")
                return False
            
            cmd = self._build_adb_command('install', '-r', apk_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if 'Success' in result.stdout:
                self.logger.info(f"Installed {apk_path}")
                return True
            else:
                self.logger.error(f"Install failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Install failed: {e}")
            return False
    
    def uninstall_app(self, package_name: str) -> bool:
        """Uninstall app from device"""
        try:
            cmd = self._build_adb_command('uninstall', package_name)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if 'Success' in result.stdout:
                self.logger.info(f"Uninstalled {package_name}")
                return True
            else:
                self.logger.error(f"Uninstall failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Uninstall failed: {e}")
            return False