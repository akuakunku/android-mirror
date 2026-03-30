#!/usr/bin/env python3
"""
Simple Auto Reload for Android Mirror
"""

import sys
import os
import time
import subprocess
import signal

def main():
    print("=" * 50)
    print("🐍 Android Mirror - Auto Reload Mode")
    print("=" * 50)
    print("📁 Press Ctrl+C to stop")
    print("💡 Save files and the app will auto-restart\n")
    
    process = None
    
    # Get last modified time
    last_mtime = {}
    
    def check_files():
        nonlocal last_mtime, process
        reload_needed = False
        
        # Check all Python files
        for root, dirs, files in os.walk('.'):
            # Skip certain directories
            if '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py') and file not in ['simple_reload.py', 'hot_reload.py']:
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        if filepath not in last_mtime:
                            last_mtime[filepath] = mtime
                        elif mtime != last_mtime[filepath]:
                            last_mtime[filepath] = mtime
                            reload_needed = True
                            print(f"\n🔄 File changed: {file}")
                    except:
                        pass
        
        return reload_needed
    
    try:
        # Start initial process
        process = subprocess.Popen([sys.executable, 'main.py'] + sys.argv[1:])
        
        while True:
            time.sleep(1)
            
            if check_files():
                print("🔄 Reloading application...\n")
                
                # Kill current process
                if process and process.poll() is None:
                    if sys.platform == 'win32':
                        process.terminate()
                    else:
                        process.send_signal(signal.SIGTERM)
                    time.sleep(0.5)
                
                # Start new process
                process = subprocess.Popen([sys.executable, 'main.py'] + sys.argv[1:])
            
            # Check if process crashed
            if process and process.poll() is not None:
                print("⚠️ Application crashed, restarting...")
                process = subprocess.Popen([sys.executable, 'main.py'] + sys.argv[1:])
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        if process and process.poll() is None:
            if sys.platform == 'win32':
                process.terminate()
            else:
                process.send_signal(signal.SIGTERM)
            process.wait()
        print("✅ Application stopped")

if __name__ == '__main__':
    main()