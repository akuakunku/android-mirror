"""
Coordinate mapper between PC display and Android device
"""

from typing import Tuple

class CoordinateMapper:
    """Map coordinates between PC and Android device"""
    
    def __init__(self):
        self.pc_width = 1920
        self.pc_height = 1080
        self.device_width = 1080
        self.device_height = 1920
        self.rotation = 0  # 0, 90, 180, 270
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
    def set_pc_resolution(self, width: int, height: int):
        """Set PC display resolution"""
        self.pc_width = width
        self.pc_height = height
        
    def set_device_resolution(self, width: int, height: int):
        """Set Android device resolution"""
        self.device_width = width
        self.device_height = height
        
    def set_rotation(self, rotation: int):
        """Set device rotation"""
        self.rotation = rotation % 360
        
    def set_scale(self, scale: float):
        """Set scaling factor for display"""
        self.scale_factor = scale
        
    def set_offset(self, x: int, y: int):
        """Set offset for window position"""
        self.offset_x = x
        self.offset_y = y
        
    def map_to_device(self, pc_x: int, pc_y: int) -> Tuple[int, int]:
        """
        Map PC coordinates to device coordinates
        
        Args:
            pc_x, pc_y: Coordinates on PC window
            
        Returns:
            Tuple of device coordinates
        """
        # Apply offset
        relative_x = pc_x - self.offset_x
        relative_y = pc_y - self.offset_y
        
        # Apply scaling
        scaled_x = relative_x / self.scale_factor
        scaled_y = relative_y / self.scale_factor
        
        # Apply rotation
        device_x, device_y = self._apply_rotation(scaled_x, scaled_y)
        
        # Clamp to device bounds
        device_x = max(0, min(self.device_width, device_x))
        device_y = max(0, min(self.device_height, device_y))
        
        return int(device_x), int(device_y)
    
    def _apply_rotation(self, x: float, y: float) -> Tuple[float, float]:
        """Apply device rotation to coordinates"""
        if self.rotation == 0:
            return x, y
        elif self.rotation == 90:
            return y, self.device_width - x
        elif self.rotation == 180:
            return self.device_width - x, self.device_height - y
        elif self.rotation == 270:
            return self.device_height - y, x
        return x, y
    
    def map_to_pc(self, device_x: int, device_y: int) -> Tuple[int, int]:
        """
        Map device coordinates to PC coordinates
        
        Args:
            device_x, device_y: Coordinates on Android device
            
        Returns:
            Tuple of PC coordinates
        """
        # Apply inverse rotation
        x, y = self._apply_inverse_rotation(device_x, device_y)
        
        # Apply scaling
        scaled_x = x * self.scale_factor
        scaled_y = y * self.scale_factor
        
        # Apply offset
        pc_x = scaled_x + self.offset_x
        pc_y = scaled_y + self.offset_y
        
        return int(pc_x), int(pc_y)
    
    def _apply_inverse_rotation(self, x: float, y: float) -> Tuple[float, float]:
        """Apply inverse device rotation"""
        if self.rotation == 0:
            return x, y
        elif self.rotation == 90:
            return self.device_height - y, x
        elif self.rotation == 180:
            return self.device_width - x, self.device_height - y
        elif self.rotation == 270:
            return y, self.device_width - x
        return x, y