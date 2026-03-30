"""
File Transfer Dialog for Android Mirror
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QLabel, QProgressBar, QMessageBox, QFileDialog,
    QInputDialog, QLineEdit, QMenu, QAction,
    QHeaderView, QApplication, QWidget, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
from core.file_transfer import FileTransfer
from utils.logger import get_logger


class TransferThread(QThread):
    """Thread for file transfer operations"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, transfer_func, *args, **kwargs):
        super().__init__()
        self.transfer_func = transfer_func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.transfer_func(*self.args, **self.kwargs)
            self.finished.emit(result, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class FileTransferDialog(QDialog):
    """File Transfer Dialog"""
    
    def __init__(self, file_transfer: FileTransfer, parent=None):
        super().__init__(parent)
        self.file_transfer = file_transfer
        self.logger = get_logger(__name__)
        self.current_path = "/storage/emulated/0"
        self.transfer_thread = None
        
        # Storage locations dengan emoji
        self.storage_locations = {
            "📱 Internal Storage": "/storage/emulated/0",
            "💾 SD Card (if available)": "/storage/sdcard1",
            "🗂 External Storage": "/storage/extSdCard",
            "🔧 Root": "/"
        }
        
        self.setWindowTitle("File Transfer - Android Mirror")
        self.setMinimumSize(950, 650)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._setup_ui()
        self._refresh_current_directory()
    
    def _get_file_icon(self, filename: str, is_dir: bool) -> str:
        """Get appropriate emoji icon for file/folder"""
        if is_dir:
            return "📁 "
        
        # File icons based on extension
        ext = os.path.splitext(filename)[1].lower()
        
        icons = {
            # Images
            '.jpg': '🖼️ ', '.jpeg': '🖼️ ', '.png': '🖼️ ', '.gif': '🖼️ ',
            '.bmp': '🖼️ ', '.webp': '🖼️ ', '.heic': '🖼️ ',
            
            # Videos
            '.mp4': '🎬 ', '.mkv': '🎬 ', '.avi': '🎬 ', '.mov': '🎬 ',
            '.wmv': '🎬 ', '.flv': '🎬 ', '.webm': '🎬 ',
            
            # Audio
            '.mp3': '🎵 ', '.wav': '🎵 ', '.flac': '🎵 ', '.m4a': '🎵 ',
            '.aac': '🎵 ', '.ogg': '🎵 ',
            
            # Documents
            '.pdf': '📄 ', '.doc': '📝 ', '.docx': '📝 ', '.txt': '📄 ',
            '.rtf': '📄 ', '.odt': '📄 ',
            
            # Spreadsheets
            '.xls': '📊 ', '.xlsx': '📊 ', '.csv': '📊 ',
            
            # Presentations
            '.ppt': '📽️ ', '.pptx': '📽️ ',
            
            # Archives
            '.zip': '🗜️ ', '.rar': '🗜️ ', '.7z': '🗜️ ', '.tar': '🗜️ ',
            '.gz': '🗜️ ',
            
            # Code/Programming
            '.py': '🐍 ', '.java': '☕ ', '.js': '📜 ', '.html': '🌐 ',
            '.css': '🎨 ', '.json': '📋 ', '.xml': '📋 ',
            
            # Executables
            '.exe': '⚙️ ', '.apk': '📱 ', '.msi': '⚙️ ',
        }
        
        return icons.get(ext, '📄 ')
    
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Storage selector and path bar
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("Storage:"))
        
        self.storage_combo = QComboBox()
        for name, path in self.storage_locations.items():
            self.storage_combo.addItem(name, path)
        self.storage_combo.currentIndexChanged.connect(self._on_storage_changed)
        storage_layout.addWidget(self.storage_combo)
        
        storage_layout.addWidget(QLabel("Current Path:"))
        self.path_label = QLabel(self.current_path)
        self.path_label.setStyleSheet("font-family: monospace; padding: 5px; background: #f0f0f0; border-radius: 3px;")
        self.path_label.setWordWrap(True)
        storage_layout.addWidget(self.path_label, 1)
        
        self.up_btn = QPushButton("⬆️ Up")
        self.up_btn.clicked.connect(self._go_up)
        storage_layout.addWidget(self.up_btn)
        
        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.clicked.connect(self._go_home)
        storage_layout.addWidget(self.home_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._refresh_current_directory)
        storage_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(storage_layout)
        
        # Splitter for device and local
        splitter = QSplitter(Qt.Horizontal)
        
        # Device files panel
        device_widget = self._create_device_panel()
        splitter.addWidget(device_widget)
        
        # Local files panel
        local_widget = self._create_local_panel()
        splitter.addWidget(local_widget)
        
        splitter.setSizes([475, 475])
        layout.addWidget(splitter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.push_btn = QPushButton("📤 Push to Device →")
        self.push_btn.clicked.connect(self._push_file)
        self.push_btn.setEnabled(False)
        self.push_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.push_btn)
        
        self.pull_btn = QPushButton("← Pull to PC 📥")
        self.pull_btn.clicked.connect(self._pull_file)
        self.pull_btn.setEnabled(False)
        self.pull_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.pull_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_device_panel(self):
        """Create device files panel"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("📱 Android Device")
        header.setFont(QFont("Arial", 10, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 8px; background: #e3f2fd; border-radius: 5px;")
        layout.addWidget(header)
        
        # File tree
        self.device_tree = QTreeWidget()
        self.device_tree.setHeaderLabels(["Name", "Size", "Modified"])
        self.device_tree.setColumnWidth(0, 200)
        self.device_tree.setColumnWidth(1, 100)
        self.device_tree.setColumnWidth(2, 100)
        self.device_tree.itemDoubleClicked.connect(self._on_device_item_double_click)
        self.device_tree.itemClicked.connect(self._on_device_item_click)
        self.device_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_tree.customContextMenuRequested.connect(self._show_device_context_menu)
        layout.addWidget(self.device_tree)
        
        return container
    
    def _create_local_panel(self):
        """Create local files panel"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("💻 PC - Local Files")
        header.setFont(QFont("Arial", 10, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 8px; background: #f3e5f5; border-radius: 5px;")
        layout.addWidget(header)
        
        # File tree
        self.local_tree = QTreeWidget()
        self.local_tree.setHeaderLabels(["Name", "Size", "Modified"])
        self.local_tree.setColumnWidth(0, 300)
        self.local_tree.setColumnWidth(1, 100)
        self.local_tree.setColumnWidth(2, 150)
        self.local_tree.itemDoubleClicked.connect(self._on_local_item_double_click)
        self.local_tree.itemClicked.connect(self._on_local_item_click)
        self.local_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.local_tree.customContextMenuRequested.connect(self._show_local_context_menu)
        layout.addWidget(self.local_tree)
        
        # Path bar
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("📂 PC Path:"))
        self.local_path_label = QLabel(os.getcwd())
        self.local_path_label.setStyleSheet("font-family: monospace; padding: 5px; background: #f5f5f5; border-radius: 3px;")
        self.local_path_label.setWordWrap(True)
        path_layout.addWidget(self.local_path_label, 1)
        
        self.browse_btn = QPushButton("📂 Browse")
        self.browse_btn.clicked.connect(self._browse_local)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        return container
    
    def _on_storage_changed(self, index):
        """Handle storage selection change"""
        storage_path = self.storage_combo.currentData()
        if storage_path:
            self.current_path = storage_path
            self._refresh_current_directory()
    
    def _refresh_current_directory(self):
        """Refresh current device directory"""
        self.status_label.setText(f"📂 Loading {self.current_path}...")
        QApplication.processEvents()
        
        try:
            files = self.file_transfer.list_directory(self.current_path)
            self.device_tree.clear()
            
            # Add parent directory if not root
            if self.current_path not in ["/", "/storage", "/storage/emulated"]:
                parent_item = QTreeWidgetItem(["📁 ..", "", ""])
                parent_item.setData(0, Qt.UserRole, "parent")
                font = parent_item.font(0)
                font.setItalic(True)
                parent_item.setFont(0, font)
                parent_item.setForeground(0, QColor(100, 100, 100))
                self.device_tree.addTopLevelItem(parent_item)
            
            folder_count = 0
            file_count = 0
            
            # Add files and directories
            for file in files:
                name = file['name']
                is_dir = file['is_dir']
                
                # Skip current and parent directory entries
                if name in ['.', '..']:
                    continue
                
                # Get icon
                icon = self._get_file_icon(name, is_dir)
                display_name = f"{icon}{name}"
                
                # Format size
                if is_dir:
                    size_text = "📁"
                    folder_count += 1
                else:
                    size_text = self._format_size(file['size'])
                    file_count += 1
                
                modified = file['modified']
                
                item = QTreeWidgetItem([display_name, size_text, modified])
                item.setData(0, Qt.UserRole, file)
                
                # Set color based on type
                if is_dir:
                    item.setForeground(0, QColor(0, 100, 200))  # Blue for folders
                else:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        item.setForeground(0, QColor(200, 100, 0))  # Orange for images
                    elif ext in ['.mp4', '.mkv', '.avi', '.mov']:
                        item.setForeground(0, QColor(150, 0, 150))  # Purple for videos
                    elif ext in ['.mp3', '.wav', '.flac']:
                        item.setForeground(0, QColor(0, 150, 0))  # Green for audio
                    elif ext in ['.pdf', '.doc', '.docx', '.txt']:
                        item.setForeground(0, QColor(0, 100, 150))  # Blue for documents
                    elif ext == '.apk':
                        item.setForeground(0, QColor(200, 100, 0))  # Orange for APK
                
                self.device_tree.addTopLevelItem(item)
            
            self.path_label.setText(self.current_path)
            self._update_storage_combo()
            
            self.status_label.setText(f"✅ Loaded: {folder_count} folders, {file_count} files")
            self.logger.info(f"Loaded directory: {self.current_path} ({folder_count} folders, {file_count} files)")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.logger.error(f"Failed to load directory: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load directory:\n{str(e)}")
    
    def _update_storage_combo(self):
        """Update storage combo selection based on current path"""
        for i in range(self.storage_combo.count()):
            storage_path = self.storage_combo.itemData(i)
            if storage_path and self.current_path.startswith(storage_path):
                self.storage_combo.blockSignals(True)
                self.storage_combo.setCurrentIndex(i)
                self.storage_combo.blockSignals(False)
                break
    
    def _refresh_local_directory(self):
        """Refresh local directory"""
        local_path = self.local_path_label.text()
        
        try:
            self.local_tree.clear()
            
            if not os.path.exists(local_path):
                self.local_path_label.setText(os.getcwd())
                local_path = os.getcwd()
            
            files = os.listdir(local_path)
            
            # Add parent directory
            parent = os.path.dirname(local_path)
            if parent and parent != local_path:
                parent_item = QTreeWidgetItem(["📁 ..", "", ""])
                parent_item.setData(0, Qt.UserRole, "parent")
                font = parent_item.font(0)
                font.setItalic(True)
                parent_item.setFont(0, font)
                parent_item.setForeground(0, QColor(100, 100, 100))
                self.local_tree.addTopLevelItem(parent_item)
            
            folder_count = 0
            file_count = 0
            
            for name in sorted(files):
                full_path = os.path.join(local_path, name)
                try:
                    is_dir = os.path.isdir(full_path)
                    size = os.path.getsize(full_path) if not is_dir else 0
                    modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Get icon
                    icon = self._get_file_icon(name, is_dir)
                    display_name = f"{icon}{name}"
                    
                    if is_dir:
                        size_text = "📁"
                        folder_count += 1
                    else:
                        size_text = self._format_size(size)
                        file_count += 1
                    
                    item = QTreeWidgetItem([display_name, size_text, modified])
                    item.setData(0, Qt.UserRole, full_path)
                    
                    if is_dir:
                        item.setForeground(0, QColor(0, 100, 200))  # Blue for folders
                    
                    self.local_tree.addTopLevelItem(item)
                    
                except Exception as e:
                    continue
            
            self.status_label.setText(f"✅ PC: {folder_count} folders, {file_count} files")
            
        except Exception as e:
            self.logger.error(f"Failed to load local directory: {e}")
            self.status_label.setText("❌ Error loading PC directory")
    
    def _on_device_item_double_click(self, item, column):
        """Handle device item double click"""
        data = item.data(0, Qt.UserRole)
        
        if data == "parent":
            self._go_up()
        elif isinstance(data, dict) and data.get('is_dir'):
            new_path = os.path.join(self.current_path, data['name'])
            new_path = new_path.replace('\\', '/')
            self.current_path = new_path
            self._refresh_current_directory()
    
    def _on_local_item_double_click(self, item, column):
        """Handle local item double click"""
        data = item.data(0, Qt.UserRole)
        
        if data == "parent":
            current = self.local_path_label.text()
            parent = os.path.dirname(current)
            if parent and parent != current:
                self.local_path_label.setText(parent)
                self._refresh_local_directory()
        elif data and os.path.isdir(data):
            self.local_path_label.setText(data)
            self._refresh_local_directory()
    
    def _on_device_item_click(self, item, column):
        """Handle device item selection"""
        data = item.data(0, Qt.UserRole)
        if data and data != "parent" and isinstance(data, dict) and not data.get('is_dir'):
            self.pull_btn.setEnabled(True)
        else:
            self.pull_btn.setEnabled(False)
    
    def _on_local_item_click(self, item, column):
        """Handle local item selection"""
        data = item.data(0, Qt.UserRole)
        if data and data != "parent" and os.path.isfile(data):
            self.push_btn.setEnabled(True)
        else:
            self.push_btn.setEnabled(False)
    
    def _show_device_context_menu(self, position):
        """Show context menu for device files"""
        item = self.device_tree.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if not data or data == "parent" or not isinstance(data, dict):
            return
        
        menu = QMenu()
        delete_action = QAction("🗑 Delete", self)
        delete_action.triggered.connect(lambda: self._delete_device_file(data))
        menu.addAction(delete_action)
        
        if not data.get('is_dir'):
            info_action = QAction("ℹ Info", self)
            info_action.triggered.connect(lambda: self._show_file_info(data))
            menu.addAction(info_action)
        
        menu.exec_(self.device_tree.viewport().mapToGlobal(position))
    
    def _show_local_context_menu(self, position):
        """Show context menu for local files"""
        item = self.local_tree.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if not data or data == "parent" or os.path.isdir(data):
            return
        
        menu = QMenu()
        delete_action = QAction("🗑 Delete", self)
        delete_action.triggered.connect(lambda: self._delete_local_file(data))
        menu.addAction(delete_action)
        
        menu.exec_(self.local_tree.viewport().mapToGlobal(position))
    
    def _go_up(self):
        """Go to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self.current_path = parent
            self._refresh_current_directory()
    
    def _go_home(self):
        """Go to home directory (internal storage)"""
        self.current_path = "/storage/emulated/0"
        for i in range(self.storage_combo.count()):
            if self.storage_combo.itemData(i) == self.current_path:
                self.storage_combo.setCurrentIndex(i)
                break
        self._refresh_current_directory()
    
    def _browse_local(self):
        """Browse local directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.local_path_label.text())
        if directory:
            self.local_path_label.setText(directory)
            self._refresh_local_directory()
    
    def _push_file(self):
        """Push file to device"""
        selected = self.local_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a file to push.")
            return
        
        item = selected[0]
        local_path = item.data(0, Qt.UserRole)
        
        if not local_path or local_path == "parent":
            return
        
        if os.path.isdir(local_path):
            QMessageBox.warning(self, "Directory", "Please select a file, not a directory.")
            return
        
        remote_path = os.path.join(self.current_path, os.path.basename(local_path))
        remote_path = remote_path.replace('\\', '/')
        
        reply = QMessageBox.question(self, "Confirm Push", 
                                     f"Push file to device?\n\n"
                                     f"From: {local_path}\n"
                                     f"To: {remote_path}",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self._start_transfer(self.file_transfer.push_file, local_path, remote_path, "Push")
    
    def _pull_file(self):
        """Pull file from device"""
        selected = self.device_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a file to pull.")
            return
        
        item = selected[0]
        file_data = item.data(0, Qt.UserRole)
        
        if not file_data or file_data == "parent":
            return
        
        if file_data.get('is_dir'):
            QMessageBox.warning(self, "Directory", "Please select a file, not a directory.")
            return
        
        remote_path = os.path.join(self.current_path, file_data['name'])
        remote_path = remote_path.replace('\\', '/')
        local_path = os.path.join(self.local_path_label.text(), file_data['name'])
        
        reply = QMessageBox.question(self, "Confirm Pull", 
                                     f"Pull file from device?\n\n"
                                     f"From: {remote_path}\n"
                                     f"To: {local_path}",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self._start_transfer(self.file_transfer.pull_file, remote_path, local_path, "Pull")
    
    def _delete_device_file(self, file_data):
        """Delete file from device"""
        remote_path = os.path.join(self.current_path, file_data['name'])
        remote_path = remote_path.replace('\\', '/')
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Delete file from device?\n\n{remote_path}\n\nThis action cannot be undone!",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.status_label.setText("Deleting...")
            QApplication.processEvents()
            
            if self.file_transfer.delete_file(remote_path):
                self.status_label.setText("Deleted successfully")
                self._refresh_current_directory()
            else:
                self.status_label.setText("Delete failed")
                QMessageBox.warning(self, "Error", "Failed to delete file.")
    
    def _delete_local_file(self, local_path):
        """Delete local file"""
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Delete local file?\n\n{local_path}\n\nThis action cannot be undone!",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(local_path):
                    os.remove(local_path)
                    self.status_label.setText("Deleted successfully")
                    self._refresh_local_directory()
                else:
                    QMessageBox.warning(self, "Error", "Cannot delete directory.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")
    
    def _show_file_info(self, file_data):
        """Show file information"""
        remote_path = os.path.join(self.current_path, file_data['name'])
        remote_path = remote_path.replace('\\', '/')
        info = self.file_transfer.get_file_info(remote_path)
        
        if info:
            icon = self._get_file_icon(file_data['name'], file_data['is_dir'])
            info_text = f"{icon} File Information:\n\n"
            info_text += f"Name: {file_data['name']}\n"
            info_text += f"Path: {remote_path}\n"
            info_text += f"Size: {self._format_size(info['size'])}\n"
            info_text += f"Modified: {info['modified']}\n"
            info_text += f"Type: {'📁 Directory' if file_data['is_dir'] else '📄 File'}\n"
            
            QMessageBox.information(self, "File Info", info_text)
        else:
            QMessageBox.warning(self, "Error", "Failed to get file information.")
    
    def _start_transfer(self, transfer_func, source, dest, operation):
        """Start file transfer in background thread"""
        self.transfer_thread = TransferThread(transfer_func, source, dest)
        self.transfer_thread.progress.connect(self._update_progress)
        self.transfer_thread.finished.connect(lambda success, error: self._transfer_finished(success, error, operation))
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"{operation}ing...")
        
        self.push_btn.setEnabled(False)
        self.pull_btn.setEnabled(False)
        
        self.transfer_thread.start()
    
    def _update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def _transfer_finished(self, success, error, operation):
        """Handle transfer completion"""
        self.progress_bar.setVisible(False)
        self.push_btn.setEnabled(True)
        self.pull_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✅ {operation} completed successfully!")
            self.logger.info(f"{operation} completed successfully")
            self._refresh_current_directory()
            self._refresh_local_directory()
            QMessageBox.information(self, "Success", f"{operation} completed successfully!")
        else:
            self.status_label.setText(f"❌ {operation} failed: {error}")
            self.logger.error(f"{operation} failed: {error}")
            QMessageBox.warning(self, "Error", f"{operation} failed:\n{error}")
    
    def _format_size(self, size):
        """Format file size with units"""
        if size == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def showEvent(self, event):
        """Handle dialog show event"""
        super().showEvent(event)
        self._refresh_local_directory()
        self._refresh_current_directory()