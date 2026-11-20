run:
	uv run flask --app main run --host 0.0.0.0 --port 8080

test:
	uv run python -m pytest -q

lint:
	uv run ruff check .

dev:
	npx concurrently "make run" "npx start-hexlet-devops-deploy-crud-frontend"