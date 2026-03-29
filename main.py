import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import qInstallMessageHandler


def _qt_msg_handler(msg_type, _context, message):
    if 'setPointSize' in message:
        return
    print(message, file=sys.stderr)

qInstallMessageHandler(_qt_msg_handler)

from src.database import init_db, migrate_from_files
from src.windows.field_manager_window import Field_Manager

init_db()
if os.path.isdir('fields'):
    migrate_from_files()

APP_STYLE = """
QWidget {
    background-color: #f0f2f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
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
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    selection-background-color: #c8e6c9;
    selection-color: #1a1a1a;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    padding: 5px 8px;
    min-height: 24px;
    color: #1a1a1a;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #e8f5e9;
    color: #1a1a1a;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #c8e6c9;
    color: #1a1a1a;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f5f7f5;
    gridline-color: #eee;
}
QTableWidget::item { color: #1a1a1a; }
QTableWidget::item:selected {
    background-color: #c8e6c9;
    color: #1a1a1a;
}
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(APP_STYLE)

    window = Field_Manager()
    window.show()

    app.exec()
