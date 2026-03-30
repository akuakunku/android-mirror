#!/usr/bin/env python3
"""
Android Mirror - Main Application Entry Point
"""

import sys
import os
import argparse
import platform
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon  # Tambahkan QIcon
from core.mirror import AndroidMirror
from ui.main_window import MainWindow
from utils.logger import setup_logger
from utils.config import load_config

# Global logger untuk exception handler
_global_logger = None

def get_global_logger():
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    return _global_logger

def check_scrcpy():
    """Check if scrcpy is available"""
    # Cek di folder proyek
    project_dir = os.path.dirname(__file__)
    local_scrcpy = os.path.join(project_dir, 'scrcpy', 'scrcpy.exe')
    if os.path.exists(local_scrcpy):
        return True, local_scrcpy
    
    # Cek di PATH
    import shutil
    system_scrcpy = shutil.which('scrcpy')
    if system_scrcpy:
        return True, system_scrcpy
    
    return False, None

def check_adb():
    """Check if ADB is available"""
    import shutil
    adb_path = shutil.which('adb')
    if adb_path:
        return True, adb_path
    
    # Cek di folder scrcpy
    project_dir = os.path.dirname(__file__)
    local_adb = os.path.join(project_dir, 'scrcpy', 'adb.exe')
    if os.path.exists(local_adb):
        return True, local_adb
    
    return False, None

def check_system_requirements():
    """Check all system requirements"""
    issues = []
    
    # Check scrcpy
    scrcpy_ok, scrcpy_path = check_scrcpy()
    if not scrcpy_ok:
        issues.append("scrcpy not found")
    
    # Check ADB
    adb_ok, adb_path = check_adb()
    if not adb_ok:
        issues.append("ADB not found")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        issues.append(f"Python {python_version.major}.{python_version.minor} (need 3.8+)")
    
    return issues, {'scrcpy': scrcpy_path, 'adb': adb_path}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Android Mirror Application - Display and control Android device',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     # Start with default settings
  python main.py --max-fps 30        # Limit to 30 FPS
  python main.py --max-size 720      # Limit resolution to 720p
  python main.py --no-audio          # Disable audio streaming
  python main.py --stay-awake        # Keep device awake while mirroring
        """
    )
    parser.add_argument('--max-fps', type=int, default=60,
                       help='Maximum FPS for mirroring (default: 60)')
    parser.add_argument('--max-size', type=int, default=1280,
                       help='Maximum display size in pixels (default: 1280)')
    parser.add_argument('--bit-rate', type=str, default='8M',
                       help='Video bit rate e.g., 2M, 4M, 8M (default: 8M)')
    parser.add_argument('--no-audio', action='store_true',
                       help='Disable audio streaming')
    parser.add_argument('--stay-awake', action='store_true',
                       help='Keep device awake while mirroring')
    parser.add_argument('--device', type=str, default=None,
                       help='Device serial to auto-connect')
    parser.add_argument('--wifi', action='store_true',
                       help='Use WiFi connection (requires IP in --device)')
    return parser.parse_args()

def show_splash_screen(app):
    """Show splash screen while loading"""
    try:
        # Create a simple splash screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(Qt.transparent)
        
        splash = QSplashScreen(splash_pixmap)
        splash.setStyleSheet("""
            QSplashScreen {
                background-color: #1e1e1e;
                border-radius: 10px;
            }
        """)
        
        # Show loading message
        splash.show()
        splash.showMessage(
            "Loading Android Mirror...\n\n"
            "Checking system requirements...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        app.processEvents()
        
        return splash
    except Exception as e:
        print(f"Splash screen error: {e}")
        return None

def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger()
    global _global_logger
    _global_logger = logger
    
    logger.info("=" * 50)
    logger.info("Android Mirror Application Starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info("=" * 50)
    
    # Parse arguments early for logging
    args = parse_arguments()
    logger.info(f"Command line arguments: {vars(args)}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Android Mirror")
    app.setOrganizationName("AndroidMirror")
    app.setStyle('Fusion')  # Modern style
    
    # Set application icon (if exists)
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icons', 'app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show splash screen
    splash = show_splash_screen(app)
    if splash:
        splash.showMessage(
            "Checking system requirements...\n\n"
            "• Python OK\n"
            "• Checking scrcpy...\n"
            "• Checking ADB...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        app.processEvents()
    
    # Check system requirements
    issues, paths = check_system_requirements()
    
    if issues:
        if splash:
            splash.close()
        
        error_msg = "System Requirements Check Failed:\n\n"
        for issue in issues:
            error_msg += f"✗ {issue}\n"
        error_msg += "\nPlease install missing components and try again.\n\n"
        error_msg += "Required:\n"
        error_msg += "  • scrcpy: https://github.com/Genymobile/scrcpy\n"
        error_msg += "  • ADB: https://developer.android.com/studio/releases/platform-tools"
        
        logger.error(error_msg)
        QMessageBox.critical(None, "System Requirements Failed", error_msg)
        return 1
    
    logger.info(f"✓ scrcpy found: {paths['scrcpy']}")
    logger.info(f"✓ ADB found: {paths['adb']}")
    
    if splash:
        splash.showMessage(
            "Loading configuration...\n\n"
            "✓ Python OK\n"
            "✓ scrcpy OK\n"
            "✓ ADB OK\n"
            "Loading settings...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        app.processEvents()
    
    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        config = {}
    
    if splash:
        splash.showMessage(
            "Initializing UI...\n\n"
            "✓ Python OK\n"
            "✓ scrcpy OK\n"
            "✓ ADB OK\n"
            "✓ Settings loaded\n"
            "Starting interface...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        app.processEvents()
    
    # Create main window
    try:
        window = MainWindow(config, args)
        
        # Auto-connect if device specified
        if args.device:
            QTimer.singleShot(500, lambda: auto_connect_device(window, args))
        
        window.show()
        
        if splash:
            splash.finish(window)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        if splash:
            splash.close()
        logger.error(f"Failed to create main window: {e}", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
                            f"Failed to start application:\n\n{str(e)}")
        return 1
    
    # Start application
    return app.exec_()

def auto_connect_device(window, args):
    """Auto-connect to specified device"""
    try:
        logger = get_global_logger()
        
        if args.wifi:
            # Connect via WiFi
            if ':' in args.device:
                ip = args.device.split(':')[0]
            else:
                ip = args.device
            window.device_manager.connect_wireless(ip)
            window._refresh_devices()
        else:
            # USB device will be detected automatically
            window._refresh_devices()
            
        # Select the device if found
        for i in range(window.device_combo.count()):
            if args.device in window.device_combo.itemText(i):
                window.device_combo.setCurrentIndex(i)
                break
                
        logger.info(f"Auto-connected to device: {args.device}")
    except Exception as e:
        logger = get_global_logger()
        logger.error(f"Auto-connect failed: {e}")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger = get_global_logger()
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger = get_global_logger()
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)