from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QBrush

class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.value = 0
        self.maximum = 100
        
    def set_value(self, value, maximum=100):
        self.value = value
        self.maximum = maximum
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        width = self.width()
        height = self.height()
        adjust = 20
        rect = QRectF(adjust, adjust, width-adjust*2, height-adjust*2)
        
        # Background Track
        painter.setPen(QPen(QColor(30, 30, 30), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawArc(rect, 0, 360 * 16)
        
        # Progress Arc
        if self.maximum > 0:
            angle = min(360, (self.value / self.maximum) * 360)
            
            # Gradient
            gradient = QConicalGradient(width/2, height/2, 90)
            gradient.setColorAt(0, QColor("#00ff88"))
            gradient.setColorAt(1, QColor("#00cc6a"))
            
            pen = QPen(QBrush(gradient), 10)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Draw arc (start angle 90 degrees = 12 o'clock, negative span for clockwise)
            painter.drawArc(rect, 90 * 16, -angle * 16)
        
        # Text
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 36)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(self.value))
        
        # Subtext
        font.setPointSize(12)
        painter.setFont(font)
        painter.setPen(QColor("#8b9bb4"))
        painter.drawText(rect.adjusted(0, 40, 0, 0), Qt.AlignCenter, f"of {self.maximum}")
