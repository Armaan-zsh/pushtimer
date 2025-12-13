from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QColor, QFont
import datetime

class StatsDialog(QDialog):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setWindowTitle("Statistics Dashboard")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background: #0f1115; color: white;")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Performance Stats")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)
        
        # Stats Cards
        stats_layout = QHBoxLayout()
        stats = self.tracker.get_stats()
        streak = self.tracker.get_streak()
        
        stats_layout.addWidget(self.create_card("Total 🔥", str(stats['total']), "#ff9800"))
        stats_layout.addWidget(self.create_card("Best Day 🏆", str(stats['best_day']), "#00ff88"))
        stats_layout.addWidget(self.create_card("Streak ⚡", str(streak), "#7000ff"))
        stats_layout.addWidget(self.create_card("Avg/Day 📈", str(stats['avg']), "#00d4ff"))
        
        layout.addLayout(stats_layout)
        
        # Bar Chart
        chart_container = QWidget()
        chart_container.setStyleSheet("background: #1a1d24; border-radius: 15px;")
        chart_container.setFixedHeight(250)
        chart_layout = QVBoxLayout(chart_container)
        
        chart_label = QLabel("Last 7 Days Activity")
        chart_label.setStyleSheet("color: #8b9bb4; font-weight: bold; padding: 10px;")
        chart_layout.addWidget(chart_label)
        
        self.bar_chart = BarChartWidget(self.tracker)
        chart_layout.addWidget(self.bar_chart)
        
        layout.addWidget(chart_container)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        export_btn = QPushButton("💾 Export to CSV")
        export_btn.setFixedSize(150, 45)
        export_btn.setStyleSheet("""
            QPushButton {
                background: #2d333b; color: white; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background: #3c4450; }
        """)
        export_btn.clicked.connect(self.export_data)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 45)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #2d333b; color: white; border-radius: 8px;
            }
            QPushButton:hover { background: #3c4450; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def create_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #1a1d24;
                border-radius: 15px;
                border: 1px solid {color}44;
            }}
        """)
        layout = QVBoxLayout(card)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #8b9bb4; font-size: 14px;")
        layout.addWidget(t_lbl)
        
        v_lbl = QLabel(str(value))
        v_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        layout.addWidget(v_lbl)
        
        return card
        
    def export_data(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "pushup_history.csv", "CSV Files (*.csv)"
        )
        if filename:
            try:
                self.tracker.export_csv(filename)
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")


class BarChartWidget(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.data = tracker.get_all_data()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Get last 7 days data
        days = []
        counts = []
        today = datetime.date.today()
        max_val = 1
        
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            d_str = d.isoformat()
            count = self.data.get(d_str, 0)
            
            days.append(d.strftime("%a"))
            counts.append(count)
            if count > max_val: max_val = count
            
        # Draw Bars
        bar_width = (width - 40) / 7 - 10
        x_start = 20
        
        for i in range(7):
            val = counts[i]
            bar_height = (val / max_val) * (height - 40)
            
            x = x_start + i * (bar_width + 10)
            y = height - 30 - bar_height
            
            # Bar
            painter.setBrush(QBrush(QColor("#00ff88")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 4, 4)
            
            # Value Label
            if val > 0:
                painter.setPen(QColor("white"))
                painter.drawText(x, y - 5, bar_width, 10, Qt.AlignCenter, str(val))
            
            # Day Label
            painter.setPen(QColor("#8b9bb4"))
            painter.drawText(x, height - 20, bar_width, 20, Qt.AlignCenter, days[i])
