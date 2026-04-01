#!/usr/bin/env python3
"""
Simple build script for Android Mirror
"""

import os
import sys
import subprocess
import shutil

def main():
    print("=" * 60)
    print("🚀 Building Android Mirror")
    print("=" * 60)
    
    # Clean previous builds
    print("\n📁 Cleaning previous builds...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    print("✓ Cleaned")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'AndroidMirror',
        '--add-data', f'scrcpy{os.pathsep}scrcpy',
        '--add-data', f'config.yaml{os.pathsep}.',
        '--hidden-import', 'PyQt5',
        '--hidden-import', 'PyQt5.sip',
        '--hidden-import', 'cv2',
        '--hidden-import', 'numpy',
        '--hidden-import', 'pynput',
        '--hidden-import', 'yaml',
        '--hidden-import', 'watchdog',
        'main.py'
    ]
    
    print(f"\n🔧 Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n❌ Build failed!")
        return
    
    print("\n✅ Build successful!")
    
    # Create portable package
    print("\n📦 Creating portable package...")
    
    portable_dir = 'AndroidMirror_Portable'
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    
    os.makedirs(portable_dir)
    
    # Copy executable
    if os.path.exists('dist/AndroidMirror.exe'):
        shutil.copy('dist/AndroidMirror.exe', portable_dir)
        print("✓ Copied AndroidMirror.exe")
    
    # Copy scrcpy
    if os.path.exists('scrcpy'):
        shutil.copytree('scrcpy', os.path.join(portable_dir, 'scrcpy'))
        print("✓ Copied scrcpy folder")
    
    # Copy config
    if os.path.exists('config.yaml'):
        shutil.copy('config.yaml', portable_dir)
        print("✓ Copied config.yaml")
    
    # Create launcher
    with open(os.path.join(portable_dir, 'launch.bat'), 'w') as f:
        f.write('@echo off\nstart "" "%~dp0AndroidMirror.exe"\n')
    print("✓ Created launch.bat")
    
    # Calculate size
    total_size = 0
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            total_size += os.path.getsize(os.path.join(root, file))
    
    size_mb = total_size / (1024 * 1024)
    
    print(f"\n✅ Portable package created: {portable_dir}/")
    print(f"📁 Package size: {size_mb:.2f} MB")
    print("\n🚀 To run: double-click launch.bat or AndroidMirror.exe")
    print("=" * 60)

if __name__ == '__main__':
    main()