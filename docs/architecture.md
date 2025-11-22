# Architecture Overview

This project implements a small, modular Bingo game with a Streamlit web UI. The core is framework‑agnostic Python code living under `game/game`; presentation lives in `game/game/ui/app.py`. The persistence service lives under `persistence/persistence`. Tests validate the game logic end‑to‑end.

## Goals

- Keep core logic pure and testable
- Deterministic randomness via optional seeds
- Clear separation between game logic and UI

### Modules

- `game/game/core/bingo_card.py`
  - `BingoCard`: Generates an N×N grid of unique numbers in the range [1..pool_max].
  - Supports `free_center` for odd N: the center cell is set to 0 and always marked.
  - Operations:
    - `find(number) -> (r,c) | None`
    - `auto_mark_if_present(number) -> bool`
    - `toggle_mark(r,c)` (no‑op for free center)
    - `has_bingo` property: Validates completed rows, columns, and diagonals using only the set of marked coordinates. This keeps it UI‑agnostic and easy to test.
- `game/game/core/number_drawer.py`
  - `NumberDrawer`: Supplies numbers from a shuffled pool [1..pool_max] without repetition.
  - Operations:
    - `draw() -> int | None`
    - `remaining() -> int`
    - `reset(seed: int | None = None)`
- `game/game/clients/persistence_client.py`
  - Thin HTTP client that calls the persistence service (`PERSISTENCE_URL`) for fetching the leaderboard and recording game results. No direct imports of persistence code are used inside the game package.
- `game/game/ui/app.py`
  - Streamlit interface that wires user actions (draw numbers, call bingo, save results) to the game modules and renders display-only grids. Supports single-player and local multiplayer (two cards sharing one draw pile; first valid caller wins and both results are recorded). Analytics includes fastest-win with a guard that ignores wins with draws < board_size - 1.
- `persistence/persistence/core/repository.py`
  - SQLite repository containing all DB access, migrations, leaderboard aggregation, and cleanup of invalid legacy rows (e.g., zero-draw wins).
- `persistence/persistence/api/api.py`
  - FastAPI service exposing `/health`, `/leaderboard`, `/history` (analytics), and `/results` endpoints backed by `BingoRepository`. Runs in its own container and is consumed over HTTP by the game/UI container. Pydantic models live in `persistence/api/models.py`.

### Data Model

- `BingoCard.grid: list[list[int]]` — 2D array of numbers; free center is represented by `0` when enabled.
- `BingoCard.marked: set[tuple[int,int]]` — coordinates marked as hit.
- `NumberDrawer._pile: list[int]` — remaining numbers to draw.
- `NumberDrawer.drawn: list[int]` — history of numbers drawn (for UI/status only).
- `results.played_at: str` — UTC timestamp (SQLite datetime) when a game result was recorded, used by analytics/history.
- `session_state.cards: list[BingoCard]` — one per active player (length 1 for single-player, 2 for multiplayer).
- `session_state.player_names: list[str]` — names aligned to `cards`.

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

```text
game/
  game/
    core/
      bingo_card.py
      number_drawer.py
    clients/
      persistence_client.py
    ui/
      app.py
  tests/
    test_bingo_card.py
    test_number_drawer.py
    test_persistence_client.py
    test_app_utils.py
persistence/
  persistence/
    core/
      repository.py
      constants.py
    api/
      api.py
      models.py
  tests/
    test_repository.py
    test_api.py
tests-integration/
  test_full_game_flow.py
  test_repository_flow.py
  test_streamlit_app.py
  test_multiplayer_ui.py
```

### Related Documentation

- For setup, running the game, and test commands, see the main project README: [README.md](../README.md)
