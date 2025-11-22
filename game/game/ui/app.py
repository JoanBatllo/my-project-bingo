#!/usr/bin/env python3
"""Streamlit interface for visualizing and playing Bingo."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from game.clients.persistence_client import PersistenceClient
from game.core.bingo_card import BingoCard
from game.core.number_drawer import NumberDrawer

DEFAULT_POOL_BY_SIZE = {3: 30, 4: 60, 5: 75}
ANALYTICS_HISTORY_LIMIT = 200
DEFAULT_PLAYER_NAMES = ["Player 1", "Player 2"]


def _default_pool_max(board_size: int) -> int:
    """Return the default pool maximum for a given board size.

    Args:
        board_size (int): Selected board dimension (N).

    Returns:
        int: Suggested maximum number for the draw pool.
    """
    return DEFAULT_POOL_BY_SIZE.get(board_size, board_size * board_size)


def _reset_game(board_size: int, pool_max: int, free_center: bool, player_names: list[str] | None = None) -> None:
    """Initialize session state for a new game.

    Args:
        board_size (int): The board dimension (N for an N×N grid).
        pool_max (int): Maximum number available in the draw pool.
        free_center (bool): Whether to enable a free center on odd boards.
        player_names (list[str] | None): Names for active players.
    """
    names = player_names or [st.session_state.get("player1_name", DEFAULT_PLAYER_NAMES[0])]
    st.session_state.player_names = [name.strip() or fallback for name, fallback in zip(names, DEFAULT_PLAYER_NAMES, strict=False)]
    st.session_state.cards = [
        BingoCard(
            n=board_size,
            pool_max=pool_max,
            free_center=free_center,
        )
        for _ in st.session_state.player_names
    ]
    st.session_state.drawer = NumberDrawer(pool_max=pool_max)
    st.session_state.last_draw: int | None = None
    st.session_state.draw_history: list[int] = []
    st.session_state.last_saved_result_map = {}
    st.session_state.config = {
        "board_size": board_size,
        "pool_max": int(pool_max),
        "free_center": bool(free_center),
    }
    st.session_state.multiplayer = len(st.session_state.player_names) > 1
    st.session_state.winner_name = None
    st.session_state.winner_recorded = False


def _ensure_game() -> None:
    """Ensure session state contains a card and drawer.

    Initializes a default game configuration if no game state exists.
    Uses a 5×5 board with default pool size and no free center.
    """
    if "cards" in st.session_state and "drawer" in st.session_state:
        return
    default_size = 5
    st.session_state.player1_name = st.session_state.get("player1_name", DEFAULT_PLAYER_NAMES[0])
    st.session_state.player2_name = st.session_state.get("player2_name", DEFAULT_PLAYER_NAMES[1])
    _reset_game(default_size, _default_pool_max(default_size), free_center=False, player_names=[st.session_state.player1_name])


def _draw_number() -> tuple[int | None, dict[int, bool]]:
    """Draw a number and auto-mark all active cards.

    Returns:
        Tuple[int | None, dict[int, bool]]: The drawn number (or None) and per-player hit map.
    """
    drawer: NumberDrawer = st.session_state.drawer
    cards: list[BingoCard] = st.session_state.cards
    num = drawer.draw()
    st.session_state.last_draw = num
    if num is None:
        return None, {}
    st.session_state.draw_history.append(num)
    hits: dict[int, bool] = {}
    for idx, card in enumerate(cards):
        hits[idx] = card.auto_mark_if_present(num)
    return num, hits


def _render_card(card: BingoCard, title: str) -> None:
    """Render a bingo card as a display-only grid."""
    center = (card.n // 2, card.n // 2) if (card.n % 2 == 1 and card.free_center) else None

    st.subheader(title)
    for r in range(card.n):
        cols = st.columns(card.n, gap="small")
        for c in range(card.n):
            value = "FREE" if center == (r, c) else str(card.grid[r][c])
            marked = (r, c) in card.marked
            label = f"{'✅' if marked else '⬜️'} {value}"
            cols[c].write(label)


def _save_result_for(player_name: str, card: BingoCard, won: bool) -> None:
    """Persist a game outcome to the leaderboard database for a specific player."""
    client = PersistenceClient()
    draws_count = len(st.session_state.draw_history)
    signature = (player_name, won, card.n, card.pool_max, draws_count)
    cache = st.session_state.get("last_saved_result_map", {})
    if cache.get(player_name) == signature:
        return

    try:
        client.record_result(
            player_name=player_name,
            board_size=card.n,
            pool_max=card.pool_max,
            won=won,
            draws_count=draws_count,
        )
    except Exception as exc:  # noqa: BLE001 - surface to user
        st.error(f"Could not save result via persistence service: {exc}")
        return

    cache[player_name] = signature
    st.session_state.last_saved_result_map = cache
    st.session_state.leaderboard_cache = None
    st.session_state.history_cache = None


def _load_history(limit: int = ANALYTICS_HISTORY_LIMIT) -> list[dict]:
    """Load recent game history rows from the persistence service."""
    cached = st.session_state.get("history_cache")
    if cached is not None:
        return cached

    client = PersistenceClient()
    try:
        history_rows = client.fetch_history(limit=limit)
        st.session_state.history_cache = history_rows
        return history_rows
    except Exception as exc:  # noqa: BLE001 - surface to user
        st.error(f"Could not load history from persistence service: {exc}")
        st.session_state.history_cache = []
        return []


def _history_dataframe(history_rows: list[dict]) -> pd.DataFrame | None:
    """Convert history rows to a cleaned dataframe."""
    if not history_rows:
        return None
    df = pd.DataFrame(history_rows)
    if df.empty:
        return None
    df["played_at"] = pd.to_datetime(df["played_at"], errors="coerce")
    df["played_date"] = df["played_at"].dt.date
    return df


def _compute_streaks(wins: pd.Series) -> tuple[int, int]:
    """Compute longest win and loss streaks for a player's ordered results."""
    longest_win = longest_loss = 0
    current_win = current_loss = 0
    for won in wins:
        if bool(won):
            current_win += 1
            current_loss = 0
        else:
            current_loss += 1
            current_win = 0
        longest_win = max(longest_win, current_win)
        longest_loss = max(longest_loss, current_loss)
    return longest_win, longest_loss


