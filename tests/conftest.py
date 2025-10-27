# tests/conftest.py
import os
import sys
from pathlib import Path
import tempfile
import pytest

# --- ensure project root (folder that contains app.py, db.py, etc.) is on sys.path ---
ROOT = Path(__file__).resolve().parents[1]  # .../Smart goals tracker
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ---------------------------------------------------------------------

@pytest.fixture()
def tmp_db_path(monkeypatch):
    # create a temp file for sqlite
    fd, tmp = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    p = Path(tmp)

    # now safe to import db since ROOT is in sys.path
    import importlib
    db = importlib.import_module("db")

    # patch db.DB_PATH to use temp file
    monkeypatch.setattr(db, "DB_PATH", p, raising=True)

    # re-init schema on temp DB
    db.init_db()
    yield p
    try:
        p.unlink(missing_ok=True)
    except Exception:
        pass
