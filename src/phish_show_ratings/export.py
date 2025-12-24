import csv
from pathlib import Path

from .models import Show

COLUMNS = ["show_id", "date", "venue", "city", "state", "country", "rating"]


def write_csv(path: Path, shows: list[Show]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows([
            (s.show_id, s.date, s.venue, s.city, s.state, s.country, s.rating)
            for s in shows
        ])
