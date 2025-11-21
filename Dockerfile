FROM python:3.12-slim AS base

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md LICENSE.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src
COPY main.py .

FROM base AS cli
CMD ["uv", "run", "python", "main.py"]

FROM base AS api
EXPOSE 8000
CMD [
    "uv",
    "run",
    "uvicorn",
    "src.api.leaderboard:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]
