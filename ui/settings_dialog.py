"""
Settings Dialog for Android Mirror
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QSlider, QLineEdit, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from utils.config import get_config
from utils.logger import get_logger


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs"""
    
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self._create_general_tab()
        self._create_video_tab()
        self._create_audio_tab()
        self._create_connection_tab()
        self._create_paths_tab()
        self._create_advanced_tab()
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setMinimumHeight(35)
        save_btn.setStyleSheet("background-color: #1e1bab;")
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(35)
        save_btn.setStyleSheet("background-color: #1e1bab;")
        button_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._reset_settings)
        reset_btn.setMinimumHeight(35)
        reset_btn.setStyleSheet("background-color: #1e1bab;")
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
    def _create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme section
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Language section
        lang_group = QGroupBox("Language")
        lang_layout = QFormLayout()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Indonesian", "Japanese", "Chinese"])
        lang_layout.addRow("Language:", self.lang_combo)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Startup section
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout()
        
        self.auto_connect = QCheckBox("Auto-connect to last device")
        startup_layout.addRow(self.auto_connect)
        
        self.check_updates = QCheckBox("Check for updates on startup")
        startup_layout.addRow(self.check_updates)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "General")
        
    def _create_video_tab(self):
        """Create video settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Video quality section
        quality_group = QGroupBox("Video Quality")
        quality_layout = QFormLayout()
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x360", "854x480", "1024x576", "1280x720", "1920x1080"])
        quality_layout.addRow("Max Resolution:", self.resolution_combo)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 120)
        self.fps_spin.setSuffix(" fps")
        quality_layout.addRow("Max FPS:", self.fps_spin)
        
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["1M", "2M", "4M", "8M", "16M", "32M"])
        quality_layout.addRow("Video Bitrate:", self.bitrate_combo)
        
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["h264", "h265", "av1"])
        quality_layout.addRow("Video Codec:", self.codec_combo)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Buffer section
        buffer_group = QGroupBox("Video Buffer")
        buffer_layout = QFormLayout()
        
        self.buffer_slider = QSlider(Qt.Horizontal)
        self.buffer_slider.setRange(0, 500)
        self.buffer_slider.setTickInterval(50)
        self.buffer_slider.setTickPosition(QSlider.TicksBelow)
        
        self.buffer_label = QLabel("0 ms")
        self.buffer_slider.valueChanged.connect(lambda v: self.buffer_label.setText(f"{v} ms"))
        
        buffer_layout.addRow("Buffer Size:", self.buffer_slider)
        buffer_layout.addRow("", self.buffer_label)
        
        buffer_group.setLayout(buffer_layout)
        layout.addWidget(buffer_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Video")
        
    def _create_audio_tab(self):
        """Create audio settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Audio section
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QFormLayout()
        
        self.audio_enabled = QCheckBox("Enable Audio Streaming")
        audio_layout.addRow(self.audio_enabled)
        
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["opus", "aac", "raw"])
        self.audio_codec_combo.setEnabled(False)
        self.audio_enabled.toggled.connect(self.audio_codec_combo.setEnabled)
        audio_layout.addRow("Audio Codec:", self.audio_codec_combo)
        
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["64k", "128k", "192k", "256k"])
        self.audio_bitrate_combo.setEnabled(False)
        self.audio_enabled.toggled.connect(self.audio_bitrate_combo.setEnabled)
        audio_layout.addRow("Audio Bitrate:", self.audio_bitrate_combo)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Audio")
        
    def _create_connection_tab(self):
        """Create connection settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # WiFi settings
        wifi_group = QGroupBox("WiFi Settings")
        wifi_layout = QFormLayout()
        
        self.wifi_port = QSpinBox()
        self.wifi_port.setRange(1024, 65535)
        self.wifi_port.setValue(5555)
        wifi_layout.addRow("ADB Port:", self.wifi_port)
        
        self.wifi_timeout = QSpinBox()
        self.wifi_timeout.setRange(5, 60)
        self.wifi_timeout.setSuffix(" seconds")
        wifi_layout.addRow("Connection Timeout:", self.wifi_timeout)
        
        self.auto_reconnect = QCheckBox("Auto-reconnect on disconnect")
        wifi_layout.addRow(self.auto_reconnect)
        
        wifi_group.setLayout(wifi_layout)
        layout.addWidget(wifi_group)
        
        # Network scan settings
        scan_group = QGroupBox("Network Scan")
        scan_layout = QFormLayout()
        
        self.scan_timeout = QSpinBox()
        self.scan_timeout.setRange(1, 10)
        self.scan_timeout.setSuffix(" seconds")
        scan_layout.addRow("Scan Timeout:", self.scan_timeout)
        
        self.scan_range_start = QSpinBox()
        self.scan_range_start.setRange(1, 254)
        scan_layout.addRow("IP Range Start:", self.scan_range_start)
        
        self.scan_range_end = QSpinBox()
        self.scan_range_end.setRange(1, 254)
        scan_layout.addRow("IP Range End:", self.scan_range_end)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Connection")
        
    def _create_paths_tab(self):
        """Create paths settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Paths section
        paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout()
        
        # Screenshot path
        screenshot_layout = QHBoxLayout()
        self.screenshot_path = QLineEdit()
        self.screenshot_path.setReadOnly(True)
        screenshot_layout.addWidget(self.screenshot_path)
        
        screenshot_browse = QPushButton("Browse")
        screenshot_browse.clicked.connect(lambda: self._browse_folder(self.screenshot_path))
        screenshot_layout.addWidget(screenshot_browse)
        paths_layout.addRow("Screenshot Folder:", screenshot_layout)
        
        # Recording path
        record_layout = QHBoxLayout()
        self.record_path = QLineEdit()
        self.record_path.setReadOnly(True)
        record_layout.addWidget(self.record_path)
        
        record_browse = QPushButton("Browse")
        record_browse.clicked.connect(lambda: self._browse_folder(self.record_path))
        record_layout.addWidget(record_browse)
        paths_layout.addRow("Recording Folder:", record_layout)
        
        # Log path
        log_layout = QHBoxLayout()
        self.log_path = QLineEdit()
        self.log_path.setReadOnly(True)
        log_layout.addWidget(self.log_path)
        
        log_browse = QPushButton("Browse")
        log_browse.clicked.connect(lambda: self._browse_folder(self.log_path))
        log_layout.addWidget(log_browse)
        paths_layout.addRow("Log Folder:", log_layout)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # Scrcpy path
        scrcpy_group = QGroupBox("Scrcpy")
        scrcpy_layout = QFormLayout()
        
        scrcpy_path_layout = QHBoxLayout()
        self.scrcpy_path = QLineEdit()
        self.scrcpy_path.setReadOnly(True)
        scrcpy_path_layout.addWidget(self.scrcpy_path)
        
        scrcpy_browse = QPushButton("Browse")
        scrcpy_browse.clicked.connect(self._browse_scrcpy)
        scrcpy_path_layout.addWidget(scrcpy_browse)
        
        scrcpy_layout.addRow("Scrcpy Path:", scrcpy_path_layout)
        
        scrcpy_group.setLayout(scrcpy_layout)
        layout.addWidget(scrcpy_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Paths")
        
    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout()
        
        self.show_fps = QCheckBox("Show FPS in window title")
        advanced_layout.addRow(self.show_fps)
        
        self.stay_awake = QCheckBox("Keep device awake while mirroring")
        advanced_layout.addRow(self.stay_awake)
        
        self.turn_screen_off = QCheckBox("Turn screen off while mirroring")
        advanced_layout.addRow(self.turn_screen_off)
        
        self.power_off_on_close = QCheckBox("Power off device on mirroring close")
        advanced_layout.addRow(self.power_off_on_close)
        
        self.always_on_top = QCheckBox("Keep window always on top")
        advanced_layout.addRow(self.always_on_top)
        
        self.fullscreen = QCheckBox("Start in fullscreen mode")
        advanced_layout.addRow(self.fullscreen)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Debug section
        debug_group = QGroupBox("Debugging")
        debug_layout = QFormLayout()
        
        self.debug_mode = QCheckBox("Enable debug logging")
        debug_layout.addRow(self.debug_mode)
        
        self.verbose_log = QCheckBox("Verbose logging")
        self.verbose_log.setEnabled(False)
        self.debug_mode.toggled.connect(self.verbose_log.setEnabled)
        debug_layout.addRow(self.verbose_log)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Advanced")
        
    def _browse_folder(self, line_edit):
        """Browse for folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", line_edit.text())
        if folder:
            line_edit.setText(folder)
            
    def _browse_scrcpy(self):
        """Browse for scrcpy executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select scrcpy.exe", 
            self.scrcpy_path.text(),
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.scrcpy_path.setText(file_path)
    
    def _load_settings(self):
        """Load settings from config"""
        # General
        self.theme_combo.setCurrentText(self.config.get('ui.theme', 'Dark'))
        self.lang_combo.setCurrentText(self.config.get('ui.language', 'English'))
        self.auto_connect.setChecked(self.config.get('startup.auto_connect', False))
        self.check_updates.setChecked(self.config.get('startup.check_updates', True))
        
        # Video
        resolution_map = {
            640: "640x360", 854: "854x480", 1024: "1024x576",
            1280: "1280x720", 1920: "1920x1080"
        }
        max_size = self.config.get('display.max_size', 1280)
        self.resolution_combo.setCurrentText(resolution_map.get(max_size, "1280x720"))
        self.fps_spin.setValue(self.config.get('display.max_fps', 60))
        self.bitrate_combo.setCurrentText(self.config.get('video.bit_rate', '8M'))
        self.codec_combo.setCurrentText(self.config.get('video.video_codec', 'h264'))
        self.buffer_slider.setValue(self.config.get('video.buffer', 100))
        
        # Audio
        self.audio_enabled.setChecked(self.config.get('audio.enabled', True))
        self.audio_codec_combo.setCurrentText(self.config.get('audio.codec', 'opus'))
        self.audio_bitrate_combo.setCurrentText(self.config.get('audio.bit_rate', '128k'))
        
        # Connection
        self.wifi_port.setValue(self.config.get('connection.wireless_port', 5555))
        self.wifi_timeout.setValue(self.config.get('connection.timeout_seconds', 10))
        self.auto_reconnect.setChecked(self.config.get('connection.auto_reconnect', True))
        self.scan_timeout.setValue(self.config.get('network.scan_timeout', 3))
        self.scan_range_start.setValue(self.config.get('network.scan_start', 1))
        self.scan_range_end.setValue(self.config.get('network.scan_end', 254))
        
        # Paths
        self.screenshot_path.setText(self.config.get('paths.screenshots', os.path.expanduser('~/Pictures')))
        self.record_path.setText(self.config.get('paths.recordings', os.path.expanduser('~/Videos')))
        self.log_path.setText(self.config.get('paths.logs', 'logs'))
        self.scrcpy_path.setText(self.config.get('paths.scrcpy', ''))
        
        # Advanced
        self.show_fps.setChecked(self.config.get('advanced.show_fps', True))
        self.stay_awake.setChecked(self.config.get('device.stay_awake', True))
        self.turn_screen_off.setChecked(self.config.get('device.turn_screen_off', False))
        self.power_off_on_close.setChecked(self.config.get('device.power_off_on_close', False))
        self.always_on_top.setChecked(self.config.get('window.always_on_top', False))
        self.fullscreen.setChecked(self.config.get('window.fullscreen', False))
        self.debug_mode.setChecked(self.config.get('logging.level', 'INFO') == 'DEBUG')
        self.verbose_log.setChecked(self.config.get('logging.verbose', False))
        
    def _save_settings(self):
        """Save settings to config"""
        try:
            # General
            self.config.set('ui.theme', self.theme_combo.currentText())
            self.config.set('ui.language', self.lang_combo.currentText())
            self.config.set('startup.auto_connect', self.auto_connect.isChecked())
            self.config.set('startup.check_updates', self.check_updates.isChecked())
            
            # Video
            resolution = self.resolution_combo.currentText().split('x')[0]
            self.config.set('display.max_size', int(resolution))
            self.config.set('display.max_fps', self.fps_spin.value())
            self.config.set('video.bit_rate', self.bitrate_combo.currentText())
            self.config.set('video.video_codec', self.codec_combo.currentText())
            self.config.set('video.buffer', self.buffer_slider.value())
            
            # Audio
            self.config.set('audio.enabled', self.audio_enabled.isChecked())
            self.config.set('audio.codec', self.audio_codec_combo.currentText())
            self.config.set('audio.bit_rate', self.audio_bitrate_combo.currentText())
            
            # Connection
            self.config.set('connection.wireless_port', self.wifi_port.value())
            self.config.set('connection.timeout_seconds', self.wifi_timeout.value())
            self.config.set('connection.auto_reconnect', self.auto_reconnect.isChecked())
            self.config.set('network.scan_timeout', self.scan_timeout.value())
            self.config.set('network.scan_start', self.scan_range_start.value())
            self.config.set('network.scan_end', self.scan_range_end.value())
            
            # Paths
            self.config.set('paths.screenshots', self.screenshot_path.text())
            self.config.set('paths.recordings', self.record_path.text())
            self.config.set('paths.logs', self.log_path.text())
            self.config.set('paths.scrcpy', self.scrcpy_path.text())
            
            # Advanced
            self.config.set('advanced.show_fps', self.show_fps.isChecked())
            self.config.set('device.stay_awake', self.stay_awake.isChecked())
            self.config.set('device.turn_screen_off', self.turn_screen_off.isChecked())
            self.config.set('device.power_off_on_close', self.power_off_on_close.isChecked())
            self.config.set('window.always_on_top', self.always_on_top.isChecked())
            self.config.set('window.fullscreen', self.fullscreen.isChecked())
            
            log_level = 'DEBUG' if self.debug_mode.isChecked() else 'INFO'
            self.config.set('logging.level', log_level)
            self.config.set('logging.verbose', self.verbose_log.isChecked())
            
            # Save config
            self.config.save()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!\n\nSome changes may require restart to take effect.")
            self.settings_saved.emit()
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
            
    def _reset_settings(self):
        """Reset all settings to default"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to default?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self.theme_combo.setCurrentIndex(0)  # Dark
            self.lang_combo.setCurrentIndex(0)   # English
            self.auto_connect.setChecked(False)
            self.check_updates.setChecked(True)
            
            self.resolution_combo.setCurrentText("1280x720")
            self.fps_spin.setValue(60)
            self.bitrate_combo.setCurrentText("8M")
            self.codec_combo.setCurrentText("h264")
            self.buffer_slider.setValue(100)
            
            self.audio_enabled.setChecked(True)
            self.audio_codec_combo.setCurrentText("opus")
            self.audio_bitrate_combo.setCurrentText("128k")
            
            self.wifi_port.setValue(5555)
            self.wifi_timeout.setValue(10)
            self.auto_reconnect.setChecked(True)
            self.scan_timeout.setValue(3)
            self.scan_range_start.setValue(1)
            self.scan_range_end.setValue(254)
            
            self.screenshot_path.setText(os.path.expanduser('~/Pictures'))
            self.record_path.setText(os.path.expanduser('~/Videos'))
            self.log_path.setText('logs')
            self.scrcpy_path.clear()
            
            self.show_fps.setChecked(True)
            self.stay_awake.setChecked(True)
            self.turn_screen_off.setChecked(False)
            self.power_off_on_close.setChecked(False)
            self.always_on_top.setChecked(False)
            self.fullscreen.setChecked(False)
            self.debug_mode.setChecked(False)
            self.verbose_log.setChecked(False)
            
            QMessageBox.information(self, "Reset", "Settings have been reset to default values.")