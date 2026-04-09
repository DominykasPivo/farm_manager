from src.database import get_all_rotation_configs, upsert_rotation_config

ROTATION_CYCLE = [
    'Ž. Kvieciai',  # 1
    'Ž. Rapsas',    # 2
    'Žirniai',      # 3  legume slot
    'Ž. Kvieciai',  # 4
    'Ž. Rapsas',    # 5
    'Ž. Kvieciai',  # 6
    'Žirniai',      # 7  legume slot
    'Ž. Kvieciai',  # 8
    'Ž. Rapsas',    # 9
]

LEGUME_POSITIONS = {3, 7}  # 1-based positions in cycle


def get_rotation_year(position: int, offset: int, legume_choice: str) -> str:
    """Return the crop name for (position + offset - 1) steps ahead."""
    idx = (position - 1 + offset) % 9
    crop = ROTATION_CYCLE[idx]
    if (idx + 1) in LEGUME_POSITIONS:
        crop = legume_choice
    return crop


def default_position_for_crop(crop_type: str) -> int:
    """Return the first matching position in the cycle for a given crop type, or 1."""
    is_legume = crop_type in ('Žirniai', 'Soja')
    for i, crop in enumerate(ROTATION_CYCLE):
        if is_legume and (i + 1) in LEGUME_POSITIONS:
            return i + 1
        if not is_legume and crop == crop_type:
            return i + 1
    return 1
