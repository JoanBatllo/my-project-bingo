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
- Unit and integration tests with `pytest`

## Project Structure

└── my-project-bingo
    ├── LICENSE.md
    ├── README.md
    ├── docs
    │   └── architecture.md
    ├── main.py
    ├── pyproject.toml
    ├── uv.lock
    ├── src
    │   ├── __init__.py
    │   ├── game
    │   │   ├── __init__.py
    │   │   ├── bingo_card.py
    │   │   ├── exceptions.py
    │   │   ├── number_drawer.py
    │   │   └── win_checker.py
    │   └── ui
    │       ├── __init__.py
    │       └── streamlit_app.py
    └── tests
        ├── integration
        │   ├── __init__.py
        │   └── test_full_game_flow.py
        └── unit
            ├── __init__.py
            ├── test_bingo_card.py
            ├── test_number_drawer.py
            └── test_win_checker.py

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/JoanBatllo/my-project-bingo.git
cd my-project-bingo
```

### 2. Install dependencies with [uv](https://github.com/astral-sh/uv)
```bash
uv sync
```

`uv sync` will create `.venv/` for you and install both runtime and dev dependencies.

### 3. Activate the environment (optional)
```bash
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
```
If you prefer not to activate the virtual environment, prefix commands with `uv run ...`.

## How to run the game
```bash
uv run streamlit run src/ui/streamlit_app.py
```
You can also use `make streamlit` or `make run`. The app launches at http://localhost:8501 with clickable cells, draw controls, and live bingo status.

### Run via Docker
```bash
make docker-build
make docker-run
```
Streamlit via Docker Compose:
```bash
docker compose up bingo-streamlit
```
`docker-run` builds and starts the API container; `docker compose up bingo-streamlit` launches the Streamlit UI.

## How to Run Tests

All tests are written with **pytest**.

### Run all tests
```bash
uv run pytest
```

### Run tests with coverage
```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Continuous Integration (GitHub Actions)

This project includes a **CI workflow** that automatically runs all tests when pushing to `main`.

The workflow:
1. Sets up Python 3.12
2. Installs dependencies
3. Runs pytest with coverage

Workflow file: `.github/workflows/tests.yml`

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
