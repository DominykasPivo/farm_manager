from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt

from src.services.field_service import get_all_farmers, add_farmer, update_farmer, delete_farmer


class FarmerManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Ūkininkai')
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        heading = QLabel('Ūkininkai')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        add_btn = QPushButton('Pridėti')
        add_btn.clicked.connect(self._add)
        rename_btn = QPushButton('Pervadinti')
        rename_btn.setProperty('secondary', 'true')
        rename_btn.clicked.connect(self._rename)
        delete_btn = QPushButton('Ištrinti')
        delete_btn.setProperty('danger', 'true')
        delete_btn.clicked.connect(self._delete)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rename_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        close_btn = QPushButton('Uždaryti')
        close_btn.setProperty('secondary', 'true')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        for farmer in get_all_farmers():
            item = QListWidgetItem(farmer['name'])
            item.setData(Qt.ItemDataRole.UserRole, farmer['id'])
            self.list_widget.addItem(item)

    def _selected_item(self):
        return self.list_widget.currentItem()

    def _add(self):
        name, ok = QInputDialog.getText(self, 'Naujas ūkininkas', 'Vardas:')
        if not ok or not name.strip():
            return
        try:
            add_farmer(name.strip())
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko pridėti: {e}')
            return
        self._refresh()

    def _rename(self):
        item = self._selected_item()
        if item is None:
            return
        farmer_id = item.data(Qt.ItemDataRole.UserRole)
        name, ok = QInputDialog.getText(self, 'Pervadinti', 'Naujas vardas:', text=item.text())
        if not ok or not name.strip():
            return
        try:
            update_farmer(farmer_id, name.strip())
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko pervadinti: {e}')
            return
        self._refresh()

    def _delete(self):
        item = self._selected_item()
        if item is None:
            return
        farmer_id = item.data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(
            self, 'Patvirtinkite trynimą',
            f"Ištrinti ūkininką '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_farmer(farmer_id)
        except ValueError as e:
            QMessageBox.warning(self, 'Negalima ištrinti', str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko ištrinti: {e}')
            return
        self._refresh()
