import json
import os

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.database import add_polygon, get_all_polygons, get_field

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
    .filter-btn {{
      display: flex;
      align-items: center;
      gap: 6px;
      width: 100%;
      margin: 2px 0;
      padding: 5px 8px;
      background: rgba(255,255,255,0.1);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 3px;
      cursor: pointer;
      font-size: 12px;
      text-align: left;
    }}
    .filter-btn:hover {{ background: rgba(255,255,255,0.2); }}
    .filter-btn.active {{
      background: rgba(255,255,255,0.3);
      border-color: rgba(255,255,255,0.7);
    }}
    .filter-dot {{
      width: 10px; height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map', {{ maxZoom: 19 }}).setView([{lat}, {lng}], {zoom});

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
    new L.Control.Draw({{
      draw: {{
        polygon:      {{ shapeOptions: {{ color: '#fff', weight: 2, fillOpacity: 0.1 }} }},
        polyline:     false,
        rectangle:    false,
        circle:       false,
        marker:       false,
        circlemarker: false
      }},
      edit: {{ featureGroup: drawnItems }}
    }}).addTo(map);

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
      'Sėja':              '#2196f3',
      'Tręšimas':          '#9c27b0',
      'Žolinimas':         '#009688',
      'Derliaus nuėmimas': '#4caf50',
      'Lėkščiavimas':      '#ff9800',
      'Akėjimas':          '#795548',
      'Purškimas':         '#f44336',
      'Lyginimas':         '#607d8b',
      'Krovimo darbai':    '#fdd835',
      'Žemės dirbimas':    '#8d6e63'
    }};
    function typeColor(t)     {{ return TYPE_COLORS[t]     || '#ff7800'; }}
    function activityColor(a) {{ return ACTIVITY_COLORS[a] || '#777'; }}

    // ── Polygon store (for filtering) ─────────────────────────────────
    var polygonLayers = [];

    function loadPolygons(polygons) {{
      polygons.forEach(function(p) {{ addPolygon(p); }});
    }}

    function addPolygon(p) {{
      var color = typeColor(p.field_type);
      var layer = L.geoJSON(JSON.parse(p.coordinates), {{
        style: {{ color: color, weight: 2, fillColor: color, fillOpacity: 0.2 }},
        onEachFeature: function(feature, l) {{
          l.on('click', function() {{
            if (window.bridge) {{ window.bridge.on_field_clicked(p.field_id); }}
          }});
          l.on('mouseover', function() {{ l.setStyle({{ fillOpacity: 0.45, weight: 3 }}); }});
          l.on('mouseout',  function() {{ l.setStyle({{ fillOpacity: 0.2,  weight: 2 }}); }});
        }}
      }}).addTo(map);

      var badgeHtml = '';
      if (p.last_activity) {{
        var ac = activityColor(p.last_activity);
        badgeHtml = '<br><span class="activity-badge" style="background:' + ac + '">' + p.last_activity + '</span>';
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
        last_activity: p.last_activity || ''
      }});
    }}

    // ── Filtering ─────────────────────────────────────────────────────
    var activeFilter = '';

    function filterByActivity(activity) {{
      activeFilter = activity;
      polygonLayers.forEach(function(item) {{
        var match = !activity || item.last_activity === activity;
        item.layer.setStyle({{
          opacity:     match ? 1    : 0.12,
          fillOpacity: match ? 0.2  : 0.04
        }});
        item.markerLayer.setOpacity(match ? 1 : 0.15);
      }});
    }}

    // ── Filter control ────────────────────────────────────────────────
    var FilterControl = L.Control.extend({{
      options: {{ position: 'bottomleft' }},
      onAdd: function() {{
        var container = L.DomUtil.create('div', 'filter-control');
        L.DomEvent.disableClickPropagation(container);

        var title = L.DomUtil.create('div', 'filter-title', container);
        title.textContent = 'Filtruoti pagal veiklą';

        var entries = [
          {{ label: 'Visi laukai',          activity: '' }},
          {{ label: 'Sėja',                activity: 'Sėja' }},
          {{ label: 'Tręšimas',            activity: 'Tręšimas' }},
          {{ label: 'Žolinimas',           activity: 'Žolinimas' }},
          {{ label: 'Derliaus nuėmimas',   activity: 'Derliaus nuėmimas' }},
          {{ label: 'Lėkščiavimas',        activity: 'Lėkščiavimas' }},
          {{ label: 'Akėjimas',            activity: 'Akėjimas' }},
          {{ label: 'Purškimas',           activity: 'Purškimas' }},
          {{ label: 'Lyginimas',           activity: 'Lyginimas' }},
          {{ label: 'Krovimo darbai',      activity: 'Krovimo darbai' }},
          {{ label: 'Žemės dirbimas',      activity: 'Žemės dirbimas' }}
        ];

        var buttons = [];
        entries.forEach(function(entry) {{
          var btn = L.DomUtil.create('button', 'filter-btn', container);
          var dot = L.DomUtil.create('span', 'filter-dot', btn);
          dot.style.background = entry.activity ? activityColor(entry.activity) : '#aaa';
          btn.appendChild(document.createTextNode(entry.label));
          if (!entry.activity) btn.classList.add('active');
          buttons.push(btn);

          L.DomEvent.on(btn, 'click', function() {{
            buttons.forEach(function(b) {{ b.classList.remove('active'); }});
            btn.classList.add('active');
            filterByActivity(entry.activity);
          }});
        }});

        return container;
      }}
    }});
    new FilterControl().addTo(map);
  </script>
</body>
</html>
"""


class MapBridge(QObject):
    polygon_drawn = pyqtSignal(str)
    field_clicked = pyqtSignal(int)

    @pyqtSlot(str)
    def on_polygon_drawn(self, geojson: str):
        self.polygon_drawn.emit(geojson)

    @pyqtSlot(int)
    def on_field_clicked(self, field_id: int):
        self.field_clicked.emit(field_id)


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
        toolbar.addStretch()
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
                'last_activity': None,
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
                'last_activity': None,
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
