import json
from unittest.mock import Mock

import httpx
import pytest

from phish_show_ratings.models import Show
from phish_show_ratings.scraper import extract_show_id, fetch_year, parse_shows


def test_extract_show_id():
    href = "/setlists/phish-december-29-2024-madison-square-garden-new-york-ny-usa.html"
    expected = "december-29-2024-madison-square-garden-new-york-ny-usa"
    assert extract_show_id(href) == expected


def test_extract_show_id_simple():
    href = "/setlists/phish-test-show.html"
    assert extract_show_id(href) == "test-show"


def ratings_html(rows):
    return (
        "<html><script>PhishNet.State = "
        + json.dumps({"top_rated_shows_data": rows})
        + "; otherCode();</script></html>"
    )


@pytest.fixture
def show_row():
    return {
        "showDate": "2024-12-29",
        "showUrl": "/setlists/phish-december-29-2024-msg.html",
        "venue": "Madison Square Garden",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "rating": 4.6184,
        "ratingLabel": "4.618",
    }


@pytest.mark.parametrize(
    "html",
    [
        "<html></html>",
        '<table id="ratings-list"></table>',
        "<script>PhishNet.State = {broken};</script>",
        "<script>PhishNet.State = {};</script>",
        '<script>PhishNet.State = {"top_rated_shows_data": null};</script>',
    ],
)
def test_parse_shows_rejects_missing_or_invalid_data(html):
    with pytest.raises(ValueError, match="ratings data for 2024"):
        parse_shows(html, 2024)


def test_parse_shows_explicit_empty_year():
    assert parse_shows(ratings_html([]), 2006) == []


def test_parse_shows_valid_state(show_row):
    shows = parse_shows(ratings_html([show_row]), 2024)
    assert len(shows) == 1
    assert shows[0] == Show(
        "december-29-2024-msg",
        "2024-12-29",
        "Madison Square Garden",
        "New York",
        "NY",
        "USA",
        4.618,
        2024,
    )


def test_parse_shows_optional_location(show_row):
    show_row.update(city="", state=None, country="")
    show = parse_shows(ratings_html([show_row]), 2024)[0]
    assert (show.city, show.state, show.country) == (None, None, None)


def test_parse_shows_rounds_like_displayed_rating(show_row):
    show_row["rating"] = 3.7055
    assert parse_shows(ratings_html([show_row]), 2024)[0].rating == 3.706


@pytest.mark.parametrize(
    "key,value",
    [
        ("showDate", "2023-12-29"),
        ("showDate", "not-a-date"),
        ("showUrl", "https://example.com/show"),
        ("venue", ""),
        ("city", []),
        ("rating", True),
        ("rating", "4.5"),
        ("rating", -1),
        ("rating", 6),
        ("rating", float("nan")),
        ("rating", float("inf")),
    ],
)
def test_parse_shows_rejects_invalid_rows(show_row, key, value):
    show_row[key] = value
    with pytest.raises(ValueError, match="Invalid ratings data"):
        parse_shows(ratings_html([show_row]), 2024)


def test_parse_shows_rejects_missing_field(show_row):
    del show_row["rating"]
    with pytest.raises(ValueError, match="Invalid ratings data"):
        parse_shows(ratings_html([show_row]), 2024)


def test_parse_shows_rejects_duplicate_shows(show_row):
    with pytest.raises(ValueError, match="Duplicate show IDs"):
        parse_shows(ratings_html([show_row, show_row]), 2024)


def test_fetch_year_with_mocked_client():
    mock_response = Mock()
    mock_response.text = "<html>mocked</html>"
    mock_response.raise_for_status = Mock()

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    result = fetch_year(2024, client=mock_client)

    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "2024" in call_args[0][0]
    assert result == "<html>mocked</html>"


def test_fetch_year_raises_on_http_error():
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=Mock(), response=Mock()
    )

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    try:
        fetch_year(2024, client=mock_client)
        assert False, "Expected HTTPStatusError"
    except httpx.HTTPStatusError:
        pass
