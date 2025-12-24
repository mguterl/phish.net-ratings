import csv

import pytest

from phish_show_ratings.export import write_csv
from phish_show_ratings.models import Show


@pytest.fixture
def sample_shows():
    return [
        Show("show-1", "2024-01-01", "Venue A", "City A", "ST", "USA", 4.5, 2024),
        Show("show-2", "2024-01-02", "Venue B", None, None, None, 4.0, 2024),
    ]


def test_write_csv_creates_file(tmp_path, sample_shows):
    path = tmp_path / "output.csv"
    write_csv(path, sample_shows)
    assert path.exists()


def test_write_csv_creates_parent_directories(tmp_path, sample_shows):
    path = tmp_path / "nested" / "dir" / "output.csv"
    write_csv(path, sample_shows)
    assert path.exists()


def test_write_csv_contains_header(tmp_path, sample_shows):
    path = tmp_path / "output.csv"
    write_csv(path, sample_shows)

    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)

    assert header == ["show_id", "date", "venue", "city", "state", "country", "rating"]


def test_write_csv_contains_data(tmp_path, sample_shows):
    path = tmp_path / "output.csv"
    write_csv(path, sample_shows)

    with open(path) as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0] == ["show-1", "2024-01-01", "Venue A", "City A", "ST", "USA", "4.5"]


def test_write_csv_handles_none_values(tmp_path, sample_shows):
    path = tmp_path / "output.csv"
    write_csv(path, sample_shows)

    with open(path) as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)

    assert rows[1] == ["show-2", "2024-01-02", "Venue B", "", "", "", "4.0"]


def test_write_csv_empty_shows(tmp_path):
    path = tmp_path / "output.csv"
    write_csv(path, [])

    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert header == ["show_id", "date", "venue", "city", "state", "country", "rating"]
    assert rows == []
