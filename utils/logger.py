"""
Logging configuration for the application
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Global logger instance
_logger = None

def setup_logger(name='android_mirror', log_level=logging.INFO):
    """Setup logger with file and console handlers"""
    global _logger
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding fix
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Fix for Windows console encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with UTF-8 encoding
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'  # Force UTF-8 encoding
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    _logger = logger
    return logger

def get_logger(name=None):
    """Get logger instance"""
    global _logger
    if _logger is None:
        setup_logger()
    
    if name:
        return _logger.getChild(name)
    return _logger

class LoggerMixin:
    """Mixin class to add logging capability"""
    
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger