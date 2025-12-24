from phish_show_ratings.models import Show


def test_show_creation():
    show = Show(
        show_id="december-29-2024-msg",
        date="2024-12-29",
        venue="Madison Square Garden",
        city="New York",
        state="NY",
        country="USA",
        rating=4.618,
        year=2024,
    )
    assert show.show_id == "december-29-2024-msg"
    assert show.rating == 4.618
    assert show.year == 2024


def test_show_with_none_location():
    show = Show(
        show_id="test-show",
        date="2024-01-01",
        venue="Test Venue",
        city=None,
        state=None,
        country=None,
        rating=4.0,
        year=2024,
    )
    assert show.city is None
    assert show.state is None
    assert show.country is None
