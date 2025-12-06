from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon
from .dialogs import ReminderDialog
import datetime

class NotificationManager(QObject):
    reminder_needed = Signal()
    
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.reminder_dialog = None
        self.notification_timeout = 120  # 2 minutes
        self.setup_tray_icon()
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon()
        # ... setup icon ...
        
    def show_reminder(self):
        """Show the reminder once"""
        if self.reminder_dialog and self.reminder_dialog.isVisible():
            return  # Already showing
            
        self.reminder_dialog = ReminderDialog()
        self.reminder_dialog.finished.connect(self.on_reminder_finished)
        self.reminder_dialog.show()
        # Bring to front
        self.reminder_dialog.raise_()
        self.reminder_dialog.activateWindow()
        
    def on_reminder_finished(self, result):
        if result:
            count = self.reminder_dialog.get_count()
            self.tracker.save_pushups(count)
        else:
            self.tracker.save_pushups(0)
            
        # Destroy the dialog
        self.reminder_dialog.deleteLater()
        self.reminder_dialog = None
