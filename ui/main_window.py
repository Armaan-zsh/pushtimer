from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QSpinBox, QMessageBox, QProgressBar,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QSystemTrayIcon
)
from PySide6.QtCore import QTimer, Qt, QDateTime, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta
import json
from pathlib import Path
from .dialogs import SettingsDialog, NotificationDialog
from .heatmap_widget import HeatmapWidget

class MainWindow(QMainWindow):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.setup_ui()
        self.setup_timers()
        self.load_theme()
        
    def setup_ui(self):
        self.setWindowTitle("Pushup Timer")
        self.setMinimumSize(400, 300)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Pushup Timer")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Today's total
        self.today_label = QLabel("Today: 0 pushups")
        self.today_label.setAlignment(Qt.AlignCenter)
        font = self.today_label.font()
        font.setPointSize(14)
        self.today_label.setFont(font)
        layout.addWidget(self.today_label)
        
        # Countdown timer
        self.timer_label = QLabel("Next reminder in: 35:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        timer_font = QFont()
        timer_font.setPointSize(18)
        timer_font.setFamily("Monospace")
        self.timer_label.setFont(timer_font)
        layout.addWidget(self.timer_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 35 * 60)  # 35 minutes in seconds
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.heatmap_btn = QPushButton("View Heatmap")
        self.heatmap_btn.clicked.connect(self.show_heatmap)
        self.heatmap_btn.setMinimumHeight(40)
        button_layout.addWidget(self.heatmap_btn)
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        self.settings_btn.setMinimumHeight(40)
        button_layout.addWidget(self.settings_btn)
        
        self.pause_btn = QPushButton("Pause Timer")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setMinimumHeight(40)
        button_layout.addWidget(self.pause_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Timer running")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Update today's total
        self.update_today_total()
        
    def setup_timers(self):
        # Countdown timer (updates every second)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # Update every second
        
        # Next reminder time
        self.next_reminder = QDateTime.currentDateTime().addSecs(
            self.tracker.config.get("timer_minutes", 35) * 60
        )
        self.update_countdown()
        
    def update_countdown(self):
        now = QDateTime.currentDateTime()
        if self.tracker.is_paused:
            self.timer_label.setText("Timer paused")
            self.status_label.setText("Paused")
            self.pause_btn.setText("Resume Timer")
            self.progress_bar.setValue(0)
            return
        
        seconds_left = now.secsTo(self.next_reminder)
        if seconds_left <= 0:
            self.next_reminder = now.addSecs(
                self.tracker.config.get("timer_minutes", 35) * 60
            )
            seconds_left = now.secsTo(self.next_reminder)
        
        minutes = seconds_left // 60
        seconds = seconds_left % 60
        self.timer_label.setText(f"Next reminder in: {minutes:02d}:{seconds:02d}")
        
        # Update progress bar
        total_seconds = self.tracker.config.get("timer_minutes", 35) * 60
        progress = total_seconds - seconds_left
        self.progress_bar.setValue(progress)
        
    def update_today_total(self):
        total = self.tracker.get_today_total()
        self.today_label.setText(f"Today: {total} pushups")
        
    def show_reminder_dialog(self):
        """Show non-modal notification dialog"""
        # Only show one at a time
        if hasattr(self, '_notification_dialog') and self._notification_dialog:
            if self._notification_dialog.isVisible():
                return
            else:
                self._notification_dialog = None
                
        self._notification_dialog = NotificationDialog()
        self._notification_dialog.action_taken.connect(self.on_notification_closed)
        self._notification_dialog.show()
        
    def on_notification_closed(self, action_type):
        """Handle notification dialog closing with different actions"""
        if hasattr(self, '_notification_dialog'):
            self._notification_dialog.deleteLater()
            self._notification_dialog = None
            
        # Action types:
        # -2 = Grace period cancel (do nothing, don't reset timer)
        # -1 = Snooze for 5 minutes
        # 0 = Skip (log 0 pushups)
        # >0 = Log pushups
        
        if action_type == -2:
            # Grace period cancel - do nothing
            self.show_notification("Reminder Cancelled", 
                                 "No action taken. Next reminder in 35 minutes.")
            return
            
        elif action_type == -1:
            # Snooze for 5 minutes
            self.tracker.pause_timer()
            
            # Calculate new reminder time
            self.next_reminder = QDateTime.currentDateTime().addSecs(5 * 60)
            
            # Set a one-time timer for 5 minutes
            QTimer.singleShot(5 * 60 * 1000, self.snooze_ended)
            
            self.status_label.setText("Snoozed for 5 min")
            self.pause_btn.setText("Resume Timer")
            self.show_notification("Snoozed", 
                                 "Reminder paused for 5 minutes. Back in 5 minutes!")
            return
            
        elif action_type >= 0:
            # Skip (0) or Log (>0)
            self.tracker.save_pushups(action_type)
            self.update_today_total()
            
            # Restart timer
            self.tracker.start_timer()
            self.next_reminder = QDateTime.currentDateTime().addSecs(
                self.tracker.config.get("timer_minutes", 35) * 60
            )
            
            # Show confirmation
            if action_type > 0:
                self.show_notification("Pushups Logged", 
                                     f"Great job! {action_type} pushups logged.")
            else:
                self.show_notification("Skipped", 
                                     "Logged 0 pushups. Next reminder in 35 minutes.")
            
    def snooze_ended(self):
        """Called when snooze period ends"""
        self.tracker.resume_timer()
        self.next_reminder = QDateTime.currentDateTime().addSecs(
            self.tracker.config.get("timer_minutes", 35) * 60
        )
        self.status_label.setText("Timer running")
        self.pause_btn.setText("Pause Timer")
        self.show_notification("Snooze Ended", 
                             "Back to regular reminders every 35 minutes!")
            
    def show_notification(self, title, message):
        """Show system tray notification"""
        try:
            QSystemTrayIcon.showMessage(self, title, message, QSystemTrayIcon.Information, 3000)
        except:
            pass
        
    def show_heatmap(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Pushup Heatmap")
        dialog.setMinimumSize(800, 400)
        
        layout = QVBoxLayout(dialog)
        heatmap = HeatmapWidget(self.tracker)
        layout.addWidget(heatmap)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
        
    def show_settings(self):
        dialog = SettingsDialog(self.tracker.config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            self.tracker.config.update(new_config)
            self.tracker.save_config()
            self.tracker.reminder_time = new_config.get("timer_minutes", 35) * 60 * 1000
            if not self.tracker.is_paused:
                self.tracker.start_timer()
            self.load_theme()
            
    def toggle_pause(self):
        if self.tracker.is_paused:
            self.tracker.resume_timer()
            self.pause_btn.setText("Pause Timer")
            self.status_label.setText("Timer running")
        else:
            self.tracker.pause_timer()
            self.pause_btn.setText("Resume Timer")
            self.status_label.setText("Paused")
            
    def load_theme(self):
        theme = self.tracker.config.get("theme", "light")
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: white;
                    border: 1px solid #555;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                }
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("")
    
    def closeEvent(self, event):
        """Override close event to hide instead of quit"""
        # Just hide the window, don't close the app
        self.hide()
        event.ignore()  # Don't process the close event
        
        # Show notification
        self.show_notification("Pushup Timer", 
                             "App is still running in system tray. Right-click the green icon to show window.")
