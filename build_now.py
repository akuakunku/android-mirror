#!/usr/bin/env python3
"""
Simple build script for Android Mirror
"""

import os
import sys
import subprocess
import shutil
import time

def force_remove_file(filepath):
    """Force remove file even if it's in use"""
    try:
        if os.path.exists(filepath):
            os.chmod(filepath, 0o777)
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"  Warning: Could not remove {filepath}: {e}")
        return False

def force_remove_dir(dirpath):
    """Force remove directory even if it's in use"""
    try:
        if os.path.exists(dirpath):
            for root, dirs, files in os.walk(dirpath):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        os.chmod(filepath, 0o777)
                    except:
                        pass
            shutil.rmtree(dirpath, ignore_errors=True)
            return True
    except Exception as e:
        print(f"  Warning: Could not remove {dirpath}: {e}")
        return False

def kill_processes():
    """Kill any running AndroidMirror processes"""
    if sys.platform == 'win32':
        try:
            subprocess.run(['taskkill', '/f', '/im', 'AndroidMirror.exe'], 
                          capture_output=True, timeout=5)
            print("  ✓ Killed existing AndroidMirror processes")
        except:
            pass
        try:
            subprocess.run(['taskkill', '/f', '/im', 'scrcpy.exe'], 
                          capture_output=True, timeout=5)
        except:
            pass

