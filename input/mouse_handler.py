"""
Mouse input handler for Android device
"""

import threading
import time
from typing import Optional, Callable, Tuple
from pynput import mouse
from utils.logger import get_logger
from core.controller import InputController

class MouseHandler:
    """Handle mouse events and convert to Android touch events"""
    
    def __init__(self, controller: InputController, coordinate_mapper):
        self.controller = controller
        self.coordinate_mapper = coordinate_mapper
        self.logger = get_logger(__name__)
        self.listener = None
        self.is_listening = False
        self.last_click_time = 0
        self.double_click_threshold = 300  # milliseconds
        
        # Gesture tracking
        self.touch_start_pos = None
        self.touch_start_time = None
        self.is_dragging = False
        
        # Callbacks
        self.on_tap = None
        self.on_double_tap = None
        self.on_long_press = None
        self.on_swipe = None
        
    def start(self):
        """Start mouse listener"""
        if self.is_listening:
            self.logger.warning("Mouse handler already running")
            return
        
        self.listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move,
            on_scroll=self._on_scroll
        )
        self.listener.start()
        self.is_listening = True
        self.logger.info("Mouse handler started")
    
    def stop(self):
        """Stop mouse listener"""
        if self.listener:
            self.listener.stop()
            self.is_listening = False
            self.logger.info("Mouse handler stopped")
    
    def _on_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events"""
        try:
            # Convert coordinates to device coordinates
            device_x, device_y = self.coordinate_mapper.map_to_device(x, y)
            
            if button == mouse.Button.left:
                if pressed:
                    # Mouse down
                    current_time = time.time() * 1000
                    time_since_last = current_time - self.last_click_time
                    
                    if time_since_last < self.double_click_threshold:
                        # Double click
                        self.controller.double_tap(device_x, device_y)
                        if self.on_double_tap:
                            self.on_double_tap(device_x, device_y)
                        self.last_click_time = 0  # Reset
                    else:
                        # Start tracking for long press
                        self.touch_start_pos = (device_x, device_y)
                        self.touch_start_time = current_time
                        
                        # Start long press timer
                        self._start_long_press_timer(device_x, device_y)
                else:
                    # Mouse up
                    if self.touch_start_pos and not self.is_dragging:
                        # Check if it was a tap (not a long press)
                        tap_duration = (time.time() * 1000) - self.touch_start_time
                        if tap_duration < 500:  # Less than 500ms
                            self.controller.tap(device_x, device_y)
                            if self.on_tap:
                                self.on_tap(device_x, device_y)
                    
                    # Reset tracking
                    self.touch_start_pos = None
                    self.touch_start_time = None
                    self.is_dragging = False
                    
            elif button == mouse.Button.right:
                if pressed:
                    # Right click = Back button
                    self.controller.press_back()
            elif button == mouse.Button.middle:
                if pressed:
                    # Middle click = Home button
                    self.controller.press_home()
                    
        except Exception as e:
            self.logger.error(f"Mouse click handler error: {e}")
    
    def _on_move(self, x: int, y: int):
        """Handle mouse movement for dragging"""
        try:
            if self.touch_start_pos and self.touch_start_time:
                device_x, device_y = self.coordinate_mapper.map_to_device(x, y)
                
                # Calculate distance moved
                start_x, start_y = self.touch_start_pos
                distance = ((device_x - start_x) ** 2 + (device_y - start_y) ** 2) ** 0.5
                
                # If moved more than threshold, consider as drag/swipe
                if distance > 10 and not self.is_dragging:
                    self.is_dragging = True
                    
                    # Cancel long press timer
                    if hasattr(self, '_long_press_timer'):
                        self._long_press_timer.cancel()
                
                # Update current position for dragging
                if self.is_dragging:
                    # Send move event (for future implementation)
                    pass
                    
        except Exception as e:
            self.logger.error(f"Mouse move handler error: {e}")
    
    def _on_scroll(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse scroll events"""
        try:
            # Convert scroll to swipe gesture
            device_x, device_y = self.coordinate_mapper.map_to_device(x, y)
            
            # Determine scroll direction
            if dy > 0:
                # Scroll up = swipe down
                self.controller.swipe(device_x, device_y, device_x, device_y + 200, 100)
            elif dy < 0:
                # Scroll down = swipe up
                self.controller.swipe(device_x, device_y, device_x, device_y - 200, 100)
                
        except Exception as e:
            self.logger.error(f"Mouse scroll handler error: {e}")
    
    def _start_long_press_timer(self, x: int, y: int):
        """Start timer for long press detection"""
        def long_press_action():
            if self.touch_start_pos and not self.is_dragging:
                self.controller.long_press(x, y)
                if self.on_long_press:
                    self.on_long_press(x, y)
                self.logger.debug(f"Long press at ({x}, {y})")
        
        self._long_press_timer = threading.Timer(0.5, long_press_action)
        self._long_press_timer.start()
    
    def set_callbacks(self, on_tap=None, on_double_tap=None, on_long_press=None, on_swipe=None):
        """Set callback functions for gestures"""
        self.on_tap = on_tap
        self.on_double_tap = on_double_tap
        self.on_long_press = on_long_press
        self.on_swipe = on_swipe