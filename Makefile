.PHONY: check lint typecheck test fix

check: lint typecheck test

lint:
	uv run ruff check .

typecheck:
	uv run mypy src/phish_show_ratings

test:
	uv run pytest

fix:
	uv run ruff check --fix .
