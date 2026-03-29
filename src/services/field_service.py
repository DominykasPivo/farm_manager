import json
import os

from src.database import (
    get_all_fields, get_field, add_field, update_field, delete_field,
    set_field_status, set_field_harvested,
    add_polygon, get_all_polygons, get_field_polygons,
)

CROP_TYPES = ['Ž. Miežiai', 'Kvieciai', 'Ž. Kvieciai', 'Rapsas', 'Ž. Rapsas', 'Soja']

_CONFIG_PATH = 'config.json'
_DEFAULT_VIEW = {'lat': 55.1694, 'lng': 23.8813, 'zoom': 7}


def load_map_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, 'r') as f:
                data = json.load(f)
            if all(k in data for k in ('lat', 'lng', 'zoom')):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return _DEFAULT_VIEW.copy()


def save_map_config(data: dict):
    try:
        with open(_CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')


def load_template(name: str) -> str:
    path = os.path.normpath(os.path.join(_TEMPLATES_DIR, name))
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
