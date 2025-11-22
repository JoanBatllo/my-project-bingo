# Docker Deployment Plan

This document consolidates the early design for containerizing *My Project Bingo*.
It explains how we will build the Docker image, orchestrate multiple containers
with Docker Compose, and configure networking, volumes, and environment
variables. Although the plan may evolve, documenting it in one place keeps the
direction clear for future iterations.

## 1. Container Build Strategy (Dockerfiles)

Each service ships with its own Dockerfile under its folder:

- **game/Dockerfile** – installs `uv`, syncs deps from `pyproject.toml` + `uv.lock`, copies the game package, and runs Streamlit on port 8501.
- **persistence/Dockerfile** – installs `uv`, syncs deps from its `pyproject.toml` + `uv.lock`, copies the persistence package, and runs the FastAPI app on port 8000.

Both images inherit from `python:3.12-slim`, set `PYTHONPATH=/app/src`, and use `uv sync --frozen --no-dev --no-install-project` during build to match the committed lockfiles.

## 2. Runtime Services (Docker Compose)

Compose builds **two images**, each from its own Dockerfile:

- **`persistence`**
  - Purpose: exposes a FastAPI app (`src.persistence.api:app`) backed by SQLite.
  - Image: `my-project-bingo-persistence` (built from `persistence/Dockerfile`) which runs
    `uvicorn ... --port 8000`.
  - Ports: binds container port `8000` to host `8000` for browser access or
    service-to-service communication.
  - Environment: `BINGO_DB_PATH` so records and API reads are consistent.

- **`bingo-game`**
  - Purpose: publishes the Streamlit UI for playing/viewing bingo in the
    browser; talks to the persistence API over HTTP.
  - Image: `my-project-bingo-game` (built from `game/Dockerfile`) which runs
    `streamlit run game/ui/app.py`.
  - Ports: binds container port `8501` to host `8501` for browser access.
  - Environment: `PERSISTENCE_URL` pointing to the persistence service (set to
    `http://persistence:8000` in Compose).

- **Future `tests` profile (optional)**
  - Could reuse the image to launch `uv run pytest`. Keeping this as a profile
    prevents the container from starting automatically but documents how CI or
    developers can run the full suite inside Docker.

## 3. Networking, Volumes, and Environment

- **Network Topology** – A custom bridge network `bingo-network` connects the two
  services. They can communicate internally using service names (e.g., `persistence:8000`),
  while both services publish ports to the host for browser access.
- **Persistent Volume** – A bind mount from `./persistence/data` to `/app/data` in the
  persistence service. SQLite stores `bingo.db` there so data survives container restarts.
  The volume is only mounted in the persistence service, not shared between containers.
  If we later replace SQLite with another backend, the volume mount points are the only
  change needed in Compose.
- **Environment Variables** – `BINGO_DB_PATH` standardizes how code discovers
  the database location. Additional knobs (e.g., logging levels, API limits)
  should be surfaced the same way so containers remain configuration-driven.
- **Resource Considerations** – even though we build two images, both inherit
  from the shared base stage so runtimes and dependencies stay perfectly in
  sync.

## 4. Detailed Deployment Topology

Before rendering the workflow, we spell out each responsibility:

- **Dockerfile pipeline** – base `python:3.12-slim`, install `uv`, copy
  dependency manifests and application code, run `uv sync --no-dev`. Each service
  has its own Dockerfile that builds a separate runtime image.
- **API image** – built from `persistence/Dockerfile`, exposes port `8000`, and runs
  `uv run uvicorn persistence.api.api:app --host 0.0.0.0 --port 8000`.
- **Streamlit image** – built from `game/Dockerfile`, exposes `8501`, and runs
  `streamlit run game/ui/app.py --server.address=0.0.0.0 --server.port=8501`.
- **Compose services** – `persistence` runs Uvicorn exposing
  `GET /leaderboard` and `POST /results`, while `bingo-game`
  publishes `8501:8501` and calls the persistence API via `PERSISTENCE_URL`.
  Future optional profiles (tests or linting) would reuse the same pattern.
