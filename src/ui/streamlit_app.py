#!/usr/bin/env python3
"""Streamlit interface for visualizing and playing Bingo."""

from __future__ import annotations

from typing import Tuple

import streamlit as st

from src.game.bingo_card import BingoCard
from src.game.number_drawer import NumberDrawer
from src.game.win_checker import has_bingo


DEFAULT_POOL_BY_SIZE = {3: 30, 4: 60, 5: 75}


def _default_pool_max(board_size: int) -> int:
    return DEFAULT_POOL_BY_SIZE.get(board_size, board_size * board_size)


def _reset_game(board_size: int, pool_max: int, free_center: bool) -> None:
    st.session_state.card = BingoCard(
        n=board_size,
        pool_max=pool_max,
        free_center=free_center,
    )
    st.session_state.drawer = NumberDrawer(pool_max=pool_max)
    st.session_state.last_draw: int | None = None
    st.session_state.draw_history: list[int] = []
    st.session_state.config = {
        "board_size": board_size,
        "pool_max": int(pool_max),
        "free_center": bool(free_center),
    }


def _ensure_game() -> None:
    if "card" in st.session_state and "drawer" in st.session_state:
        return
    default_size = 5
    _reset_game(default_size, _default_pool_max(default_size), free_center=False)


def _draw_number() -> Tuple[int | None, bool]:
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


def main() -> None:
    st.set_page_config(
        page_title="Bingo Visualizer",
        page_icon="🎉",
        layout="wide",
    )
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
        if st.button("New game / reset", use_container_width=True):
            _reset_game(board_size, pool_max, free_center)
            st.success("New card ready!")

    metrics = st.columns(4)
    metrics[0].metric("Board", f"{card.n}×{card.n}")
    metrics[1].metric("Last draw", st.session_state.last_draw or "—")
    metrics[2].metric("Drawn so far", len(drawer.drawn))
    metrics[3].metric("Remaining in pool", drawer.remaining())

    bingo_now = has_bingo(card.marked, card.n)
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
        if has_bingo(card.marked, card.n):
            st.success("BINGO! ✅")
        else:
            st.warning("Not yet. Keep going!")

    _render_card()

    st.subheader("Draw history")
    if st.session_state.draw_history:
        recent = ", ".join(map(str, st.session_state.draw_history[-15:]))
        st.write(f"Recent draws ({len(st.session_state.draw_history)} total): {recent}")
    else:
        st.write("No numbers drawn yet.")


if __name__ == "__main__":
    main()
