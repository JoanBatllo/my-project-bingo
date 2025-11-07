#!/usr/bin/env python3
import sqlite3
from typing import List, Dict, Any


class BingoRepository:
    """Handles all SQLite persistence for players, games, and results."""

    def __init__(self, db_path: str = "bingo.db"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self._conn.cursor()
        # players
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # games
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_size INTEGER NOT NULL,
                pool_max INTEGER NOT NULL,
                finished_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # results
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                won INTEGER NOT NULL,
                draws_count INTEGER NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
            """
        )
        self._conn.commit()

    # --- private helper ---

    def _get_or_create_player(self, name: str) -> int:
        """Return player ID, creating a new player if not found."""
        name = name.strip() or "Anonymous"
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM players WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return int(row["id"])
        cur.execute("INSERT INTO players (name) VALUES (?)", (name,))
        self._conn.commit()
        return int(cur.lastrowid)

    # --- public API ---

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
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO games (board_size, pool_max) VALUES (?, ?)",
            (board_size, pool_max),
        )
        game_id = int(cur.lastrowid)
        cur.execute(
            """
            INSERT INTO results (player_id, game_id, won, draws_count)
            VALUES (?, ?, ?, ?)
            """,
            (player_id, game_id, 1 if won else 0, draws_count),
        )
        self._conn.commit()

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return leaderboard data (player name, wins, games, win rate)."""
        sql = """
        SELECT
            p.name AS name,
            COUNT(*) AS games_played,
            SUM(CASE WHEN r.won = 1 THEN 1 ELSE 0 END) AS wins,
            ROUND(
                100.0 * SUM(CASE WHEN r.won = 1 THEN 1 ELSE 0 END)
                / COUNT(*),
                1
            ) AS win_rate
        FROM results r
        JOIN players p ON p.id = r.player_id
        GROUP BY p.id, p.name
        ORDER BY wins DESC, games_played DESC
        LIMIT ?;
        """
        cur = self._conn.cursor()
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "BingoRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()