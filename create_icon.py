"""
Create a valid icon file for Windows
"""

from PIL import Image, ImageDraw
import os

def create_icon():
    """Create a simple icon"""
    icon_dir = 'resources/icons'
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    
    # Create a 256x256 image
    img = Image.new('RGBA', (256, 256), color=(76, 175, 80, 255))  # Green background
    draw = ImageDraw.Draw(img)
    
    # Draw a phone shape
    draw.rectangle([50, 30, 206, 226], fill=(33, 33, 33, 255), outline=(255, 255, 255, 255), width=3)
    draw.rectangle([80, 180, 176, 200], fill=(76, 175, 80, 255))
    
    # Draw screen
    draw.rectangle([60, 40, 196, 170], fill=(0, 0, 0, 255))
    
    # Draw "M" on screen
    draw.text((110, 100), "M", fill=(76, 175, 80, 255), anchor='mm')
    
    # Save as ICO
    icon_path = os.path.join(icon_dir, 'app_icon.ico')
    
    # Save as multiple sizes for Windows
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    images[0].save(icon_path, format='ICO', sizes=sizes, append_images=images[1:])
    print(f"✓ Created icon: {icon_path}")
    
    return icon_path

if __name__ == '__main__':
    create_icon()