import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .config import DB_PATH
from .models import Show


def init_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shows (
            show_id TEXT PRIMARY KEY,
            date TEXT,
            venue TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            rating REAL,
            year INTEGER,
            updated_at TEXT
        )
    """)
    return conn


def upsert_shows(conn: sqlite3.Connection, shows: list[Show]) -> None:
    now = datetime.now(UTC).isoformat()
    rows = [(s.show_id, s.date, s.venue, s.city, s.state, s.country,
             s.rating, s.year, now) for s in shows]
    conn.executemany(
        "INSERT OR REPLACE INTO shows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows
    )


def get_shows_by_year(conn: sqlite3.Connection, year: int) -> list[Show]:
    cursor = conn.execute(
        "SELECT show_id, date, venue, city, state, country, rating, year "
        "FROM shows WHERE year = ? ORDER BY rating DESC",
        (year,)
    )
    return [Show(*row) for row in cursor]


def get_years(conn: sqlite3.Connection) -> list[int]:
    cursor = conn.execute("SELECT DISTINCT year FROM shows ORDER BY year")
    return [row[0] for row in cursor]
