"""
WiFi Connection Dialog for Android Mirror
"""

import threading
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QProgressBar, QGroupBox, QFormLayout,
    QSpinBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMetaObject, Q_ARG, Q_RETURN_ARG
from PyQt5.QtGui import QFont
from adb.device_manager import DeviceManager
from utils.logger import get_logger


class ScanThread(QThread):
    """Thread for network scanning"""
    device_found = pyqtSignal(str)
    scan_finished = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, device_manager, network_prefix, start_ip, end_ip):
        super().__init__()
        self.device_manager = device_manager
        self.network_prefix = network_prefix
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.running = True
        
    def run(self):
        try:
            self.status_update.emit(f"Scanning {self.network_prefix}* ...")
            
            found = self.device_manager.scan_network_for_devices(
                self.network_prefix, self.start_ip, self.end_ip
            )
            
            for ip in found:
                if self.running:
                    self.device_found.emit(ip)
            
            self.status_update.emit(f"Scan completed. Found {len(found)} device(s)")
            
        except Exception as e:
            self.status_update.emit(f"Scan error: {e}")
        finally:
            self.scan_finished.emit()
    
    def stop(self):
        self.running = False


class ConnectionWorker(QThread):
    """Worker thread for connection operations"""
    finished = pyqtSignal(bool, str)
    status = pyqtSignal(str)
    
    def __init__(self, device_manager, ip, port, operation='connect'):
        super().__init__()
        self.device_manager = device_manager
        self.ip = ip
        self.port = port
        self.operation = operation  # 'connect' or 'enable_wifi'
        self.serial = None
        
    def run(self):
        try:
            if self.operation == 'connect':
                self.status.emit(f"Connecting to {self.ip}:{self.port}...")
                success = self.device_manager.connect_wireless(self.ip, self.port)
                if success:
                    self.finished.emit(True, f"Connected to {self.ip}:{self.port}")
                else:
                    self.finished.emit(False, f"Failed to connect to {self.ip}:{self.port}")
            
            elif self.operation == 'enable_wifi' and self.serial:
                self.status.emit(f"Enabling WiFi debugging on {self.serial}...")
                success = self.device_manager.enable_wifi_debugging(self.serial)
                if success:
                    ip = self.device_manager.get_device_ip(self.serial)
                    if ip:
                        self.finished.emit(True, f"WiFi debugging enabled. Device IP: {ip}")
                    else:
                        self.finished.emit(True, "WiFi debugging enabled. Check device IP in WiFi settings.")
                else:
                    self.finished.emit(False, "Failed to enable WiFi debugging")
                    
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class WiFiConnectionDialog(QDialog):
    """Dialog for WiFi connection"""
    
    def __init__(self, device_manager: DeviceManager, parent=None):
        super().__init__(parent)
        self.device_manager = device_manager
        self.logger = get_logger(__name__)
        self.scan_thread = None
        self.connection_worker = None
        
        self.setWindowTitle("WiFi Connection")
        self.setMinimumSize(550, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Manual connection section
        manual_group = QGroupBox("Manual Connection")
        manual_layout = QFormLayout()
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        manual_layout.addRow("IP Address:", self.ip_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5555)
        manual_layout.addRow("Port:", self.port_input)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.clicked.connect(self._manual_connect)
        manual_layout.addRow(self.connect_btn)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # Auto scan section
        scan_group = QGroupBox("Auto Scan Network")
        scan_layout = QVBoxLayout()
        
        # Network prefix input
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Network Prefix:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setText("192.168.1.")
        self.prefix_input.setPlaceholderText("192.168.1.")
        prefix_layout.addWidget(self.prefix_input)
        scan_layout.addLayout(prefix_layout)
        
        # IP range
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("IP Range:"))
        self.start_ip = QSpinBox()
        self.start_ip.setRange(1, 254)
        self.start_ip.setValue(1)
        range_layout.addWidget(self.start_ip)
        range_layout.addWidget(QLabel("to"))
        self.end_ip = QSpinBox()
        self.end_ip.setRange(1, 254)
        self.end_ip.setValue(254)
        range_layout.addWidget(self.end_ip)
        scan_layout.addLayout(range_layout)
        
        # Scan button
        self.scan_btn = QPushButton("🔍 Scan Network")
        self.scan_btn.clicked.connect(self._start_scan)
        scan_layout.addWidget(self.scan_btn)
        
        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)
        
        # Status label
        self.scan_status = QLabel("Ready")
        self.scan_status.setStyleSheet("color: #666; padding: 5px;")
        self.scan_status.setWordWrap(True)
        scan_layout.addWidget(self.scan_status)
        
        # Found devices list
        scan_layout.addWidget(QLabel("Found Devices:"))
        self.device_list = QListWidget()
        self.device_list.itemDoubleClicked.connect(self._connect_to_scanned_device)
        scan_layout.addWidget(self.device_list)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # USB to WiFi helper
        helper_group = QGroupBox("USB to WiFi Helper")
        helper_layout = QVBoxLayout()
        
        helper_text = QLabel(
            "To switch from USB to WiFi:\n"
            "1. Connect device via USB\n"
            "2. Click 'Enable WiFi Debugging' below\n"
            "3. Disconnect USB cable\n"
            "4. Connect via WiFi using IP address shown"
        )
        helper_text.setWordWrap(True)
        helper_text.setStyleSheet("color: #666;")
        helper_layout.addWidget(helper_text)
        
        self.enable_wifi_btn = QPushButton("🔌 Enable WiFi Debugging on USB Device")
        self.enable_wifi_btn.clicked.connect(self._enable_wifi_debugging)
        helper_layout.addWidget(self.enable_wifi_btn)
        
        helper_group.setLayout(helper_layout)
        layout.addWidget(helper_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _update_status(self, message):
        """Update status label safely"""
        self.scan_status.setText(message)
    
    def _add_device_item(self, ip):
        """Add device item to list (called from main thread via signal)"""
        item = QListWidgetItem(f"📱 {ip}:5555")
        item.setData(Qt.UserRole, ip)
        self.device_list.addItem(item)
    
    def _manual_connect(self):
        """Connect to manually entered IP"""
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
        
        if not ip:
            QMessageBox.warning(self, "Invalid IP", "Please enter an IP address.")
            return
        
        # Disable buttons during connection
        self.connect_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.enable_wifi_btn.setEnabled(False)
        self._update_status(f"Connecting to {ip}:{port}...")
        
        # Create worker thread
        self.connection_worker = ConnectionWorker(self.device_manager, ip, port, 'connect')
        self.connection_worker.status.connect(self._update_status)
        self.connection_worker.finished.connect(self._on_connection_finished)
        self.connection_worker.start()
    
    def _on_connection_finished(self, success, message):
        """Handle connection finished"""
        # Re-enable buttons
        self.connect_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.enable_wifi_btn.setEnabled(True)
        
        if success:
            self._update_status(f"✓ {message}")
            # Refresh parent's device list
            if self.parent():
                self.parent()._refresh_devices()
            QMessageBox.information(self, "Success", message)
            # Auto-close after successful connection
            self.accept()
        else:
            self._update_status(f"✗ {message}")
            QMessageBox.warning(self, "Connection Failed", 
                               f"{message}\n\n"
                               "Make sure:\n"
                               "1. Device is on the same network\n"
                               "2. USB debugging is enabled\n"
                               "3. WiFi debugging is enabled (run: adb tcpip 5555)")
    
    def _start_scan(self):
        """Start network scan"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_btn.setText("🔍 Scan Network")
            return
        
        network_prefix = self.prefix_input.text().strip()
        start = self.start_ip.value()
        end = self.end_ip.value()
        
        if not network_prefix:
            QMessageBox.warning(self, "Invalid Network", "Please enter network prefix.")
            return
        
        # Clear list
        self.device_list.clear()
        self.scan_progress.setVisible(True)
        self.scan_progress.setRange(0, 0)
        self.scan_btn.setText("⏹ Stop Scan")
        self._update_status("Scanning...")
        
        self.scan_thread = ScanThread(self.device_manager, network_prefix, start, end)
        self.scan_thread.device_found.connect(self._add_device_item)  # Direct connection, auto-queued
        self.scan_thread.scan_finished.connect(self._on_scan_finished)
        self.scan_thread.status_update.connect(self._update_status)
        self.scan_thread.start()
    
    def _on_scan_finished(self):
        """Handle scan completion"""
        self.scan_progress.setVisible(False)
        self.scan_btn.setText("🔍 Scan Network")
        
        if self.device_list.count() == 0:
            self._update_status("No devices found. Make sure WiFi debugging is enabled on your device.")
        else:
            self._update_status(f"Found {self.device_list.count()} device(s). Double-click to connect.")
    
    def _connect_to_scanned_device(self, item):
        """Connect to device from scanned list"""
        ip = item.data(Qt.UserRole)
        if ip:
            self.ip_input.setText(ip)
            self._manual_connect()
    
    def _enable_wifi_debugging(self):
        """Enable WiFi debugging on USB-connected device"""
        # Get USB devices
        devices = self.device_manager.list_devices()
        usb_devices = [d for d in devices if d.get('connection_type') == 'USB']
        
        if not usb_devices:
            QMessageBox.warning(self, "No USB Device", 
                               "No USB device found. Please connect a device via USB.")
            return
        
        if len(usb_devices) == 1:
            serial = usb_devices[0]['serial']
            self._do_enable_wifi(serial)
        else:
            # Multiple USB devices, ask which one
            from PyQt5.QtWidgets import QInputDialog
            items = [f"{d['serial']} ({d.get('model', 'Unknown')})" for d in usb_devices]
            item, ok = QInputDialog.getItem(self, "Select Device", 
                                            "Select USB device:", items, 0, False)
            if ok and item:
                serial = item.split()[0]
                self._do_enable_wifi(serial)
    
    def _do_enable_wifi(self, serial):
        """Actually enable WiFi debugging"""
        # Disable buttons
        self.connect_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.enable_wifi_btn.setEnabled(False)
        self._update_status(f"Enabling WiFi debugging on {serial}...")
        
        # Create worker thread
        self.connection_worker = ConnectionWorker(self.device_manager, None, None, 'enable_wifi')
        self.connection_worker.serial = serial
        self.connection_worker.status.connect(self._update_status)
        self.connection_worker.finished.connect(self._on_wifi_enable_finished)
        self.connection_worker.start()
    
    def _on_wifi_enable_finished(self, success, message):
        """Handle WiFi enable finished"""
        # Re-enable buttons
        self.connect_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.enable_wifi_btn.setEnabled(True)
        
        if success:
            self._update_status(f"✓ {message}")
            QMessageBox.information(self, "Success", message)
            
            # Try to extract IP from message
            import re
            match = re.search(r'IP: (\d+\.\d+\.\d+\.\d+)', message)
            if match:
                self.ip_input.setText(match.group(1))
        else:
            self._update_status(f"✗ {message}")
            QMessageBox.warning(self, "Failed", message)