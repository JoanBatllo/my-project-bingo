#!/usr/bin/env python3
"""Streamlit interface for visualizing and playing Bingo."""

from __future__ import annotations

import streamlit as st

from game.clients.persistence_client import PersistenceClient
from game.core.bingo_card import BingoCard
from game.core.number_drawer import NumberDrawer

DEFAULT_POOL_BY_SIZE = {3: 30, 4: 60, 5: 75}


def _default_pool_max(board_size: int) -> int:
    """Return the default pool maximum for a given board size.

    Args:
        board_size (int): Selected board dimension (N).

    Returns:
        int: Suggested maximum number for the draw pool.
    """
    return DEFAULT_POOL_BY_SIZE.get(board_size, board_size * board_size)


def _reset_game(board_size: int, pool_max: int, free_center: bool) -> None:
    """Initialize session state for a new game.

    Args:
        board_size (int): The board dimension (N for an N×N grid).
        pool_max (int): Maximum number available in the draw pool.
        free_center (bool): Whether to enable a free center on odd boards.
    """
    st.session_state.card = BingoCard(
        n=board_size,
        pool_max=pool_max,
        free_center=free_center,
    )
    st.session_state.drawer = NumberDrawer(pool_max=pool_max)
    st.session_state.last_draw: int | None = None
    st.session_state.draw_history: list[int] = []
    st.session_state.last_saved_result = None
    st.session_state.config = {
        "board_size": board_size,
        "pool_max": int(pool_max),
        "free_center": bool(free_center),
    }


def _ensure_game() -> None:
    """Ensure session state contains a card and drawer.

    Returns:
        None
    """
    if "card" in st.session_state and "drawer" in st.session_state:
        return
    default_size = 5
    _reset_game(default_size, _default_pool_max(default_size), free_center=False)


def _draw_number() -> tuple[int | None, bool]:
    """Draw a number and auto-mark the card if present.

    Returns:
        Tuple[int | None, bool]: The drawn number (or None) and whether it was on the card.
    """
    drawer: NumberDrawer = st.session_state.drawer
    card: BingoCard = st.session_state.card
    num = drawer.draw()
    st.session_state.last_draw = num
    if num is None:
        return None, False
    st.session_state.draw_history.append(num)
    hit = card.auto_mark_if_present(num)
    return num, hit


