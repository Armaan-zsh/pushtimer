from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QSpinBox, QMessageBox, QProgressBar,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QSystemTrayIcon,
    QTextEdit, QApplication, QComboBox, QMenu
)
from PySide6.QtCore import QTimer, Qt, QDateTime, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QImage, QAction, QKeySequence
import json
from pathlib import Path

from .dialogs import SettingsDialog, NotificationDialog
from .heatmap_widget import HeatmapWidget
from .history_dialog import HistoryDialog
from .widgets import ProgressRing
from .stats_dialog import StatsDialog
from .floating_widget import FloatingWidget
import sounds

import qrcode
import socket
import netifaces

class MainWindow(QMainWindow):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.setup_ui()
        self.setup_actions()
        self.setup_timers()
        self.load_theme()
        
    def setup_ui(self):
        self.setWindowTitle("Pushup Timer")
        self.setMinimumSize(450, 600)
        
        # Central Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Gradient Background
        self.setStyleSheet("""
            QMainWindow {
                background: #0f1115;
            }
        """)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- HEADER (Streak & Title) ---
        header = QWidget()
        header.setStyleSheet("background: #1a1d24; border-bottom: 2px solid #2d333b;")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel("PUSHTIMER")
        title_label.setStyleSheet("color: #ffffff; font-weight: 800; font-size: 18px; letter-spacing: 2px;")
        
        self.streak_label = QLabel("🔥 0 Day Streak")
        self.streak_label.setStyleSheet("""
            color: #ff9800; 
            font-weight: bold; 
            font-size: 14px;
            background: rgba(255, 152, 0, 0.1);
            padding: 6px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 152, 0, 0.3);
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.streak_label)
        layout.addWidget(header)
        
        # --- MAIN CONTENT ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 10, 30, 30)
        content_layout.setSpacing(20)
        
        # Progress Ring
        ring_container = QWidget()
        ring_layout = QVBoxLayout(ring_container)
        self.progress_ring = ProgressRing()
        ring_layout.addWidget(self.progress_ring, 0, Qt.AlignCenter)
        content_layout.addWidget(ring_container)
        
        # Timer Status
        self.status_container = QWidget()
        self.status_container.setStyleSheet("background: #1a1d24; border-radius: 15px; padding: 10px;")
        status_layout = QVBoxLayout(self.status_container)
        
        self.timer_label = QLabel("Reminder: 35:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("color: #8b9bb4; font-size: 18px; font-family: monospace; font-weight: bold;")
        status_layout.addWidget(self.timer_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #2d333b;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: #00ff88;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.status_container)
        
        # Buttons Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Helper to create buttons
        def create_btn(text, icon_char, color="#ffffff", bg="#2d333b"):
            btn = QPushButton(f"{icon_char}  {text}")
            btn.setMinimumHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {color};
                    border: none;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 14px;
                    text-align: left;
                    padding-left: 20px;
                }}
                QPushButton:hover {{
                    background: {bg}dd; 
                    border: 1px solid {color}55;
                }}
            """)
            return btn
        
        # Row 1
        self.log_btn = create_btn("Quick Log", "✓", "#00ff88", "#0d4429")
        self.log_btn.clicked.connect(lambda: self.tracker.save_pushups(20)) # Quick log default
        grid_layout.addWidget(self.log_btn, 0, 0)
        
        self.heatmap_btn = create_btn("Heatmap", "📅")
        self.heatmap_btn.clicked.connect(self.show_heatmap)
        grid_layout.addWidget(self.heatmap_btn, 0, 1)
        
        # Row 2
        self.history_btn = create_btn("History", "📝")
        self.history_btn.clicked.connect(self.show_history)
        grid_layout.addWidget(self.history_btn, 1, 0)
        
        self.stats_btn = create_btn("Stats", "📊") # New
        self.stats_btn.clicked.connect(self.show_stats)
        grid_layout.addWidget(self.stats_btn, 1, 1)

        # Row 3
        self.sync_btn = create_btn("Phone Sync", "📱")
        self.sync_btn.clicked.connect(self.show_sync_dialog)
        grid_layout.addWidget(self.sync_btn, 2, 0)
        
        self.settings_btn = create_btn("Settings", "⚙️")
        self.settings_btn.clicked.connect(self.show_settings)
        grid_layout.addWidget(self.settings_btn, 2, 1)
        
        # Row 4 (Mini Timer)
        self.float_btn = create_btn("Mini Timer", "🧱")
        self.float_btn.clicked.connect(self.show_floating_timer)
        grid_layout.addWidget(self.float_btn, 3, 0)
        
        content_layout.addLayout(grid_layout)
        
        # Pause Button (Main)
        self.pause_btn = QPushButton("⏸  Pause Timer")
        self.pause_btn.setMinimumHeight(45)
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff9800;
                border: 2px solid #ff9800;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 152, 0, 0.1);
            }
        """)
        content_layout.addWidget(self.pause_btn)
        
        layout.addLayout(content_layout)
        
        self.update_today_total()
        self.update_streak()
        
    def setup_actions(self):
        # Shortcuts
        self.log_action = QAction(self)
        self.log_action.setShortcut(QKeySequence("Ctrl+L"))
        self.log_action.triggered.connect(lambda: self.tracker.save_pushups(self.tracker.config.get("reminder_pushups", 20))) # Need to add config for this or dialog
        self.addAction(self.log_action)

        self.history_action = QAction(self)
        self.history_action.setShortcut(QKeySequence("Ctrl+H"))
        self.history_action.triggered.connect(self.show_history)
        self.addAction(self.history_action)

        self.stats_action = QAction(self)
        self.stats_action.setShortcut(QKeySequence("Ctrl+S")) # Conflict with save? Usually fine in non-editor apps
        self.stats_action.triggered.connect(self.show_stats)
        self.addAction(self.stats_action)
        
    def setup_timers(self):
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        
        self.next_reminder = QDateTime.currentDateTime().addSecs(
            self.tracker.config.get("timer_minutes", 35) * 60
        )
        self.update_countdown()
        
    def update_countdown(self):
        now = QDateTime.currentDateTime()
        if self.tracker.is_paused:
            self.timer_label.setText("⏸ Paused")
            self.pause_btn.setText("▶ Resume Timer")
            self.progress_bar.setValue(0)
            if hasattr(self, 'floating_widget') and self.floating_widget and self.floating_widget.isVisible():
                self.floating_widget.update_time("Paused")
            return
        
        seconds_left = now.secsTo(self.next_reminder)
        if seconds_left <= 0:
            self.next_reminder = now.addSecs(
                self.tracker.config.get("timer_minutes", 35) * 60
            )
            seconds_left = now.secsTo(self.next_reminder)
        
        minutes = seconds_left // 60
        seconds = seconds_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.timer_label.setText(f"Reminder: {time_str}")
        
        if hasattr(self, 'floating_widget') and self.floating_widget and self.floating_widget.isVisible():
            self.floating_widget.update_time(time_str)
        
        total_seconds = self.tracker.config.get("timer_minutes", 35) * 60
        progress = total_seconds - seconds_left
        
        # Update progress bar range carefully
        self.progress_bar.setRange(0, total_seconds)
        self.progress_bar.setValue(progress)
        
    def update_today_total(self):
        total = self.tracker.get_today_total()
        goal = self.tracker.config.get("daily_goal", 100)
        self.progress_ring.set_value(total, goal)
        self.update_streak()
        
    def update_streak(self):
        streak = self.tracker.get_streak()
        self.streak_label.setText(f"🔥 {streak} Day Streak")
        
    def show_reminder_dialog(self):
        if hasattr(self, '_notification_dialog') and self._notification_dialog:
            if self._notification_dialog.isVisible():
                return
            else:
                self._notification_dialog = None
        
        if self.tracker.config.get("sound_enabled", True):
            sounds.play_sound()
            
        self._notification_dialog = NotificationDialog()
        self._notification_dialog.action_taken.connect(self.on_notification_closed)
        self._notification_dialog.show()
        
    def on_notification_closed(self, action_type):
        if hasattr(self, '_notification_dialog'):
            self._notification_dialog.deleteLater()
            self._notification_dialog = None
            
        if action_type == -2: # Grace cancel
            self.show_notification("Reminder Cancelled", "No action taken.")
            return
            
        elif action_type == -1: # Snooze
            self.tracker.pause_timer()
            self.next_reminder = QDateTime.currentDateTime().addSecs(5 * 60)
            QTimer.singleShot(5 * 60 * 1000, self.snooze_ended)
            
            self.pause_btn.setText("▶ Resume Timer")
            self.show_notification("Snoozed", "Back in 5 minutes! 💤")
            return
            
        elif action_type >= 0:
            self.tracker.save_pushups(action_type)
            self.update_today_total()
            
            self.tracker.start_timer()
            self.next_reminder = QDateTime.currentDateTime().addSecs(
                self.tracker.config.get("timer_minutes", 35) * 60
            )
            
            if action_type > 0:
                self.show_notification("BEAST MODE! 💪", f"{action_type} pushups logged. Keep it up!")
            else:
                self.show_notification("Skipped", "No worries, get them next time.")
            
    def snooze_ended(self):
        self.tracker.resume_timer()
        self.next_reminder = QDateTime.currentDateTime().addSecs(
            self.tracker.config.get("timer_minutes", 35) * 60
        )
        self.pause_btn.setText("⏸ Pause Timer")
        self.show_notification("Snooze Ended", "Time to drop and give me 20! 🏋️")
            
    def show_notification(self, title, message):
        try:
            QSystemTrayIcon.showMessage(self, title, message, QSystemTrayIcon.Information, 3000)
        except:
            pass
        
    def show_sync_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Phone Sync")
        dialog.setFixedSize(500, 650)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📱 Sync with Your Phone")
        title_font = title.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # IP Selector
        layout.addWidget(QLabel("Select Network/IP:"))
        ip_combo = QComboBox()
        
        # Find all IPs
        ips = []
        try:
            # Method 1: All interfaces (most robust)
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        if ip and ip != '127.0.0.1':
                            ips.append(ip)
        except:
            pass
            
        # Fallback
        if not ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ips.append(s.getsockname()[0])
                s.close()
            except:
                ips.append("127.0.0.1")
                
        ip_combo.addItems(ips)
        layout.addWidget(ip_combo)
        
        # QR Code Container
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setMinimumHeight(200)
        layout.addWidget(qr_label)
        
        # URL display
        url_label = QLabel()
        url_label.setAlignment(Qt.AlignCenter)
        url_label.setStyleSheet("font-family: monospace; font-size: 14px; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(url_label)
        
        def update_qr():
            ip = ip_combo.currentText()
            url = f"http://{ip}:8080"
            
            # QR Code
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to QPixmap
            qr_img = qr_img.convert("RGBA")
            data = qr_img.tobytes("raw", "RGBA")
            qimage = QImage(data, qr_img.size[0], qr_img.size[1], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            qr_label.setPixmap(pixmap)
            
            url_label.setText(url)
            return url

        ip_combo.currentTextChanged.connect(update_qr)
        current_url = update_qr() # Init
        
        # Instructions
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setHtml("""
        <h3>📲 How to Connect:</h3>
        <ol>
            <li>Ensure laptop and phone are on the <strong>same WiFi/Hotspot</strong>.</li>
            <li>If the URL doesn't work, <strong>try a different IP</strong> from the dropdown above.</li>
            <li>Scan QR code or type URL in your phone browser.</li>
        </ol>
        """)
        instructions.setMaximumHeight(150)
        layout.addWidget(instructions)
        
        # Status
        status_label = QLabel("")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        test_btn = QPushButton("Test This Connection")
        def test_connection():
            url = url_label.text()
            import urllib.request
            import urllib.error
            try:
                response = urllib.request.urlopen(f"{url}/api/today", timeout=2)
                if response.getcode() == 200:
                    status_label.setText("✅ Server Reachable (Locally)")
                    status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    status_label.setText("⚠️ Server Error")
            except Exception as e:
                status_label.setText(f"❌ Unreachable: {e}")
                status_label.setStyleSheet("color: red;")
        test_btn.clicked.connect(test_connection)
        button_layout.addWidget(test_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()
        
    def show_history(self):
        dialog = HistoryDialog(self.tracker, self)
        if dialog.exec():
            self.update_today_total()

    def show_heatmap(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Pushup Heatmap (GitHub Style)")
        dialog.setMinimumSize(900, 250)
        
        # Dark theme for dialog
        dialog.setStyleSheet("background: #1a1d24; color: white;")
        
        layout = QVBoxLayout(dialog)
        heatmap = HeatmapWidget(self.tracker)
        layout.addWidget(heatmap)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                 background: #2d333b; color: white; border: none; padding: 8px; border-radius: 6px;
            }
            QPushButton:hover { background: #3c4450; }
        """)
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
            # self.load_theme() # Theme is consistent now
            self.update_today_total()
            
    def toggle_pause(self):
        if self.tracker.is_paused:
            self.tracker.resume_timer()
            self.pause_btn.setText("⏸ Pause Timer")
        else:
            self.tracker.pause_timer()
            self.pause_btn.setText("▶ Resume Timer")
        self.update_countdown()
            
    def load_theme(self):
        # We are enforcing the dark theme now
        pass
    
    def show_stats(self):
        dialog = StatsDialog(self.tracker, self)
        dialog.exec()
        
    def show_floating_timer(self):
        if not hasattr(self, 'floating_widget') or not self.floating_widget:
            self.floating_widget = FloatingWidget(self.tracker)
            self.floating_widget.show()
        else:
            self.floating_widget.show()
            self.floating_widget.activateWindow()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        self.show_notification("Pushup Timer Minimized", 
                             "Still running! Click tray icon to open.")
