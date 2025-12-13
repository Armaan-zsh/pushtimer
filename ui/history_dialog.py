from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QLabel, QDateEdit, QSpinBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QDate
import datetime

class HistoryDialog(QDialog):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        self.setWindowTitle("Edit History")
        self.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Pushup History")
        font = header.font()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Add Entry Section
        add_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(0, 9999)
        self.count_spin.setValue(10)
        
        add_btn = QPushButton("Add/Update Entry")
        add_btn.clicked.connect(self.add_entry)
        
        add_layout.addWidget(QLabel("Date:"))
        add_layout.addWidget(self.date_edit)
        add_layout.addWidget(QLabel("Count:"))
        add_layout.addWidget(self.count_spin)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Date", "Count"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # Edit via top controls for safety
        self.table.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.table)
        
        # Instructions
        help_lbl = QLabel("Select a row to edit. Use top controls to save.")
        help_lbl.setStyleSheet("color: gray;")
        help_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(help_lbl)
        
        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def load_data(self):
        data = self.tracker.get_all_data()
        # Sort by date desc
        sorted_dates = sorted(data.keys(), reverse=True)
        
        self.table.setRowCount(len(sorted_dates))
        
        for i, date_str in enumerate(sorted_dates):
            count = data[date_str]
            
            date_item = QTableWidgetItem(date_str)
            count_item = QTableWidgetItem(str(count))
            
            self.table.setItem(i, 0, date_item)
            self.table.setItem(i, 1, count_item)
            
    def on_cell_clicked(self, row, col):
        date_str = self.table.item(row, 0).text()
        count = int(self.table.item(row, 1).text())
        
        qdate = QDate.fromString(date_str, "yyyy-MM-dd")
        self.date_edit.setDate(qdate)
        self.count_spin.setValue(count)
        
    def add_entry(self):
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        count = self.count_spin.value()
        
        reply = QMessageBox.question(
            self, "Confirm Update", 
            f"Set pushups for {date_str} to {count}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tracker.update_pushups_for_date(date_str, count)
            self.load_data()
            QMessageBox.information(self, "Success", "History updated!")
