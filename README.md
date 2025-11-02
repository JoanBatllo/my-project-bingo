# My-project-bingo: Terminal Bingo

![Tests](https://github.com/JoanBatllo/my-project-bingo/actions/workflows/tests.yml/badge.svg)

## Overview
**My Project Bingo** is a simple **terminal-based Bingo game** developed in Python.  
It allows players to generate a configurable Bingo card (`3×3`, `4×4`, or `5×5`), draw random numbers without repetition, mark hits automatically, and validate "Bingo!", all within a clean command-line interface.

This project is built following **Scrum methodology**, divided into sprints, with a focus on modular, testable, and maintainable code.

## Features
- Configurable board size (`3×3`, `4×4`, `5×5`)
- Random, non-repeating number draws
- Automatic and manual marking of numbers
- “Bingo!” validation (rows, columns, diagonals)
- Fully functional terminal UI
- Unit and integration tests with `pytest`

## Project Structure

└── my-project-bingo  
    ├── LICENSE.md  
    ├── README.md  
    ├── docs  
    │   ├── README_SCRUM.md  
    │   ├── architecture.md  
    │   └── changelog.md  
    ├── main.py  
    ├── requirements.txt  
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
    │       └── cli.py  
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

### 2. Create a Virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## How to run the game
```bash
python main.py
```

Commands available inside the game:  
 • S → Show current Bingo card  
 • D → Draw a number (auto-marks if found)  
 • M r,c → Manually toggle a cell mark (e.g. M 1,2)  
 • B → Call “Bingo!” (system validates)  
 • I → Show current game status  
 • R → Reset and generate a new card  
 • Q → Quit the game  

## How to Run Tests

All tests are written with **pytest**.

### Run all tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov=src --cov-report=term-missing
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