def main():
    print("=" * 60)
    print("🚀 Building Android Mirror")
    print("=" * 60)
    
    # Kill any running processes
    print("\n🔪 Killing running processes...")
    kill_processes()
    time.sleep(1)
    
    # Clean previous builds
    print("\n📁 Cleaning previous builds...")
    
    if os.path.exists('build'):
        force_remove_dir('build')
        print("  ✓ Removed build folder")
    
    if os.path.exists('dist'):
        force_remove_dir('dist')
        print("  ✓ Removed dist folder")
    
    portable_dir = 'AndroidMirror_Portable'
    if os.path.exists(portable_dir):
        logs_dir = os.path.join(portable_dir, 'logs')
        if os.path.exists(logs_dir):
            force_remove_dir(logs_dir)
        force_remove_dir(portable_dir)
        print(f"  ✓ Removed {portable_dir} folder")
    
    print("✓ Cleaned")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Build command with complete options
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--noconsole',
        '--name', 'AndroidMirror',
        '--add-data', f'scrcpy{os.pathsep}scrcpy',
        '--add-data', f'config.yaml{os.pathsep}.',
        '--add-data', f'adb{os.pathsep}adb',  # Tambahkan folder adb
        '--hidden-import', 'PyQt5',
        '--hidden-import', 'PyQt5.sip',
        '--hidden-import', 'cv2',
        '--hidden-import', 'numpy',
        '--hidden-import', 'pynput',
        '--hidden-import', 'yaml',
        '--hidden-import', 'watchdog',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'adb',
        '--hidden-import', 'adb.device_manager',
        '--collect-all', 'PyQt5',
        '--collect-all', 'cv2',
        '--collect-all', 'numpy',
        '--collect-all', 'PIL',
        '--collect-all', 'adb',
        '--uac-admin',
        '--clean',
        '--noconfirm',
        'main.py'
    ]
    
    print(f"\n🔧 Building executable...")
    print("⏳ This may take a few minutes...")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n❌ Build failed!")
        return
    
    print("\n✅ Build successful!")
    
    # Create portable package
    print("\n📦 Creating portable package...")
    
    portable_dir = 'AndroidMirror_Portable'
    os.makedirs(portable_dir, exist_ok=True)
    
    # Copy executable
    if os.path.exists('dist/AndroidMirror.exe'):
        shutil.copy('dist/AndroidMirror.exe', portable_dir)
        print("✓ Copied AndroidMirror.exe")
    else:
        print("❌ Executable not found!")
        return
    
    # Copy scrcpy folder
    if os.path.exists('scrcpy'):
        dest_scrcpy = os.path.join(portable_dir, 'scrcpy')
        if os.path.exists(dest_scrcpy):
            force_remove_dir(dest_scrcpy)
        shutil.copytree('scrcpy', dest_scrcpy)
        print("✓ Copied scrcpy folder")
    
    # Copy config
    if os.path.exists('config.yaml'):
        shutil.copy('config.yaml', portable_dir)
        print("✓ Copied config.yaml")
    
    # ============ CREATE LAUNCHERS ============
    
    # 1. VBS Launcher (BEST - no console at all)
    vbs_content = '''Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.Run chr(34) & strPath & "\\AndroidMirror.exe" & chr(34), 0, False
'''
    with open(os.path.join(portable_dir, 'AndroidMirror.vbs'), 'w', encoding='utf-8') as f:
        f.write(vbs_content)
    print("✓ Created AndroidMirror.vbs (silent - no console)")
    
    # 2. BAT Launcher
    bat_content = '''@echo off
title Android Mirror
echo ========================================
echo   Android Mirror - Portable Version
echo ========================================
echo.
echo Starting Android Mirror...
start "" "%~dp0AndroidMirror.exe"
echo.
echo Application started!
echo You can close this window now.
timeout /t 2 >nul
exit
'''
    with open(os.path.join(portable_dir, 'launch.bat'), 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("✓ Created launch.bat")
    
    # 3. Silent BAT
    silent_bat = '''@echo off
start "" "%~dp0AndroidMirror.exe"
exit
'''
    with open(os.path.join(portable_dir, 'start.bat'), 'w', encoding='utf-8') as f:
        f.write(silent_bat)
    print("✓ Created start.bat (silent)")
    
    # 4. PowerShell Launcher
    ps_content = '''$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $scriptPath "AndroidMirror.exe"
Start-Process -FilePath $exePath -WindowStyle Hidden
'''
    with open(os.path.join(portable_dir, 'launch.ps1'), 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("✓ Created launch.ps1")
    
    # 5. Desktop Shortcut Creator
    shortcut_vbs = '''Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDesktop = objShell.SpecialFolders("Desktop")
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strExe = strPath & "\\AndroidMirror.exe"
strShortcut = strDesktop & "\\Android Mirror.lnk"

Set objShortcut = objShell.CreateShortcut(strShortcut)
objShortcut.TargetPath = strExe
objShortcut.WorkingDirectory = strPath
objShortcut.Description = "Android Mirror"
objShortcut.IconLocation = strExe & ", 0"
objShortcut.WindowStyle = 7
objShortcut.Save()

MsgBox "Shortcut created on Desktop!", 64, "Android Mirror"
'''
    with open(os.path.join(portable_dir, 'create_shortcut.vbs'), 'w', encoding='utf-8') as f:
        f.write(shortcut_vbs)
    print("✓ Created create_shortcut.vbs")
    
    # 6. README
    readme_content = """========================================
   Android Mirror - Portable Version
========================================

📌 HOW TO RUN:

1. BEST (No console at all):
   Double-click "AndroidMirror.vbs"

2. Double-click "launch.bat"
3. Double-click "start.bat" (silent)

4. Create Desktop Shortcut:
   Double-click "create_shortcut.vbs"

========================================
🔧 FEATURES
========================================
- Screen mirroring via USB/WiFi
- Screenshot capture
- Screen recording
- File transfer
- Performance optimization

========================================
"""
    with open(os.path.join(portable_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ Created README.txt")
    
    # Calculate size
    total_size = 0
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    
    size_mb = total_size / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("✅ BUILD COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Portable folder: {portable_dir}/")
    print(f"📦 Package size: {size_mb:.2f} MB")
    print(f"\n🚀 Run: {portable_dir}\\AndroidMirror.vbs")
    print("=" * 60)

if __name__ == '__main__':
    main()