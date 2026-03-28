import sqlite3
import os
import shutil

DB_PATH = 'farm_manager.db'
IMAGES_DIR = 'field_images'
FUEL_PRESET_KEY = '__kuro_kaina__'


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fields (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            hectares     REAL,
            type         TEXT,
            picture_path TEXT
        );
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id    INTEGER NOT NULL,
            date        TEXT NOT NULL,
            type        TEXT NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS polygons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id    INTEGER NOT NULL,
            coordinates TEXT NOT NULL,
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS price_presets (
            log_type TEXT PRIMARY KEY,
            price    REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS fertilizers (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            price_per_kg REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS seeds (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            price_per_kg REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS chemicals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            price_per_l  REAL NOT NULL DEFAULT 0
        );
    """)
    # Migrate: add cost column to logs if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE logs ADD COLUMN cost REAL")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


def get_all_fields():
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, hectares, type, picture_path FROM fields ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def get_field(field_id: int):
    conn = _connect()
    row = conn.execute(
        "SELECT id, name, hectares, type, picture_path FROM fields WHERE id = ?",
        (field_id,)
    ).fetchone()
    conn.close()
    return row


def add_field(name: str, hectares: float, field_type: str, picture_path) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO fields (name, hectares, type, picture_path) VALUES (?, ?, ?, ?)",
        (name, hectares, field_type, picture_path)
    )
    field_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return field_id


def update_field(field_id: int, name: str, hectares: float, field_type: str, picture_path):
    conn = _connect()
    conn.execute(
        "UPDATE fields SET name=?, hectares=?, type=?, picture_path=? WHERE id=?",
        (name, hectares, field_type, picture_path, field_id)
    )
    conn.commit()
    conn.close()


def delete_field(field_id: int):
    conn = _connect()
    conn.execute("DELETE FROM fields WHERE id = ?", (field_id,))
    conn.commit()
    conn.close()


def get_field_logs(field_id: int):
    conn = _connect()
    rows = conn.execute(
        "SELECT id, field_id, date, type, description, cost FROM logs "
        "WHERE field_id = ? ORDER BY date DESC, id DESC",
        (field_id,)
    ).fetchall()
    conn.close()
    return rows


def add_log(field_id: int, date: str, log_type: str, description: str, cost=None) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO logs (field_id, date, type, description, cost) VALUES (?, ?, ?, ?, ?)",
        (field_id, date, log_type, description, cost)
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_all_presets() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT log_type, price FROM price_presets").fetchall()
    conn.close()
    return {r['log_type']: r['price'] for r in rows}


def set_preset(log_type: str, price: float):
    conn = _connect()
    conn.execute(
        "INSERT INTO price_presets (log_type, price) VALUES (?, ?) "
        "ON CONFLICT(log_type) DO UPDATE SET price = excluded.price",
        (log_type, price)
    )
    conn.commit()
    conn.close()


def get_preset(log_type: str) -> float:
    conn = _connect()
    row = conn.execute(
        "SELECT price FROM price_presets WHERE log_type = ?", (log_type,)
    ).fetchone()
    conn.close()
    return row['price'] if row else 0.0


def get_field_cost_summary(field_id: int) -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT type, SUM(cost) as total FROM logs "
        "WHERE field_id = ? AND cost IS NOT NULL GROUP BY type ORDER BY type",
        (field_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_fields_cost_summary(date_from=None, date_to=None) -> list:
    conn = _connect()
    query = """
        SELECT f.name AS field_name, l.type, SUM(l.cost) AS total
        FROM logs l
        JOIN fields f ON l.field_id = f.id
        WHERE l.cost IS NOT NULL
    """
    params = []
    if date_from:
        query += " AND l.date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND l.date <= ?"
        params.append(date_to + ' 23:59')
    query += " GROUP BY f.id, l.type ORDER BY f.name, l.type"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_fertilizers() -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, price_per_kg FROM fertilizers ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_fertilizer(name: str, price_per_kg: float) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO fertilizers (name, price_per_kg) VALUES (?, ?)",
        (name, price_per_kg)
    )
    fert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fert_id


def update_fertilizer(fert_id: int, name: str, price_per_kg: float):
    conn = _connect()
    conn.execute(
        "UPDATE fertilizers SET name=?, price_per_kg=? WHERE id=?",
        (name, price_per_kg, fert_id)
    )
    conn.commit()
    conn.close()


def delete_fertilizer(fert_id: int):
    conn = _connect()
    conn.execute("DELETE FROM fertilizers WHERE id = ?", (fert_id,))
    conn.commit()
    conn.close()


def get_all_seeds() -> list:
    conn = _connect()
    rows = conn.execute("SELECT id, name, price_per_kg FROM seeds ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_seed(name: str, price_per_kg: float) -> int:
    conn = _connect()
    cursor = conn.execute("INSERT INTO seeds (name, price_per_kg) VALUES (?, ?)", (name, price_per_kg))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def update_seed(seed_id: int, name: str, price_per_kg: float):
    conn = _connect()
    conn.execute("UPDATE seeds SET name=?, price_per_kg=? WHERE id=?", (name, price_per_kg, seed_id))
    conn.commit()
    conn.close()


def delete_seed(seed_id: int):
    conn = _connect()
    conn.execute("DELETE FROM seeds WHERE id = ?", (seed_id,))
    conn.commit()
    conn.close()


def get_all_chemicals() -> list:
    conn = _connect()
    rows = conn.execute("SELECT id, name, price_per_l FROM chemicals ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_chemical(name: str, price_per_l: float) -> int:
    conn = _connect()
    cursor = conn.execute("INSERT INTO chemicals (name, price_per_l) VALUES (?, ?)", (name, price_per_l))
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid


def update_chemical(chem_id: int, name: str, price_per_l: float):
    conn = _connect()
    conn.execute("UPDATE chemicals SET name=?, price_per_l=? WHERE id=?", (name, price_per_l, chem_id))
    conn.commit()
    conn.close()


def delete_chemical(chem_id: int):
    conn = _connect()
    conn.execute("DELETE FROM chemicals WHERE id = ?", (chem_id,))
    conn.commit()
    conn.close()


def add_polygon(field_id: int, coordinates: str) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO polygons (field_id, coordinates) VALUES (?, ?)",
        (field_id, coordinates)
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_all_polygons() -> list:
    conn = _connect()
    rows = conn.execute("""
        SELECT p.id, p.field_id, p.coordinates, f.name AS field_name, f.type AS field_type,
               (SELECT l.type FROM logs l
                WHERE l.field_id = f.id
                ORDER BY l.date DESC, l.id DESC LIMIT 1) AS last_activity
        FROM polygons p
        JOIN fields f ON p.field_id = f.id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_field_polygons(field_id: int) -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, field_id, coordinates FROM polygons WHERE field_id = ?",
        (field_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def migrate_from_files():
    """
    One-time migration from the flat-file fields/ layout to SQLite.
    After a successful migration fields/ is renamed to fields_backup/.
    """
    fields_root = 'fields'
    if not os.path.isdir(fields_root):
        return

    os.makedirs(IMAGES_DIR, exist_ok=True)

    try:
        field_dirs = [
            d for d in os.listdir(fields_root)
            if os.path.isdir(os.path.join(fields_root, d))
        ]
    except OSError:
        return

    for field_dir_name in field_dirs:
        field_folder = os.path.join(fields_root, field_dir_name)
        info_path = os.path.join(field_folder, 'info.txt')

        if not os.path.exists(info_path):
            continue

        # Parse info.txt
        name = field_dir_name
        hectares = 0.0
        field_type = ''
        raw_picture = ''

        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) > 0:
                name = lines[0].strip()
            if len(lines) > 1:
                try:
                    hectares = float(lines[1].replace('Hectares:', '').strip())
                except ValueError:
                    hectares = 0.0
            if len(lines) > 2:
                field_type = lines[2].replace('Type:', '').strip()
            if len(lines) > 3:
                raw_picture = lines[3].replace('Picture:', '').strip()
        except OSError:
            continue

        # Skip if already migrated
        conn = _connect()
        existing = conn.execute(
            "SELECT id FROM fields WHERE name = ?", (name,)
        ).fetchone()
        conn.close()
        if existing:
            continue

        field_id = add_field(name, hectares, field_type, None)

        # Handle image
        picture_path_db = None
        if raw_picture:
            pic_basename = os.path.basename(raw_picture)
            src_path = os.path.join(field_folder, pic_basename)
            if not os.path.exists(src_path) and os.path.exists(raw_picture):
                src_path = raw_picture
            elif not os.path.exists(src_path):
                src_path = None

            if src_path and os.path.exists(src_path):
                pic_ext = os.path.splitext(src_path)[1].lower()
                dest_filename = f"{field_id}{pic_ext}"
                dest_path = os.path.join(IMAGES_DIR, dest_filename)
                try:
                    shutil.copy2(src_path, dest_path)
                    picture_path_db = dest_filename
                except OSError:
                    pass

        if picture_path_db is not None:
            update_field(field_id, name, hectares, field_type, picture_path_db)

        # Migrate logs
        logs_folder = os.path.join(field_folder, 'logs')
        if os.path.isdir(logs_folder):
            try:
                log_files = [f for f in os.listdir(logs_folder) if f.endswith('.txt')]
            except OSError:
                log_files = []

            for log_filename in log_files:
                log_path = os.path.join(logs_folder, log_filename)
                file_date = os.path.splitext(log_filename)[0]

                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except OSError:
                    continue

                sections = content.strip().split('---\n')
                for section in sections:
                    section = section.strip()
                    if not section:
                        continue

                    log_data = {}
                    for line in section.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            log_data[key.strip()] = value.strip()

                    log_type = log_data.get('Type', '')
                    description = log_data.get('Description', '')
                    date = log_data.get('Date', file_date)

                    if log_type and description:
                        add_log(field_id, date, log_type, description)

    try:
        os.rename(fields_root, fields_root + '_backup')
    except OSError:
        pass
