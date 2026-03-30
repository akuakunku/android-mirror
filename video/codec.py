"""
Video codec handling
"""

from utils.logger import get_logger

class VideoCodec:
    """Handle video codec operations"""
    
    SUPPORTED_CODECS = ['h264', 'h265', 'av1']
    
    def __init__(self, codec: str = 'h264'):
        self.logger = get_logger(__name__)
        self.codec = codec if codec in self.SUPPORTED_CODECS else 'h264'
        
    def get_codec_name(self) -> str:
        """Get codec name for scrcpy"""
        if self.codec == 'h265':
            return 'h265'
        elif self.codec == 'av1':
            return 'av1'
        return 'h264'
    
    def get_ffmpeg_codec(self) -> str:
        """Get FFmpeg codec name"""
        codec_map = {
            'h264': 'libx264',
            'h265': 'libx265',
            'av1': 'libaom-av1'
        }
        return codec_map.get(self.codec, 'libx264')