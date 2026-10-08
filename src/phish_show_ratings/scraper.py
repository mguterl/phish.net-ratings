import json
import math
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import httpx
from selectolax.parser import HTMLParser

from .config import BASE_URL
from .models import Show


def extract_show_id(href: str) -> str:
    return href.removeprefix("/setlists/phish-").removesuffix(".html")


def parse_shows(html: str, year: int) -> list[Show]:
    parser = HTMLParser(html)
    for script in parser.css("script"):
        text = script.text()
        match = re.search(r"\bPhishNet\.State\s*=\s*", text)
        if match is None:
            continue
        try:
            state, _ = json.JSONDecoder().raw_decode(text[match.end() :].lstrip())
            rows = state["top_rated_shows_data"]
            if not isinstance(rows, list):
                raise ValueError("Ratings data must be a list")
            shows = [_parse_show(row, year) for row in rows]
            if len({show.show_id for show in shows}) != len(shows):
                raise ValueError("Duplicate show IDs")
            return shows
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid ratings data for {year}: {exc}") from exc
    raise ValueError(f"Missing PhishNet.State ratings data for {year}")


def _parse_show(row: Any, year: int) -> Show:
    def string(key: str, *, optional: bool = False) -> str | None:
        value = row[key]
        if optional and value in (None, ""):
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid {key}")
        return value

    show_date = string("showDate")
    href = string("showUrl")
    venue = string("venue")
    assert show_date is not None and href is not None and venue is not None
    if date.fromisoformat(show_date).year != year:
        raise ValueError("Show date does not match requested year")
    if not href.startswith("/setlists/phish-") or not href.endswith(".html"):
        raise ValueError("Invalid show URL")
    rating = row["rating"]
    if (
        isinstance(rating, bool)
        or not isinstance(rating, (int, float))
        or not math.isfinite(rating)
        or not 0 <= rating <= 5
    ):
        raise ValueError("Invalid rating")
    # Preserve the three-decimal precision of the original displayed ratings.
    return Show(
        show_id=extract_show_id(href),
        date=show_date,
        venue=venue,
        city=string("city", optional=True),
        state=string("state", optional=True),
        country=string("country", optional=True),
        rating=float(Decimal(str(rating)).quantize(Decimal("0.001"), ROUND_HALF_UP)),
        year=year,
    )


def fetch_year(year: int, client: httpx.Client | None = None) -> str:
    if client is None:
        response = httpx.get(f"{BASE_URL}/{year}", timeout=30)
    else:
        response = client.get(f"{BASE_URL}/{year}", timeout=30)
    response.raise_for_status()
    return response.text
