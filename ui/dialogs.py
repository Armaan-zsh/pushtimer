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
        # Use these flags for proper behavior
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 200)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main widget with proper styling
        main_widget = QWidget(self)
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: white;
                border: 3px solid #4CAF50;
                border-radius: 12px;
            }
        """)
        main_widget.setGeometry(0, 0, 320, 200)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title - FIXED EMOJI AND TEXT
        title = QLabel("💪 Pushup Time!")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2E7D32; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Message - FIXED TYPO: "Draw many machines" → "How many pushups"
        message = QLabel("35 minutes are up!\nHow many pushups did you do?")
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 14px;
                padding: 5px;
            }
        """)
        layout.addWidget(message)
        
        # Input section
        input_layout = QHBoxLayout()
        input_layout.addStretch()
        
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(0, 999)
        self.count_spinbox.setValue(10)
        self.count_spinbox.setMinimumWidth(120)
        self.count_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 16px;
                font-weight: bold;
                padding: 8px 12px;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                background-color: white;
                color: #333;
            }
            QSpinBox:focus {
                border-color: #2196F3;
            }
            QSpinBox::up-button {
                width: 20px;
                border-left: 1px solid #ccc;
            }
            QSpinBox::down-button {
                width: 20px;
                border-left: 1px solid #ccc;
            }
        """)
        input_layout.addWidget(self.count_spinbox)
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # Buttons - FIXED: "SETTLE" → "Skip", "LIVE WHEN LIVE" → "Log Pushups"
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        skip_btn = QPushButton("Skip")
        skip_btn.setFixedHeight(40)
        skip_btn.clicked.connect(self.skip)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        
        log_btn = QPushButton("Log Pushups")
        log_btn.setFixedHeight(40)
        log_btn.clicked.connect(self.log)
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
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
        """When dialog is shown, start the auto-close timer and position it"""
        self.timer.start(120000)  # 2 minutes
        
        # Position at bottom right
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 50
        self.move(x, y)
        
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
        """Draw shadow effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(4, 4, self.width(), self.height(), 12, 12)
        
        # Main widget is already drawn by Qt, we just need the shadow

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
