import json
import os

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.database import add_polygon, get_all_polygons, get_field, set_field_status, set_field_harvested

CONFIG_PATH = 'config.json'
DEFAULT_VIEW = {'lat': 55.1694, 'lng': 23.8813, 'zoom': 7}

MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
  <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
  <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    #map {{ width: 100vw; height: 100vh; }}

    .field-label {{
      background: rgba(0,0,0,0.65);
      color: #fff;
      padding: 4px 7px;
      border-radius: 4px;
      font-size: 12px;
      white-space: nowrap;
      line-height: 1.5;
    }}

    .activity-badge {{
      display: inline-block;
      padding: 1px 5px;
      border-radius: 3px;
      font-size: 11px;
      margin-top: 2px;
      font-weight: normal;
    }}

    .filter-control {{
      background: rgba(0,0,0,0.72);
      padding: 8px 10px;
      border-radius: 5px;
      min-width: 160px;
    }}
    .filter-title {{
      color: #ccc;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 5px;
    }}
    .filter-row {{
      display: flex;
      flex-direction: column;
      margin-bottom: 6px;
    }}
    .filter-row-label {{
      color: #bbb;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 3px;
    }}
    .filter-select {{
      width: 100%;
      background: rgba(255,255,255,0.12);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.25);
      border-radius: 3px;
      padding: 5px 7px;
      font-size: 12px;
      cursor: pointer;
      appearance: none;
      -webkit-appearance: none;
      outline: 0 !important;
    }}
    .filter-select:hover {{
      background: rgba(255,255,255,0.25);
      border-color: rgba(100,180,255,0.8);
      outline: 0 !important;
    }}
    .filter-select:focus,
    .filter-select:active {{
      outline: 0 !important;
      box-shadow: none !important;
      border-color: rgba(255,255,255,0.25);
    }}
    .filter-select option {{
      background: #2a2a2a;
      color: #fff;
    }}

    .field-status-popup .leaflet-popup-content-wrapper {{
      background: #1e1e1e;
      color: #fff;
      border-radius: 8px;
      padding: 0;
      box-shadow: 0 3px 14px rgba(0,0,0,0.6);
    }}
    .field-status-popup .leaflet-popup-tip {{
      background: #1e1e1e;
    }}
    .field-status-popup .leaflet-popup-content {{
      margin: 0;
    }}
    .field-status-popup .leaflet-popup-close-button {{
      color: #aaa;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map', {{ maxZoom: 19 }}).setView([{lat}, {lng}], {zoom});
    var HARVEST_MODE = 0;

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
      {{
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        maxZoom: 19
      }}
    ).addTo(map);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
      {{ maxZoom: 19, opacity: 0.8 }}
    ).addTo(map);

    // Search bar
    var geocoder = L.Control.geocoder({{
      defaultMarkGeocode: false,
      placeholder: 'Ieškoti vietos ar adreso...',
      collapsed: false
    }})
    .on('markgeocode', function(e) {{ map.setView(e.geocode.center, 15); }})
    .addTo(map);

    function removeSearch() {{ geocoder.remove(); }}

    // QWebChannel bridge
    new QWebChannel(qt.webChannelTransport, function(channel) {{
      window.bridge = channel.objects.bridge;
    }});

    // Draw toolbar — polygon only
    var drawnItems = new L.FeatureGroup().addTo(map);
    var drawControl = new L.Control.Draw({{
      draw: {{
        polygon:      {{ shapeOptions: {{ color: '#fff', weight: 2, fillOpacity: 0.1 }} }},
        polyline:     false,
        rectangle:    false,
        circle:       false,
        marker:       false,
        circlemarker: false
      }},
      edit: {{ featureGroup: drawnItems }}
    }});
    drawControl.addTo(map);

    map.on('draw:created', function(e) {{
      drawnItems.addLayer(e.layer);
      if (window.bridge) {{
        window.bridge.on_polygon_drawn(JSON.stringify(e.layer.toGeoJSON()));
      }}
    }});

    // ── Color maps ────────────────────────────────────────────────────
    var TYPE_COLORS = {{
      'Z. mieziai':  '#29b6f6',
      'kvieciai':    '#fdd835',
      'Z. kvieciai': '#ffb300',
      'Rapsas':      '#c6ef00',
      'Z. rapsas':   '#66bb6a'
    }};
    var ACTIVITY_COLORS = {{
      'Sėja':                  '#2196f3',
      'Tręšimas':              '#9c27b0',
      'Žolinimas':             '#009688',
      'Derliaus nuėmimas':     '#4caf50',
      'Derliaus pristatymas':  '#00897b',
      'Lėkščiavimas':          '#ff9800',
      'Akėjimas':              '#795548',
      'Purškimas':             '#f44336',
      'Lyginimas':             '#607d8b',
      'Krovimo darbai':        '#fdd835',
      'Žemės dirbimas':        '#8d6e63'
    }};
    var STATUS_TYPES = [
      'Sėja', 'Tręšimas', 'Žolinimas',
      'Derliaus nuėmimas', 'Derliaus pristatymas',
      'Lėkščiavimas', 'Akėjimas', 'Purškimas',
      'Lyginimas', 'Krovimo darbai', 'Žemės dirbimas'
    ];
    function typeColor(t)     {{ return TYPE_COLORS[t]     || '#ff7800'; }}
    function activityColor(a) {{ return ACTIVITY_COLORS[a] || '#777'; }}
    function fieldColor(status, lastActivity, fieldType) {{
      if (status && ACTIVITY_COLORS[status]) return ACTIVITY_COLORS[status];
      if (lastActivity && ACTIVITY_COLORS[lastActivity]) return ACTIVITY_COLORS[lastActivity];
      return typeColor(fieldType);
    }}
    function _clickStatusBtn(fieldId, idx) {{
      setFieldStatus(fieldId, idx >= 0 ? STATUS_TYPES[idx] : '');
    }}

    // ── Polygon store ─────────────────────────────────────────────────
    var polygonLayers = [];

    function loadPolygons(polygons) {{
      polygons.forEach(function(p) {{ addPolygon(p); }});
    }}

    function addPolygon(p) {{
      var color = HARVEST_MODE
        ? (p.field_harvested ? '#fdd835' : '#9e9e9e')
        : fieldColor(p.field_status, p.last_activity, p.field_type);
      var layer = L.geoJSON(JSON.parse(p.coordinates), {{
        style: {{ color: color, weight: 2, fillColor: color, fillOpacity: 0.2 }},
        onEachFeature: function(feature, l) {{
          l.on('click', function(e) {{ showFieldPopup(p.field_id, e.latlng); }});
          l.on('mouseover', function() {{ l.setStyle({{ fillOpacity: 0.45, weight: 3 }}); }});
          l.on('mouseout',  function() {{ l.setStyle({{ fillOpacity: 0.2,  weight: 2 }}); }});
        }}
      }}).addTo(map);

      var badgeText = p.field_status || p.last_activity || '';
      var badgeHtml = '';
      if (badgeText) {{
        var ac = activityColor(badgeText);
        badgeHtml = '<br><span class="activity-badge" style="background:' + ac + '">' + badgeText + '</span>';
      }}
      var labelHtml = '<b>' + p.field_name + '</b><br>'
                    + '<span style="opacity:0.85;font-size:11px">' + (p.field_type || '') + '</span>'
                    + badgeHtml;

      var markerLayer = L.marker(layer.getBounds().getCenter(), {{
        icon: L.divIcon({{ className: 'field-label', html: labelHtml }}),
        interactive: false
      }}).addTo(map);

      polygonLayers.push({{
        layer: layer,
        markerLayer: markerLayer,
        status: p.field_status || '',
        last_activity: p.last_activity || '',
        field_type: p.field_type || '',
        field_id: p.field_id,
        field_name: p.field_name || '',
        harvested: p.field_harvested ? true : false
      }});
    }}

    // ── Field status popup ────────────────────────────────────────────
    function showFieldPopup(fieldId, latlng) {{
      var item = null;
      for (var i = 0; i < polygonLayers.length; i++) {{
        if (polygonLayers[i].field_id === fieldId) {{ item = polygonLayers[i]; break; }}
      }}
      if (!item) return;
      if (HARVEST_MODE) {{
        L.popup({{ className: 'field-status-popup', maxWidth: 260 }})
          .setLatLng(latlng)
          .setContent(buildHarvestPopupContent(fieldId, item.field_name, item.harvested))
          .openOn(map);
      }} else {{
        L.popup({{ className: 'field-status-popup', maxWidth: 300, minWidth: 260 }})
          .setLatLng(latlng)
          .setContent(buildPopupContent(fieldId, item.field_name, item.status))
          .openOn(map);
      }}
    }}

    function buildHarvestPopupContent(fieldId, fieldName, harvested) {{
      var html = '<div style="padding:10px 12px;min-width:200px">';
      html += '<div style="font-weight:bold;font-size:13px;margin-bottom:8px;color:#fff">' + fieldName + '</div>';
      if (harvested) {{
        html += '<button onclick="_toggleHarvestBtn(' + fieldId + ',0)" '
              + 'style="background:#9e9e9e;color:#fff;border:none;border-radius:4px;'
              + 'padding:6px 14px;cursor:pointer;font-size:12px;width:100%">Atžymėti nuimtą</button>';
      }} else {{
        html += '<button onclick="_toggleHarvestBtn(' + fieldId + ',1)" '
              + 'style="background:#fdd835;color:#111;border:none;border-radius:4px;'
              + 'padding:6px 14px;cursor:pointer;font-size:12px;width:100%">&#x2714; Pažymėti nuimtą</button>';
      }}
      html += '</div>';
      return html;
    }}

    function _toggleHarvestBtn(fieldId, val) {{
      updatePolygonHarvest(fieldId, val === 1);
      if (window.bridge) {{ window.bridge.set_harvested(fieldId, val); }}
      map.closePopup();
    }}

    function updatePolygonHarvest(fieldId, harvested) {{
      for (var i = 0; i < polygonLayers.length; i++) {{
        var item = polygonLayers[i];
        if (item.field_id === fieldId) {{
          item.harvested = harvested;
          var c = harvested ? '#fdd835' : '#9e9e9e';
          item.layer.setStyle({{ color: c, fillColor: c }});
          break;
        }}
      }}
    }}

    function buildPopupContent(fieldId, fieldName, currentStatus) {{
      var html = '<div style="padding:10px 12px;">';
      html += '<div style="font-weight:bold;font-size:13px;margin-bottom:8px;color:#fff">' + fieldName + '</div>';
      html += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px">';
      STATUS_TYPES.forEach(function(t, i) {{
        var color = ACTIVITY_COLORS[t] || '#777';
        var border = (t === currentStatus) ? '2px solid #000' : '2px solid transparent';
        html += '<button onclick="_clickStatusBtn(' + fieldId + ',' + i + ')" '
              + 'style="background:' + color + ';color:#fff;border:' + border + ';border-radius:4px;'
              + 'padding:3px 7px;font-size:11px;cursor:pointer">' + t + '</button>';
      }});
      html += '</div>';
      html += '<div style="display:flex;justify-content:space-between;gap:8px">';
      html += '<button onclick="_clickStatusBtn(' + fieldId + ',-1)" '
            + 'style="background:#555;color:#fff;border:none;border-radius:4px;'
            + 'padding:4px 10px;cursor:pointer;font-size:11px">&#x2715; I&#x161;valyti</button>';
      html += '<button onclick="openFieldView(' + fieldId + ')" '
            + 'style="background:#1976d2;color:#fff;border:none;border-radius:4px;'
            + 'padding:4px 10px;cursor:pointer;font-size:11px">Atidaryti &#x2192;</button>';
      html += '</div></div>';
      return html;
    }}

    function setFieldStatus(fieldId, status) {{
      updatePolygonStatus(fieldId, status);
      if (window.bridge) {{ window.bridge.set_field_status(fieldId, status); }}
      map.closePopup();
    }}

    function openFieldView(fieldId) {{
      map.closePopup();
      if (window.bridge) {{ window.bridge.on_field_clicked(fieldId); }}
    }}

    function updatePolygonStatus(fieldId, status) {{
      for (var i = 0; i < polygonLayers.length; i++) {{
        var item = polygonLayers[i];
        if (item.field_id === fieldId) {{
          item.status = status || '';
          var c = fieldColor(item.status, item.last_activity, item.field_type);
          item.layer.setStyle({{ color: c, fillColor: c }});
          rebuildMarkerLabel(item);
          break;
        }}
      }}
    }}

    function rebuildMarkerLabel(item) {{
      var badgeText = item.status || item.last_activity || '';
      var badgeHtml = '';
      if (badgeText) {{
        var ac = activityColor(badgeText);
        badgeHtml = '<br><span class="activity-badge" style="background:' + ac + '">' + badgeText + '</span>';
      }}
      var labelHtml = '<b>' + item.field_name + '</b><br>'
                    + '<span style="opacity:0.85;font-size:11px">' + (item.field_type || '') + '</span>'
                    + badgeHtml;
      item.markerLayer.setIcon(L.divIcon({{ className: 'field-label', html: labelHtml }}));
    }}

    // ── Filtering ─────────────────────────────────────────────────────
    var activeStatusFilter = '';
    var activeTypeFilter = '';

    function applyFilters() {{
      polygonLayers.forEach(function(item) {{
        var matchStatus = !activeStatusFilter || item.status === activeStatusFilter;
        var matchType   = !activeTypeFilter   || item.field_type === activeTypeFilter;
        var match = matchStatus && matchType;
        item.layer.setStyle({{
          opacity:     match ? 1    : 0.12,
          fillOpacity: match ? 0.2  : 0.04
        }});
        item.markerLayer.setOpacity(match ? 1 : 0.15);
      }});
    }}

    function filterByStatus(status) {{ activeStatusFilter = status; applyFilters(); }}
    function filterByType(type)     {{ activeTypeFilter   = type;   applyFilters(); }}

    // ── Combined filter control (bottom-left) ────────────────────────
    var FilterControl = L.Control.extend({{
      options: {{ position: 'bottomleft' }},
      onAdd: function() {{
        var container = L.DomUtil.create('div', 'filter-control');
        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);

        var title = L.DomUtil.create('div', 'filter-title', container);
        title.textContent = 'Filtrai';

        // Status dropdown
        var statusRow = L.DomUtil.create('div', 'filter-row', container);
        var statusLbl = L.DomUtil.create('div', 'filter-row-label', statusRow);
        statusLbl.textContent = 'Statusas';
        var statusSelect = L.DomUtil.create('select', 'filter-select', statusRow);
        var allStatusOpt = document.createElement('option');
        allStatusOpt.value = ''; allStatusOpt.textContent = 'Visi statusai';
        statusSelect.appendChild(allStatusOpt);
        STATUS_TYPES.forEach(function(s) {{
          var opt = document.createElement('option');
          opt.value = s; opt.textContent = s;
          statusSelect.appendChild(opt);
        }});
        L.DomEvent.on(statusSelect, 'change', function() {{ filterByStatus(statusSelect.value); statusSelect.blur(); }});

        // Type dropdown
        var typeRow = L.DomUtil.create('div', 'filter-row', container);
        var typeLbl = L.DomUtil.create('div', 'filter-row-label', typeRow);
        typeLbl.textContent = 'Tipas';
        var typeSelect = L.DomUtil.create('select', 'filter-select', typeRow);
        [
          ['', 'Visi tipai'],
          ['Z. mieziai', 'Z. mieziai'],
          ['kvieciai', 'Kvieciai'],
          ['Z. kvieciai', 'Z. kvieciai'],
          ['Rapsas', 'Rapsas'],
          ['Z. rapsas', 'Z. rapsas']
        ].forEach(function(e) {{
          var opt = document.createElement('option');
          opt.value = e[0]; opt.textContent = e[1];
          typeSelect.appendChild(opt);
        }});
        L.DomEvent.on(typeSelect, 'change', function() {{ filterByType(typeSelect.value); typeSelect.blur(); }});

        return container;
      }}
    }});
    var filterControl = new FilterControl();
    filterControl.addTo(map);

    // ── Harvest mode toggle ───────────────────────────────────────────
    function setHarvestMode(val) {{
      HARVEST_MODE = val;
      if (val) {{
        drawControl.remove();
        filterControl.remove();
      }} else {{
        drawControl.addTo(map);
        filterControl.addTo(map);
      }}
      polygonLayers.forEach(function(item) {{
        var c = val
          ? (item.harvested ? '#fdd835' : '#9e9e9e')
          : fieldColor(item.status, item.last_activity, item.field_type);
        item.layer.setStyle({{ color: c, fillColor: c }});
        rebuildMarkerLabel(item);
      }});
      map.closePopup();
    }}
  </script>
</body>
</html>
"""


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


def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
            if all(k in data for k in ('lat', 'lng', 'zoom')):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_VIEW.copy()


def _save_config(data: dict):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


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
        config = _load_config()
        html = MAP_HTML.format(
            lat=config['lat'],
            lng=config['lng'],
            zoom=config['zoom']
        )
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
            _save_config({'lat': lat, 'lng': lng, 'zoom': zoom})
            self.web_view.page().runJavaScript("removeSearch()")
            self.home_btn.setText('Pradinė vieta išsaugota')
            self.home_btn.setEnabled(False)
            self.home_btn.setToolTip('Pradinė vieta nustatyta. Atidarykite žemėlapį iš naujo, kad galėtumėte ieškoti.')
