"""
Keyboard input handler for Android device
"""

from pynput import keyboard
from utils.logger import get_logger
from core.controller import InputController

class KeyboardHandler:
    """Handle keyboard events and convert to Android input"""
    
    # Key mapping dictionary
    KEY_MAP = {
        # Navigation
        keyboard.Key.enter: 66,  # KEYCODE_ENTER
        keyboard.Key.backspace: 67,  # KEYCODE_DEL
        keyboard.Key.tab: 61,  # KEYCODE_TAB
        keyboard.Key.space: 62,  # KEYCODE_SPACE
        keyboard.Key.esc: 111,  # KEYCODE_ESCAPE
        
        # Arrow keys
        keyboard.Key.up: 19,  # KEYCODE_DPAD_UP
        keyboard.Key.down: 20,  # KEYCODE_DPAD_DOWN
        keyboard.Key.left: 21,  # KEYCODE_DPAD_LEFT
        keyboard.Key.right: 22,  # KEYCODE_DPAD_RIGHT
        
        # Function keys
        keyboard.Key.f1: 131,  # KEYCODE_F1
        keyboard.Key.f2: 132,  # KEYCODE_F2
        keyboard.Key.f3: 133,  # KEYCODE_F3
        keyboard.Key.f4: 134,  # KEYCODE_F4
        keyboard.Key.f5: 135,  # KEYCODE_F5
        keyboard.Key.f6: 136,  # KEYCODE_F6
        keyboard.Key.f7: 137,  # KEYCODE_F7
        keyboard.Key.f8: 138,  # KEYCODE_F8
        keyboard.Key.f9: 139,  # KEYCODE_F9
        keyboard.Key.f10: 140,  # KEYCODE_F10
        keyboard.Key.f11: 141,  # KEYCODE_F11
        keyboard.Key.f12: 142,  # KEYCODE_F12
        
        # Media keys
        keyboard.Key.media_play_pause: 85,  # KEYCODE_MEDIA_PLAY_PAUSE
        keyboard.Key.media_previous: 88,  # KEYCODE_MEDIA_PREVIOUS
        keyboard.Key.media_next: 87,  # KEYCODE_MEDIA_NEXT
        keyboard.Key.volume_up: 24,  # KEYCODE_VOLUME_UP
        keyboard.Key.volume_down: 25,  # KEYCODE_VOLUME_DOWN
        keyboard.Key.volume_mute: 164,  # KEYCODE_VOLUME_MUTE
    }
    
    def __init__(self, controller: InputController):
        self.controller = controller
        self.logger = get_logger(__name__)
        self.listener = None
        self.is_listening = False
        
        # Modifier keys state
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        
    def start(self):
        """Start keyboard listener"""
        if self.is_listening:
            self.logger.warning("Keyboard handler already running")
            return
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        self.is_listening = True
        self.logger.info("Keyboard handler started")
    
    def stop(self):
        """Stop keyboard listener"""
        if self.listener:
            self.listener.stop()
            self.is_listening = False
            self.logger.info("Keyboard handler stopped")
    
    def _on_press(self, key):
        """Handle key press events"""
        try:
            # Handle modifier keys
            if key == keyboard.Key.shift:
                self.shift_pressed = True
            elif key == keyboard.Key.ctrl:
                self.ctrl_pressed = True
            elif key == keyboard.Key.alt:
                self.alt_pressed = True
            
            # Check if it's a special key
            if key in self.KEY_MAP:
                self.controller.press_key(self.KEY_MAP[key])
                self.logger.debug(f"Pressed special key: {key}")
                return
            
            # Handle regular characters
            if hasattr(key, 'char') and key.char:
                char = key.char
                
                # Handle uppercase if shift is pressed
                if self.shift_pressed:
                    char = char.upper()
                
                self.controller.input_text(char)
                self.logger.debug(f"Typed character: {char}")
                
            # Handle shortcut keys
            if self.ctrl_pressed:
                if key == keyboard.Key.space:
                    # Ctrl+Space for voice input
                    pass
                    
        except Exception as e:
            self.logger.error(f"Key press handler error: {e}")
    
    def _on_release(self, key):
        """Handle key release events"""
        try:
            # Update modifier keys state
            if key == keyboard.Key.shift:
                self.shift_pressed = False
            elif key == keyboard.Key.ctrl:
                self.ctrl_pressed = False
            elif key == keyboard.Key.alt:
                self.alt_pressed = False
                
        except Exception as e:
            self.logger.error(f"Key release handler error: {e}")
    
    def set_key_mapping(self, custom_mapping: dict):
        """Update key mapping with custom values"""
        self.KEY_MAP.update(custom_mapping)
        self.logger.debug("Key mapping updated")