# My-project-bingo: Streamlit Bingo

![Tests](https://github.com/JoanBatllo/my-project-bingo/actions/workflows/tests.yml/badge.svg)

## Overview
**My Project Bingo** is a simple Bingo game developed in Python with a **Streamlit** web UI. Generate a configurable Bingo card (`3×3`, `4×4`, or `5×5`), draw random numbers without repetition, mark hits automatically, and validate "Bingo!" in the browser.

This project is built following **Scrum methodology**, divided into sprints, with a focus on modular, testable, and maintainable code.

## Features
- Configurable board size (`3×3`, `4×4`, `5×5`)
- Random, non-repeating number draws
- Automatic and manual marking of numbers
- “Bingo!” validation (rows, columns, diagonals)
- Streamlit UI with clickable cells, draw controls, and live status
- SQLite-backed leaderboard exposed via a persistence service (record wins/losses and view standings in-app)
- Unit and integration tests with `pytest`

## Project Structure

└── my-project-bingo
    ├── game/               # Streamlit UI + game logic (game package)
    │   ├── pyproject.toml  # runtime deps for the game container
    │   ├── uv.lock
    │   ├── Dockerfile
    │   └── src/game/...    # bingo_card, number_drawer, leaderboard_client, ui/streamlit_app.py (win checks via BingoCard.has_bingo)
    ├── persistence/        # FastAPI persistence/leaderboard service
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   ├── Dockerfile
    │   └── src/persistence/...  # repository, api endpoints
    ├── tests/              # unit + integration tests (import from game.* / persistence.*)
    ├── docker-compose.yml  # runs persistence + game containers on a shared bridge
    ├── Makefile            # common tasks (build, up, down, test)
    └── docs/               # architecture and docker plan

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/JoanBatllo/my-project-bingo.git
cd my-project-bingo
```

## How to run the game
- Build and run via Docker Compose:
  ```bash
  docker compose build
  docker compose up persistence bingo-game
  ```
  - Persistence API: http://localhost:8000
  - Streamlit UI: http://localhost:8501 (talks to persistence at `http://persistence:8000` inside the network)

- Local testing-only (no Docker): ensure `PYTHONPATH=game/src:persistence/src` then run `pytest`.

## How to Run Tests

All tests are written with **pytest**.

### Run all tests
```bash
PYTHONPATH=game/src:persistence/src pytest
```

### Run tests with coverage
```bash
PYTHONPATH=game/src:persistence/src pytest --cov=game --cov=persistence --cov-report=term-missing
```

## Continuous Integration (GitHub Actions)

This project includes a **CI workflow** that automatically runs all tests when pushing to `main`.

The workflow (tests.yml) will need updates if you change paths; currently CI may not reflect the split containers.

## Technologies Used
- **Python 3.12**
- **pytest / pytest-cov**
- **GitHub Actions (CI/CD)**
- **Scrum methodology**

## Documentation
- Architecture: [`docs/architecture.md`](docs/architecture.md)

## Future Improvements
- Multiplayer mode (local or online)
- Save/load Bingo sessions
- Add difficulty modes and random events
- Optional graphical interface (Tkinter or web)
- Sound effects and animations for “Bingo!”

## Team & Roles (Scrum)
- **Product Owner: Joan Batlló**
- **Scrum Master: Josep Cubedo**
- **Developers: Adria Anglada, Teo Arqués, Natan Viejo, Marc Farras**

## 📝 License
This project is licensed under the terms of the **MIT License**.
See the full text in the [LICENSE.md](LICENSE.md) file.
