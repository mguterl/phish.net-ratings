"""Integration test for the full pipeline with mocked HTTP."""

from contextlib import closing
from unittest.mock import Mock

import httpx
import pytest

from phish_show_ratings.db import get_shows_by_year, get_years, init_db, upsert_shows
from phish_show_ratings.export import write_csv
from phish_show_ratings.scraper import fetch_year, parse_shows

MOCK_HTML_2024 = """
<html>
<body>
<table id="ratings-list">
    <tbody>
        <tr>
            <td>4.618</td>
            <td><a href="/setlists/phish-december-29-2024-msg.html">2024-12-29</a></td>
            <td>Madison Square Garden</td>
            <td>Extra</td>
            <td>New York</td>
            <td>NY</td>
            <td>USA</td>
        </tr>
        <tr>
            <td>4.500</td>
            <td><a href="/setlists/phish-december-28-2024-msg.html">2024-12-28</a></td>
            <td>Madison Square Garden</td>
            <td>Extra</td>
            <td>New York</td>
            <td>NY</td>
            <td>USA</td>
        </tr>
    </tbody>
</table>
</body>
</html>
"""

MOCK_HTML_2023 = """
<html>
<body>
<table id="ratings-list">
    <tbody>
        <tr>
            <td>4.750</td>
            <td><a href="/setlists/phish-december-31-2023-msg.html">2023-12-31</a></td>
            <td>Madison Square Garden</td>
            <td>Extra</td>
            <td>New York</td>
            <td>NY</td>
            <td>USA</td>
        </tr>
    </tbody>
</table>
</body>
</html>
"""


@pytest.fixture
def mock_client():
    def make_response(html: str) -> Mock:
        response = Mock()
        response.text = html
        response.raise_for_status = Mock()
        return response

    client = Mock(spec=httpx.Client)

    def get_side_effect(url: str, timeout: int = 30) -> Mock:
        if "2024" in url:
            return make_response(MOCK_HTML_2024)
        elif "2023" in url:
            return make_response(MOCK_HTML_2023)
        raise httpx.HTTPStatusError("Not Found", request=Mock(), response=Mock())

    client.get.side_effect = get_side_effect
    return client


def test_full_pipeline(tmp_path, mock_client):
    """Test the complete fetch -> parse -> store -> export pipeline."""
    db_path = tmp_path / "test.db"
    csv_dir = tmp_path / "csv"

    with closing(init_db(db_path)) as conn:
        for year in [2023, 2024]:
            html = fetch_year(year, client=mock_client)
            shows = parse_shows(html, year)
            upsert_shows(conn, shows)

        conn.commit()

        years = get_years(conn)
        assert years == [2023, 2024]

        for year in years:
            shows = get_shows_by_year(conn, year)
            csv_path = csv_dir / f"ratings_{year}.csv"
            write_csv(csv_path, shows)

    assert (csv_dir / "ratings_2023.csv").exists()
    assert (csv_dir / "ratings_2024.csv").exists()

    with open(csv_dir / "ratings_2024.csv") as f:
        lines = f.readlines()
        assert len(lines) == 3
        assert "december-29-2024-msg" in lines[1]


def test_pipeline_rollback_on_failure(tmp_path, mock_client):
    """Test that failed fetches don't commit partial data."""
    db_path = tmp_path / "test.db"

    with closing(init_db(db_path)) as conn:
        html = fetch_year(2024, client=mock_client)
        shows = parse_shows(html, 2024)
        upsert_shows(conn, shows)

        try:
            fetch_year(1999, client=mock_client)
        except httpx.HTTPStatusError:
            conn.rollback()

        cursor = conn.execute("SELECT COUNT(*) FROM shows")
        assert cursor.fetchone()[0] == 0


def test_pipeline_idempotent(tmp_path, mock_client):
    """Test that running the pipeline twice produces the same result."""
    db_path = tmp_path / "test.db"

    with closing(init_db(db_path)) as conn:
        for _ in range(2):
            for year in [2023, 2024]:
                html = fetch_year(year, client=mock_client)
                shows = parse_shows(html, year)
                upsert_shows(conn, shows)
            conn.commit()

        cursor = conn.execute("SELECT COUNT(*) FROM shows")
        assert cursor.fetchone()[0] == 3