def _render_analytics_tab() -> None:
    """Render the analytics dashboard."""
    st.subheader("Game insights")
    history_rows = _load_history()
    df = _history_dataframe(history_rows)

    if df is None or df.empty:
        st.info("No game history yet. Save a few games to unlock analytics.")
        return

    st.caption(f"Using the latest {len(df)} recorded games.")

    # Win rate trend
    st.markdown("##### Win rate trend over time")
    win_trend = (
        df.dropna(subset=["played_date"])
        .groupby("played_date")["won"]
        .mean()
        .mul(100)
        .reset_index(name="win_rate_pct")
    )
    if not win_trend.empty:
        win_trend = win_trend.sort_values("played_date")
        st.line_chart(win_trend.set_index("played_date")["win_rate_pct"], y_label="Win rate (%)")
    else:
        st.write("No dated games available.")

    st.divider()

    # Draw efficiency
    st.markdown("##### Draw efficiency")
    efficiency = df.groupby("board_size")["draws_count"].agg(["mean", "min", "max"]).round(2)
    st.dataframe(
        efficiency.rename(columns={"mean": "avg_draws", "min": "best", "max": "worst"}),
        width="stretch",
    )
    draw_hist = df["draws_count"].value_counts().sort_index()
    st.bar_chart(draw_hist, y_label="Games", x_label="Draws to finish")

    st.divider()

    # Board difficulty
    st.markdown("##### Board size difficulty")
    win_rate_by_size = df.groupby("board_size")["won"].mean().mul(100).sort_index()
    st.bar_chart(win_rate_by_size, y_label="Win rate (%)", x_label="Board size")

    st.divider()

    # Fastest win spotlight
    st.markdown("##### Fastest win")
    cols = st.columns(3)
    wins_df = df[df["won"]]
    if not wins_df.empty:
        # Require at least (board_size - 1) draws to avoid trivial/buggy wins
        wins_df = wins_df[wins_df["draws_count"] >= (wins_df["board_size"] - 1)]
    if not wins_df.empty:
        fastest = wins_df.sort_values(["draws_count", "played_at"]).iloc[0]
        cols[0].metric("Fastest win", f"{int(fastest['draws_count'])} draws", help="Fewest draws needed for a win")
        cols[1].metric("Board", f"{int(fastest['board_size'])}×{int(fastest['board_size'])}")
        cols[2].metric("Player", fastest["name"])
    else:
        cols[0].write("No wins recorded yet.")

    st.divider()

    # Player ranking with streaks and luck
    st.markdown("##### Player ranking (beyond win rate)")
    player_stats = (
        df.groupby("name")
        .agg(
            games=("won", "count"),
            wins=("won", "sum"),
            avg_draws=("draws_count", "mean"),
        )
        .assign(win_rate=lambda g: (g["wins"] / g["games"]).mul(100))
    )

    # Streaks per player (ordered by played_at)
    streak_win = {}
    streak_loss = {}
    for name, group in df.sort_values("played_at").groupby("name"):
        win_streak, loss_streak = _compute_streaks(group["won"])
        streak_win[name] = win_streak
        streak_loss[name] = loss_streak
    player_stats["longest_win_streak"] = pd.Series(streak_win)
    player_stats["longest_loss_streak"] = pd.Series(streak_loss)

    player_stats = player_stats.reset_index().rename(columns={"name": "player"})
    player_stats["avg_draws"] = player_stats["avg_draws"].round(1)
    player_stats["win_rate"] = player_stats["win_rate"].round(1)
    player_stats = player_stats.sort_values(by=["wins", "win_rate"], ascending=False)

    st.dataframe(
        player_stats[
            ["player", "games", "wins", "win_rate", "avg_draws", "longest_win_streak", "longest_loss_streak"]
        ],
        hide_index=True,
        width="stretch",
    )


