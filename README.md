
## ⚙️ Configuration
You can edit `config.yaml` to customize:
- Video quality and FPS
- Audio settings
- WiFi connection settings
- File save locations

## 🔧 Troubleshooting

### Application doesn't start
- Make sure all files are in the same folder
- Try running as administrator
- Check Windows Defender/Firewall

### Device not detected
- Enable USB debugging on Android
- Allow USB debugging authorization on device
- Try different USB cable/port

### WiFi connection issues
- Make sure device and PC are on same network
- Run `adb tcpip 5555` via USB first
- Use the "WiFi Connect" button in the app

## 📝 Notes
- Do not delete the `scrcpy` folder
- First run may take a few seconds
- All settings are saved in config.yaml

## 🔗 Links
- GitHub: https://github.com/akuakunku/android-mirror
- Scrcpy: https://github.com/Genymobile/scrcpy

## 📄 License
MIT License - Free for personal and commercial use
"""
    with open(os.path.join(portable_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("  ✓ Created README.txt")
    
    # 6. Create start script (no pause)
    start_content = '''@echo off
start "" "%~dp0AndroidMirror.exe"
exit
'''
    with open(os.path.join(portable_dir, 'start.bat'), 'w', encoding='utf-8') as f:
        f.write(start_content)
    print("  ✓ Created start.bat")
    
    # 7. Create run without console
    vbs_content = '''Set objShell = CreateObject("Wscript.Shell")
objShell.Run "AndroidMirror.exe", 0, False
'''
    with open(os.path.join(portable_dir, 'run.vbs'), 'w', encoding='utf-8') as f:
        f.write(vbs_content)
    print("  ✓ Created run.vbs")
    
    return portable_dir

def create_zip(portable_dir):
    """Create zip archive of portable package"""
    print("\n🗜️ Creating ZIP archive...")
    
    zip_name = 'AndroidMirror_Portable.zip'
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(portable_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(portable_dir))
                zipf.write(file_path, arcname)
    
    size = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"  ✓ Created {zip_name} ({size:.2f} MB)")
    return zip_name

def calculate_size(directory):
    """Calculate directory size in MB"""
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total / (1024 * 1024)

def main():
    """Main build function"""
    print("=" * 60)
    print("🚀 Android Mirror - Portable Build Tool")
    print("=" * 60)
    
    # Step 1: Clean previous builds
    clean_build()
    
    # Step 2: Check requirements
    check_requirements()
    
    # Step 3: Build executable
    if not build_exe():
        print("\n❌ Build failed! Please check the error above.")
        return 1
    
    # Step 4: Create portable package
    portable_dir = create_portable()
    
    # Step 5: Calculate size
    size_mb = calculate_size(portable_dir)
    
    # Step 6: Create ZIP
    zip_file = create_zip(portable_dir)
    
    print("\n" + "=" * 60)
    print("✅ Build Complete!")
    print("=" * 60)
    print(f"\n📁 Portable folder: {portable_dir}/")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"\n🗜️ ZIP archive: {zip_file}")
    print(f"\n🚀 To use:")
    print(f"   1. Extract {zip_file} (or use {portable_dir} folder)")
    print(f"   2. Double-click launch.bat or start.bat")
    print(f"\n💡 Tip: For silent start, use run.vbs")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())