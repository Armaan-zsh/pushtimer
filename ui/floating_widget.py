from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QTimer, QDateTime, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QMouseEvent, QPen, QBrush

class FloatingWidget(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        
        # Window attributes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(140, 70)
        
        # Init UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.label = QLabel("35:00")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-weight: bold; font-family: monospace; font-size: 20px;")
        layout.addWidget(self.label)
        
        self.sub_label = QLabel("Pushup Timer")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("color: #00ff88; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.sub_label)
        
        # Timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
        
        # Dragging logic
        self.old_pos = None
        
        # Initial position (bottom right)
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.width() - 160, screen_geo.height() - 100)
        
    def update_time(self, text, progress_percent=0):
        self.label.setText(text)
        # We could also repaint a progress ring here if we wanted
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.setBrush(QBrush(QColor(15, 17, 21, 230)))
        painter.setPen(QPen(QColor(0, 255, 136), 2))
        painter.drawRoundedRect(2, 2, self.width()-4, self.height()-4, 15, 15)
        
    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
