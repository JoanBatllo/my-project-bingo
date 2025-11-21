FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY ./pyproject.toml /app/pyproject.toml
COPY ./uv.lock /app/uv.lock
COPY ./src /app/src
RUN uv sync --frozen --no-dev

CMD ["sh", "-c", "uv run uvicorn src.api:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}"]
