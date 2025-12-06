# Add these new imports at the top of ui/dialogs.py
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox

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

# Keep the existing SettingsDialog class
