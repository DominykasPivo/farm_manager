from src.database import (
    get_field_logs, add_log, delete_log, get_field_cost_summary, get_all_fields_cost_summary,
    get_preset, FUEL_PRESET_KEY,
)
from src.services.preset_service import get_all_fertilizers, get_all_seeds, get_all_chemicals

LOG_FIELDS = {
    'Sėja':              [('Veislė', 'veisle'), ('Kiekis (kg/ha)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Tręšimas':          [('Trąšos', 'trasos'), ('Kiekis (kg/ha)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Žolinimas':         [('Veislės', 'veisles'), ('Kuras (Litrai)', 'kuras')],
    'Derliaus nuėmimas':    [('Tonažas (iš 1 ha)', 'tonazas'), ('Kiekis (pristatymo - Tonos)', 'kiekis_k'), ('Kuras (Litrai)', 'kuras')],
    'Derliaus pristatymas': [('Klasė', 'klase'), ('Tonažas (t)', 'tonazas'), ('Kaina (€/t)', 'kaina_t'), ('Kuras (Litrai)', 'kuras')],
    'Lėkščiavimas':      [('Kuras (Litrai)', 'kuras')],
    'Akėjimas':          [('Kuras (Litrai)', 'kuras')],
    'Purškimas':         [('Chemija', 'chemija'), ('Kiekis (l/ha)', 'kiekis'), ('Kuras (Litrai)', 'kuras')],
    'Lyginimas':         [('Kuras (Litrai)', 'kuras')],
    'Krovimo darbai':    [('Kuras (Litrai)', 'kuras')],
    'Žemės dirbimas':    [('Kuras (Litrai)', 'kuras')],
}

LOG_TYPES = list(LOG_FIELDS.keys())

HARVEST_CLASSES = ['Extra', '1-klasė', '2-klasė', '3-klasė', 'Pašariniai']

# Maps log_type → (field_key, get_products_fn, price_field, price_suffix, empty_hint)
PRODUCT_CONFIG = {
    'Tręšimas': ('trasos',  get_all_fertilizers, 'price_per_kg', '€/kg', 'trąšas'),
    'Sėja':     ('veisle',  get_all_seeds,        'price_per_kg', '€/kg', 'sėklas'),
    'Purškimas':('chemija', get_all_chemicals,    'price_per_l',  '€/l',  'chemines medžiagas'),
}


def calculate_cost(log_type: str, fuel_liters: float, hectares: float,
                   product_price: float = 0.0, kiekis: float = 0.0,
                   tonazas: float = 0.0, kaina_t: float = 0.0) -> float:
    fuel_price = get_preset(FUEL_PRESET_KEY)
    base_price = get_preset(log_type)
    if log_type in PRODUCT_CONFIG:
        return base_price + (product_price * kiekis * hectares) + (fuel_liters * fuel_price)
    elif log_type == 'Derliaus pristatymas':
        return tonazas * kaina_t
    else:
        return base_price + (fuel_liters * fuel_price)
