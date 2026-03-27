from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateTimeEdit, QVBoxLayout,
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import QDateTime, Qt

from src.database import get_field, get_field_logs, add_log

# Each entry: (display label, storage key)
LOG_FIELDS = {
    'Sėja':              [('Veislė', 'veisle'), ('Kiekis (norma)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Tręšimas':          [('Trąšos', 'trasos'), ('Kiekis (kg/ha)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Žolinimas':         [('Veislės', 'veisles'), ('Kuras (Litrai)', 'kuras')],
    'Derliaus nuėmimas': [('Tonažas (iš 1 ha)', 'tonazas'), ('Kuras (Litrai)', 'kuras')],
    'Lėkščiavimas':      [('Kuras (Litrai)', 'kuras')],
    'Akėjimas':          [('Kuras (Litrai)', 'kuras')],
    'Purškimas':         [('Chemija', 'chemija'), ('Kiekis (norma)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Lyginimas':         [('Kuras (Litrai)', 'kuras')],
    'Krovimo darbai':    [('Kuras (Litrai)', 'kuras')],
    'Žemės dirbimas':    [('Kuras (Litrai)', 'kuras')],
}

LOG_TYPES = list(LOG_FIELDS.keys())


class AddFieldLogs(QDialog):
    def __init__(self, field_id, parent=None):
        super().__init__(parent)
        self.field_id = field_id
        self._dynamic_inputs = []

        field = get_field(field_id)
        field_name = field['name'] if field else str(field_id)
        self.setWindowTitle(f'Naujas įrašas — {field_name}')
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Naujas įrašas')
        heading.setStyleSheet('font-size: 15px; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        # Fixed fields
        fixed_form = QFormLayout()
        fixed_form.setSpacing(10)

        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.date_input.setDisplayFormat('yyyy-MM-dd HH:mm')
        self.date_input.setCalendarPopup(True)

        self.type_input = QComboBox()
        self.type_input.addItems(LOG_TYPES)

        fixed_form.addRow('Data:', self.date_input)
        fixed_form.addRow('Tipas:', self.type_input)
        layout.addLayout(fixed_form)

        # Dynamic fields (rebuilt when type changes)
        self.dyn_form = QFormLayout()
        self.dyn_form.setSpacing(10)
        layout.addLayout(self.dyn_form)

        self._rebuild_fields(LOG_TYPES[0])
        self.type_input.currentTextChanged.connect(self._rebuild_fields)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._save_log)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _rebuild_fields(self, log_type):
        while self.dyn_form.rowCount() > 0:
            self.dyn_form.removeRow(0)

        self._dynamic_inputs = []
        for label, _key in LOG_FIELDS.get(log_type, []):
            inp = QLineEdit()
            self.dyn_form.addRow(f'{label}:', inp)
            self._dynamic_inputs.append((label, inp))

        self.adjustSize()

    def _save_log(self):
        date = self.date_input.dateTime().toString('yyyy-MM-dd HH:mm')
        log_type = self.type_input.currentText()

        parts = [f'{lbl}: {inp.text().strip()}' for lbl, inp in self._dynamic_inputs
                 if inp.text().strip()]
        description = '\n'.join(parts)

        add_log(self.field_id, date, log_type, description)
        self.accept()


class ViewLogsWindow(QWidget):
    def __init__(self, field_id, parent=None):
        super().__init__(parent)
        self.field_id = field_id

        field = get_field(field_id)
        field_name = field['name'] if field else str(field_id)
        self.setWindowTitle(f'Žurnalas — {field_name}')
        self.setMinimumSize(700, 460)
        self.resize(860, 520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        title = QLabel(f'Veiklos žurnalas: {field_name}')
        title.setStyleSheet('font-size: 14px; font-weight: bold; color: #2e7d32;')
        top_row.addWidget(title)
        top_row.addStretch()
        add_btn = QPushButton('Pridėti įrašą')
        add_btn.clicked.connect(self._open_add_log)
        top_row.addWidget(add_btn)
        layout.addLayout(top_row)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Data ir laikas', 'Tipas', 'Duomenys'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background: #c8e6c9; color: #1a1a1a; }
            QHeaderView::section {
                background: #f5f5f5;
                border: none;
                border-bottom: 1px solid #ddd;
                padding: 6px 8px;
                font-weight: bold;
                color: #555;
            }
        """)
        layout.addWidget(self.table)

        self._load_logs()

    def _open_add_log(self):
        dialog = AddFieldLogs(self.field_id, self)
        if dialog.exec():
            self._load_logs()

    def _load_logs(self):
        logs = get_field_logs(self.field_id)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(log['date']))
            self.table.setItem(row, 1, QTableWidgetItem(log['type']))
            # Show multi-line description as single line summary
            summary = log['description'].replace('\n', '  |  ')
            self.table.setItem(row, 2, QTableWidgetItem(summary))

        self.table.setSortingEnabled(True)
        self.table.sortItems(0, Qt.SortOrder.DescendingOrder)