def _record_multiplayer_results(winner_index: int) -> None:
    """Save results for all players, marking only one winner."""
    if st.session_state.get("winner_recorded"):
        return
    for idx, card in enumerate(st.session_state.cards):
        name = st.session_state.player_names[idx]
        _save_result_for(name, card, won=idx == winner_index)
    st.session_state.winner_recorded = True


def _render_gameplay(cards: list[BingoCard], drawer: NumberDrawer) -> None:
    """Render the main gameplay tab with single or multiplayer support."""
    prev_multiplayer = st.session_state.get("multiplayer", False)
    with st.sidebar:
        st.header("Game setup")
        enable_multiplayer = st.checkbox(
            "Multiplayer mode",
            value=prev_multiplayer,
            help="Two local players share the draw pool.",
        )
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
            "Player 1 name",
            key="player1_name",
            help="Name saved to the leaderboard when recording results.",
        )
        if enable_multiplayer:
            st.text_input(
                "Player 2 name",
                key="player2_name",
                help="Second player sharing the draw pool.",
            )
        requested_players = (
            [st.session_state.get("player1_name", DEFAULT_PLAYER_NAMES[0])]
            if not enable_multiplayer
            else [
                st.session_state.get("player1_name", DEFAULT_PLAYER_NAMES[0]),
                st.session_state.get("player2_name", DEFAULT_PLAYER_NAMES[1]),
            ]
        )
        if enable_multiplayer != prev_multiplayer:
            _reset_game(board_size, pool_max, free_center, player_names=requested_players)
            st.success("Multiplayer setting applied. New cards ready.")
        if st.button("New game / reset", width="stretch"):
            _reset_game(board_size, pool_max, free_center, player_names=requested_players)
            st.success("New card ready!")

    metrics = st.columns(4)
    metrics[0].metric("Board", f"{cards[0].n}×{cards[0].n}")
    metrics[1].metric("Last draw", st.session_state.last_draw or "—")
    metrics[2].metric("Drawn so far", len(drawer.drawn))
    metrics[3].metric("Remaining in pool", drawer.remaining())

    bingo_states = [card.has_bingo for card in cards]
    if st.session_state.get("winner_name"):
        st.success(f"{st.session_state.winner_name} already won this round. 🎉")
    elif any(bingo_states):
        st.success("Someone has Bingo! First to call it wins.")
    else:
        st.info("No bingo yet. Keep drawing numbers.")

    action_cols = st.columns([2, 1])
    if action_cols[0].button("Draw next number", width="stretch", disabled=bool(st.session_state.get("winner_name"))):
        num, hits = _draw_number()
        if num is None:
            st.warning("No numbers left to draw.")
        else:
            hit_players = [st.session_state.player_names[idx] for idx, was_hit in hits.items() if was_hit]
            if hit_players:
                st.success(f"Drew {num} — hit for {', '.join(hit_players)}!")
            else:
                st.write(f"Drew {num}. No hits this time.")

    if not st.session_state.get("multiplayer"):
        if action_cols[1].button("Call Bingo", width="stretch"):
            if cards[0].has_bingo:
                st.success("BINGO! ✅")
            else:
                st.warning("Not yet. Keep going!")

        save_cols = st.columns(2)
        if save_cols[0].button("Save as win", width="stretch", disabled=not cards[0].has_bingo):
            _save_result_for(st.session_state.player_names[0], cards[0], True)
        if save_cols[1].button("Save as loss", width="stretch"):
            _save_result_for(st.session_state.player_names[0], cards[0], False)
    else:
        st.markdown("#### Call Bingo")
        call_cols = st.columns(len(cards))
        for idx, card in enumerate(cards):
            name = st.session_state.player_names[idx]
            if call_cols[idx].button(
                f"Call Bingo ({name})",
                width="stretch",
                disabled=bool(st.session_state.get("winner_name")),
            ):
                if st.session_state.get("winner_name"):
                    st.info(f"{st.session_state.winner_name} already won.")
                elif card.has_bingo:
                    st.session_state.winner_name = name
                    st.success(f"{name} called Bingo first and wins!")
                    _record_multiplayer_results(idx)
                else:
                    st.warning(f"{name} does not have Bingo yet.")

    for idx, card in enumerate(cards):
        _render_card(card, f"{st.session_state.player_names[idx]}'s card")

    st.subheader("Leaderboard")
    if "leaderboard_cache" not in st.session_state or st.session_state.leaderboard_cache is None:
        client = PersistenceClient()
        try:
            leaderboard_rows = client.fetch_leaderboard(limit=10)
            st.session_state.leaderboard_cache = leaderboard_rows
        except Exception as exc:  # noqa: BLE001 - surface to user
            st.error(f"Could not load leaderboard from persistence service: {exc}")
            st.session_state.leaderboard_cache = []
            leaderboard_rows = []
    else:
        leaderboard_rows = st.session_state.leaderboard_cache

    if st.button("Refresh leaderboard", width="content"):
        client = PersistenceClient()
        try:
            leaderboard_rows = client.fetch_leaderboard(limit=10)
            st.session_state.leaderboard_cache = leaderboard_rows
            st.success("Leaderboard refreshed!")
        except Exception as exc:  # noqa: BLE001 - surface to user
            st.error(f"Could not load leaderboard from persistence service: {exc}")
            leaderboard_rows = st.session_state.leaderboard_cache

    if leaderboard_rows:
        sorted_rows = sorted(leaderboard_rows, key=lambda r: float(r["win_rate"]), reverse=True)
        display_rows = [
            {
                "Player": row["name"],
                "Games": row["games_played"],
                "Wins": row["wins"],
                "Win rate": f"{float(row['win_rate']) * 100:.1f}%",
            }
            for row in sorted_rows
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


def main() -> None:
    """Entry point for the Streamlit Bingo UI.

    Sets up the page configuration, initializes game state, and renders
    the complete user interface including game controls, leaderboard,
    draw history, and analytics.
    """
    st.set_page_config(
        page_title="Bingo Visualizer",
        page_icon="🎉",
        layout="wide",
    )
    _ensure_game()

    st.title("Bingo Visualizer")
    st.caption("Draw numbers, auto-mark hits, and watch for a winning line.")

    cards: list[BingoCard] = st.session_state.cards
    drawer: NumberDrawer = st.session_state.drawer

    game_tab, analytics_tab = st.tabs(["Play", "Analytics dashboard"])
    with game_tab:
        _render_gameplay(cards, drawer)
    with analytics_tab:
        _render_analytics_tab()


if __name__ == "__main__":
    main()
