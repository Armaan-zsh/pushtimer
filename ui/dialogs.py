from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QMessageBox, QFormLayout, QComboBox, QCheckBox,
    QLineEdit, QDialogButtonBox, QWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QColor, QPen, QBrush

class NotificationDialog(QWidget):
    """Non-modal notification with 10-second grace period - Modern Dark Theme"""
    action_taken = Signal(int)  # Signal: -2=grace cancel, -1=snooze, 0=skip, >0=pushup count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 280)
        
        self.grace_period_active = True
        self.grace_seconds_left = 10
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        main_widget = QWidget(self)
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1d24, stop:1 #0f1115);
                border: 2px solid #00ff88;
                border-radius: 20px;
            }
        """)
        main_widget.setGeometry(0, 0, 380, 280)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(18)
        
        # Title with countdown
        self.title_label = QLabel("💪 PUSHUP TIME!")
        title_font = QFont("Segoe UI", 18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #00ff88; letter-spacing: 2px;")
        layout.addWidget(self.title_label)
        
        # Countdown badge
        self.countdown_label = QLabel("⏱️ Auto-close in 10s")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            color: #8b9bb4;
            font-size: 12px;
            padding: 4px 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        """)
        layout.addWidget(self.countdown_label)
        
        # Message
        message = QLabel("35 minutes are up!\nHow many pushups did you do?")
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("color: #ffffff; font-size: 14px; line-height: 1.4;")
        layout.addWidget(message)
        
        # Input with + / - buttons
        input_layout = QHBoxLayout()
        input_layout.setSpacing(0)
        input_layout.addStretch()
        
        minus_btn = QPushButton("−")
        minus_btn.setFixedSize(50, 50)
        minus_btn.clicked.connect(lambda: self.count_spinbox.setValue(self.count_spinbox.value() - 1))
        minus_btn.setStyleSheet("""
            QPushButton {
                background: #1a1d24;
                color: #00ff88;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid #00ff88;
                border-radius: 12px;
            }
            QPushButton:hover { background: #00ff88; color: #000; }
            QPushButton:pressed { background: #00cc6a; }
        """)
        input_layout.addWidget(minus_btn)
        
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(0, 999)
        self.count_spinbox.setValue(10)
        self.count_spinbox.setFixedSize(100, 50)
        self.count_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.count_spinbox.setAlignment(Qt.AlignCenter)
        self.count_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 28px;
                font-weight: bold;
                padding: 8px;
                border: none;
                background: transparent;
                color: #ffffff;
            }
        """)
        input_layout.addWidget(self.count_spinbox)
        
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(50, 50)
        plus_btn.clicked.connect(lambda: self.count_spinbox.setValue(self.count_spinbox.value() + 1))
        plus_btn.setStyleSheet("""
            QPushButton {
                background: #1a1d24;
                color: #00ff88;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid #00ff88;
                border-radius: 12px;
            }
            QPushButton:hover { background: #00ff88; color: #000; }
            QPushButton:pressed { background: #00cc6a; }
        """)
        input_layout.addWidget(plus_btn)
        
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # Buttons row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        snooze_btn = QPushButton("⏸ Snooze")
        snooze_btn.setFixedHeight(45)
        snooze_btn.clicked.connect(lambda: self.take_action(-1))
        snooze_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 152, 0, 0.2);
                color: #FF9800;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #FF9800;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #FF9800;
                color: #000;
            }
        """)
        
        skip_btn = QPushButton("✕ Skip")
        skip_btn.setFixedHeight(45)
        skip_btn.clicked.connect(lambda: self.take_action(0))
        skip_btn.setStyleSheet("""
            QPushButton {
                background: rgba(244, 67, 54, 0.2);
                color: #f44336;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #f44336;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #f44336;
                color: #fff;
            }
        """)
        
        log_btn = QPushButton("✓ LOG")
        log_btn.setFixedHeight(45)
        log_btn.clicked.connect(lambda: self.take_action(self.count_spinbox.value()))
        log_btn.setStyleSheet("""
            QPushButton {
                background: #00ff88;
                color: #000;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background: #00cc6a;
            }
        """)
        
        button_layout.addWidget(snooze_btn)
        button_layout.addWidget(skip_btn)
        button_layout.addWidget(log_btn, stretch=1)
        layout.addLayout(button_layout)
        
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(lambda: self.take_action(0))
        
    def setup_timers(self):
        self.grace_timer = QTimer()
        self.grace_timer.timeout.connect(self.update_grace_period)
        self.grace_timer.start(1000)
        
        self.auto_close_timer.start(120000)
        
    def update_grace_period(self):
        self.grace_seconds_left -= 1
        self.countdown_label.setText(f"⏱️ Auto-close in {self.grace_seconds_left}s")
        
        if self.grace_seconds_left <= 0:
            self.grace_period_active = False
            self.grace_timer.stop()
            
            main_widget = self.findChild(QWidget, "mainWidget")
            if main_widget:
                main_widget.setStyleSheet("""
                    QWidget#mainWidget {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #1a1d24, stop:1 #0f1115);
                        border: 2px solid #7000ff;
                        border-radius: 20px;
                    }
                """)
            
            self.title_label.setStyleSheet("color: #7000ff; letter-spacing: 2px;")
            self.countdown_label.setText("✅ Ready to log!")
            self.countdown_label.setStyleSheet("""
                color: #00ff88;
                font-size: 12px;
                padding: 4px 12px;
                background: rgba(0,255,136,0.1);
                border-radius: 10px;
            """)
            
    def take_action(self, action_type):
        self.grace_timer.stop()
        self.auto_close_timer.stop()
        self.action_taken.emit(action_type)
        self.close()
        
    def showEvent(self, event):
        super().showEvent(event)
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 50
        self.move(x, y)
        
    def closeEvent(self, event):
        if self.grace_period_active:
            self.grace_timer.stop()
            self.auto_close_timer.stop()
            self.action_taken.emit(-2)
        else:
            self.action_taken.emit(0)
        
        event.accept()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Drop shadow effect
        painter.setBrush(QBrush(QColor(0, 255, 136, 30)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(6, 6, self.width() - 6, self.height() - 6, 20, 20)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("Settings")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.timer_spinbox = QSpinBox()
        self.timer_spinbox.setRange(1, 120)
        self.timer_spinbox.setValue(self.config.get("timer_minutes", 35))
        layout.addRow("Timer minutes:", self.timer_spinbox)
        
        self.reminder_spinbox = QSpinBox()
        self.reminder_spinbox.setRange(10, 300)
        self.reminder_spinbox.setValue(self.config.get("reminder_seconds", 60))
        layout.addRow("Reminder display seconds:", self.reminder_spinbox)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.config.get("theme", "light"))
        layout.addRow("Theme:", self.theme_combo)
        
        self.aggregate_combo = QComboBox()
        self.aggregate_combo.addItems(["add", "replace"])
        self.aggregate_combo.setCurrentText(self.config.get("aggregate_mode", "add"))
        layout.addRow("Aggregate mode:", self.aggregate_combo)
        
        self.enable_sync_check = QCheckBox()
        self.enable_sync_check.setChecked(self.config.get("enable_phone_sync", True))
        layout.addRow("Enable phone sync:", self.enable_sync_check)
        
        self.autostart_check = QCheckBox()
        self.autostart_check.setChecked(self.config.get("autostart", True))
        layout.addRow("Start automatically on login:", self.autostart_check)
        
        self.start_minimized_check = QCheckBox()
        self.start_minimized_check.setChecked(self.config.get("start_minimized", True))
        layout.addRow("Start minimized:", self.start_minimized_check)
        
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
            "enable_phone_sync": self.enable_sync_check.isChecked(),
            "autostart": self.autostart_check.isChecked(),
            "start_minimized": self.start_minimized_check.isChecked()
        }
