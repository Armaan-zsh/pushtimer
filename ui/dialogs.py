from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QMessageBox, QFormLayout, QComboBox, QCheckBox,
    QLineEdit, QDialogButtonBox, QWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QColor, QPen, QBrush

class NotificationDialog(QWidget):
    """Non-modal notification that doesn't block other windows"""
    closed = Signal(int)  # Signal with pushup count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 180)
        
        self.count = 0
        self.setup_ui()
        
    def setup_ui(self):
        # Main widget with rounded corners
        self.main_widget = QWidget(self)
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 10px;
                border: 2px solid #4CAF50;
            }
        """)
        self.main_widget.setGeometry(0, 0, 300, 180)
        
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("💪 Pushup Time!")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        message = QLabel("35 minutes are up!\nHow many pushups did you do?")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        
        # Input
        input_layout = QHBoxLayout()
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(0, 999)
        self.count_spinbox.setValue(10)
        self.count_spinbox.setMinimumWidth(80)
        input_layout.addStretch()
        input_layout.addWidget(self.count_spinbox)
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        skip_btn = QPushButton("Skip")
        skip_btn.clicked.connect(self.skip)
        skip_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                background-color: #f44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        log_btn = QPushButton("Log Pushups")
        log_btn.clicked.connect(self.log)
        log_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        
        button_layout.addWidget(skip_btn)
        button_layout.addWidget(log_btn)
        layout.addLayout(button_layout)
        
        # Auto-close timer (2 minutes)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.auto_close)
        
    def showEvent(self, event):
        """When dialog is shown, start the auto-close timer"""
        self.timer.start(120000)  # 2 minutes
        super().showEvent(event)
        
    def skip(self):
        """User clicked Skip"""
        self.timer.stop()
        self.closed.emit(0)
        self.close()
        
    def log(self):
        """User clicked Log Pushups"""
        self.timer.stop()
        self.closed.emit(self.count_spinbox.value())
        self.close()
        
    def auto_close(self):
        """Auto-close after 2 minutes"""
        self.closed.emit(0)
        self.close()
        
    def paintEvent(self, event):
        """Draw drop shadow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(5, 5, self.width() - 10, self.height() - 10, 10, 10)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("Settings")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Timer minutes
        self.timer_spinbox = QSpinBox()
        self.timer_spinbox.setRange(1, 120)
        self.timer_spinbox.setValue(self.config.get("timer_minutes", 35))
        layout.addRow("Timer minutes:", self.timer_spinbox)
        
        # Reminder seconds
        self.reminder_spinbox = QSpinBox()
        self.reminder_spinbox.setRange(10, 300)
        self.reminder_spinbox.setValue(self.config.get("reminder_seconds", 60))
        layout.addRow("Reminder display seconds:", self.reminder_spinbox)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.config.get("theme", "light"))
        layout.addRow("Theme:", self.theme_combo)
        
        # Aggregate mode
        self.aggregate_combo = QComboBox()
        self.aggregate_combo.addItems(["add", "replace"])
        self.aggregate_combo.setCurrentText(self.config.get("aggregate_mode", "add"))
        layout.addRow("Aggregate mode:", self.aggregate_combo)
        
        # Checkboxes
        self.autostart_check = QCheckBox()
        self.autostart_check.setChecked(self.config.get("autostart", True))
        layout.addRow("Start automatically on login:", self.autostart_check)
        
        self.start_minimized_check = QCheckBox()
        self.start_minimized_check.setChecked(self.config.get("start_minimized", True))
        layout.addRow("Start minimized:", self.start_minimized_check)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_config(self):
        return {
            "timer_minutes": self.timer_spinbox.value(),
            "reminder_seconds": self.reminder_spinbox.value(),
            "theme": self.theme_combo.currentText(),
            "aggregate_mode": self.aggregate_combo.currentText(),
            "autostart": self.autostart_check.isChecked(),
            "start_minimized": self.start_minimized_check.isChecked()
        }
