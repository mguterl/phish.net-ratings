from unittest.mock import Mock

import httpx

from phish_show_ratings.scraper import extract_show_id, fetch_year, parse_shows


def test_extract_show_id():
    href = "/setlists/phish-december-29-2024-madison-square-garden-new-york-ny-usa.html"
    expected = "december-29-2024-madison-square-garden-new-york-ny-usa"
    assert extract_show_id(href) == expected


def test_extract_show_id_simple():
    href = "/setlists/phish-test-show.html"
    assert extract_show_id(href) == "test-show"


def test_parse_shows_empty_html():
    shows = parse_shows("<html></html>", 2024)
    assert shows == []


def test_parse_shows_no_table():
    html = "<html><body><div>No table here</div></body></html>"
    shows = parse_shows(html, 2024)
    assert shows == []


def test_parse_shows_with_valid_table():
    html = """
    <table id="ratings-list"><tbody><tr>
        <td>4.618</td>
        <td><a href="/setlists/phish-december-29-2024-msg.html">2024-12-29</a></td>
        <td>Madison Square Garden</td>
        <td>Extra Cell</td>
        <td>New York</td>
        <td>NY</td>
        <td>USA</td>
    </tr></tbody></table>
    """
    shows = parse_shows(html, 2024)
    assert len(shows) == 1
    assert shows[0].show_id == "december-29-2024-msg"
    assert shows[0].date == "2024-12-29"
    assert shows[0].venue == "Madison Square Garden"
    assert shows[0].city == "New York"
    assert shows[0].state == "NY"
    assert shows[0].country == "USA"
    assert shows[0].rating == 4.618
    assert shows[0].year == 2024


def test_parse_shows_skips_rows_without_link():
    html = """
    <table id="ratings-list">
        <tbody>
            <tr>
                <td>4.0</td>
                <td>No link here</td>
                <td>Venue</td>
                <td>Extra</td>
                <td>City</td>
                <td>State</td>
                <td>Country</td>
            </tr>
        </tbody>
    </table>
    """
    shows = parse_shows(html, 2024)
    assert shows == []


def test_parse_shows_skips_rows_with_insufficient_cells():
    html = """
    <table id="ratings-list">
        <tbody>
            <tr>
                <td>4.0</td>
                <td><a href="/setlists/phish-test.html">Date</a></td>
            </tr>
        </tbody>
    </table>
    """
    shows = parse_shows(html, 2024)
    assert shows == []


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
