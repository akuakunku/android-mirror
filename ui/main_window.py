"""
Main GUI window for Android Mirror
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QStatusBar,
    QToolBar, QAction, QMessageBox, QFileDialog,
    QSlider, QCheckBox, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QImage
from core.mirror import AndroidMirror
from core.controller import InputController
from core.recorder import ScreenRecorder
from core.file_transfer import FileTransfer
from adb.device_manager import DeviceManager
from utils.logger import get_logger
import cv2
import numpy as np

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config: dict, args):
        super().__init__()
        self.config = config
        self.args = args
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.device_manager = DeviceManager(config)
        self.mirror = AndroidMirror(config)
        self.controller = InputController()
        self.recorder = ScreenRecorder()
        self.file_transfer = FileTransfer()
        
        # UI setup
        self.setWindowTitle("Android Mirror Controller")
        self.setMinimumSize(500, 400)
        self.setFixedSize(650, 650)  # Increased for optimization section
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        # Create UI
        self._create_toolbar()
        self._create_status_bar()
        self._create_control_panel()
        
        # State
        self.is_mirroring = False
        
        # Load devices
        self._refresh_devices()
        
    def _create_toolbar(self):
        """Create main toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Start/Stop mirroring
        self.start_action = QAction("▶ Start", self)
        self.start_action.triggered.connect(self.start_mirroring)
        toolbar.addAction(self.start_action)
        
        self.stop_action = QAction("⏹ Stop", self)
        self.stop_action.triggered.connect(self.stop_mirroring)
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.stop_action)
        
        toolbar.addSeparator()
        
        # Screenshot
        screenshot_action = QAction("📷 Screenshot", self)
        screenshot_action.triggered.connect(self.take_screenshot)
        toolbar.addAction(screenshot_action)
        
        # Record
        self.record_action = QAction("🔴 Record", self)
        self.record_action.triggered.connect(self.toggle_recording)
        toolbar.addAction(self.record_action)
        
        toolbar.addSeparator()
        
        # Settings
        settings_action = QAction("⚙ Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        # Help
        help_action = QAction("❓ Help", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
        
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Device info label
        self.device_label = QLabel("📱 No device connected")
        self.status_bar.addWidget(self.device_label)
        
        # Mirroring status
        self.mirror_status = QLabel("⭕ Not mirroring")
        self.status_bar.addPermanentWidget(self.mirror_status)
        
        # Recording indicator
        self.recording_label = QLabel("")
        self.status_bar.addPermanentWidget(self.recording_label)
        
    def _create_control_panel(self):
        """Create control panel"""
        # Device section
        device_group = QGroupBox("Device Connection")
        device_layout = QGridLayout()
        
        device_layout.addWidget(QLabel("Device:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo, 0, 1)
        
        self.connect_btn = QPushButton("🔌 Connect USB")
        self.connect_btn.clicked.connect(self.connect_device)
        device_layout.addWidget(self.connect_btn, 0, 2)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_devices)
        device_layout.addWidget(refresh_btn, 1, 1)
        
        wifi_btn = QPushButton("📶 WiFi Connect")
        wifi_btn.clicked.connect(self.wifi_connect)
        device_layout.addWidget(wifi_btn, 1, 2)
        
        device_group.setLayout(device_layout)
        self.layout.addWidget(device_group)
        
        # Control section
        control_group = QGroupBox("Screen Control")
        control_layout = QGridLayout()
        
        # Mirroring controls
        self.mirror_btn = QPushButton("🎬 START MIRRORING")
        self.mirror_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.mirror_btn.clicked.connect(self.start_mirroring)
        control_layout.addWidget(self.mirror_btn, 0, 0, 1, 2)
        
        self.stop_mirror_btn = QPushButton("⏹ STOP MIRRORING")
        self.stop_mirror_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_mirror_btn.clicked.connect(self.stop_mirroring)
        self.stop_mirror_btn.setEnabled(False)
        control_layout.addWidget(self.stop_mirror_btn, 1, 0, 1, 2)
        
        control_group.setLayout(control_layout)
        self.layout.addWidget(control_group)
        
        # Actions section
        actions_group = QGroupBox("Actions")
        actions_layout = QGridLayout()
        
        screenshot_btn = QPushButton("📸 Take Screenshot")
        screenshot_btn.clicked.connect(self.take_screenshot)
        actions_layout.addWidget(screenshot_btn, 0, 0)
        
        self.record_btn = QPushButton("🎥 Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        actions_layout.addWidget(self.record_btn, 0, 1)
        
        file_btn = QPushButton("📁 File Transfer")
        file_btn.clicked.connect(self.open_file_transfer)
        actions_layout.addWidget(file_btn, 1, 0)
        
        info_btn = QPushButton("ℹ Device Info")
        info_btn.clicked.connect(self.show_device_info)
        actions_layout.addWidget(info_btn, 1, 1)
        
        actions_group.setLayout(actions_layout)
        self.layout.addWidget(actions_group)
        
        # ============ OPTIMIZATION SECTION ============
        opt_group = QGroupBox("Performance Optimization")
        opt_layout = QVBoxLayout()
        
        self.opt_label = QLabel("Select optimization mode for connection:")
        opt_layout.addWidget(self.opt_label)
        
        self.opt_combo = QComboBox()
        self.opt_combo.addItem("🚀 Low Latency (Fastest - for WiFi)", "latency")
        self.opt_combo.addItem("⚖️ Balanced (Recommended)", "balanced")
        self.opt_combo.addItem("🎨 High Quality (Best visual - for USB)", "quality")
        self.opt_combo.setCurrentIndex(1)  # Default balanced
        self.opt_combo.currentIndexChanged.connect(self._on_optimization_changed)
        opt_layout.addWidget(self.opt_combo)
        
        # Info label
        self.opt_info = QLabel(
            "📡 WiFi Tips:\n"
            "• Low Latency: 720p @30fps, minimal buffer\n"
            "• Balanced: 1024p @45fps, recommended for WiFi\n"
            "• High Quality: 1080p+ @60fps, best for USB"
        )
        self.opt_info.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        self.opt_info.setWordWrap(True)
        opt_layout.addWidget(self.opt_info)
        
        opt_group.setLayout(opt_layout)
        self.layout.addWidget(opt_group)
        
        # Tips section
        tips_group = QGroupBox("Tips & Shortcuts")
        tips_layout = QVBoxLayout()
        
        tips_text = QLabel(
            "🎮 **Mouse Controls:**\n"
            "  • Left Click → Tap\n"
            "  • Right Click → Back\n"
            "  • Middle Click → Home\n"
            "  • Drag → Swipe\n"
            "  • Scroll → Scroll\n\n"
            "⌨ **Keyboard Shortcuts:**\n"
            "  • Type directly → Text input\n"
            "  • Arrow Keys → Navigation\n"
            "  • Enter → Select/Enter\n"
            "  • ESC → Back\n"
            "  • F1-F12 → Function keys\n\n"
            "📡 **WiFi Tips:**\n"
            "  • Use Low Latency mode for better WiFi performance\n"
            "  • Position device closer to WiFi router\n"
            "  • Use 5GHz WiFi if available"
        )
        tips_text.setTextFormat(Qt.RichText)
        tips_text.setWordWrap(True)
        tips_layout.addWidget(tips_text)
        
        tips_group.setLayout(tips_layout)
        self.layout.addWidget(tips_group)
        
        self.layout.addStretch()
    
    def _on_optimization_changed(self, index):
        """Handle optimization mode change"""
        mode = self.opt_combo.currentData()
        
        if mode == 'latency':
            self.opt_info.setText(
                "🚀 Low Latency Mode:\n"
                "• Resolution: 720p\n"
                "• Frame Rate: 30 fps\n"
                "• Bitrate: 2 Mbps\n"
                "• Audio: Disabled\n"
                "• Best for: WiFi connections with high latency"
            )
        elif mode == 'balanced':
            self.opt_info.setText(
                "⚖️ Balanced Mode:\n"
                "• Resolution: 1024p\n"
                "• Frame Rate: 45 fps\n"
                "• Bitrate: 4 Mbps\n"
                "• Audio: Enabled\n"
                "• Best for: Most WiFi connections"
            )
        elif mode == 'quality':
            self.opt_info.setText(
                "🎨 High Quality Mode:\n"
                "• Resolution: 1080p+\n"
                "• Frame Rate: 60 fps\n"
                "• Bitrate: 16 Mbps\n"
                "• Audio: Enabled\n"
                "• Best for: USB or very fast WiFi"
            )
    
    def _refresh_devices(self):
        """Refresh device list"""
        devices = self.device_manager.list_devices()
        self.device_combo.clear()
        
        for device in devices:
            connection_type = device.get('connection_type', 'Unknown')
            text = f"{device['serial']} ({connection_type})"
            self.device_combo.addItem(text, device['serial'])
        
        if devices:
            self.device_label.setText(f"📱 Device: {len(devices)} connected")
        else:
            self.device_label.setText("📱 No device connected")
            
    def on_device_changed(self, index):
        """Handle device selection change"""
        if index >= 0:
            serial = self.device_combo.itemData(index)
            self.controller.device_serial = serial
            self.recorder.device_serial = serial
            self.file_transfer.device_serial = serial
            
    def connect_device(self):
        """Connect to selected device"""
        index = self.device_combo.currentIndex()
        if index >= 0:
            serial = self.device_combo.itemData(index)
            self.status_bar.showMessage(f"Connecting to {serial}...", 2000)
            # Test connection
            devices = self.device_manager.list_devices()
            if any(d['serial'] == serial for d in devices):
                self.status_bar.showMessage(f"✅ Connected to {serial}", 3000)
                self.logger.info(f"Connected to {serial}")
            else:
                self.status_bar.showMessage(f"❌ Failed to connect to {serial}", 3000)
            
    def wifi_connect(self):
        """Open WiFi connection dialog"""
        from .wifi_dialog import WiFiConnectionDialog
        
        dialog = WiFiConnectionDialog(self.device_manager, self)
        dialog.exec_()
        self._refresh_devices()  # Refresh after dialog closes
            
    def start_mirroring(self):
        """Start screen mirroring"""
        if not self.device_combo.currentIndex() >= 0:
            QMessageBox.warning(self, "No Device", 
                              "Please select a device first!")
            return
            
        try:
            serial = self.device_combo.currentData()
            
            # Get optimization mode
            opt_mode = self.opt_combo.currentData()
            
            # Start mirroring with selected optimization
            if self.mirror.start_mirroring(serial, optimization=opt_mode):
                self.is_mirroring = True
                self.start_action.setEnabled(False)
                self.stop_action.setEnabled(True)
                self.mirror_btn.setEnabled(False)
                self.stop_mirror_btn.setEnabled(True)
                self.mirror_status.setText("🟢 Mirroring active")
                
                mode_names = {
                    'latency': 'Low Latency',
                    'balanced': 'Balanced',
                    'quality': 'High Quality'
                }
                self.status_bar.showMessage(
                    f"✅ Mirroring started ({mode_names.get(opt_mode, 'Balanced')} mode) - scrcpy window opened", 
                    5000
                )
                self.logger.info(f"Mirroring started with {opt_mode} optimization")
            else:
                QMessageBox.critical(self, "Error", 
                                   "Failed to start mirroring!\n\n"
                                   "Make sure:\n"
                                   "1. USB debugging is enabled\n"
                                   "2. Device is connected\n"
                                   "3. scrcpy is properly installed")
        except Exception as e:
            self.logger.error(f"Start mirroring failed: {e}")
            QMessageBox.critical(self, "Error", str(e))
            
    def stop_mirroring(self):
        """Stop screen mirroring"""
        try:
            self.mirror.stop_mirroring()
            self.is_mirroring = False
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.mirror_btn.setEnabled(True)
            self.stop_mirror_btn.setEnabled(False)
            self.mirror_status.setText("⭕ Not mirroring")
            self.status_bar.showMessage("Mirroring stopped", 3000)
            self.logger.info("Mirroring stopped")
        except Exception as e:
            self.logger.error(f"Stop mirroring failed: {e}")
    
    def take_screenshot(self):
        """Take screenshot"""
        if not self.is_mirroring:
            QMessageBox.warning(self, "Not Mirroring", 
                              "Start mirroring first!")
            return
            
        try:
            from datetime import datetime
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Screenshot", 
                f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG Files (*.png);;JPEG Files (*.jpg)"
            )
            if file_path:
                screenshot = self.mirror.capture_screenshot()
                if screenshot:
                    with open(file_path, 'wb') as f:
                        f.write(screenshot)
                    self.status_bar.showMessage(f"✅ Screenshot saved: {file_path}", 3000)
                    self.logger.info(f"Screenshot saved to {file_path}")
                else:
                    self.status_bar.showMessage("❌ Failed to capture screenshot", 3000)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to take screenshot: {e}")
            
    def toggle_recording(self):
        """Toggle screen recording"""
        if self.recorder.is_recording:
            file_path = self.recorder.stop_recording()
            if file_path:
                self.status_bar.showMessage(f"✅ Recording saved: {file_path}", 5000)
                self.recording_label.setText("")
                self.record_action.setText("🔴 Record")
                self.record_btn.setText("🎥 Start Recording")
                self.logger.info(f"Recording saved to {file_path}")
            else:
                self.status_bar.showMessage("❌ Recording failed!", 3000)
        else:
            from datetime import datetime
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Recording",
                f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                "MP4 Files (*.mp4)"
            )
            if file_path:
                if self.recorder.start_recording(file_path):
                    self.status_bar.showMessage("🔴 Recording started...", 3000)
                    self.recording_label.setText("🔴 RECORDING")
                    self.record_action.setText("⏹ Stop")
                    self.record_btn.setText("⏹ Stop Recording")
                    self.logger.info(f"Recording started: {file_path}")
                else:
                    self.status_bar.showMessage("❌ Failed to start recording", 3000)
                
    def open_file_transfer(self):
        """Open file transfer dialog"""
        from .file_transfer_dialog import FileTransferDialog
        
        # Pastikan device terpilih
        if not self.device_combo.currentIndex() >= 0:
            QMessageBox.warning(self, "No Device", 
                            "Please select a device first!")
            return
        
        # Update device serial di file_transfer
        serial = self.device_combo.currentData()
        self.file_transfer.device_serial = serial
        
        # Buka dialog
        dialog = FileTransferDialog(self.file_transfer, self)
        dialog.exec_()
        
    def show_device_info(self):
        """Show device information"""
        index = self.device_combo.currentIndex()
        if index >= 0:
            serial = self.device_combo.itemData(index)
            info = self.device_manager.get_device_info(serial)
            
            info_text = f"Device Information:\n\n"
            info_text += f"Serial: {serial}\n"
            info_text += f"Model: {info.get('model', 'Unknown')}\n"
            info_text += f"Manufacturer: {info.get('manufacturer', 'Unknown')}\n"
            info_text += f"Android Version: {info.get('android_version', 'Unknown')}\n"
            info_text += f"Resolution: {info.get('resolution', 'Unknown')}\n"
            
            QMessageBox.information(self, "Device Info", info_text)
            
    def open_settings(self):
        """Open settings dialog"""
        from .settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec_()
    
    def _on_settings_saved(self):
        """Handle settings saved"""
        self.status_bar.showMessage("Settings saved. Some changes may require restart.", 5000)
        self.logger.info("Settings updated")
            
    def show_help(self):
        """Show help dialog"""
        QMessageBox.information(self, "Help", 
            "Android Mirror Controller\n\n"
            "How to use:\n"
            "1. Connect Android device via USB\n"
            "2. Enable USB debugging on device\n"
            "3. Click 'Refresh' to detect device\n"
            "4. Select device and click 'START MIRRORING'\n"
            "5. scrcpy window will open automatically\n\n"
            "For wireless connection:\n"
            "1. Connect via USB first\n"
            "2. Run: adb tcpip 5555\n"
            "3. Disconnect USB\n"
            "4. Click 'WiFi Connect' and enter device IP\n\n"
            "For better WiFi performance:\n"
            "• Use Low Latency optimization mode\n"
            "• Use 5GHz WiFi if available\n"
            "• Position device closer to router\n\n"
            "For more info: https://github.com/Genymobile/scrcpy")
            
    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_mirroring()
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        event.accept()