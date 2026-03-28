from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFormLayout, QDoubleSpinBox, QScrollArea, QWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from src.database import (
    get_all_presets, set_preset, FUEL_PRESET_KEY,
    get_all_fertilizers, add_fertilizer, update_fertilizer, delete_fertilizer,
    get_all_seeds,       add_seed,       update_seed,       delete_seed,
    get_all_chemicals,   add_chemical,   update_chemical,   delete_chemical,
)
from src.windows.field_logs import LOG_TYPES


# ── Generic add/edit dialog ───────────────────────────────────────────────────

class _ProductDialog(QDialog):
    def __init__(self, title, price_suffix, placeholder, name='', price=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText(placeholder)
        form.addRow('Pavadinimas:', self.name_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 99999)
        self.price_input.setDecimals(4)
        self.price_input.setSuffix(f' {price_suffix}')
        self.price_input.setValue(price)
        form.addRow('Kaina:', self.price_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton('Išsaugoti')
        ok_btn.clicked.connect(self._validate)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _validate(self):
        if not self.name_input.text().strip():
            self.name_input.setFocus()
            return
        self.accept()

    def result_data(self):
        return self.name_input.text().strip(), self.price_input.value()


# ── Reusable product-list tab ─────────────────────────────────────────────────

class _ProductTabWidget(QWidget):
    """Generic tab: a table of products (name + price) with Add/Edit/Delete."""

    def __init__(self, hint, col_header, price_suffix, dialog_title, placeholder,
                 get_fn, add_fn, update_fn, delete_fn, parent=None):
        super().__init__(parent)
        self._price_suffix = price_suffix
        self._dialog_title = dialog_title
        self._placeholder = placeholder
        self._get_fn = get_fn
        self._add_fn = add_fn
        self._update_fn = update_fn
        self._delete_fn = delete_fn

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(8)

        hint_lbl = QLabel(hint)
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet('color: #666; font-size: 8pt; padding: 0 4px 4px 4px;')
        layout.addWidget(hint_lbl)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(['Pavadinimas', col_header])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 4px; }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background: #c8e6c9; color: #1a1a1a; }
            QHeaderView::section {
                background: #f5f5f5; border: none;
                border-bottom: 1px solid #ddd; padding: 6px 8px;
                font-weight: bold; color: #555;
            }
        """)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton('Pridėti')
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton('Redaguoti')
        edit_btn.setProperty('secondary', 'true')
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton('Trinti')
        del_btn.setProperty('secondary', 'true')
        del_btn.clicked.connect(self._delete)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._load()

    def _load(self):
        products = self._get_fn()
        self._table.setRowCount(len(products))
        price_key = list(products[0].keys())[2] if products else 'price'
        for i, p in enumerate(products):
            name_item = QTableWidgetItem(p['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, p['id'])
            self._table.setItem(i, 0, name_item)
            price_val = p[price_key]
            price_item = QTableWidgetItem(f'{price_val:.4f} {self._price_suffix}')
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 1, price_item)

    def _selected_id(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add(self):
        dlg = _ProductDialog(self._dialog_title, self._price_suffix, self._placeholder, parent=self)
        if dlg.exec():
            name, price = dlg.result_data()
            self._add_fn(name, price)
            self._load()

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            return
        row = self._table.currentRow()
        current_name = self._table.item(row, 0).text()
        try:
            current_price = float(self._table.item(row, 1).text().split()[0])
        except ValueError:
            current_price = 0.0
        dlg = _ProductDialog(self._dialog_title, self._price_suffix, self._placeholder,
                             name=current_name, price=current_price, parent=self)
        if dlg.exec():
            name, price = dlg.result_data()
            self._update_fn(pid, name, price)
            self._load()

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            return
        name = self._table.item(self._table.currentRow(), 0).text()
        reply = QMessageBox.question(
            self, 'Patvirtinti trynimą', f'Ištrinti „{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_fn(pid)
            self._load()


# ── Main dialog ───────────────────────────────────────────────────────────────

class PricePresetsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Kainos nustatymai')
        self.setMinimumSize(420, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Kainos nustatymai')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        tabs = QTabWidget()
        tabs.addTab(self._build_prices_tab(), 'Veiklos kainos')
        tabs.addTab(_ProductTabWidget(
            hint='Trąšų kaina naudojama skaičiuojant Tręšimo sąnaudas (€/kg × kg/ha × ha).',
            col_header='Kaina (€/kg)', price_suffix='€/kg',
            dialog_title='Trąša', placeholder='pvz. KAN, Urea, NPK...',
            get_fn=get_all_fertilizers, add_fn=add_fertilizer,
            update_fn=update_fertilizer, delete_fn=delete_fertilizer,
        ), 'Trąšos')
        tabs.addTab(_ProductTabWidget(
            hint='Sėklų kaina naudojama skaičiuojant Sėjos sąnaudas (€/kg × kg/ha × ha).',
            col_header='Kaina (€/kg)', price_suffix='€/kg',
            dialog_title='Sėkla', placeholder='pvz. Žieminiai kviečiai, Rapsai...',
            get_fn=get_all_seeds, add_fn=add_seed,
            update_fn=update_seed, delete_fn=delete_seed,
        ), 'Sėklos')
        tabs.addTab(_ProductTabWidget(
            hint='Chemijos kaina naudojama skaičiuojant Purškimo sąnaudas (€/l × l/ha × ha).',
            col_header='Kaina (€/l)', price_suffix='€/l',
            dialog_title='Chemija', placeholder='pvz. Roundup, Karate...',
            get_fn=get_all_chemicals, add_fn=add_chemical,
            update_fn=update_chemical, delete_fn=delete_chemical,
        ), 'Chemija')
        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        back_btn = QPushButton('← Grįžti')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self.reject)
        btn_row.addWidget(back_btn)
        btn_row.addStretch()
        save_btn = QPushButton('Išsaugoti kainas')
        save_btn.clicked.connect(self._save_prices)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _build_prices_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 10, 0, 0)
        tab_layout.setSpacing(0)

        hint = QLabel('Bazinė kaina už kiekvieną veiklos tipą. Kuro kaina pridedama automatiškai pagal įvestus litrus.')
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #666; font-size: 8pt; padding: 0 4px 8px 4px;')
        tab_layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        inner = QWidget()
        self._prices_form = QFormLayout(inner)
        self._prices_form.setSpacing(10)
        scroll.setWidget(inner)
        tab_layout.addWidget(scroll)

        presets = get_all_presets()
        self._spinboxes = {}

        fuel_spin = QDoubleSpinBox()
        fuel_spin.setRange(0, 9999)
        fuel_spin.setDecimals(4)
        fuel_spin.setSuffix(' €/l')
        fuel_spin.setValue(presets.get(FUEL_PRESET_KEY, 0.0))
        fuel_label = QLabel('<b>Kuro kaina (€/l):</b>')
        fuel_label.setTextFormat(Qt.TextFormat.RichText)
        self._prices_form.addRow(fuel_label, fuel_spin)
        self._spinboxes[FUEL_PRESET_KEY] = fuel_spin

        sep_lbl = QLabel('Bazinės veiklos kainos:')
        sep_lbl.setStyleSheet('color: #555; font-size: 8pt; padding-top: 6px;')
        self._prices_form.addRow(sep_lbl)

        for log_type in LOG_TYPES:
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0, 9_999_999)
            spinbox.setDecimals(2)
            spinbox.setSuffix(' €')
            spinbox.setValue(presets.get(log_type, 0.0))
            self._prices_form.addRow(f'{log_type}:', spinbox)
            self._spinboxes[log_type] = spinbox

        return tab

    def _save_prices(self):
        for key, spinbox in self._spinboxes.items():
            set_preset(key, spinbox.value())
        self.accept()