- **Persistence** – bind mount from `./persistence/data` to `/app/data` stores the
  SQLite DB; the persistence service uses `BINGO_DB_PATH` environment variable.
- **Networking** – custom bridge network `bingo-network` provides internal connectivity;
  both services map host ports so browsers can reach them.

```
        +------------------+        +-----------------------+
        |   bingo-game      |        |   persistence         |
        | (Streamlit UI)    |        | (FastAPI / Uvicorn)   |
        | Port: 8501        |        | Port: 8000            |
        +---------+---------+        +-----------+-----------+
                  |                              |
                  |   HTTP (PERSISTENCE_URL)    |
                  +--------------+---------------+
                                 |
                    bind mount: ./persistence/data
                    (/app/data/bingo.db)
```

```mermaid
flowchart TD
    %% Dockerfile build chain
    subgraph GameDockerfile["Game Dockerfile"]
        G1["Base Image: python:3.12-slim"]
        G2["Install uv tool"]
        G3["Copy game/ (pyproject.toml + code)"]
        G4["Run uv sync --no-dev"]
        G1 --> G2 --> G3 --> G4
    end

    subgraph PersistenceDockerfile["Persistence Dockerfile"]
        P1["Base Image: python:3.12-slim"]
        P2["Install uv tool"]
        P3["Copy persistence/ (pyproject.toml + code)"]
        P4["Run uv sync --no-dev"]
        P1 --> P2 --> P3 --> P4
    end

    subgraph Images["Final Docker Images"]
        API_IMG["API image\n(persistence/Dockerfile, EXPOSE 8000)"]
        ST_IMG["Streamlit image\n(game/Dockerfile, EXPOSE 8501)"]
    end
    P4 --> API_IMG
    G4 --> ST_IMG

    subgraph Compose["Docker Compose Services"]
        direction LR
        subgraph ST["bingo-game container"]
            S1["Runs Streamlit image"]
            S2["Publishes 8501:8501"]
        end
        subgraph API["persistence container"]
            L1["Runs API image"]
            L2["Exposes GET /leaderboard + POST /results"]
            L3["Publishes 8000:8000"]
        end
    end
    ST_IMG --> S1
    API_IMG --> L1

    subgraph Volume["Bind Mount"]
        V1["SQLite DB ./persistence/data/bingo.db"]
        V2["Mounted at /app/data"]
    end
    L1 -->|BINGO_DB_PATH| V2
    V2 --> V1

    subgraph Network["bingo-network (Bridge)"]
        N1["Internal service communication"]
    end
    ST <--> N1
    API <--> N1
    S1 -->|HTTP (PERSISTENCE_URL)| API
    L3 -->|host port 8000| Host[(External clients)]
    S2 -->|host port 8501| Host

    subgraph Future["Future Expansion"]
        F1["Tests profile (pytest)"]
        F2["Linting service (ruff/mypy)"]
        F3["Additional APIs (stats, multiplayer)"]
    end
    Compose --> Future

    %% Styling
    classDef build fill:#fde68a,stroke:#d97706,color:#7c2d12;
    classDef image fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;
    classDef service fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef data fill:#fef3c7,stroke:#f97316,color:#7c2d12;
    classDef net fill:#f3e8ff,stroke:#9333ea,color:#581c87;
    classDef future fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;

    class A1,A2,A3,A4,A5,BaseStage build;
    class API_IMG,ST_IMG image;
    class S1,S2,L1,L2,L3 service;
    class V1 data;
    class N1,Host net;
    class F1,F2,F3 future;
```

## 5. Next Steps

- Prototype the FastAPI leaderboard endpoint locally to confirm the container
  boundaries satisfy the data-sharing requirements.
- Decide whether the `tests` profile should become part of CI or stay manual.
- Evaluate logging/monitoring needs (e.g., mount a separate volume for logs or
  add structured logging env vars) once the services run for extended periods.

This single document now captures the full deployment plan, making it easier to
track updates as the architecture matures.
