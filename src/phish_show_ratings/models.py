from dataclasses import dataclass


@dataclass
class Show:
    show_id: str
    date: str
    venue: str
    city: str | None
    state: str | None
    country: str | None
    rating: float
    year: int
