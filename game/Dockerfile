FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy game project (build context is ./game, so copy everything)
COPY . /app
RUN uv venv && uv sync --no-dev

CMD ["uv", "run", "streamlit", "run", "game/ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
