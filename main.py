#!/usr/bin/env python3
"""
Pushup Timer Application
Runs every 35 minutes, tracks pushups, shows heatmap
"""

import sys
import json
import sqlite3
import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from ui.main_window import MainWindow

class PushupTracker(QObject):
    reminder_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.app_dir = Path.home() / ".local/share/pushtimer"
        self.config_dir = Path.home() / ".config/pushtimer"
        self.db_path = self.app_dir / "pushups.db"
        self.config_path = self.config_dir / "config.json"
        
        # Create directories
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Init
        self.init_db()
        self.load_config()
        
        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_reminder)
        self.is_paused = False
        self.reminder_time = self.config.get("timer_minutes", 35) * 60 * 1000
        
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pushups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                count INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON pushups(date)')
        conn.commit()
        conn.close()
    
    def load_config(self):
        """Load or create default configuration"""
        default_config = {
            "timer_minutes": 35,
            "reminder_seconds": 60,
            "daily_goal": 100,
            "autostart": True,
            "start_minimized": True,
            "theme": "dark",
            "aggregate_mode": "add",
            "sound_enabled": True
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                self.config = {**default_config, **loaded_config}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def start_timer(self):
        if not self.is_paused:
            self.timer.start(self.reminder_time)
    
    def pause_timer(self):
        self.is_paused = True
        self.timer.stop()
    
    def resume_timer(self):
        self.is_paused = False
        self.timer.start(self.reminder_time)
    
    def show_reminder(self):
        self.reminder_signal.emit()
    
    def save_pushups(self, count):
        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if self.config.get("aggregate_mode") == "replace":
            cursor.execute("DELETE FROM pushups WHERE date = ?", (today,))
        
        cursor.execute(
            "INSERT INTO pushups (date, count, timestamp) VALUES (?, ?, ?)",
            (today, count, now)
        )
        conn.commit()
        conn.close()
        self.start_timer()
    
    def update_pushups_for_date(self, date_str, count):
        now = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pushups WHERE date = ?", (date_str,))
        cursor.execute(
            "INSERT INTO pushups (date, count, timestamp) VALUES (?, ?, ?)",
            (date_str, count, now)
        )
        conn.commit()
        conn.close()
        if date_str == datetime.date.today().isoformat():
            self.start_timer()

    def get_today_total(self):
        today = datetime.date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(count) FROM pushups WHERE date = ?", (today,))
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0
    
    def get_all_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(count) as total FROM pushups GROUP BY date ORDER BY date")
        data = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return data

    # --- NEW MEGA FEATURES ---

    def get_streak(self):
        """Calculate current streak of days with >= 1 pushup"""
        data = self.get_all_data()
        if not data: return 0
        
        sorted_dates = sorted(data.keys(), reverse=True)
        today = datetime.date.today()
        streak = 0
        
        # Check today first
        if today.isoformat() in data and data[today.isoformat()] > 0:
            streak += 1
            current_date = today - datetime.timedelta(days=1)
        else:
            # If no pushups today yet, check if we had some yesterday (streak active but at risk)
            # or if streak is already broken.
            # Technically streak is 0 if not done today, but let's be kind and check yesterday
            current_date = today - datetime.timedelta(days=1)
            if current_date.isoformat() not in data:
                return 0 # Broken streak
        
        while True:
            date_str = current_date.isoformat()
            if date_str in data and data[date_str] > 0:
                streak += 1
                current_date -= datetime.timedelta(days=1)
            else:
                break
        return streak

    def get_stats(self):
        """Get comprehensive stats"""
        data = self.get_all_data()
        if not data:
            return {"total": 0, "best_day": 0, "avg": 0, "weekly_avg": 0}
            
        values = list(data.values())
        total = sum(values)
        best_day = max(values)
        avg = total / len(values)
        
        # Last 7 days
        today = datetime.date.today()
        last_week_total = 0
        for i in range(7):
            d = (today - datetime.timedelta(days=i)).isoformat()
            last_week_total += data.get(d, 0)
        weekly_avg = last_week_total / 7
        
        return {
            "total": total,
            "best_day": best_day,
            "avg": round(avg, 1),
            "weekly_avg": round(weekly_avg, 1)
        }

    def export_csv(self, file_path):
        """Export data to CSV"""
        data = self.get_all_data()
        with open(file_path, 'w') as f:
            f.write("Date,Count\n")
            for date in sorted(data.keys()):
                f.write(f"{date},{data[date]}\n")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pushup Timer")
    app.setQuitOnLastWindowClosed(False)
    
    tracker = PushupTracker()
    
    # Start web server
    from web_server import PushupWebServer
    try:
        server = PushupWebServer(tracker.db_path)
        server.start_in_thread()
    except Exception as e:
        print(f"Failed to start web server: {e}")

    window = MainWindow(tracker)
    
    # System tray
    tray_icon = QSystemTrayIcon()
    
    # Try to load icon
    icon_path = Path(__file__).parent / "assets/icons/pushtimer.svg"
    if icon_path.exists():
        tray_icon.setIcon(QIcon(str(icon_path)))
    else:
        # Create simple icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(76, 175, 80))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(QPen(Qt.GlobalColor.white, 4))
        painter.drawLine(24, 28, 40, 28)
        painter.drawLine(24, 36, 40, 36)
        painter.end()
        tray_icon.setIcon(QIcon(pixmap))
    
    tray_menu = QMenu()
    
    log_now_action = QAction("Log Pushups Now")
    log_now_action.triggered.connect(window.show_reminder_dialog)
    tray_menu.addAction(log_now_action)
    
    show_action = QAction("Show Window")
    show_action.triggered.connect(window.show)
    tray_menu.addAction(show_action)
    
    pause_action = QAction("Pause Timer")
    pause_action.triggered.connect(tracker.pause_timer)
    tray_menu.addAction(pause_action)
    
    resume_action = QAction("Resume Timer")
    resume_action.triggered.connect(tracker.resume_timer)
    tray_menu.addAction(resume_action)
    
    tray_menu.addSeparator()
    
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    tray_menu.addAction(quit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    tracker.reminder_signal.connect(window.show_reminder_dialog)
    tracker.start_timer()
    
    if tracker.config.get("start_minimized", True):
        window.hide()
    else:
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
