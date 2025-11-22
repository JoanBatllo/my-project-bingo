# My-project-bingo: Streamlit Bingo

![Tests](https://github.com/JoanBatllo/my-project-bingo/actions/workflows/tests.yml/badge.svg)

## Overview

**My Project Bingo** is a simple Bingo game developed in Python with a **Streamlit** web UI. Generate a configurable Bingo card (`3×3`, `4×4`, or `5×5`), draw random numbers without repetition, automatically mark hits on your card, and validate "Bingo!" in the browser.

This project is built following **Scrum methodology**, divided into sprints, with a focus on modular, testable, and maintainable code.

## Features

- Configurable board size (`3×3`, `4×4`, or `5×5`)
- Customizable number pool (configurable maximum value)
- Optional free center for odd-sized boards (3×3, 5×5)
- Random, non-repeating number draws from a shuffled pool
- Automatic marking of numbers when drawn (if present on your card)
- "Bingo!" validation (rows, columns, diagonals)
- Display-only bingo card with visual indicators for marked cells
- Real-time game metrics (board size, last draw, drawn count, remaining pool)
- Draw history tracking (shows recent draws)
- SQLite-backed leaderboard exposed via a persistence service
- Record game results (wins/losses) to the leaderboard
- View leaderboard standings with player statistics (games played, wins, win rate)
- Cached leaderboard API calls for better performance
- Player name customization for leaderboard entries
- Unit and integration tests with `pytest`

## Project Structure

```text
└── my-project-bingo
    ├── game/                    # Streamlit UI + game logic (game package)
    │   ├── pyproject.toml       # runtime deps for the game container
    │   ├── uv.lock
    │   ├── Dockerfile
    │   ├── game/                # game package source code
    │   │   ├── core/            # bingo_card, number_drawer (win checks via BingoCard.has_bingo)
    │   │   ├── clients/         # persistence_client (HTTP client for persistence service)
    │   │   └── ui/              # streamlit app.py
    │   └── tests/               # unit tests for game package
    ├── persistence/             # FastAPI persistence/leaderboard service
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   ├── Dockerfile
    │   ├── persistence/         # persistence package source code
    │   │   ├── core/            # repository, constants
    │   │   └── api/             # FastAPI endpoints
    │   └── tests/               # unit tests for persistence package
    ├── tests-integration/       # integration tests (full game flow, repository flow, streamlit app)
    ├── docker-compose.yml       # runs persistence + game containers on a shared bridge
    ├── Makefile                 # common tasks (build, up, down, test, lint)
    └── docs/                    # architecture and docker plan
```

## Installation & Setup

### Prerequisites

- **Docker** and **Docker Compose** (for running the application)
- **uv** package manager (for local development and testing)
- **Python 3.10+** (for local development)

### 1. Clone the repository

```bash
git clone https://github.com/JoanBatllo/my-project-bingo.git
cd my-project-bingo
```

### 2. Install dependencies (for local development)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

## How to Run the Game

### Using Docker Compose (Recommended)

The easiest way to run the application is using the provided Makefile commands:

> **Tip**: Run `make help` to see all available Makefile commands.

```bash
# Build and start all services
make build
make up

# Or rebuild and restart (useful after code changes)
make rebuild
```

Alternatively, you can use Docker Compose directly:

```bash
docker compose build
docker compose up persistence bingo-game
```

**Access the application:**

- **Persistence API**: <http://localhost:8000>
- **Streamlit UI**: <http://localhost:8501> (talks to persistence at `http://persistence:8000` inside the network)

### How to Play

1. **Configure your game** (in the sidebar):
   - Select board size (3×3, 4×4, or 5×5)
   - Set the maximum number in the pool
   - Enable free center (for odd-sized boards only)
   - Enter your player name (optional, defaults to "Anonymous")

2. **Start a new game**: Click "New game / reset" to generate a new bingo card

3. **Draw numbers**: Click "Draw next number" to draw a random number from the pool
   - If the drawn number is on your card, it will be automatically marked
   - The draw history shows all numbers drawn so far

4. **Check for Bingo**: The app automatically detects when you complete a line (row, column, or diagonal)
   - Click "Call Bingo" to verify your win

5. **Save your result**:
   - Click "Save as win" if you got Bingo (only enabled when Bingo is detected)
   - Click "Save as loss" to record a game that didn't result in Bingo

6. **View leaderboard**: The leaderboard shows player statistics including games played, wins, and win rate
   - Click "Refresh leaderboard" to update the standings

### Stop the application

```bash
make down
# or
docker compose down
```

### View logs

To view container logs:

```bash
make logs
# or
docker compose logs -f
```

## How to Run Tests

All tests are written with **pytest**. The project uses **uv** for dependency management.

### Run all tests (Recommended)

Using the Makefile:

```bash
make test
```

This runs:

- Unit tests for the persistence package
- Unit tests for the game package
- Integration tests

### Run tests individually

```bash
# Run persistence unit tests
make test-persistence
# or
cd persistence && uv run pytest

# Run game unit tests
make test-game
# or
cd game && uv run pytest

# Run integration tests
make test-integration
# or
uv run pytest tests-integration/
```

### Run tests with coverage

Each package has its own coverage configuration. Coverage reports are generated in HTML format:

```bash
# Run tests with coverage for persistence
cd persistence && uv run pytest

# Run tests with coverage for game
cd game && uv run pytest
```

Coverage HTML reports are available in `persistence/htmlcov/` and `game/htmlcov/` respectively.

## Code Quality

### Linting

The project uses **ruff** for linting and code formatting:

```bash
# Check for linting issues
make lint

# Auto-fix linting issues
make lint-fix
```

### Clean up

Remove caches and coverage artifacts:

```bash
make clean
```

## Continuous Integration (GitHub Actions)

This project includes a **CI workflow** that automatically runs all tests when pushing to `main`. The workflow is configured in `.github/workflows/tests.yml`.

## Technologies Used

- **Python 3.10+** (project requires Python >=3.10)
- **Streamlit** - Web UI framework
- **FastAPI** - REST API framework for persistence service
- **SQLite** - Database for leaderboard persistence
- **Docker & Docker Compose** - Containerization and orchestration
- **uv** - Fast Python package manager
- **pytest & pytest-cov** - Testing framework and coverage reporting
- **ruff** - Fast Python linter and formatter
- **requests** - HTTP client library for persistence service communication
- **GitHub Actions** - CI/CD pipeline
- **Scrum methodology** - Project management approach

## Documentation

- Architecture: [`docs/architecture.md`](docs/architecture.md)

## Team & Roles (Scrum)

- **Product Owner: Joan Batlló**
- **Developers: Adria Anglada, Teo Arqués, Natan Viejo, Marc Farras and Josep Cubedo**

## 📝 License

This project is licensed under the terms of the **MIT License**.
See the full text in the [LICENSE.md](LICENSE.md) file.
