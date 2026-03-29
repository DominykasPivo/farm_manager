from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDateTimeEdit, QDoubleSpinBox, QFormLayout,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QMessageBox, QInputDialog,
)
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QFont

from src.services.vehicle_service import (
    get_all_vehicles, add_vehicle, delete_vehicle,
    get_vehicle_logs, add_vehicle_log, delete_vehicle_log,
    get_all_vehicle_cost_summary,
)


class AddVehicleLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Naujas įrašas')
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Naujas išlaidų įrašas')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(10)

        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.date_input.setDisplayFormat('yyyy-MM-dd HH:mm')
        self.date_input.setCalendarPopup(True)
        form.addRow('Data:', self.date_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText('pvz. Keitė alyvą, Pakeitė padangą...')
        form.addRow('Aprašymas:', self.desc_input)

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 9_999_999)
        self.cost_input.setDecimals(2)
        self.cost_input.setSuffix(' €')
        form.addRow('Kaina (€):', self.cost_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._validate)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _validate(self):
        if not self.desc_input.text().strip():
            self.desc_input.setFocus()
            return
        self.accept()

    def result_data(self):
        return (
            self.date_input.dateTime().toString('yyyy-MM-dd HH:mm'),
            self.desc_input.text().strip(),
            self.cost_input.value(),
        )


class VehicleExpensesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Transporto išlaidos')
        self.setMinimumSize(820, 500)
        self.resize(1000, 580)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        self._current_vehicle_id = None  # None = "Kita"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        heading_row = QHBoxLayout()
        heading = QLabel('Transporto išlaidos')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        heading_row.addWidget(heading)
        heading_row.addStretch()
        total_btn = QPushButton('Bendra suvestinė')
        total_btn.setProperty('secondary', 'true')
        total_btn.clicked.connect(self._open_total_summary)
        heading_row.addWidget(total_btn)
        outer.addLayout(heading_row)

        main_row = QHBoxLayout()
        main_row.setSpacing(12)
        outer.addLayout(main_row)

        # ── Left panel ────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(220)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(6)

        left_title = QLabel('Transporto priemonės')
        left_title.setStyleSheet('font-weight: bold; color: #555; font-size: 9pt;')
        left_layout.addWidget(left_title)

        self.vehicle_list = QListWidget()
        self.vehicle_list.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 4px; }
            QListWidget::item { padding: 5px 8px; }
            QListWidget::item:selected { background: #c8e6c9; color: #1a1a1a; }
        """)
        self.vehicle_list.currentRowChanged.connect(self._on_vehicle_selected)
        left_layout.addWidget(self.vehicle_list)

        veh_btn_row = QHBoxLayout()
        add_veh_btn = QPushButton('Pridėti')
        add_veh_btn.clicked.connect(self._add_vehicle)
        self.del_veh_btn = QPushButton('Trinti')
        self.del_veh_btn.setProperty('secondary', 'true')
        self.del_veh_btn.setEnabled(False)
        self.del_veh_btn.clicked.connect(self._delete_vehicle)
        veh_btn_row.addWidget(add_veh_btn)
        veh_btn_row.addWidget(self.del_veh_btn)
        left_layout.addLayout(veh_btn_row)

        main_row.addWidget(left)

        # ── Right panel ───────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        top_row = QHBoxLayout()
        self.panel_title = QLabel('Kita')
        self.panel_title.setStyleSheet('font-size: 10pt; font-weight: bold; color: #2e7d32;')
        top_row.addWidget(self.panel_title)
        top_row.addStretch()
        add_log_btn = QPushButton('Pridėti įrašą')
        add_log_btn.clicked.connect(self._add_log)
        top_row.addWidget(add_log_btn)
        self.del_log_btn = QPushButton('Trinti įrašą')
        self.del_log_btn.setProperty('danger', 'true')
        self.del_log_btn.setEnabled(False)
        self.del_log_btn.clicked.connect(self._delete_log)
        top_row.addWidget(self.del_log_btn)
        top_row.addSpacing(8)
        right_layout.addLayout(top_row)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(['Data ir laikas', 'Aprašymas', 'Kaina (€)'])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSortingEnabled(True)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background: #c8e6c9; color: #1a1a1a; }
            QHeaderView::section {
                background: #f5f5f5; border: none;
                border-bottom: 1px solid #ddd; padding: 6px 8px;
                font-weight: bold; color: #555;
            }
        """)
        self.log_table.itemSelectionChanged.connect(
            lambda: self.del_log_btn.setEnabled(bool(self.log_table.selectedItems()))
        )
        right_layout.addWidget(self.log_table)

        self.summary_box = QGroupBox('Suvestinė')
        self.summary_box.setStyleSheet('QGroupBox { font-weight: bold; font-size: 9pt; color: #2e7d32; }')
        self.summary_layout = QVBoxLayout(self.summary_box)
        self.summary_layout.setContentsMargins(10, 6, 10, 6)
        self.summary_layout.setSpacing(4)
        right_layout.addWidget(self.summary_box)

        main_row.addWidget(right)

        bottom_row = QHBoxLayout()
        back_btn = QPushButton('← Grįžti')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self.close)
        bottom_row.addWidget(back_btn)
        bottom_row.addStretch()
        outer.addLayout(bottom_row)

        self._load_vehicles()

    # ── Vehicle list ──────────────────────────────────────────────────

    def _load_vehicles(self):
        self.vehicle_list.blockSignals(True)
        self.vehicle_list.clear()

        kita_item = QListWidgetItem('Kita')
        font = QFont()
        font.setItalic(True)
        kita_item.setFont(font)
        kita_item.setData(Qt.ItemDataRole.UserRole, None)
        self.vehicle_list.addItem(kita_item)

        for v in get_all_vehicles():
            item = QListWidgetItem(v['name'])
            item.setData(Qt.ItemDataRole.UserRole, v['id'])
            self.vehicle_list.addItem(item)

        self.vehicle_list.blockSignals(False)

        # restore selection
        target_id = self._current_vehicle_id
        for i in range(self.vehicle_list.count()):
            if self.vehicle_list.item(i).data(Qt.ItemDataRole.UserRole) == target_id:
                self.vehicle_list.setCurrentRow(i)
                return
        self.vehicle_list.setCurrentRow(0)

    def _on_vehicle_selected(self, row):
        if row < 0:
            return
        item = self.vehicle_list.item(row)
        if item is None:
            return
        self._current_vehicle_id = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        self.panel_title.setText(name)
        self.del_veh_btn.setEnabled(self._current_vehicle_id is not None)
        self._load_logs()

    def _add_vehicle(self):
        name, ok = QInputDialog.getText(self, 'Pridėti transporto priemonę', 'Pavadinimas:')
        name = name.strip()
        if not ok or not name:
            return
        try:
            add_vehicle(name)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko pridėti: {e}')
            return
        self._load_vehicles()

    def _delete_vehicle(self):
        vid = self._current_vehicle_id
        if vid is None:
            return
        row = self.vehicle_list.currentRow()
        name = self.vehicle_list.item(row).text()
        confirm = QMessageBox.question(
            self, 'Patvirtinti trynimą',
            f'Ištrinti „{name}" ir visus jos įrašus?\nŠio veiksmo negalima atšaukti.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_vehicle(vid)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko ištrinti: {e}')
            return
        self._current_vehicle_id = None
        self._load_vehicles()

    # ── Log table ─────────────────────────────────────────────────────

    def _load_logs(self):
        logs = get_vehicle_logs(self._current_vehicle_id)
        self.log_table.setSortingEnabled(False)
        self.log_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            date_item = QTableWidgetItem(log['date'])
            date_item.setData(Qt.ItemDataRole.UserRole, log['id'])
            self.log_table.setItem(row, 0, date_item)
            self.log_table.setItem(row, 1, QTableWidgetItem(log['description']))
            cost_item = QTableWidgetItem(f"{log['cost']:.2f} €")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.log_table.setItem(row, 2, cost_item)
        self.log_table.setSortingEnabled(True)
        self.log_table.sortItems(0, Qt.SortOrder.DescendingOrder)
        self._refresh_summary()

    def _add_log(self):
        dlg = AddVehicleLogDialog(self)
        if dlg.exec():
            date, description, cost = dlg.result_data()
            try:
                add_vehicle_log(self._current_vehicle_id, date, description, cost)
            except Exception as e:
                QMessageBox.warning(self, 'Klaida', f'Nepavyko išsaugoti įrašo: {e}')
                return
            self._load_logs()

    def _delete_log(self):
        row = self.log_table.currentRow()
        if row < 0:
            return
        log_id = self.log_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        date = self.log_table.item(row, 0).text()
        desc = self.log_table.item(row, 1).text()
        confirm = QMessageBox.question(
            self, 'Patvirtinti trynimą',
            f'Ištrinti įrašą „{desc}" ({date})?\nŠio veiksmo negalima atšaukti.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_vehicle_log(log_id)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko ištrinti įrašo: {e}')
            return
        self._load_logs()

    # ── Summary ───────────────────────────────────────────────────────

    def _refresh_summary(self):
        while self.summary_layout.count():
            child = self.summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        logs = get_vehicle_logs(self._current_vehicle_id)
        total = sum(log['cost'] for log in logs)

        if not logs:
            lbl = QLabel('Nėra įrašų.')
            lbl.setStyleSheet('color: #888;')
            self.summary_layout.addWidget(lbl)
            return

        total_lbl = QLabel(f'Iš viso:  <b>{total:.2f} €</b>')
        total_lbl.setTextFormat(Qt.TextFormat.RichText)
        total_lbl.setStyleSheet('font-size: 10pt; color: #1b5e20;')
        self.summary_layout.addWidget(total_lbl)

    def _open_total_summary(self):
        rows = get_all_vehicle_cost_summary()

        dlg = QDialog(self)
        dlg.setWindowTitle('Bendra suvestinė')
        dlg.setMinimumWidth(360)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel('Visos transporto išlaidos')
        title.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Transporto priemonė', 'Suma (€)'])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 4px; gridline-color: #eee; }
            QTableWidget::item { padding: 4px 8px; }
            QHeaderView::section {
                background: #f5f5f5; border: none;
                border-bottom: 1px solid #ddd; padding: 6px 8px;
                font-weight: bold; color: #555;
            }
        """)

        table.setRowCount(len(rows))
        grand_total = 0.0
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r['name']))
            cost_item = QTableWidgetItem(f"{r['total']:.2f} €")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(i, 1, cost_item)
            grand_total += r['total']

        layout.addWidget(table)

        total_lbl = QLabel(f'Iš viso:  <b>{grand_total:.2f} €</b>')
        total_lbl.setTextFormat(Qt.TextFormat.RichText)
        total_lbl.setStyleSheet('font-size: 10pt; color: #1b5e20; padding: 4px 0;')
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_lbl)

        close_btn = QPushButton('Uždaryti')
        close_btn.setProperty('secondary', 'true')
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        if not rows:
            table.hide()
            no_data = QLabel('Nėra įrašų.')
            no_data.setStyleSheet('color: #888;')
            layout.insertWidget(2, no_data)

        dlg.exec()
