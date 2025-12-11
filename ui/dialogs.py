from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QMessageBox, QFormLayout, QComboBox, QCheckBox,
    QLineEdit, QDialogButtonBox, QWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QColor, QPen, QBrush

class NotificationDialog(QWidget):
    """Non-modal notification with 10-second grace period"""
    action_taken = Signal(int)  # Signal: -2=grace cancel, -1=snooze, 0=skip, >0=pushup count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(340, 220)
        
        self.grace_period_active = True
        self.grace_seconds_left = 10
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        # Main widget with rounded corners
        main_widget = QWidget(self)
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: white;
                border: 3px solid #ff4444;
                border-radius: 12px;
            }
        """)
        main_widget.setGeometry(0, 0, 340, 220)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with countdown
        self.title_label = QLabel("💪 Pushup Time! (Closing in 10s)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #ff4444; margin-bottom: 5px;")
        layout.addWidget(self.title_label)
        
        # Message
        message = QLabel("35 minutes are up!\nHow many pushups did you do?")
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("color: #555; font-size: 14px;")
        layout.addWidget(message)
        
        # Input
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
        """)
        input_layout.addWidget(self.count_spinbox)
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # Warning label for grace period
        self.warning_label = QLabel("⚠️ Close in 10s to cancel reminder!")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setStyleSheet("color: #ff4444; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.warning_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Snooze button
        snooze_btn = QPushButton("Snooze 5 min")
        snooze_btn.setFixedHeight(40)
        snooze_btn.clicked.connect(lambda: self.take_action(-1))
        snooze_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        # Skip button
        skip_btn = QPushButton("Skip (0)")
        skip_btn.setFixedHeight(40)
        skip_btn.clicked.connect(lambda: self.take_action(0))
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
        """)
        
        # Log button
        log_btn = QPushButton("Log Pushups")
        log_btn.setFixedHeight(40)
        log_btn.clicked.connect(lambda: self.take_action(self.count_spinbox.value()))
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
        """)
        
        button_layout.addWidget(snooze_btn)
        button_layout.addWidget(skip_btn)
        button_layout.addWidget(log_btn)
        layout.addLayout(button_layout)
        
        # Auto-close timer (2 minutes)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(lambda: self.take_action(0))
        
    def setup_timers(self):
        # Grace period timer (10 seconds)
        self.grace_timer = QTimer()
        self.grace_timer.timeout.connect(self.update_grace_period)
        self.grace_timer.start(1000)  # Update every second
        
        # Start auto-close timer (2 minutes)
        self.auto_close_timer.start(120000)
        
    def update_grace_period(self):
        self.grace_seconds_left -= 1
        
        # Update title
        self.title_label.setText(f"💪 Pushup Time! (Closing in {self.grace_seconds_left}s)")
        
        if self.grace_seconds_left <= 0:
            # Grace period ended
            self.grace_period_active = False
            self.grace_timer.stop()
            
            # Change border to green
            main_widget = self.findChild(QWidget, "mainWidget")
            if main_widget:
                main_widget.setStyleSheet("""
                    QWidget#mainWidget {
                        background-color: white;
                        border: 3px solid #4CAF50;
                        border-radius: 12px;
                    }
                """)
            
            # Update title and warning
            self.title_label.setText("💪 Pushup Time!")
            self.title_label.setStyleSheet("color: #4CAF50; margin-bottom: 5px;")
            self.warning_label.setText("✅ Timer will reset if closed now")
            
    def take_action(self, action_type):
        """Handle any button click"""
        # Stop all timers
        self.grace_timer.stop()
        self.auto_close_timer.stop()
        
        # Emit the action
        self.action_taken.emit(action_type)
        self.close()
        
    def showEvent(self, event):
        """When dialog is shown, position it"""
        super().showEvent(event)
        
        # Position at bottom right
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 50
        self.move(x, y)
        
    def closeEvent(self, event):
        """Handle window close (X button)"""
        # If user clicks X during grace period, cancel reminder
        if self.grace_period_active:
            # Grace period close - cancel everything
            self.grace_timer.stop()
            self.auto_close_timer.stop()
            # -2 means grace period cancel (no action)
            self.action_taken.emit(-2)
        else:
            # Normal close - treat as skip
            self.action_taken.emit(0)
        
        event.accept()
        
    def paintEvent(self, event):
        """Draw shadow effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(4, 4, self.width(), self.height(), 12, 12)


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
