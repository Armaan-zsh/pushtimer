from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QToolTip, QVBoxLayout
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent
import datetime
from math import ceil

class HeatmapWidget(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.data = tracker.get_all_data()
        self.cell_size = 12
        self.cell_margin = 2
        self.week_width = 7 * (self.cell_size + self.cell_margin)
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate weeks to show (52 weeks)
        today = QDate.currentDate()
        start_date = today.addDays(-52 * 7)
        
        # Find max pushups for color scaling
        max_count = max(self.data.values()) if self.data else 1
        
        # Draw heatmap
        x_offset = 20  # Space for day labels
        y_offset = 20  # Space for month labels
        
        # Draw day labels (Sun-Sat)
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        for i, day in enumerate(days):
            painter.drawText(
                x_offset + i * (self.cell_size + self.cell_margin),
                y_offset - 5,
                self.cell_size,
                10,
                Qt.AlignCenter,
                day[0]  # Just first letter
            )
        
        # Draw cells
        current_date = start_date
        month_labels = {}
        
        for week in range(52):
            week_x = x_offset + week * (self.cell_size + self.cell_margin)
            
            # Track month for labels
            month = current_date.toString("MMM")
            if month not in month_labels:
                month_labels[month] = week_x
            
            for day in range(7):
                date_str = current_date.toString("yyyy-MM-dd")
                count = self.data.get(date_str, 0)
                
                # Calculate color intensity
                if count == 0:
                    color = QColor("#ebedf0")  # Light gray for no activity
                else:
                    # Scale from light green to dark green
                    intensity = min(count / max_count, 1.0)
                    green = 144 + int(111 * intensity)
                    color = QColor(235, green, 52)
                
                # Draw cell
                cell_y = y_offset + day * (self.cell_size + self.cell_margin)
                painter.fillRect(
                    week_x, cell_y,
                    self.cell_size, self.cell_size,
                    QBrush(color)
                )
                
                # Draw border
                painter.setPen(QPen(Qt.gray, 0.5))
                painter.drawRect(
                    week_x, cell_y,
                    self.cell_size, self.cell_size
                )
                
                current_date = current_date.addDays(1)
        
        # Draw month labels
        painter.setPen(Qt.black)
        for month, x_pos in month_labels.items():
            painter.drawText(
                x_pos, y_offset + 7 * (self.cell_size + self.cell_margin) + 15,
                30, 15,
                Qt.AlignLeft,
                month
            )
        
        # Draw legend
        legend_y = y_offset + 7 * (self.cell_size + self.cell_margin) + 40
        painter.drawText(20, legend_y, "Less")
        
        # Draw color squares for legend
        for i in range(5):
            intensity = i / 4.0
            green = 144 + int(111 * intensity)
            color = QColor(235, green, 52)
            
            x_pos = 60 + i * 20
            painter.fillRect(
                x_pos, legend_y,
                15, 15,
                QBrush(color)
            )
            painter.setPen(QPen(Qt.gray, 0.5))
            painter.drawRect(x_pos, legend_y, 15, 15)
        
        painter.drawText(160, legend_y, "More")
        
    def mouseMoveEvent(self, event):
        # Calculate which cell is hovered
        x_offset = 20
        y_offset = 20
        
        today = QDate.currentDate()
        start_date = today.addDays(-52 * 7)
        
        cell_x = (event.pos().x() - x_offset) // (self.cell_size + self.cell_margin)
        cell_y = (event.pos().y() - y_offset) // (self.cell_size + self.cell_margin)
        
        if 0 <= cell_x < 52 and 0 <= cell_y < 7:
            days_offset = cell_x * 7 + cell_y
            hover_date = start_date.addDays(days_offset)
            date_str = hover_date.toString("yyyy-MM-dd")
            count = self.data.get(date_str, 0)
            
            QToolTip.showText(
                event.globalPos(),
                f"{date_str} — {count} pushups",
                self
            )
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # TODO: Implement edit dialog for clicked date
            pass
    
    def sizeHint(self):
        return self.minimumSizeHint()
    
    def minimumSizeHint(self):
        width = 20 + 52 * (self.cell_size + self.cell_margin)
        height = 100 + 7 * (self.cell_size + self.cell_margin)
        return self.minimumSize()
