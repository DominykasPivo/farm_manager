from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QFrame,
                             QListWidget, QListWidgetItem, QLineEdit)
from PyQt6.QtCore import Qt

from src.windows.field_manager import AddFieldWindow, ViewFieldWindow
from src.windows.map_window import MapWindow
from src.windows.price_presets import PricePresetsDialog
from src.windows.cost_report import CostReportWindow
from src.services.field_service import get_all_fields, CROP_TYPES


class Field_Manager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Laukų valdymas')
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        add_btn = QPushButton('Pridėti lauką')
        add_btn.clicked.connect(self.open_add_field_window)
        layout.addWidget(add_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Ieškoti lauko...')
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.refresh_fields)
        layout.addWidget(self.search_box)

        self.type_filter_box = QComboBox()
        self.type_filter_box.addItem('Visi tipai', userData=None)
        for ct in CROP_TYPES:
            self.type_filter_box.addItem(ct, userData=ct)
        self.type_filter_box.currentIndexChanged.connect(self.refresh_fields)
        layout.addWidget(self.type_filter_box)

        self.all_fields_list = QListWidget()
        self.all_fields_list.setMinimumHeight(150)
        self.all_fields_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.all_fields_list)

        btn_row = QHBoxLayout()
        view_btn = QPushButton('Peržiūrėti')
        view_btn.clicked.connect(self.view_selected_field)
        map_btn = QPushButton('Žemėlapis')
        map_btn.setProperty('secondary', 'true')
        map_btn.clicked.connect(self.open_map)
        btn_row.addWidget(view_btn)
        btn_row.addWidget(map_btn)
        layout.addLayout(btn_row)

        self.refresh_fields()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        presets_btn = QPushButton('Kainos nustatymai')
        presets_btn.setProperty('secondary', 'true')
        presets_btn.clicked.connect(self._open_presets)
        layout.addWidget(presets_btn)

        report_btn = QPushButton('Sąnaudų ataskaita')
        report_btn.setProperty('secondary', 'true')
        report_btn.clicked.connect(self._open_report)
        layout.addWidget(report_btn)

        layout.addStretch()

        self.view_field_window = None
        self.map_window = None
        self.cost_report_window = None

        self.adjustSize()

    def refresh_fields(self):
        search = self.search_box.text().strip().lower()
        selected_type = self.type_filter_box.currentData()
        fields = get_all_fields()
        if selected_type:
            fields = [f for f in fields if f['type'] == selected_type]
        if search:
            fields = [f for f in fields if search in f['name'].lower()]
        self.all_fields_list.clear()
        if not fields:
            item = QListWidgetItem('Nėra laukų')
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.all_fields_list.addItem(item)
        else:
            for field in fields:
                label = ('✓  ' if field['harvested'] else '') + field['name']
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, field['id'])
                self.all_fields_list.addItem(item)

    def open_add_field_window(self):
        add_window = AddFieldWindow()
        add_window.exec()
        self.refresh_fields()

    def _on_item_double_clicked(self, item):
        field_id = item.data(Qt.ItemDataRole.UserRole)
        if field_id is not None:
            self.view_field_window = ViewFieldWindow(field_id, parent=self, main_window=self)
            self.view_field_window.show()

    def view_selected_field(self):
        item = self.all_fields_list.currentItem()
        if item is None:
            return
        field_id = item.data(Qt.ItemDataRole.UserRole)
        if field_id is not None:
            self.view_field_window = ViewFieldWindow(field_id, parent=self, main_window=self)
            self.view_field_window.show()

    def open_map(self):
        self.map_window = MapWindow(main_window=self)
        self.map_window.show()


    def _open_presets(self):
        dialog = PricePresetsDialog(self)
        dialog.exec()

    def _open_report(self):
        self.cost_report_window = CostReportWindow(self)
        self.cost_report_window.show()
