import sqlite3
from .config import settings

def get_conn():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(settings.db_path)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            replacements_json TEXT NOT NULL,
            output_path TEXT,
            error TEXT,
            rating INTEGER,
            rating_note TEXT
        )
        """)
        conn.commit()
