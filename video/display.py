"""
Video display window
"""

import cv2
import threading
from typing import Optional
from utils.logger import get_logger

class VideoDisplay:
    """Handle video display window"""
    
    def __init__(self, window_name: str = "Android Mirror"):
        self.logger = get_logger(__name__)
        self.window_name = window_name
        self.is_showing = False
        self.display_thread = None
        self.current_frame = None
        self._stop_event = threading.Event()
        
    def show_frame(self, frame):
        """Display a single frame"""
        if frame is not None:
            self.current_frame = frame
            cv2.imshow(self.window_name, frame)
            cv2.waitKey(1)
    
    def start_display(self):
        """Start display loop"""
        self.is_showing = True
        self._stop_event.clear()
        self.display_thread = threading.Thread(target=self._display_loop)
        self.display_thread.start()
        self.logger.info(f"Display window '{self.window_name}' started")
    
    def _display_loop(self):
        """Main display loop"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        while not self._stop_event.is_set():
            if self.current_frame is not None:
                cv2.imshow(self.window_name, self.current_frame)
            
            # Check for key press
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:  # q or ESC
                self.stop_display()
                break
    
    def stop_display(self):
        """Stop display"""
        self.is_showing = False
        self._stop_event.set()
        cv2.destroyWindow(self.window_name)
        self.logger.info("Display window stopped")
    
    def update_frame(self, frame):
        """Update current frame"""
        self.current_frame = frame
    
    def set_window_size(self, width: int, height: int):
        """Set window size"""
        cv2.resizeWindow(self.window_name, width, height)