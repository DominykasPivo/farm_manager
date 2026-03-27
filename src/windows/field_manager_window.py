from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLabel, QFrame)
from PyQt6.QtCore import Qt

from src.windows.field_manager import AddFieldWindow, ViewFieldWindow
from src.windows.map_window import MapWindow
from src.database import get_all_fields


class Field_Manager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Laukų valdymas')
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel('Laukų valdymas')
        title.setStyleSheet('font-size: 15px; font-weight: bold; color: #2e7d32;')
        layout.addWidget(title)

        add_btn = QPushButton('Pridėti lauką')
        add_btn.clicked.connect(self.open_add_field_window)
        layout.addWidget(add_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        select_label = QLabel('Pasirinkite lauką:')
        select_label.setStyleSheet('color: #555; font-size: 12px;')
        layout.addWidget(select_label)

        self.all_fields_box = QComboBox()
        layout.addWidget(self.all_fields_box)
        self.refresh_fields()

        btn_row = QHBoxLayout()
        view_btn = QPushButton('Peržiūrėti')
        view_btn.clicked.connect(self.view_selected_field)
        map_btn = QPushButton('Žemėlapis')
        map_btn.setProperty('secondary', 'true')
        map_btn.clicked.connect(self.open_map)
        btn_row.addWidget(view_btn)
        btn_row.addWidget(map_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        self.add_field_window = None
        self.view_field_window = None
        self.map_window = None

        self.adjustSize()

    def refresh_fields(self):
        self.all_fields_box.clear()
        fields = get_all_fields()
        if not fields:
            self.all_fields_box.addItem('Nėra laukų')
        else:
            for field in fields:
                self.all_fields_box.addItem(field['name'], userData=field['id'])

    def open_add_field_window(self):
        add_window = AddFieldWindow()
        add_window.exec()
        self.refresh_fields()

    def view_selected_field(self):
        field_id = self.all_fields_box.currentData()
        if field_id is not None:
            self.view_field_window = ViewFieldWindow(field_id, parent=self, main_window=self)
            self.view_field_window.show()

    def open_map(self):
        self.map_window = MapWindow(main_window=self)
        self.map_window.show()
