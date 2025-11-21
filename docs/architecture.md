## Architecture Overview

This project implements a small, modular Bingo game with a Streamlit web UI. The core is framework‑agnostic Python code living under `game/src/game`; presentation lives in `game/src/ui/streamlit_app.py`. The persistence service lives under `persistence/src/persistence`. Tests validate the game logic end‑to‑end.

### Goals
- Keep core logic pure and testable
- Deterministic randomness via optional seeds
- Clear separation between game logic and UI

### Modules
- `game/src/game/bingo_card.py`
  - `BingoCard`: Generates an N×N grid of unique numbers in the range [1..pool_max].
  - Supports `free_center` for odd N: the center cell is set to 0 and always marked.
  - Operations:
    - `find(number) -> (r,c) | None`
    - `auto_mark_if_present(number) -> bool`
    - `toggle_mark(r,c)` (no‑op for free center)
    - `render(color_fn=None) -> str` for human‑readable output
- `game/src/game/number_drawer.py`
  - `NumberDrawer`: Supplies numbers from a shuffled pool [1..pool_max] without repetition.
  - Operations:
    - `draw() -> int | None`
    - `remaining() -> int`
    - `reset(seed: int | None = None)`
- (win checking now lives in `BingoCard.has_bingo`)
  - Validates completed rows, columns, and diagonals using only the set of marked coordinates. This keeps it UI‑agnostic and easy to test.
- `game/src/game/leaderboard_client.py`
  - Thin HTTP client that calls the persistence service (`PERSISTENCE_URL`) for fetching the leaderboard and recording game results. No direct imports of persistence code are used inside the game package.
- `game/src/ui/streamlit_app.py`
  - Streamlit interface that wires user actions (draw, toggle marks, call bingo) to the game modules and renders the board interactively.
- `persistence/src/persistence/repository.py`
  - SQLite repository containing all DB access, migrations, and leaderboard aggregation.
- `persistence/src/persistence/api.py`
  - FastAPI service exposing `/health`, `/leaderboard`, and `/results` endpoints backed by `BingoRepository`. Runs in its own container and is consumed over HTTP by the game/UI container.

### Data Model
- `BingoCard.grid: list[list[int]]` — 2D array of numbers; free center is represented by `0` when enabled.
- `BingoCard.marked: set[tuple[int,int]]` — coordinates marked as hit.
- `NumberDrawer._pile: list[int]` — remaining numbers to draw.
- `NumberDrawer.drawn: list[int]` — history of numbers drawn (for UI/status only).

### Randomness & Reproducibility
- Both `BingoCard` and `NumberDrawer` accept an optional `seed` to initialize their own `random.Random` instance. This allows deterministic cards and draw sequences in tests or demos.
- `NumberDrawer.reset(seed=...)` updates the RNG seed when provided.

### Free Center Behavior
- For odd boards (e.g., 5×5), enabling `free_center=True` sets the center cell to `0`, keeps it permanently marked, and renders it as `FREE`.
- Toggling the center is ignored so it stays marked, which reduces the requirement to 4 additional marks for any line that includes the center.

### Error Handling
- `BingoCard` raises `ValueError` when:
  - `n` is not in {3,4,5}
  - `pool_max < n*n`
  - `free_center` is requested with even `n`
- `NumberDrawer` raises `ValueError` if `pool_max < 1`.

### Rendering
- `BingoCard.render` determines a fixed cell width based on the largest number (and the word `FREE`) and optionally applies a `color_fn(text, name)` callable to style elements without hard‑coupling to any terminal library.

### Integration Flow
1. Create `BingoCard` and `NumberDrawer` with the same (optional) seed.
2. Repeatedly draw a number.
3. Call `auto_mark_if_present` on the card.
4. Check `card.has_bingo` after each draw.

### Testing Strategy
- Unit tests cover:
  - Card construction, uniqueness, marking, free center, and rendering basics
  - Number drawing without repetition, reset behavior, and seeded reproducibility
  - Win detection on rows, columns, and diagonals
- An integration test simulates the minimal gameplay loop to ensure modules work together.

### Directory Structure (relevant)
```
game/
  src/game/
    bingo_card.py
    number_drawer.py
    (win checks now on BingoCard)
    leaderboard_client.py
  src/ui/
    streamlit_app.py
persistence/
  src/persistence/
    repository.py
    api.py
tests/
  unit/
  integration/
```

### Related Documentation
- For setup, running the game, and test commands, see the main project README: [README.md](../README.md)
