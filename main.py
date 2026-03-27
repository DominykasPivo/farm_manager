import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

from src.database import init_db, migrate_from_files
from src.windows.field_manager_window import Field_Manager

init_db()
if os.path.isdir('fields'):
    migrate_from_files()

APP_STYLE = """
QWidget {
    background-color: #f0f2f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}
QDialog {
    background-color: #ffffff;
}
QPushButton {
    background-color: #2e7d32;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover   { background-color: #388e3c; }
QPushButton:pressed { background-color: #1b5e20; }
QPushButton:disabled { background-color: #a5d6a7; color: #fff; }
QPushButton[danger="true"] { background-color: #c62828; }
QPushButton[danger="true"]:hover { background-color: #e53935; }
QPushButton[secondary="true"] {
    background-color: transparent;
    color: #2e7d32;
    border: 1px solid #2e7d32;
}
QPushButton[secondary="true"]:hover { background-color: #e8f5e9; }
QLineEdit, QComboBox, QTextEdit, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 5px 8px;
    min-height: 24px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
    border-color: #2e7d32;
}
QComboBox::drop-down { border: none; padding-right: 4px; }
QLabel { background: transparent; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #d0d0d0; }
QCalendarWidget QWidget { background: #ffffff; }
QCalendarWidget #qt_calendar_navigationbar {
    background: #f5f5f5;
    min-height: 36px;
    max-height: 36px;
    padding: 0px;
}
QCalendarWidget QToolButton {
    background: transparent;
    color: #1a1a1a;
    border: none;
    padding: 2px 6px;
    min-height: 0;
    min-width: 0;
}
QCalendarWidget QToolButton::menu-indicator { image: none; }
QCalendarWidget QSpinBox {
    background: transparent;
    border: none;
    color: #1a1a1a;
    min-height: 0;
    padding: 0;
}
QCalendarWidget QAbstractItemView {
    selection-background-color: #2e7d32;
    selection-color: #ffffff;
    background: #ffffff;
}
"""


class FarmManager(QWidget):
    def __init__(self):
        super().__init__()
        self.field_manager = None
        self.setWindowTitle('Ūkio valdytojas')
        self.setFixedSize(280, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel('Ūkio valdytojas')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet('font-size: 16px; font-weight: bold; color: #2e7d32;')
        layout.addWidget(title)

        start_btn = QPushButton('Pradėti')
        start_btn.clicked.connect(self.openFieldManager)
        layout.addWidget(start_btn)

    def openFieldManager(self):
        if self.field_manager is not None:
            self.field_manager.close()
        self.field_manager = Field_Manager()
        self.field_manager.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    form = FarmManager()
    form.show()

    app.exec()
