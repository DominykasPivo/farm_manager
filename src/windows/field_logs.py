from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateTimeEdit, QDoubleSpinBox, QVBoxLayout, QGroupBox,
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import QDateTime, Qt

from src.database import (
    get_field, get_field_logs, add_log, get_preset, get_field_cost_summary,
    get_all_fertilizers, get_all_seeds, get_all_chemicals, FUEL_PRESET_KEY,
)

# Each entry: (display label, storage key)
LOG_FIELDS = {
    'Sėja':              [('Veislė', 'veisle'), ('Kiekis (norma)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Tręšimas':          [('Trąšos', 'trasos'), ('Kiekis (kg/ha)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Žolinimas':         [('Veislės', 'veisles'), ('Kuras (Litrai)', 'kuras')],
    'Derliaus nuėmimas':    [('Tonažas (iš 1 ha)', 'tonazas'), ('Kiekis (pristatymo - Tonos)', 'kiekis_k'), ('Kuras (Litrai)', 'kuras')],
    'Derliaus pristatymas': [('Klasė', 'klase'), ('Tonažas (t)', 'tonazas'), ('Kaina (€/t)', 'kaina_t'), ('Kuras (Litrai)', 'kuras')],
    'Lėkščiavimas':      [('Kuras (Litrai)', 'kuras')],
    'Akėjimas':          [('Kuras (Litrai)', 'kuras')],
    'Purškimas':         [('Chemija', 'chemija'), ('Kiekis (norma)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Lyginimas':         [('Kuras (Litrai)', 'kuras')],
    'Krovimo darbai':    [('Kuras (Litrai)', 'kuras')],
    'Žemės dirbimas':    [('Kuras (Litrai)', 'kuras')],
}

LOG_TYPES = list(LOG_FIELDS.keys())

# Maps log_type → (field_key, get_products_fn, price_field, price_suffix, empty_hint)
_PRODUCT_CONFIG = {
    'Tręšimas': ('trasos',  get_all_fertilizers, 'price_per_kg', '€/kg', 'trąšas'),
    'Sėja':     ('veisle',  get_all_seeds,        'price_per_kg', '€/kg', 'sėklas'),
    'Purškimas':('chemija', get_all_chemicals,    'price_per_l',  '€/l',  'chemines medžiagas'),
}

HARVEST_CLASSES = ['Extra', '1-klasė', '2-klasė', '3-klasė', 'Pašariniai']


class AddFieldLogs(QDialog):
    def __init__(self, field_id, parent=None):
        super().__init__(parent)
        self.field_id = field_id
        self._dynamic_inputs = []

        field = get_field(field_id)
        field_name = field['name'] if field else str(field_id)
        self._field_hectares = field['hectares'] if field and field['hectares'] else 0.0
        self.setWindowTitle(f'Naujas įrašas — {field_name}')
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Naujas įrašas')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
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

        # Cost field
        cost_form = QFormLayout()
        cost_form.setSpacing(10)
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 9_999_999)
        self.cost_input.setDecimals(2)
        self.cost_input.setSuffix(' €')
        self.cost_input.setSpecialValueText('—')
        cost_form.addRow('Kaina (€):', self.cost_input)
        layout.addLayout(cost_form)

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

        self._dynamic_inputs = []  # (label, key, widget)
        product_cfg = _PRODUCT_CONFIG.get(log_type)

        for label, key in LOG_FIELDS.get(log_type, []):
            if product_cfg and key == product_cfg[0]:
                _, get_fn, price_field, price_suffix, hint = product_cfg
                widget = QComboBox()
                products = get_fn()
                if products:
                    for p in products:
                        widget.addItem(
                            f'{p["name"]}  ({p[price_field]:.4f} {price_suffix})',
                            userData=p[price_field],
                        )
                else:
                    widget.addItem(f'— pridėkite {hint} nustatymuose —', userData=0.0)
                    widget.setEnabled(False)
                widget.currentIndexChanged.connect(self._recalc_cost)
            elif log_type == 'Derliaus pristatymas' and key == 'klase':
                widget = QComboBox()
                for cls in HARVEST_CLASSES:
                    widget.addItem(cls)
            else:
                widget = QLineEdit()
                if key == 'kuras' or (product_cfg and key == 'kiekis') or \
                        (log_type == 'Derliaus pristatymas' and key in ('tonazas', 'kaina_t')):
                    widget.textChanged.connect(self._recalc_cost)

            self.dyn_form.addRow(f'{label}:', widget)
            self._dynamic_inputs.append((label, key, widget))

        self._recalc_cost()
        self.adjustSize()

    def _recalc_cost(self):
        log_type = self.type_input.currentText()
        fuel_price = get_preset(FUEL_PRESET_KEY)

        fuel_liters = 0.0
        for _, key, widget in self._dynamic_inputs:
            if key == 'kuras' and isinstance(widget, QLineEdit):
                try:
                    fuel_liters = float(widget.text().replace(',', '.').strip())
                except ValueError:
                    pass

        fuel_cost = fuel_liters * fuel_price
        base_price = get_preset(log_type)
        product_cfg = _PRODUCT_CONFIG.get(log_type)

        if product_cfg:
            product_key = product_cfg[0]
            product_price = 0.0
            kiekis = 0.0
            for _, key, widget in self._dynamic_inputs:
                if key == product_key and isinstance(widget, QComboBox):
                    product_price = widget.currentData() or 0.0
                elif key == 'kiekis' and isinstance(widget, QLineEdit):
                    try:
                        kiekis = float(widget.text().replace(',', '.').strip())
                    except ValueError:
                        pass
            product_cost = kiekis * self._field_hectares * product_price
            self.cost_input.setValue(base_price + product_cost + fuel_cost)
        elif log_type == 'Derliaus pristatymas':
            tonazas = 0.0
            kaina_t = 0.0
            for _, key, widget in self._dynamic_inputs:
                if key == 'tonazas' and isinstance(widget, QLineEdit):
                    try:
                        tonazas = float(widget.text().replace(',', '.').strip())
                    except ValueError:
                        pass
                elif key == 'kaina_t' and isinstance(widget, QLineEdit):
                    try:
                        kaina_t = float(widget.text().replace(',', '.').strip())
                    except ValueError:
                        pass
            self.cost_input.setValue(tonazas * kaina_t)
        else:
            self.cost_input.setValue(base_price + fuel_cost)

    def _save_log(self):
        date = self.date_input.dateTime().toString('yyyy-MM-dd HH:mm')
        log_type = self.type_input.currentText()

        parts = []
        for lbl, _key, widget in self._dynamic_inputs:
            if isinstance(widget, QComboBox):
                text = widget.currentText().split('  (')[0].strip()
            else:
                text = widget.text().strip()
            if text and not text.startswith('—'):
                parts.append(f'{lbl}: {text}')
        description = '\n'.join(parts)

        cost = self.cost_input.value() if self.cost_input.value() > 0 else None
        add_log(self.field_id, date, log_type, description, cost)
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
        title.setStyleSheet('font-size: 10pt; font-weight: bold; color: #2e7d32;')
        top_row.addWidget(title)
        top_row.addStretch()
        add_btn = QPushButton('Pridėti įrašą')
        add_btn.clicked.connect(self._open_add_log)
        top_row.addWidget(add_btn)
        layout.addLayout(top_row)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Data ir laikas', 'Tipas', 'Duomenys', 'Kaina (€)'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
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

        # Cost summary section
        self.summary_box = QGroupBox('Sąnaudų suvestinė')
        self.summary_box.setStyleSheet('QGroupBox { font-weight: bold; font-size: 9pt; color: #2e7d32; }')
        self.summary_layout = QVBoxLayout(self.summary_box)
        self.summary_layout.setContentsMargins(10, 6, 10, 6)
        self.summary_layout.setSpacing(4)
        layout.addWidget(self.summary_box)

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
            summary = log['description'].replace('\n', '  |  ')
            self.table.setItem(row, 2, QTableWidgetItem(summary))
            cost = log['cost']
            cost_item = QTableWidgetItem(f'{cost:.2f} €' if cost is not None else '—')
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, cost_item)

        self.table.setSortingEnabled(True)
        self.table.sortItems(0, Qt.SortOrder.DescendingOrder)
        self._refresh_summary()

    def _refresh_summary(self):
        # Clear existing summary widgets
        while self.summary_layout.count():
            child = self.summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        rows = get_field_cost_summary(self.field_id)
        if not rows:
            lbl = QLabel('Nėra sąnaudų įrašų.')
            lbl.setStyleSheet('color: #888;')
            self.summary_layout.addWidget(lbl)
            return

        grand_total = 0.0
        for r in rows:
            row_lbl = QLabel(f'{r["type"]}:  <b>{r["total"]:.2f} €</b>')
            row_lbl.setTextFormat(Qt.TextFormat.RichText)
            self.summary_layout.addWidget(row_lbl)
            grand_total += r['total']

        sep = QLabel('─' * 32)
        sep.setStyleSheet('color: #aaa;')
        self.summary_layout.addWidget(sep)

        total_lbl = QLabel(f'Iš viso:  <b>{grand_total:.2f} €</b>')
        total_lbl.setTextFormat(Qt.TextFormat.RichText)
        total_lbl.setStyleSheet('font-size: 10pt; color: #1b5e20;')
        self.summary_layout.addWidget(total_lbl)
