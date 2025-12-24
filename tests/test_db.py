
import pytest

from phish_show_ratings.db import get_shows_by_year, get_years, init_db, upsert_shows
from phish_show_ratings.models import Show


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture
def sample_shows():
    return [
        Show("show-1", "2024-01-01", "Venue A", "City A", "ST", "USA", 4.5, 2024),
        Show("show-2", "2024-01-02", "Venue B", "City B", "ST", "USA", 4.0, 2024),
        Show("show-3", "2023-12-31", "Venue C", "City C", "ST", "USA", 4.8, 2023),
    ]


def test_init_db_creates_database(tmp_path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    assert db_path.exists()
    conn.close()


def test_init_db_creates_shows_table(db_conn):
    cursor = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='shows'"
    )
    assert cursor.fetchone() is not None


def test_upsert_shows_inserts_new_shows(db_conn, sample_shows):
    upsert_shows(db_conn, sample_shows)
    db_conn.commit()
    cursor = db_conn.execute("SELECT COUNT(*) FROM shows")
    assert cursor.fetchone()[0] == 3


def test_upsert_shows_updates_existing_shows(db_conn):
    show_v1 = Show("show-1", "2024-01-01", "Venue A", "City", "ST", "USA", 4.0, 2024)
    show_v2 = Show("show-1", "2024-01-01", "Venue A", "City", "ST", "USA", 4.5, 2024)

    upsert_shows(db_conn, [show_v1])
    db_conn.commit()
    upsert_shows(db_conn, [show_v2])
    db_conn.commit()

    cursor = db_conn.execute("SELECT rating FROM shows WHERE show_id = 'show-1'")
    assert cursor.fetchone()[0] == 4.5


def test_get_shows_by_year_returns_correct_year(db_conn, sample_shows):
    upsert_shows(db_conn, sample_shows)
    db_conn.commit()

    shows_2024 = get_shows_by_year(db_conn, 2024)
    assert len(shows_2024) == 2
    assert all(s.year == 2024 for s in shows_2024)


def test_get_shows_by_year_orders_by_rating_desc(db_conn, sample_shows):
    upsert_shows(db_conn, sample_shows)
    db_conn.commit()

    shows = get_shows_by_year(db_conn, 2024)
    assert shows[0].rating == 4.5
    assert shows[1].rating == 4.0


def test_get_years_returns_distinct_years(db_conn, sample_shows):
    upsert_shows(db_conn, sample_shows)
    db_conn.commit()

    years = get_years(db_conn)
    assert years == [2023, 2024]


def test_get_years_empty_database(db_conn):
    years = get_years(db_conn)
    assert years == []


def test_upsert_shows_is_idempotent(db_conn, sample_shows):
    upsert_shows(db_conn, sample_shows)
    db_conn.commit()

    cursor = db_conn.execute("SELECT COUNT(*) FROM shows")
    count_after_first = cursor.fetchone()[0]

    upsert_shows(db_conn, sample_shows)
    db_conn.commit()

    cursor = db_conn.execute("SELECT COUNT(*) FROM shows")
    count_after_second = cursor.fetchone()[0]

    assert count_after_first == count_after_second == 3


def test_transaction_rollback(tmp_path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)

    show = Show("show-1", "2024-01-01", "Venue", "City", "ST", "USA", 4.0, 2024)
    upsert_shows(conn, [show])

    conn.rollback()

    cursor = conn.execute("SELECT COUNT(*) FROM shows")
    assert cursor.fetchone()[0] == 0
    conn.close()
