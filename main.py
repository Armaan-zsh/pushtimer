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
        
        # Create directories if they don't exist
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database and config
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
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON pushups(date)
        ''')
        conn.commit()
        conn.close()
    
    def load_config(self):
        """Load or create default configuration"""
        default_config = {
            "timer_minutes": 35,
            "reminder_seconds": 60,
            "autostart": True,
            "start_minimized": True,
            "theme": "light",
            "aggregate_mode": "add"
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
        """Start or restart the reminder timer"""
        if not self.is_paused:
            self.timer.start(self.reminder_time)
    
    def pause_timer(self):
        """Pause the timer"""
        self.is_paused = True
        self.timer.stop()
    
    def resume_timer(self):
        """Resume the timer"""
        self.is_paused = False
        self.timer.start(self.reminder_time)
    
    def show_reminder(self):
        """Emit signal to show reminder dialog"""
        self.reminder_signal.emit()
    
    def save_pushups(self, count):
        """Save pushup count to database"""
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
    
    def get_today_total(self):
        """Get total pushups for today"""
        today = datetime.date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(count) FROM pushups WHERE date = ?", (today,))
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0
    
    def get_all_data(self):
        """Get all pushup data for heatmap"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(count) as total FROM pushups GROUP BY date ORDER BY date")
        data = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return data

    def update_pushups_for_date(self, date_str, count):
        """Update/Overwrite pushups for a specific date"""
        now = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove existing entries for this date
        cursor.execute("DELETE FROM pushups WHERE date = ?", (date_str,))
        
        # Insert new single entry
        cursor.execute(
            "INSERT INTO pushups (date, count, timestamp) VALUES (?, ?, ?)",
            (date_str, count, now)
        )
        conn.commit()
        conn.close()
        
        # If we updated today, restart timer if needed
        if date_str == datetime.date.today().isoformat():
            self.start_timer()

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
