from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate

from src.database import get_all_fields_cost_summary


class CostReportWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Sąnaudų ataskaita')
        self.setMinimumSize(600, 480)
        self.resize(720, 540)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel('Sąnaudų ataskaita')
        title.setStyleSheet('font-size: 10pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(title)

        # Date filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel('Nuo:'))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_from.setDisplayFormat('yyyy-MM-dd')
        filter_row.addWidget(self.date_from)

        filter_row.addWidget(QLabel('Iki:'))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat('yyyy-MM-dd')
        filter_row.addWidget(self.date_to)

        apply_btn = QPushButton('Filtruoti')
        apply_btn.clicked.connect(self._load)
        filter_row.addWidget(apply_btn)

        clear_btn = QPushButton('Visi įrašai')
        clear_btn.setProperty('secondary', 'true')
        clear_btn.clicked.connect(self._load_all)
        filter_row.addWidget(clear_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Laukas', 'Veiklos tipas', 'Suma (€)'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
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

        bottom_row = QHBoxLayout()
        back_btn = QPushButton('← Grįžti')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self.close)
        bottom_row.addWidget(back_btn)
        bottom_row.addStretch()
        self.total_label = QLabel('Iš viso: 0.00 €')
        self.total_label.setStyleSheet('font-size: 10pt; font-weight: bold; color: #1b5e20; padding: 4px 0;')
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bottom_row.addWidget(self.total_label)
        layout.addLayout(bottom_row)

        self._load_all()

    def _load_all(self):
        self._populate(get_all_fields_cost_summary())

    def _load(self):
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        self._populate(get_all_fields_cost_summary(date_from, date_to))

    def _populate(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))

        grand_total = 0.0
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r['field_name']))
            self.table.setItem(i, 1, QTableWidgetItem(r['type']))
            total = r['total'] or 0.0
            cost_item = QTableWidgetItem(f'{total:.2f} €')
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 2, cost_item)
            grand_total += total

        self.table.setSortingEnabled(True)
        self.total_label.setText(f'Iš viso: <b>{grand_total:.2f} €</b>')
        self.total_label.setTextFormat(Qt.TextFormat.RichText)
