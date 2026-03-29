import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.services.field_service import (
    add_polygon, get_all_polygons, get_field, set_field_status, set_field_harvested,
    load_map_config, save_map_config, load_template,
)


class MapBridge(QObject):
    polygon_drawn = pyqtSignal(str)
    field_clicked = pyqtSignal(int)
    field_status_changed = pyqtSignal(int, str)
    harvest_toggled = pyqtSignal(int, bool)

    @pyqtSlot(str)
    def on_polygon_drawn(self, geojson: str):
        self.polygon_drawn.emit(geojson)

    @pyqtSlot(int)
    def on_field_clicked(self, field_id: int):
        self.field_clicked.emit(field_id)

    @pyqtSlot(int, str)
    def set_field_status(self, field_id: int, status: str):
        self.field_status_changed.emit(field_id, status)

    @pyqtSlot(int, int)
    def set_harvested(self, field_id: int, harvested: int):
        self.harvest_toggled.emit(field_id, bool(harvested))


class MapWindow(QWidget):
    def __init__(self, parent=None, main_window=None,
                 assign_to_field_id=None, on_polygon_saved=None):
        super().__init__(parent)
        self.main_window = main_window
        self.assign_to_field_id = assign_to_field_id
        self._on_polygon_saved = on_polygon_saved
        self._harvest_mode_active = False

        if assign_to_field_id:
            field = get_field(assign_to_field_id)
            name = field['name'] if field else str(assign_to_field_id)
            self.setWindowTitle(f'Braižyti ribą — {name}')
        else:
            self.setWindowTitle('Ūkio žemėlapis')
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 4, 6, 4)
        self.home_btn = QPushButton('Nustatyti kaip pradinį')
        self.home_btn.setFixedWidth(160)
        self.home_btn.setToolTip('Išsaugoti dabartinį žemėlapio vaizdą kaip pradinę vietą')
        self.home_btn.clicked.connect(self._save_home)
        toolbar.addWidget(self.home_btn)
        toolbar.addSpacing(12)
        self.harvest_toggle_btn = QPushButton('🌾 Derlius')
        self.harvest_toggle_btn.setProperty('secondary', 'true')
        self.harvest_toggle_btn.setCheckable(True)
        self.harvest_toggle_btn.clicked.connect(self._toggle_harvest_mode)
        toolbar.addWidget(self.harvest_toggle_btn)
        toolbar.addStretch()
        back_btn = QPushButton('← Grįžti')
        back_btn.setProperty('secondary', 'true')
        back_btn.clicked.connect(self.close)
        toolbar.addWidget(back_btn)
        layout.addLayout(toolbar)

        # Map
        config = load_map_config()
        html = load_template('map.html')
        html = (html
                .replace('{lat}', str(config['lat']))
                .replace('{lng}', str(config['lng']))
                .replace('{zoom}', str(config['zoom'])))

        self.web_view = QWebEngineView()

        self.channel = QWebChannel()
        self.bridge = MapBridge()
        self.channel.registerObject('bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        self.bridge.polygon_drawn.connect(self._handle_polygon_drawn)
        self.bridge.field_clicked.connect(self._handle_field_clicked)
        self.bridge.field_status_changed.connect(self._handle_set_status)
        self.bridge.harvest_toggled.connect(self._handle_harvest_toggle)
        self.web_view.loadFinished.connect(self._on_map_loaded)

        self.web_view.setHtml(html)
        layout.addWidget(self.web_view)

    def _on_map_loaded(self, ok):
        if ok:
            polygons = get_all_polygons()
            self.web_view.page().runJavaScript(
                f"loadPolygons({json.dumps(polygons)})"
            )

    def _handle_polygon_drawn(self, geojson: str):
        if self.assign_to_field_id:
            field_id = self.assign_to_field_id
            polygon_id = add_polygon(field_id, geojson)
            field = get_field(field_id)
            payload = json.dumps({
                'id': polygon_id,
                'field_id': field_id,
                'field_name': field['name'],
                'field_type': field['type'],
                'field_status': None,
                'coordinates': geojson
            })
            self.web_view.page().runJavaScript(f"addPolygon({payload})")
            self.close()
            if self._on_polygon_saved:
                self._on_polygon_saved()
            return

        from src.windows.field_manager import AddFieldFromMapDialog
        dialog = AddFieldFromMapDialog(geojson, parent=self)
        if dialog.exec():
            field_id = dialog.saved_field_id
            polygon_id = add_polygon(field_id, geojson)
            field = get_field(field_id)
            payload = json.dumps({
                'id': polygon_id,
                'field_id': field_id,
                'field_name': field['name'],
                'field_type': field['type'],
                'field_status': None,
                'coordinates': geojson
            })
            self.web_view.page().runJavaScript(f"addPolygon({payload})")

    def _handle_field_clicked(self, field_id: int):
        from src.windows.field_manager import ViewFieldWindow
        self.close()
        if self.main_window:
            self.main_window.hide()
            self.main_window.view_field_window = ViewFieldWindow(field_id, parent=None, main_window=self.main_window)
            self.main_window.view_field_window.show()
        else:
            self._view_field_window = ViewFieldWindow(field_id, parent=None, main_window=None)
            self._view_field_window.show()

    def _handle_set_status(self, field_id: int, status: str):
        set_field_status(field_id, status if status else None)
        if self.main_window and hasattr(self.main_window, 'refresh_fields'):
            self.main_window.refresh_fields()

    def _handle_harvest_toggle(self, field_id: int, harvested: bool):
        set_field_harvested(field_id, harvested)
        if self.main_window and hasattr(self.main_window, 'refresh_fields'):
            self.main_window.refresh_fields()

    def _toggle_harvest_mode(self):
        self._harvest_mode_active = not self._harvest_mode_active
        val = 1 if self._harvest_mode_active else 0
        self.web_view.page().runJavaScript(f"setHarvestMode({val})")
        if self._harvest_mode_active:
            self.harvest_toggle_btn.setText('🌾 Derlius (įjungta)')
            self.setWindowTitle('Ūkio žemėlapis — Derlius')
        else:
            self.harvest_toggle_btn.setText('🌾 Derlius')
            self.setWindowTitle('Ūkio žemėlapis')

    def _save_home(self):
        self.web_view.page().runJavaScript(
            "JSON.stringify([map.getCenter().lat, map.getCenter().lng, map.getZoom()])",
            self._on_position_received
        )

    def _on_position_received(self, result):
        if result:
            lat, lng, zoom = json.loads(result)
            save_map_config({'lat': lat, 'lng': lng, 'zoom': zoom})
            self.web_view.page().runJavaScript("removeSearch()")
            self.home_btn.setText('Pradinė vieta išsaugota')
            self.home_btn.setEnabled(False)
            self.home_btn.setToolTip('Pradinė vieta nustatyta. Atidarykite žemėlapį iš naujo, kad galėtumėte ieškoti.')