def _render_card() -> None:
    """Render the bingo card with clickable cells.

    Returns:
        None
    """
    card: BingoCard = st.session_state.card
    center = (card.n // 2, card.n // 2) if (card.n % 2 == 1 and card.free_center) else None

    st.subheader("Your card")
    for r in range(card.n):
        cols = st.columns(card.n, gap="small")
        for c in range(card.n):
            value = "FREE" if center == (r, c) else str(card.grid[r][c])
            marked = (r, c) in card.marked
            label = f"{'✅' if marked else '⬜️'} {value}"
            button_kwargs = {"type": "primary"} if marked else {}
            if cols[c].button(label, key=f"cell-{r}-{c}", use_container_width=True, **button_kwargs):
                card.toggle_mark(r, c)
                st.session_state.card = card


def _save_result(won: bool) -> None:
    """Persist a game outcome to the leaderboard database.

    Args:
        won (bool): Whether the player won the game.
    """
    client = PersistenceClient()
    card: BingoCard = st.session_state.card
    if "player_name" not in st.session_state:
        st.session_state.player_name = "Anonymous"
    draws_count = len(st.session_state.draw_history)
    signature = (st.session_state.player_name, won, card.n, card.pool_max, draws_count)
    if st.session_state.get("last_saved_result") == signature:
        st.info("Result already saved.")
        return

    try:
        client.record_result(
            player_name=st.session_state.player_name,
            board_size=card.n,
            pool_max=card.pool_max,
            won=won,
            draws_count=draws_count,
        )
    except Exception as exc:  # noqa: BLE001 - surface to user
        st.error(f"Could not save result via persistence service: {exc}")
        return

    st.session_state.last_saved_result = signature
    st.success("Result saved to leaderboard.")


def main() -> None:
    """Entry point for the Streamlit Bingo UI."""
    st.set_page_config(
        page_title="Bingo Visualizer",
        page_icon="🎉",
        layout="wide",
    )
    # Initialize player_name before any widgets are created
    if "player_name" not in st.session_state:
        st.session_state.player_name = "Anonymous"
    _ensure_game()

    st.title("Bingo Visualizer")
    st.caption("Draw numbers, mark hits, and watch for a winning line.")

    card: BingoCard = st.session_state.card
    drawer: NumberDrawer = st.session_state.drawer

    with st.sidebar:
        st.header("Game setup")
        board_size = st.selectbox(
            "Board size (N×N)",
            options=[3, 4, 5],
            index=[3, 4, 5].index(st.session_state.config.get("board_size", 5)),
        )
        pool_default = _default_pool_max(board_size)
        current_config = st.session_state.config
        pool_seed = current_config["pool_max"] if current_config.get("board_size") == board_size else pool_default
        pool_max = st.number_input(
            "Max number in pool",
            min_value=board_size * board_size,
            max_value=500,
            value=int(pool_seed),
            step=1,
            help="Numbers are drawn from 1 up to this value with no repeats.",
        )
        free_center = st.checkbox(
            "Free center (odd boards only)",
            value=bool(current_config.get("free_center", False) and board_size % 2 == 1),
            disabled=board_size % 2 == 0,
        )
        st.text_input(
            "Player name",
            key="player_name",
            help="Name saved to the leaderboard when recording results.",
        )
        if st.button("New game / reset", use_container_width=True):
            _reset_game(board_size, pool_max, free_center)
            st.success("New card ready!")

    metrics = st.columns(4)
    metrics[0].metric("Board", f"{card.n}×{card.n}")
    metrics[1].metric("Last draw", st.session_state.last_draw or "—")
    metrics[2].metric("Drawn so far", len(drawer.drawn))
    metrics[3].metric("Remaining in pool", drawer.remaining())

    bingo_now = card.has_bingo
    if bingo_now:
        st.success("BINGO! You've completed a line. 🎉")
    else:
        st.info("No bingo yet. Keep drawing or marking manually.")

    action_cols = st.columns([2, 1])
    if action_cols[0].button("Draw next number", use_container_width=True):
        num, hit = _draw_number()
        if num is None:
            st.warning("No numbers left to draw.")
        elif hit:
            st.success(f"Drew {num} — it's on your card! Auto-marked.")
        else:
            st.write(f"Drew {num}. Not on your card.")

    if action_cols[1].button("Call Bingo", use_container_width=True):
        if card.has_bingo:
            st.success("BINGO! ✅")
        else:
            st.warning("Not yet. Keep going!")

    save_cols = st.columns(2)
    if save_cols[0].button("Save as win", use_container_width=True, disabled=not bingo_now):
        _save_result(True)
    if save_cols[1].button("Save as loss", use_container_width=True):
        _save_result(False)

    _render_card()

    st.subheader("Leaderboard")
    client = PersistenceClient()
    try:
        leaderboard_rows = client.fetch_leaderboard(limit=10)
    except Exception as exc:  # noqa: BLE001 - surface to user
        st.error(f"Could not load leaderboard from persistence service: {exc}")
        leaderboard_rows = []

    if leaderboard_rows:
        display_rows = [
            {
                "Player": row["name"],
                "Games": row["games_played"],
                "Wins": row["wins"],
                "Win rate": f"{row['win_rate']*100:.1f}%",
            }
            for row in leaderboard_rows
        ]
        st.dataframe(display_rows, hide_index=True)
    else:
        st.write("No games recorded yet.")

    st.subheader("Draw history")
    if st.session_state.draw_history:
        recent = ", ".join(map(str, st.session_state.draw_history[-15:]))
        st.write(f"Recent draws ({len(st.session_state.draw_history)} total): {recent}")
    else:
        st.write("No numbers drawn yet.")


# Streamlit executes this file directly and will call main() automatically
# We only call main() when actually running under Streamlit (not during imports)
if __name__ == "__main__":
    main()
