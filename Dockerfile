FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY main.py .

EXPOSE 8080

CMD ["sh", "-c", "exec uv run --no-sync flask --app main run --host 0.0.0.0 --port ${PORT:-8080}"]
