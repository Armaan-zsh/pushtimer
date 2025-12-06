from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QMessageBox, QFormLayout, QComboBox, QCheckBox,
    QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class ReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pushup Reminder!")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Message
        message = QLabel("Did you do your pushups?")
        font = message.font()
        font.setPointSize(14)
        message.setFont(font)
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        
        # Input
        input_layout = QFormLayout()
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(0, 999)
        self.count_spinbox.setValue(10)
        self.count_spinbox.setMinimumWidth(100)
        input_layout.addRow("How many?", self.count_spinbox)
        layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.no_btn = QPushButton("No (log 0)")
        self.no_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.no_btn)
        
        self.yes_btn = QPushButton("Yes, log pushups")
        self.yes_btn.clicked.connect(self.accept)
        self.yes_btn.setDefault(True)
        button_layout.addWidget(self.yes_btn)
        
        layout.addLayout(button_layout)
        
    def get_count(self):
        return self.count_spinbox.value()

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
