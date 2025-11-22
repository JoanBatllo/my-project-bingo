FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy persistence project (build context is ./persistence, so copy everything)
COPY . /app
RUN uv venv && uv sync --no-dev

CMD ["uv", "run", "uvicorn", "persistence.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
