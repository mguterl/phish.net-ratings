import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from time import perf_counter


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        level = record.levelname
        msg = record.getMessage()

        baseline = logging.LogRecord("", 0, "", 0, None, None, None).__dict__
        extra = {k: v for k, v in record.__dict__.items()
                 if k not in baseline and not k.startswith("_")}

        fields = " ".join(f"{k}={v}" for k, v in extra.items())
        if fields:
            return f"{ts} {level:5} {msg} {fields}"
        return f"{ts} {level:5} {msg}"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("phish_show_ratings")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger


@contextmanager
def timed() -> Generator[dict[str, int]]:
    start = perf_counter()
    result: dict[str, int] = {"duration_ms": 0}
    try:
        yield result
    finally:
        result["duration_ms"] = int((perf_counter() - start) * 1000)
