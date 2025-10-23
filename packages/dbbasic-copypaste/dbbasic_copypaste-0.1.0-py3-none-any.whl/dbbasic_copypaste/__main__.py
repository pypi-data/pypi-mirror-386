#!/usr/bin/env python3
"""
dbbasic-copypaste: Clipboard manager with history
"""

import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLabel, QPushButton,
    QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QClipboard
from io import BytesIO
from PIL import Image


class ClipboardItem:
    """Represents a single clipboard history item"""
    def __init__(self, content, content_type, timestamp=None):
        self.content = content
        self.content_type = content_type  # 'text' or 'image'
        self.timestamp = timestamp or datetime.now()

    def get_preview(self, max_length=50):
        """Get a short preview of the content"""
        if self.content_type == 'text':
            text = self.content.replace('\n', ' ').strip()
            if len(text) > max_length:
                return text[:max_length] + '...'
            return text
        elif self.content_type == 'image':
            return '[Image]'
        return '[Unknown]'

    def get_display_text(self):
        """Get the full display text for the list"""
        time_str = self.timestamp.strftime('%H:%M:%S')
        preview = self.get_preview()
        return f"{time_str} - {preview}"


class ClipboardManager(QMainWindow):
    """Main clipboard manager window"""

    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.history = []
        self.max_history = 100
        self.monitoring = True

        self.init_ui()
        self.start_monitoring()

        # Capture initial clipboard content
        self.check_clipboard()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('dbbasic-copypaste - Clipboard Manager')
        self.setGeometry(100, 100, 900, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create top bar with controls
        top_bar = QHBoxLayout()

        self.status_label = QLabel('Monitoring clipboard...')
        top_bar.addWidget(self.status_label)

        top_bar.addStretch()

        self.pause_button = QPushButton('Pause Monitoring')
        self.pause_button.clicked.connect(self.toggle_monitoring)
        top_bar.addWidget(self.pause_button)

        self.clear_button = QPushButton('Clear History')
        self.clear_button.clicked.connect(self.clear_history)
        top_bar.addWidget(self.clear_button)

        main_layout.addLayout(top_bar)

        # Create splitter for history list and preview
        splitter = QSplitter(Qt.Horizontal)

        # Left side: History list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel('Clipboard History:')
        left_layout.addWidget(list_label)

        self.history_list = QListWidget()
        self.history_list.currentItemChanged.connect(self.on_history_selection_changed)
        left_layout.addWidget(self.history_list)

        splitter.addWidget(left_widget)

        # Right side: Preview and actions
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel('Preview:')
        right_layout.addWidget(preview_label)

        # Text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        right_layout.addWidget(self.text_preview)

        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setMinimumSize(200, 200)
        self.image_preview.hide()
        right_layout.addWidget(self.image_preview)

        # Action buttons
        button_layout = QHBoxLayout()

        self.restore_button = QPushButton('Restore to Clipboard')
        self.restore_button.clicked.connect(self.restore_to_clipboard)
        self.restore_button.setEnabled(False)
        button_layout.addWidget(self.restore_button)

        self.delete_button = QPushButton('Delete Item')
        self.delete_button.clicked.connect(self.delete_item)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)

        right_layout.addLayout(button_layout)

        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage('Ready')

    def start_monitoring(self):
        """Start monitoring clipboard changes"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(500)  # Check every 500ms

    def toggle_monitoring(self):
        """Toggle clipboard monitoring on/off"""
        self.monitoring = not self.monitoring
        if self.monitoring:
            self.pause_button.setText('Pause Monitoring')
            self.status_label.setText('Monitoring clipboard...')
            self.statusBar().showMessage('Monitoring resumed')
        else:
            self.pause_button.setText('Resume Monitoring')
            self.status_label.setText('Monitoring paused')
            self.statusBar().showMessage('Monitoring paused')

    def check_clipboard(self):
        """Check for clipboard changes and add to history"""
        if not self.monitoring:
            return

        mime_data = self.clipboard.mimeData()

        if mime_data.hasImage():
            image = self.clipboard.image()
            if not image.isNull():
                # Convert QImage to bytes for storage
                byte_array = BytesIO()
                # Convert QImage to PIL Image
                width = image.width()
                height = image.height()
                ptr = image.bits()
                ptr.setsize(height * width * 4)
                pil_image = Image.frombytes('RGBA', (width, height), ptr.asstring())
                pil_image.save(byte_array, format='PNG')
                image_bytes = byte_array.getvalue()

                # Check if this image is already the most recent
                if self.history and self.history[0].content_type == 'image':
                    if self.history[0].content == image_bytes:
                        return

                self.add_to_history(image_bytes, 'image')

        elif mime_data.hasText():
            text = self.clipboard.text()
            if text:
                # Check if this text is already the most recent
                if self.history and self.history[0].content_type == 'text':
                    if self.history[0].content == text:
                        return

                self.add_to_history(text, 'text')

    def add_to_history(self, content, content_type):
        """Add a new item to the clipboard history"""
        item = ClipboardItem(content, content_type)
        self.history.insert(0, item)

        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]

        self.update_history_list()
        self.statusBar().showMessage(f'Added {content_type} to history', 2000)

    def update_history_list(self):
        """Update the history list widget"""
        self.history_list.clear()
        for item in self.history:
            list_item = QListWidgetItem(item.get_display_text())
            list_item.setData(Qt.UserRole, item)
            self.history_list.addItem(list_item)

        # Automatically select the first (most recent) item
        if self.history_list.count() > 0:
            self.history_list.setCurrentRow(0)

    def on_history_selection_changed(self, current, previous):
        """Handle history selection changes"""
        if current is None:
            self.text_preview.clear()
            self.image_preview.clear()
            self.image_preview.hide()
            self.text_preview.show()
            self.restore_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return

        item = current.data(Qt.UserRole)

        if item.content_type == 'text':
            self.text_preview.setPlainText(item.content)
            self.text_preview.show()
            self.image_preview.hide()
        elif item.content_type == 'image':
            # Load image from bytes
            byte_array = BytesIO(item.content)
            pil_image = Image.open(byte_array)

            # Convert PIL Image to QPixmap
            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(img_byte_arr.getvalue())

            # Scale to fit preview area while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_preview.width() - 20,
                self.image_preview.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_preview.setPixmap(scaled_pixmap)
            self.text_preview.hide()
            self.image_preview.show()

        self.restore_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def restore_to_clipboard(self):
        """Restore the selected item to clipboard"""
        current = self.history_list.currentItem()
        if current is None:
            return

        item = current.data(Qt.UserRole)

        # Temporarily pause monitoring to avoid adding the restored item again
        was_monitoring = self.monitoring
        self.monitoring = False

        if item.content_type == 'text':
            self.clipboard.setText(item.content)
            self.statusBar().showMessage('Text restored to clipboard', 2000)
        elif item.content_type == 'image':
            # Convert bytes back to QImage
            byte_array = BytesIO(item.content)
            pil_image = Image.open(byte_array)

            # Convert PIL Image to QImage
            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            qimage = QImage()
            qimage.loadFromData(img_byte_arr.getvalue())

            self.clipboard.setImage(qimage)
            self.statusBar().showMessage('Image restored to clipboard', 2000)

        # Resume monitoring after a short delay
        QTimer.singleShot(1000, lambda: setattr(self, 'monitoring', was_monitoring))

    def delete_item(self):
        """Delete the selected history item"""
        current = self.history_list.currentItem()
        if current is None:
            return

        row = self.history_list.row(current)
        self.history.pop(row)
        self.history_list.takeItem(row)
        self.statusBar().showMessage('Item deleted', 2000)

    def clear_history(self):
        """Clear all clipboard history"""
        reply = QMessageBox.question(
            self,
            'Clear History',
            'Are you sure you want to clear all clipboard history?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.history.clear()
            self.history_list.clear()
            self.text_preview.clear()
            self.image_preview.clear()
            self.statusBar().showMessage('History cleared', 2000)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('dbbasic-copypaste')

    window = ClipboardManager()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
