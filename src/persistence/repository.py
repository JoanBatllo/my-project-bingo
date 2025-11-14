#!/usr/bin/env python3
import sqlite3
from typing import List, Dict, Any, TypedDict, Optional

from .sql_constants import (
    CREATE_TABLE_PLAYERS,
    CREATE_TABLE_GAMES,
    CREATE_TABLE_RESULTS,
    CREATE_UNIQUE_IDX_PLAYERS_NAME,
    CREATE_IDX_RESULTS_PLAYER,
    CREATE_IDX_RESULTS_GAME,
    UPSERT_PLAYER_BY_NAME,
    INSERT_OR_IGNORE_PLAYER,
    SELECT_PLAYER_ID_BY_NAME,
    PLAIN_INSERT_PLAYER,
    INSERT_GAME,
    INSERT_RESULT,
    SELECT_LEADERBOARD,
)

class BingoRepository:
    """Handles all SQLite persistence for players, games, and results."""

    def __init__(self, db_path: str = "bingo.db"):
        self._conn: Optional[sqlite3.Connection] = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        # Pragmas for safety and concurrency
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            # WAL improves reader/writer concurrency; best-effort
            self._conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.DatabaseError:
            pass
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self._conn.cursor()
        # players
        cur.execute(CREATE_TABLE_PLAYERS)
        # games
        cur.execute(CREATE_TABLE_GAMES)
        # results
        cur.execute(CREATE_TABLE_RESULTS)
        # Useful indexes
        cur.execute(CREATE_UNIQUE_IDX_PLAYERS_NAME)
        cur.execute(CREATE_IDX_RESULTS_PLAYER)
        cur.execute(CREATE_IDX_RESULTS_GAME)
        self._conn.commit()

    # --- private helper ---

    def _get_or_create_player(self, name: str) -> int:
        """Return player ID, creating a new player if not found."""
        name = name.strip() or "Anonymous"
        cur = self._conn.cursor()
        # Try insert with upsert behavior, then select id.
        try:
            cur.execute(UPSERT_PLAYER_BY_NAME, (name,))
        except sqlite3.IntegrityError:
            # Fallback for older SQLite variants; proceed to select
            pass
        else:
            # If ON CONFLICT unsupported, try OR IGNORE
            if cur.rowcount == -1:  # Some drivers don't set rowcount reliably
                cur.execute(INSERT_OR_IGNORE_PLAYER, (name,))
        cur.execute(SELECT_PLAYER_ID_BY_NAME, (name,))
        row = cur.fetchone()
        if row:
            self._conn.commit()
            return int(row["id"])
        # As a last resort (should not happen), insert plainly
        cur.execute(PLAIN_INSERT_PLAYER, (name,))
        self._conn.commit()
        return int(cur.lastrowid)

    # --- public API ---

    class LeaderboardRow(TypedDict):
        name: str
        games_played: int
        wins: int
        win_rate: float

    def record_game_result(
        self,
        player_name: str,
        board_size: int,
        pool_max: int,
        won: bool,
        draws_count: int,
    ) -> None:
        """Insert a completed game and result into the database."""
        player_id = self._get_or_create_player(player_name)
        # Atomic write: both inserts commit or rollback together
        with self._conn:
            cur = self._conn.cursor()
            cur.execute(INSERT_GAME, (board_size, pool_max))
            game_id = int(cur.lastrowid)
            cur.execute(INSERT_RESULT, (player_id, game_id, 1 if won else 0, draws_count))

    def get_leaderboard(self, limit: int = 10) -> List["BingoRepository.LeaderboardRow"]:
        """Return leaderboard data (player name, wins, games, win rate)."""
        try:
            limit_val = max(1, int(limit))
        except (TypeError, ValueError):
            limit_val = 10
        cur = self._conn.cursor()
        cur.execute(SELECT_LEADERBOARD, (limit_val,))
        rows = cur.fetchall()
        # Convert and coerce numeric types
        out: List[BingoRepository.LeaderboardRow] = []
        for row in rows:
            out.append(
                {
                    "name": str(row["name"]),
                    "games_played": int(row["games_played"]),
                    "wins": int(row["wins"] or 0),
                    "win_rate": float(row["win_rate"] or 0.0),
                }
            )
        return out

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def __enter__(self) -> "BingoRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
