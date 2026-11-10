run:
	uv run flask --app main run --host 0.0.0.0 --port 8080

test:
	uv run python -m pytest -q

lint:
	uv run ruff check .