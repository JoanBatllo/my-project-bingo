#!/usr/bin/env python3
"""SQLite repository for Bingo game results and leaderboard."""

from __future__ import annotations

import sqlite3
from typing import Any

from persistence.core.constants import (
    CREATE_INDEX_PLAYERS_NAME,
    CREATE_INDEX_RESULTS_GAME_ID,
    CREATE_INDEX_RESULTS_PLAYER_ID,
    CREATE_TABLE_GAMES,
    CREATE_TABLE_PLAYERS,
    CREATE_TABLE_RESULTS,
    INSERT_GAME,
    INSERT_PLAYER,
    INSERT_RESULT,
    PRAGMA_FOREIGN_KEYS,
    PRAGMA_JOURNAL_MODE_WAL,
    SELECT_LEADERBOARD,
    SELECT_PLAYER_BY_NAME,
)


class BingoRepository:
    """Repository for managing Bingo game data in SQLite.

    Handles player management, game recording, and leaderboard queries.
    Supports context manager usage for automatic connection cleanup.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize the repository with a database connection.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory DB.
        """
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = sqlite3.connect(db_path)
        self._create_schema()

    def _create_schema(self) -> None:
        """Create database tables and indexes if they don't exist."""
        if self._conn is None:
            return

        cursor = self._conn.cursor()

        # Enable foreign keys
        cursor.execute(PRAGMA_FOREIGN_KEYS)

        # Enable WAL mode for better concurrency (ignore errors if not supported)
        try:
            cursor.execute(PRAGMA_JOURNAL_MODE_WAL)
        except sqlite3.Error:
            pass  # WAL may not be available in all SQLite versions

        # Players table
        cursor.execute(CREATE_TABLE_PLAYERS)

        # Games table
        cursor.execute(CREATE_TABLE_GAMES)

        # Results table
        cursor.execute(CREATE_TABLE_RESULTS)

        # Indexes for performance
        cursor.execute(CREATE_INDEX_PLAYERS_NAME)
        cursor.execute(CREATE_INDEX_RESULTS_PLAYER_ID)
        cursor.execute(CREATE_INDEX_RESULTS_GAME_ID)

        self._conn.commit()

    def _get_or_create_player(self, name: str) -> int:
        """Get existing player ID or create a new player.

        Empty or whitespace-only names are normalized to "Anonymous".

        Args:
            name: Player name (may be empty or whitespace).

        Returns:
            Player ID (integer).
        """
        if self._conn is None:
            raise RuntimeError("Repository connection is closed")

        # Normalize empty/whitespace names to "Anonymous"
        normalized_name = name.strip() if name.strip() else "Anonymous"

        cursor = self._conn.cursor()

        # Try to get existing player
        cursor.execute(SELECT_PLAYER_BY_NAME, (normalized_name,))
        row = cursor.fetchone()

        if row is not None:
            return row[0]

        # Create new player
        cursor.execute(INSERT_PLAYER, (normalized_name,))
        self._conn.commit()
        return cursor.lastrowid

    def record_game_result(
        self,
        player_name: str,
        board_size: int,
        pool_max: int,
        won: bool,
        draws_count: int,
    ) -> None:
        """Record a game result in the database.

        Creates or retrieves the player, creates a game entry, and records the result.
        All operations are performed atomically in a transaction.

        Args:
            player_name: Display name of the player.
            board_size: Board dimension (N for N×N grid).
            pool_max: Maximum number in the draw pool.
            won: Whether the player won.
            draws_count: Number of draws taken.
        """
        if self._conn is None:
            raise RuntimeError("Repository connection is closed")

        cursor = self._conn.cursor()

        try:
            # Get or create player
            player_id = self._get_or_create_player(player_name)

            # Create game entry
            cursor.execute(
                INSERT_GAME,
                (board_size, pool_max),
            )
            game_id = cursor.lastrowid

            # Create result entry
            cursor.execute(
                INSERT_RESULT,
                (player_id, game_id, 1 if won else 0, draws_count),
            )

            self._conn.commit()
        except sqlite3.Error as e:
            self._conn.rollback()
            raise RuntimeError(f"Failed to record game result: {e}") from e

    def get_leaderboard(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get leaderboard entries sorted by wins and games played.

        Args:
            limit: Maximum number of entries to return. Invalid values default to 1.

        Returns:
            List of dictionaries with keys: name, wins, games_played, win_rate.
        """
        if self._conn is None:
            raise RuntimeError("Repository connection is closed")

        # Coerce limit to valid integer, default to 1 if invalid
        try:
            limit_int = max(1, int(limit))
        except (ValueError, TypeError):
            limit_int = 1

        cursor = self._conn.cursor()

        cursor.execute(SELECT_LEADERBOARD, (limit_int,))

        rows = cursor.fetchall()
        return [
            {
                "name": row[0],
                "wins": row[1],
                "games_played": row[2],
                "win_rate": float(row[3]),
            }
            for row in rows
        ]

    def close(self) -> None:
        """Close the database connection.

        Safe to call multiple times (idempotent).
        """
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> BingoRepository:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - closes connection."""
        self.close()
