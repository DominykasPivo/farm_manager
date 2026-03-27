# Farm Manager

A desktop application for managing agricultural fields. Satellite map view, field activity logging, and field metadata management.

## Prerequisites

- Python 3.11+
- pip

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/DominykasPivo/farm-manager.git
cd farm-manager
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
python main.py
```

The database (`farm_manager.db`) and image folder (`field_images/`) are created automatically on first run.

---

## Building a standalone executable

Requires the dev dependencies:
```bash
pip install -r requirements-dev.txt
pyinstaller farm_manager.spec
```

Output is in `dist/FarmManager/`. Distribute the entire folder — `FarmManager.exe` requires the files alongside it to run.

---

## Project structure

```
farm_manager/
├── main.py                        # Entry point
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Build dependencies (PyInstaller)
├── farm_manager.spec              # PyInstaller build config
└── src/
    ├── database.py                # SQLite logic (fields, logs)
    └── windows/
        ├── field_manager_window.py  # Main window
        ├── field_manager.py         # Add / view / edit fields
        ├── field_logs.py            # Field activity logs
        └── map_window.py            # Satellite map view
```

## Runtime files (gitignored)

| File/Folder | Description |
|---|---|
| `farm_manager.db` | SQLite database |
| `field_images/` | Field photos |
| `config.json` | Saved map home position |
| `fields_backup/` | Created if migrating from old txt-based data |
