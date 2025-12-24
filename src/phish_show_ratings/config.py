from pathlib import Path

BASE_URL = "https://phish.net/music/ratings"
START_YEAR = 1984
DATA_DIR = Path.cwd() / "data"
DB_PATH = DATA_DIR / "ratings.db"
CSV_DIR = DATA_DIR / "csv"
