from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QVBoxLayout, QHBoxLayout, QDateEdit,
                             QComboBox, QWidget, QScrollArea, QMessageBox, QFrame)
from PyQt6.QtCore import QDate, Qt
import os
from datetime import datetime


class AddFieldLogs(QDialog):
    def __init__(self, field_name, parent=None):
        super().__init__(parent)
        self.field_name = field_name

        self.setWindowTitle(f"Add Log - {field_name}")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        # Date input
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel('Date:'))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Log type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('Type:'))
        self.type_input = QComboBox()
        self.type_input.addItems([
            'Sėja', 'Tręšimas', 'Žolinimas', 'Poveikis ligoms',
            'Poveikis kenkėjams', 'Derliaus nuėmimas', 'Kita'
        ])
        type_layout.addWidget(self.type_input)
        layout.addLayout(type_layout)
        
        # Description
        layout.addWidget(QLabel('Description:'))
        self.desc_input = QTextEdit()
        layout.addWidget(self.desc_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.save_log)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_log(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        log_type = self.type_input.currentText()
        description = self.desc_input.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(self, "Warning", "Please enter a description.")
            return
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join('fields', self.field_name, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Save log to file (append if file already exists for this date)
        log_file = os.path.join(logs_dir, f'{date}.txt')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"Type: {log_type}\n")
            f.write(f"Date: {date}\n")
            f.write(f"Description: {description}\n")
            f.write("---\n")
        
        QMessageBox.information(self, "Success", "Log added successfully!")
        self.accept()


class ViewLogsWindow(QWidget):
    def __init__(self, field_name, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.setWindowTitle(f'Logs - {field_name}')
        self.setGeometry(400, 100, 600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Add log button
        self.add_log_btn = QPushButton('Add Log')
        self.add_log_btn.clicked.connect(self.add_log)
        main_layout.addWidget(self.add_log_btn)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for logs
        self.container_widget = QWidget()
        self.logs_layout = QVBoxLayout(self.container_widget)
        self.logs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Set the container as the scroll area's widget
        self.scroll_area.setWidget(self.container_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(self.scroll_area)
        
        # Load logs
        self.load_logs()
    
    def add_log(self):
        dialog = AddFieldLogs(self.field_name, self)
        if dialog.exec():
            self.load_logs()  # Refresh after adding
    
    def load_logs(self):
        # Clear existing logs
        for i in reversed(range(self.logs_layout.count())):
            item = self.logs_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            else:
                self.logs_layout.removeItem(item)
        
        # Load logs from directory
        logs_dir = os.path.join('fields', self.field_name, 'logs')
        
        if not os.path.exists(logs_dir):
            no_logs_label = QLabel("No logs found.")
            no_logs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.logs_layout.addWidget(no_logs_label)
            return
        
        log_files = sorted([f for f in os.listdir(logs_dir) if f.endswith('.txt')], reverse=True)
        
        if not log_files:
            no_logs_label = QLabel("No logs found.")
            no_logs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.logs_layout.addWidget(no_logs_label)
            return
        
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            log_widget = self.create_log_widget(log_path)
            if log_widget:
                self.logs_layout.addWidget(log_widget)
        
        # Add stretch to push logs to top
        self.logs_layout.addStretch()
    
    def create_log_widget(self, log_path):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        widget.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                background-color: #f9f9f9;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse log content - split by the separator line
            sections = content.strip().split('---\n')
            
            for i, section in enumerate(sections):
                if section.strip():
                    lines = section.strip().split('\n')
                    log_data = {}
                    
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            log_data[key.strip()] = value.strip()
                    
                    # Only create widgets if we have valid data
                    if any(key in log_data for key in ['Date', 'Type', 'Description']):
                        # Display log data
                        if 'Date' in log_data:
                            date_label = QLabel(f"<b>Date:</b> {log_data['Date']}")
                            date_label.setTextFormat(Qt.TextFormat.RichText)
                            layout.addWidget(date_label)
                        
                        if 'Type' in log_data:
                            type_label = QLabel(f"<b>Type:</b> {log_data['Type']}")
                            type_label.setTextFormat(Qt.TextFormat.RichText)
                            layout.addWidget(type_label)
                        
                        if 'Description' in log_data:
                            desc_label = QLabel(f"<b>Description:</b><br>{log_data['Description']}")
                            desc_label.setWordWrap(True)
                            desc_label.setTextFormat(Qt.TextFormat.RichText)
                            layout.addWidget(desc_label)
                        
                        # Add separator between log entries (except for the last one)
                        if i < len(sections) - 1:
                            separator = QFrame()
                            separator.setFrameShape(QFrame.Shape.HLine)
                            separator.setFrameShadow(QFrame.Shadow.Sunken)
                            separator.setLineWidth(1)
                            separator.setFixedHeight(10)
                            layout.addWidget(separator)
        
        except Exception as e:
            error_label = QLabel(f"Error loading log: {str(e)}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
        
        # If no widgets were added, show a message
        if layout.count() == 0:
            no_data_label = QLabel("No log data found in file")
            no_data_label.setStyleSheet("color: #888; font-style: italic;")
            layout.addWidget(no_data_label)
        
        # Make sure the widget has a minimum size
        widget.setMinimumHeight(100)
        
        return widget
