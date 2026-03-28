import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy,
    QSpacerItem, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.database import (
    add_field, delete_field, get_field,
    get_field_logs, get_field_polygons, update_field,
)
from src.windows.field_logs import ViewLogsWindow

FIELD_THUMB_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * { margin: 0; padding: 0; }
    #map { width: 100%; height: 100vh; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map', {
      zoomControl: false, attributionControl: false,
      dragging: false, scrollWheelZoom: false,
      doubleClickZoom: false, boxZoom: false, keyboard: false
    }).setView([55.17, 23.88], 7);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19 }
    ).addTo(map);

    function loadPolygons(polygons) {
      var layers = [];
      polygons.forEach(function(p) {
        var layer = L.geoJSON(JSON.parse(p.coordinates), {
          style: { color: '#ff7800', weight: 2, fillColor: '#ff7800', fillOpacity: 0.25 }
        }).addTo(map);
        layers.push(layer);
      });
      if (layers.length > 0) {
        map.fitBounds(L.featureGroup(layers).getBounds().pad(0.25));
      }
    }
  </script>
</body>
</html>
"""

CROP_TYPES = ['Z. mieziai', 'kvieciai', 'Z. kvieciai', 'Rapsas', 'Z. rapsas']


class AddFieldFromMapDialog(QDialog):
    """Triggered after drawing a polygon on the map. Creates the field record."""

    def __init__(self, geojson: str, parent=None):
        super().__init__(parent)
        self.geojson = geojson
        self.saved_field_id = None
        self.setWindowTitle('Naujas laukas')
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Naujas laukas')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(10)
        self.name_input = QLineEdit()
        self.hectares_input = QLineEdit()
        self.field_type = QComboBox()
        self.field_type.addItems(CROP_TYPES)
        form.addRow('Pavadinimas:', self.name_input)
        form.addRow('Hektarai:', self.hectares_input)
        form.addRow('Tipas:', self.field_type)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            return
        try:
            hectares = float(self.hectares_input.text().strip())
        except ValueError:
            hectares = 0.0
        field_type = self.field_type.currentText()
        try:
            self.saved_field_id = add_field(name, hectares, field_type, None)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko išsaugoti lauko: {e}')
            return
        self.accept()


class AddFieldWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pridėti lauką')
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Pridėti lauką')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(10)
        self.name_input = QLineEdit()
        self.hectares_input = QLineEdit()
        self.field_type = QComboBox()
        self.field_type.addItems(CROP_TYPES)

        form.addRow('Pavadinimas:', self.name_input)
        form.addRow('Hektarai:', self.hectares_input)
        form.addRow('Tipas:', self.field_type)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._save_field)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save_field(self):
        name = self.name_input.text().strip()
        if not name:
            return
        try:
            hectares = float(self.hectares_input.text().strip())
        except ValueError:
            hectares = 0.0
        field_type = self.field_type.currentText()

        try:
            add_field(name, hectares, field_type, None)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko išsaugoti lauko: {e}')
            return

        self.accept()


class ViewFieldWindow(QWidget):
    def __init__(self, field_id, parent=None, main_window=None):
        super().__init__()
        self.field_id = field_id
        self.parent = parent
        self.main_window = main_window

        field = get_field(field_id)
        if field is None:
            self.close()
            return

        self.field_name = field['name']
        self.setWindowTitle(f'Laukas — {field["name"]}')
        self.setMinimumSize(900, 520)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        # ── Left column ──────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(10)

        name_label = QLabel(field['name'])
        name_label.setStyleSheet('font-size: 15pt; font-weight: bold; color: #1a1a1a;')
        left.addWidget(name_label)

        form = QFormLayout()
        form.setSpacing(8)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(self._meta_label('Hektarai:'), QLabel(str(field['hectares'] or '—')))
        form.addRow(self._meta_label('Tipas:'),    QLabel(field['type'] or '—'))
        left.addLayout(form)

        # ── Mini activity log ─────────────────────────────────────────
        activity_label = QLabel('Paskutinis veikimas')
        activity_label.setStyleSheet('color: #666; font-size: 8pt; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px;')
        left.addWidget(activity_label)

        self.mini_log = QTableWidget()
        self.mini_log.setColumnCount(2)
        self.mini_log.setHorizontalHeaderLabels(['Data ir laikas', 'Tipas'])
        self.mini_log.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mini_log.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mini_log.verticalHeader().setVisible(False)
        self.mini_log.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.mini_log.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.mini_log.setAlternatingRowColors(True)
        self.mini_log.setMaximumHeight(148)
        self.mini_log.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
            }
            QTableWidget::item { padding: 3px 7px; }
            QHeaderView::section {
                background: #f5f5f5;
                border: none;
                border-bottom: 1px solid #ddd;
                padding: 4px 7px;
                font-weight: bold;
                color: #555;
            }
        """)
        left.addWidget(self.mini_log)
        self._load_mini_logs()

        left.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        back_btn = QPushButton('Atgal')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self._go_back)

        edit_btn = QPushButton('Redaguoti')
        edit_btn.clicked.connect(self._edit_field)

        boundary_btn = QPushButton('Braižyti ribą')
        boundary_btn.setProperty('secondary', 'true')
        boundary_btn.clicked.connect(self._open_draw_boundary)

        logs_btn = QPushButton('Žurnalas')
        logs_btn.clicked.connect(self._view_logs)

        del_btn = QPushButton('Ištrinti')
        del_btn.setProperty('danger', 'true')
        del_btn.clicked.connect(self._remove_field)

        for btn in (back_btn, edit_btn, boundary_btn, logs_btn, del_btn):
            btn_row.addWidget(btn)
        left.addLayout(btn_row)

        root.addLayout(left, stretch=1)

        # ── Right column: satellite thumbnail ────────────────────────
        polys = get_field_polygons(field_id)
        if polys:
            self.thumb = QWebEngineView()
            self.thumb.setMinimumSize(420, 300)
            self.thumb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.thumb.setHtml(FIELD_THUMB_HTML)
            self.thumb.loadFinished.connect(
                lambda ok: self._load_thumb_polygons() if ok else None
            )
            root.addWidget(self.thumb, stretch=1)
        else:
            placeholder = QLabel('Riba nebrėžta')
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet('color: #999; font-style: italic; font-size: 10pt;')
            placeholder.setMinimumWidth(300)
            root.addWidget(placeholder, stretch=1)

    def _meta_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet('color: #666; font-size: 9pt;')
        return lbl

    def _load_thumb_polygons(self):
        polys = get_field_polygons(self.field_id)
        self.thumb.page().runJavaScript(f"loadPolygons({json.dumps(polys)})")

    def _open_draw_boundary(self):
        from src.windows.map_window import MapWindow
        self.hide()
        self._boundary_map = MapWindow(
            assign_to_field_id=self.field_id,
            on_polygon_saved=self._on_boundary_saved,
            main_window=self.main_window,
        )
        self._boundary_map.show()

    def _on_boundary_saved(self):
        self.close()
        new_view = ViewFieldWindow(self.field_id, parent=None, main_window=self.main_window)
        if self.main_window:
            self.main_window.view_field_window = new_view
        new_view.show()

    def _load_mini_logs(self):
        logs = get_field_logs(self.field_id)[:5]
        self.mini_log.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.mini_log.setItem(row, 0, QTableWidgetItem(log['date']))
            self.mini_log.setItem(row, 1, QTableWidgetItem(log['type']))

    def _view_logs(self):
        self.logs_window = ViewLogsWindow(self.field_id, self)
        self.logs_window.show()

    def _remove_field(self):
        confirm = QMessageBox.question(
            self, 'Patvirtinkite trynimą',
            f"Ištrinti lauką '{self.field_name}'? Šio veiksmo negalima atšaukti.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_field(self.field_id)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko ištrinti lauko: {e}')
            return

        self.close()
        if self.main_window:
            self.main_window.refresh_fields()
            self.main_window.show()

    def _go_back(self):
        self.close()
        if self.main_window:
            self.main_window.show()
            self.main_window.refresh_fields()

    def _edit_field(self):
        edit_window = EditFieldWindow(self.field_id, parent=self, main_window=self.main_window)
        edit_window.exec()
        self.close()
        new_view = ViewFieldWindow(self.field_id, parent=None, main_window=self.main_window)
        new_view.show()


class EditFieldWindow(QDialog):
    def __init__(self, field_id, parent=None, main_window=None):
        super().__init__(parent)
        self.field_id = field_id
        self.main_window = main_window

        field = get_field(field_id)
        if field is None:
            self.close()
            return

        self.setWindowTitle(f'Redaguoti — {field["name"]}')
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel('Redaguoti lauką')
        heading.setStyleSheet('font-size: 11pt; font-weight: bold; color: #2e7d32;')
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit(field['name'])
        self.hectares_input = QLineEdit(str(field['hectares']) if field['hectares'] is not None else '')
        self.field_type = QComboBox()
        self.field_type.addItems([''] + CROP_TYPES)
        if field['type']:
            self.field_type.setCurrentText(field['type'])

        form.addRow('Pavadinimas:', self.name_input)
        form.addRow('Hektarai:', self.hectares_input)
        form.addRow('Tipas:', self.field_type)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('Atšaukti')
        cancel_btn.setProperty('secondary', 'true')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('Išsaugoti')
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            return
        try:
            hectares = float(self.hectares_input.text().strip())
        except ValueError:
            hectares = 0.0
        field_type = self.field_type.currentText()

        try:
            update_field(self.field_id, name, hectares, field_type, None)
        except Exception as e:
            QMessageBox.warning(self, 'Klaida', f'Nepavyko išsaugoti: {e}')
            return

        self.accept()
        if self.main_window:
            self.main_window.refresh_fields()
