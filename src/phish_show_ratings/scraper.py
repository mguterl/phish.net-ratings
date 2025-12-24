import httpx
from selectolax.parser import HTMLParser

from .config import BASE_URL
from .models import Show


def extract_show_id(href: str) -> str:
    return href.removeprefix("/setlists/phish-").removesuffix(".html")


def parse_shows(html: str, year: int) -> list[Show]:
    parser = HTMLParser(html)
    table = parser.css_first("#ratings-list")
    if not table:
        return []

    shows = []
    for row in table.css("tbody tr"):
        cells = row.css("td")
        if len(cells) < 7:
            continue

        link = cells[1].css_first("a")
        if not link:
            continue

        href = link.attributes.get("href", "")
        if not href:
            continue

        shows.append(Show(
            show_id=extract_show_id(href),
            date=cells[1].text(strip=True),
            venue=cells[2].text(strip=True),
            city=cells[4].text(strip=True) or None,
            state=cells[5].text(strip=True) or None,
            country=cells[6].text(strip=True) or None,
            rating=float(cells[0].text(strip=True)),
            year=year,
        ))

    return shows


def fetch_year(year: int, client: httpx.Client | None = None) -> str:
    if client is None:
        response = httpx.get(f"{BASE_URL}/{year}", timeout=30)
    else:
        response = client.get(f"{BASE_URL}/{year}", timeout=30)
    response.raise_for_status()
    return response.text
