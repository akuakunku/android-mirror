"""
Video streaming handler for Android mirror
"""

import threading
import cv2
import numpy as np
from typing import Optional, Callable
from utils.logger import get_logger

class VideoStreamer:
    """Handle video streaming from Android device"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.is_streaming = False
        self.current_frame = None
        self.frame_callback = None
        self.stream_thread = None
        self._stop_event = threading.Event()
        
    def start_streaming(self, source: str = "scrcpy") -> bool:
        """Start video streaming"""
        try:
            self.is_streaming = True
            self._stop_event.clear()
            self.logger.info(f"Video streaming started from {source}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            return False
    
    def stop_streaming(self):
        """Stop video streaming"""
        self.is_streaming = False
        self._stop_event.set()
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
        self.logger.info("Video streaming stopped")
    
    def set_frame_callback(self, callback: Callable):
        """Set callback for frame updates"""
        self.frame_callback = callback
    
    def update_frame(self, frame: np.ndarray):
        """Update current frame"""
        self.current_frame = frame
        if self.frame_callback:
            self.frame_callback(frame)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current video frame"""
        return self.current_frame