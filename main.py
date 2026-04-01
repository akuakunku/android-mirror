#!/usr/bin/env python3
"""
Android Mirror - Main Application Entry Point
"""

import sys
import os
import argparse
import platform
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon

# Set up basic logging before anything else
def setup_basic_logging():
    """Setup basic logging for executable"""
    try:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    except Exception:
        return None

# Initialize basic logger
logger = setup_basic_logging()

# Try to import modules with fallback
try:
    from core.mirror import AndroidMirror
    from ui.main_window import MainWindow
    from utils.logger import setup_logger, get_logger as get_utils_logger
    from utils.config import load_config
except ImportError as e:
    if logger:
        logger.error(f"Import error: {e}")
    # Fallback: try to import from current directory
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from core.mirror import AndroidMirror
        from ui.main_window import MainWindow
        from utils.logger import setup_logger, get_logger as get_utils_logger
        from utils.config import load_config
    except ImportError as e2:
        error_msg = f"Failed to import required modules:\n{str(e2)}\n\nPlease make sure all files are in the correct location."
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)
        QMessageBox.critical(None, "Import Error", error_msg)
        sys.exit(1)

# Global logger untuk exception handler
_global_logger = None

def get_global_logger():
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        try:
            _global_logger = setup_logger()
        except Exception as e:
            print(f"Warning: Could not setup logger: {e}")
            # Return a simple logger
            import logging
            _global_logger = logging.getLogger('android_mirror')
            _global_logger.setLevel(logging.INFO)
            _global_logger.addHandler(logging.StreamHandler(sys.stdout))
    return _global_logger

def check_scrcpy():
    """Check if scrcpy is available"""
    # Cek di folder proyek
    project_dir = os.path.dirname(os.path.abspath(__file__))
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
    project_dir = os.path.dirname(os.path.abspath(__file__))
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
    
    # Check Python version (for info only)
    python_version = sys.version_info
    
    return issues, {'scrcpy': scrcpy_path, 'adb': adb_path, 'python': python_version}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Android Mirror Application - Display and control Android device',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  android-mirror                     # Start with default settings
  android-mirror --max-fps 30        # Limit to 30 FPS
  android-mirror --max-size 720      # Limit resolution to 720p
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
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(Qt.transparent)
        
        splash = QSplashScreen(splash_pixmap)
        splash.setStyleSheet("""
            QSplashScreen {
                background-color: #1e1e1e;
                border-radius: 10px;
            }
        """)
        
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
    global logger
    
    # Setup logging
    try:
        log = get_global_logger()
        log.info("=" * 50)
        log.info("Android Mirror Application Starting")
        log.info(f"Python version: {sys.version}")
        log.info(f"Platform: {platform.system()} {platform.release()}")
        log.info("=" * 50)
    except Exception:
        pass
    
    # Parse arguments
    args = parse_arguments()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Android Mirror")
    app.setOrganizationName("AndroidMirror")
    app.setStyle('Fusion')
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icons', 'app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show splash screen
    splash = show_splash_screen(app)
    if splash:
        splash.showMessage(
            "Checking system requirements...\n\n"
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
        
        try:
            log.error(error_msg)
        except:
            pass
        
        QMessageBox.critical(None, "System Requirements Failed", error_msg)
        return 1
    
    if splash:
        splash.showMessage(
            "Loading configuration...\n\n"
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
    except Exception as e:
        config = {}
        try:
            log.error(f"Failed to load configuration: {e}")
        except:
            pass
    
    if splash:
        splash.showMessage(
            "Initializing UI...\n\n"
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
        
        if args.device:
            QTimer.singleShot(500, lambda: auto_connect_device(window, args))
        
        window.show()
        
        if splash:
            splash.finish(window)
        
        try:
            log.info("Application started successfully")
        except:
            pass
        
    except Exception as e:
        if splash:
            splash.close()
        error_msg = f"Failed to start application:\n\n{str(e)}"
        try:
            log.error(error_msg, exc_info=True)
        except:
            pass
        QMessageBox.critical(None, "Startup Error", error_msg)
        return 1
    
    # Start application
    return app.exec_()

def auto_connect_device(window, args):
    """Auto-connect to specified device"""
    try:
        log = get_global_logger()
        
        if args.wifi:
            if ':' in args.device:
                ip = args.device.split(':')[0]
            else:
                ip = args.device
            window.device_manager.connect_wireless(ip)
            window._refresh_devices()
        else:
            window._refresh_devices()
            
        for i in range(window.device_combo.count()):
            if args.device in window.device_combo.itemText(i):
                window.device_combo.setCurrentIndex(i)
                break
                
        log.info(f"Auto-connected to device: {args.device}")
    except Exception as e:
        log = get_global_logger()
        log.error(f"Auto-connect failed: {e}")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        try:
            log = get_global_logger()
            log.info("Application terminated by user")
        except:
            pass
        sys.exit(0)
    except Exception as e:
        try:
            log = get_global_logger()
            log.error(f"Unhandled exception: {e}", exc_info=True)
        except:
            print(f"Unhandled exception: {e}")
            traceback.print_exc()
        sys.exit(1)