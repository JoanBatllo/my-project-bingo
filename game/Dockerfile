FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY ./pyproject.toml /app/pyproject.toml
COPY ./uv.lock /app/uv.lock
RUN uv sync --frozen --no-dev --no-install-project

COPY ./src /app/src
COPY ./clients /app/clients
COPY ./ui /app/ui
CMD ["sh", "-c", "uv run streamlit run ui/app.py --server.address=${STREAMLIT_ADDRESS:-0.0.0.0} --server.port=${STREAMLIT_PORT:-8501}"]
