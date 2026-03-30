"""
Video frame decoding
"""

import cv2
import numpy as np
from typing import Optional
from utils.logger import get_logger

class VideoDecoder:
    """Decode video frames"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    def decode_frame(self, data: bytes) -> Optional[np.ndarray]:
        """Decode video frame to OpenCV format"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(data, np.uint8)
            # Decode image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            self.logger.error(f"Frame decoding failed: {e}")
            return None
    
    def resize_frame(self, frame: np.ndarray, max_size: int) -> np.ndarray:
        """Resize frame to max dimensions"""
        height, width = frame.shape[:2]
        
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(frame, (new_width, new_height))
        
        return frame
    
    def convert_color(self, frame: np.ndarray, to_rgb: bool = True) -> np.ndarray:
        """Convert color space"""
        if to_rgb:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame