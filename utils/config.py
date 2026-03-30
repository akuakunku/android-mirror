"""
Configuration management
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_default_config()
        self._load_config()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Check for config in current directory
        if os.path.exists('config.yaml'):
            return 'config.yaml'
        
        # Check in user home directory
        home_config = Path.home() / '.android-mirror' / 'config.yaml'
        if home_config.exists():
            return str(home_config)
        
        # Create default config in home directory
        home_config.parent.mkdir(parents=True, exist_ok=True)
        self._save_default_config(home_config)
        return str(home_config)
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'ui': {
                'theme': 'Dark',
                'language': 'English',
                'show_toolbar': True,
                'show_fps': True
            },
            'startup': {
                'auto_connect': False,
                'check_updates': True
            },
            'display': {
                'max_fps': 45,
                'max_size': 1024,
                'fullscreen': False,
                'always_on_top': False
            },
            'video': {
                'bit_rate': '4M',
                'video_codec': 'h264',
                'buffer': 100,
                'crop': None
            },
            'audio': {
                'enabled': True,
                'codec': 'opus',
                'bit_rate': '128k'
            },
            'device': {
                'stay_awake': True,
                'turn_screen_off': False,
                'power_off_on_close': False,
                'lock_screen_on_exit': False
            },
            'connection': {
                'default_connection': 'usb',
                'wireless_port': 5555,
                'retry_count': 3,
                'timeout_seconds': 10,
                'auto_reconnect': True
            },
            'network': {
                'scan_timeout': 3,
                'scan_start': 1,
                'scan_end': 254,
                'network_prefix': '192.168.1.'
            },
            'paths': {
                'screenshots': str(Path.home() / 'Pictures'),
                'recordings': str(Path.home() / 'Videos'),
                'logs': 'logs',
                'scrcpy': ''
            },
            'performance': {
                'wifi_mode': 'balanced',
                'usb_mode': 'quality',
                'display_buffer': 2,
                'frame_skip': False
            },
            'recording': {
                'enabled': True,
                'format': 'mp4',
                'default_path': str(Path.home() / 'Videos' / 'android_mirror')
            },
            'input': {
                'touch_enabled': True,
                'keyboard_enabled': True,
                'map_mouse': True,
                'gestures_enabled': True
            },
            'logging': {
                'level': 'INFO',
                'file_enabled': True,
                'max_file_size': '10MB',
                'backup_count': 5,
                'verbose': False
            },
            'window': {
                'always_on_top': False,
                'fullscreen': False,
                'width': 900,
                'height': 750,
                'min_width': 480,
                'min_height': 600
            },
            'advanced': {
                'show_fps': True,
                'verbose_logging': False,
                'debug_mode': False,
                'experimental_features': False
            },
            'shortcuts': {
                'start_mirroring': 'Ctrl+Shift+S',
                'stop_mirroring': 'Ctrl+Shift+X',
                'screenshot': 'Ctrl+Shift+P',
                'recording': 'Ctrl+Shift+R',
                'fullscreen': 'F11',
                'toggle_always_on_top': 'Ctrl+Shift+T'
            }
        }
    
    def _save_default_config(self, path: Path):
        """Save default configuration to file"""
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(user_config)
        except Exception as e:
            print(f"Failed to load config: {e}")
    
    def _merge_config(self, user_config: Dict):
        """Merge user config with default config"""
        def merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge(base[key], value)
                else:
                    base[key] = value
        
        merge(self.config, user_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def get_all(self) -> Dict:
        """Get all configuration"""
        return self.config.copy()
    
    def reset_to_default(self):
        """Reset configuration to default"""
        self.config = self._load_default_config()
        self.save()


# Global config instance
_config_manager = None

def load_config() -> Dict:
    """Load configuration"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_all()

def get_config() -> ConfigManager:
    """Get config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager