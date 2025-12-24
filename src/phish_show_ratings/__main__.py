import time
from contextlib import closing
from datetime import datetime

from .config import CSV_DIR, START_YEAR
from .db import get_shows_by_year, get_years, init_db, upsert_shows
from .export import write_csv
from .logging import setup_logging, timed
from .scraper import fetch_year, parse_shows


def main() -> None:
    logger = setup_logging()
    current_year = datetime.now().year
    total_shows = 0

    logger.info("Starting scrape")

    with timed() as run_t, closing(init_db()) as conn:
        for year in range(START_YEAR, current_year + 1):
            with timed() as t:
                html = fetch_year(year)
                shows = parse_shows(html, year)
                upsert_shows(conn, shows)

            if not shows:
                logger.warning("No shows found", extra={"year": year, **t})
            else:
                extra = {"year": year, "shows": len(shows), **t}
                logger.info("Fetched year", extra=extra)
                total_shows += len(shows)

            time.sleep(1)

        conn.commit()

        for year in get_years(conn):
            with timed() as t:
                shows = get_shows_by_year(conn, year)
                path = CSV_DIR / f"ratings_{year}.csv"
                write_csv(path, shows)
            logger.info("Exported CSV", extra={"year": year, "path": path.name, **t})

    logger.info("Run complete", extra={"total_shows": total_shows, **run_t})


if __name__ == "__main__":
    main()
