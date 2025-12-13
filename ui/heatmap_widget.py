from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QToolTip
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import datetime

class HeatmapWidget(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.data = tracker.get_all_data()
        self.cell_size = 14
        self.cell_margin = 3
        self.setMouseTracking(True)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(180)
        
        # Debug: print loaded data
        print(f"[Heatmap] Loaded {len(self.data)} entries")
        for date, count in sorted(self.data.items())[-5:]:
            print(f"  {date}: {count}")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        today = QDate.currentDate()
        print(f"[Heatmap] Today: {today.toString('yyyy-MM-dd')}, dayOfWeek: {today.dayOfWeek()}")
        
        # Calculate start date: 52 weeks ago, aligned to Monday
        # Qt dayOfWeek(): 1=Mon, 7=Sun
        # We want to start on a Monday, so subtract (dayOfWeek - 1) to get to current week's Monday
        # then go back 52 weeks
        start_date = today.addDays(-(52 * 7) - (today.dayOfWeek() - 1))
        print(f"[Heatmap] Start date: {start_date.toString('yyyy-MM-dd')}")
        
        # Calculate max for scaling
        max_count = max(self.data.values()) if self.data else 1
        
        x_offset = 40
        y_offset = 25
        
        # Draw Day Labels (Mon, Wed, Fri)
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(QColor("#8b9bb4"))
        
        day_names = ["Mon", "", "Wed", "", "Fri", "", ""]
        for i, day in enumerate(day_names):
            if day:
                painter.drawText(
                    5,
                    y_offset + i * (self.cell_size + self.cell_margin) + 11,
                    day
                )
        
        # Color palette (GitHub-style greens) - SOLID colors, no alpha
        colors = [
            QColor(30, 30, 30),     # Empty - dark gray
            QColor(14, 68, 41),     # Level 1 - darkest green
            QColor(0, 109, 50),     # Level 2
            QColor(38, 166, 65),    # Level 3
            QColor(57, 211, 83),    # Level 4 - brightest green
        ]
        
        # Draw Cells
        current_date = start_date
        month_labels = {}
        
        for week in range(53):
            week_x = x_offset + week * (self.cell_size + self.cell_margin)
            
            # Month label - check first day of week
            if current_date.day() <= 7:
                month = current_date.toString("MMM")
                if month not in month_labels:
                    month_labels[month] = week_x
            
            for day_idx in range(7):
                if current_date > today:
                    # Don't draw future dates
                    current_date = current_date.addDays(1)
                    continue
                    
                date_str = current_date.toString("yyyy-MM-dd")
                count = self.data.get(date_str, 0)
                
                if count > 0:
                    print(f"[Heatmap] MATCH: {date_str} = {count} at week {week}, day {day_idx}, x={week_x}")
                
                # Determine color level (0-4)
                if count == 0:
                    level = 0
                elif max_count > 0:
                    ratio = count / max_count
                    if ratio <= 0.25:
                        level = 1
                    elif ratio <= 0.5:
                        level = 2
                    elif ratio <= 0.75:
                        level = 3
                    else:
                        level = 4
                else:
                    level = 1
                
                color = colors[level]
                cell_y = y_offset + day_idx * (self.cell_size + self.cell_margin)
                
                # Draw cell
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.drawRoundedRect(
                    int(week_x), int(cell_y),
                    self.cell_size, self.cell_size,
                    3, 3
                )
                
                current_date = current_date.addDays(1)
        
        # Draw Month Labels
        painter.setPen(QColor("#8b9bb4"))
        for month, x_pos in month_labels.items():
            painter.drawText(int(x_pos), y_offset - 8, month)
        
        # Legend
        legend_x = self.width() - 160
        legend_y = self.height() - 25
        
        painter.drawText(legend_x, legend_y + 11, "Less")
        
        for i, color in enumerate(colors):
            x_pos = legend_x + 35 + i * 18
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawRoundedRect(int(x_pos), legend_y, 14, 14, 3, 3)
            
        painter.drawText(legend_x + 35 + 5 * 18 + 5, legend_y + 11, "More")
    
    def mouseMoveEvent(self, event):
        x_offset = 40
        y_offset = 25
        
        today = QDate.currentDate()
        start_date = today.addDays(-(52 * 7) - (today.dayOfWeek() - 1))
        
        # FIX: Use event.pos() not event.key()
        pos = event.pos()
        cell_x = (pos.x() - x_offset) // (self.cell_size + self.cell_margin)
        cell_y = (pos.y() - y_offset) // (self.cell_size + self.cell_margin)
        
        if 0 <= cell_x < 53 and 0 <= cell_y < 7:
            check_date = start_date.addDays(int(cell_x) * 7 + int(cell_y))
            date_str = check_date.toString("yyyy-MM-dd")
            count = self.data.get(date_str, 0)
            
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"<b>{date_str}</b><br>{count} pushups",
                self
            )
    
    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(900, 180)
        
    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(850, 180)

