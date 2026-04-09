from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QComboBox,
)
from PyQt6.QtCore import Qt

from src.database import get_all_rotation_configs, upsert_rotation_config
from src.services.rotation_service import (
    ROTATION_CYCLE, LEGUME_POSITIONS, get_rotation_year, default_position_for_crop
)

_FORECAST_YEARS = 5
_LEGUME_OPTIONS = ['Žirniai', 'Soja']

# Fixed columns before the forecast years
_COL_NAME = 0
_COL_HA = 1
_COL_CURRENT = 2
_COL_POS = 3
_COL_LEGUME = 4
_FORECAST_START = 5


class CropRotationWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Sėjomaina')
        self.setMinimumSize(820, 400)
        self.resize(1000, 480)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel('Sėjomainos prognozė')
        title.setStyleSheet('font-size: 10pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(title)

        self._current_year = date.today().year
        forecast_labels = [str(self._current_year + i + 1) for i in range(_FORECAST_YEARS)]

        col_labels = ['Laukas', 'Ha', 'Dabartinis', 'Pozicija', 'Žirniai/Soja'] + forecast_labels
        self.table = QTableWidget()
        self.table.setColumnCount(len(col_labels))
        self.table.setHorizontalHeaderLabels(col_labels)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(_FORECAST_YEARS):
            hh.setSectionResizeMode(_FORECAST_START + i, QHeaderView.ResizeMode.ResizeToContents)

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

        bottom_row = QHBoxLayout()
        back_btn = QPushButton('← Grįžti')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self.close)
        bottom_row.addWidget(back_btn)
        bottom_row.addStretch()
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._save_all)
        bottom_row.addWidget(save_btn)
        layout.addLayout(bottom_row)

        self._rows = []  # list of dicts with field data
        self._load()

    def _load(self):
        configs = get_all_rotation_configs()
        self._rows = []

        self.table.setRowCount(len(configs))
        self.table.blockSignals(True)

        for row_idx, cfg in enumerate(configs):
            field_id = cfg['field_id']
            name = cfg['name']
            hectares = cfg['hectares'] or 0.0
            current_crop = cfg['type'] or ''

            # Determine starting position: use saved config if exists, else guess from crop type
            saved_pos = cfg['position']
            # If the config came from a LEFT JOIN with no existing row, position defaults to 1
            # Try to auto-detect a sensible default if it's the first time (no explicit save)
            position = saved_pos if saved_pos else default_position_for_crop(current_crop)
            legume_choice = cfg['legume_choice'] or 'Žirniai'

            # Store row data
            self._rows.append({
                'field_id': field_id,
                'position': position,
                'legume_choice': legume_choice,
            })

            # Laukas
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, _COL_NAME, name_item)

            # Ha
            ha_item = QTableWidgetItem(f'{hectares:.2f}')
            ha_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ha_item.setFlags(ha_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, _COL_HA, ha_item)

            # Dabartinis
            cur_item = QTableWidgetItem(current_crop)
            cur_item.setFlags(cur_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, _COL_CURRENT, cur_item)

            # Pozicija — QSpinBox
            spin = QSpinBox()
            spin.setMinimum(1)
            spin.setMaximum(9)
            spin.setValue(position)
            spin.setProperty('row', row_idx)
            spin.valueChanged.connect(self._on_position_changed)
            self.table.setCellWidget(row_idx, _COL_POS, spin)

            # Žirniai/Soja — QComboBox
            combo = QComboBox()
            for opt in _LEGUME_OPTIONS:
                combo.addItem(opt)
            combo.setCurrentText(legume_choice)
            combo.setProperty('row', row_idx)
            combo.currentTextChanged.connect(self._on_legume_changed)
            self.table.setCellWidget(row_idx, _COL_LEGUME, combo)

            # Forecast columns
            self._update_forecast_row(row_idx, position, legume_choice)

        self.table.blockSignals(False)

    def _update_forecast_row(self, row_idx: int, position: int, legume_choice: str):
        for offset in range(1, _FORECAST_YEARS + 1):
            crop = get_rotation_year(position, offset, legume_choice)
            item = QTableWidgetItem(crop)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, _FORECAST_START + offset - 1, item)

    def _on_position_changed(self, value: int):
        row_idx = self.sender().property('row')
        self._rows[row_idx]['position'] = value
        legume = self._rows[row_idx]['legume_choice']
        self._update_forecast_row(row_idx, value, legume)

    def _on_legume_changed(self, text: str):
        row_idx = self.sender().property('row')
        self._rows[row_idx]['legume_choice'] = text
        position = self._rows[row_idx]['position']
        self._update_forecast_row(row_idx, position, text)

    def _save_all(self):
        for r in self._rows:
            upsert_rotation_config(r['field_id'], r['position'], r['legume_choice'])
