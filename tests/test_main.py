import sqlite3

import pytest

from phish_show_ratings import __main__ as runner
from phish_show_ratings.db import init_db
from tests.test_integration import MOCK_HTML_2024
from tests.test_scraper import ratings_html


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    db_path = tmp_path / "ratings.db"
    monkeypatch.setattr(runner, "CSV_DIR", csv_dir)
    monkeypatch.setattr(runner, "START_YEAR", 2024)
    monkeypatch.setattr(runner, "init_db", lambda: init_db(db_path))
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    return csv_dir, db_path


@pytest.mark.parametrize("bad_html", ["<html></html>", ratings_html([])])
def test_invalid_scrape_preserves_csv_and_rolls_back(pipeline, monkeypatch, bad_html):
    csv_dir, db_path = pipeline
    path = csv_dir / "ratings_2025.csv"
    original = "show_id,date,venue,city,state,country,rating\nold,2025-01-01,V,,,,4\n"
    path.write_text(original)
    monkeypatch.setattr(
        runner,
        "fetch_year",
        lambda year: MOCK_HTML_2024 if year == 2024 else bad_html,
    )
    with pytest.raises(ValueError):
        runner.main()
    assert path.read_text() == original
    assert not (csv_dir / "ratings_2024.csv").exists()
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM shows").fetchone()[0] == 0


def test_all_empty_scrape_fails(pipeline, monkeypatch):
    csv_dir, _ = pipeline
    monkeypatch.setattr(runner, "fetch_year", lambda _: ratings_html([]))
    with pytest.raises(ValueError, match="zero shows"):
        runner.main()
    assert list(csv_dir.iterdir()) == []


def test_valid_scrape_allows_empty_years(pipeline, monkeypatch):
    csv_dir, _ = pipeline
    monkeypatch.setattr(
        runner,
        "fetch_year",
        lambda year: MOCK_HTML_2024 if year == 2024 else ratings_html([]),
    )
    runner.main()
    assert len((csv_dir / "ratings_2024.csv").read_text().splitlines()) == 3
    assert not (csv_dir / "ratings_2025.csv").exists()


def test_empty_hiatus_year_preserves_archived_csv(pipeline, monkeypatch):
    csv_dir, _ = pipeline
    monkeypatch.setattr(runner, "START_YEAR", 2001)
    path = csv_dir / "ratings_2001.csv"
    original = (
        "show_id,date,venue,city,state,country,rating\nprivate,2001-12-01,V,,,,4\n"
    )
    path.write_text(original)
    monkeypatch.setattr(
        runner,
        "fetch_year",
        lambda year: MOCK_HTML_2024 if year == 2024 else ratings_html([]),
    )
    runner.main()
    assert path.read_text() == original
