#!/usr/bin/env python3
"""
System requirements checker for Android Mirror
"""

import subprocess
import sys
import shutil
import platform

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False

def check_adb():
    """Check if ADB is installed"""
    adb_path = shutil.which('adb')
    if adb_path:
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True)
            version = result.stdout.split('\n')[0]
            print(f"✓ ADB found: {version}")
            return True
        except:
            print("✓ ADB found but version check failed")
            return True
    else:
        print("✗ ADB not found. Please install Android Platform Tools")
        return False

def check_scrcpy():
    """Check if scrcpy is installed"""
    # Cek di folder proyek
    import os
    local_scrcpy = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scrcpy', 'scrcpy.exe')
    if os.path.exists(local_scrcpy):
        print(f"✓ scrcpy found in project folder")
        return True
    
    # Cek di system PATH
    scrcpy_path = shutil.which('scrcpy')
    if scrcpy_path:
        try:
            result = subprocess.run(['scrcpy', '--version'], 
                                  capture_output=True, text=True)
            version = result.stdout.split('\n')[0]
            print(f"✓ scrcpy found: {version}")
            return True
        except:
            print("✓ scrcpy found")
            return True
    else:
        print("✗ scrcpy not found. Please install scrcpy")
        print("  → Copy scrcpy folder to project directory or add to PATH")
        return False
    """Check if scrcpy is installed"""
    scrcpy_path = shutil.which('scrcpy')
    if scrcpy_path:
        try:
            result = subprocess.run(['scrcpy', '--version'], 
                                  capture_output=True, text=True)
            version = result.stdout.split('\n')[0]
            print(f"✓ scrcpy found: {version}")
            return True
        except:
            print("✓ scrcpy found")
            return True
    else:
        print("✗ scrcpy not found. Please install scrcpy")
        return False

def check_packages():
    """Check required Python packages"""
    required = ['cv2', 'PyQt5', 'numpy', 'pynput', 'yaml']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0

def check_device():
    """Check if Android device is connected"""
    try:
        result = subprocess.run(['adb', 'devices'], 
                              capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = [l for l in lines if l.strip() and 'device' in l]
        
        if devices:
            print(f"✓ {len(devices)} device(s) connected:")
            for device in devices:
                print(f"  - {device.split()[0]}")
            return True
        else:
            print("✗ No device connected")
            return False
    except:
        print("✗ Failed to check devices")
        return False

def main():
    """Main check function"""
    print("=" * 50)
    print("Android Mirror - System Requirements Check")
    print("=" * 50)
    print()
    
    checks = []
    
    print("Python Version:")
    checks.append(check_python_version())
    print()
    
    print("System Tools:")
    checks.append(check_adb())
    checks.append(check_scrcpy())
    print()
    
    print("Python Packages:")
    checks.append(check_packages())
    print()
    
    print("Device Connection:")
    checks.append(check_device())
    print()
    
    print("=" * 50)
    if all(checks):
        print("✓ All checks passed! System is ready.")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("Installation tips:")
        print("  - Install ADB: https://developer.android.com/studio/releases/platform-tools")
        print("  - Install scrcpy: https://github.com/Genymobile/scrcpy")
        print("  - Install Python packages: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())