#!/usr/bin/env python3
"""Persistence layer for the Bingo game using SQLite.

This module defines :class:`BingoRepository`, which encapsulates all data
access for players, games and results. It is responsible for:

- Creating and migrating the SQLite schema on first use.
- Recording completed games and their outcomes.
- Computing a simple leaderboard based on stored results.
"""

import sqlite3
from typing import List, Optional, TypedDict

from .sql_constants import (
    CREATE_TABLE_PLAYERS,
    CREATE_TABLE_GAMES,
    CREATE_TABLE_RESULTS,
    CREATE_TRIGGER_RESULTS_FK,
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
    """High-level API for storing players, games and results in SQLite.

    This class owns a single SQLite connection and exposes a small, focused
    interface for the rest of the application. It hides all SQL details behind
    simple Python methods.

    Attributes:
        _conn: The underlying SQLite connection. It is initialized in ``__init__``
            and closed in :meth:`close`.
    """

    class LeaderboardRow(TypedDict):
        """Typed dictionary representing one row of the leaderboard."""

        name: str
        games_played: int
        wins: int
        win_rate: float

    def __init__(self, db_path: str = "Data/bingo.db") -> None:
        """Initialize a new repository instance.

        The constructor opens a connection to the given SQLite database,
        configures a few pragmas (foreign keys, busy timeout, WAL if possible)
        and ensures that the schema exists.

        Args:
            db_path: Path to the SQLite database file. The default is
                ``"bingo.db"``. For tests or in-memory usage you can pass
                ``":memory:"`` or a temporary path.
        """
        self._conn: Optional[sqlite3.Connection] = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

        # Pragmas for safety and minimal concurrency support.
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            # WAL improves reader/writer concurrency; best-effort only.
            self._conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.DatabaseError:
            # On some environments this pragma may not be supported: ignore.
            pass

        self._create_schema()

    def _create_schema(self) -> None:
        """Create the database schema if it does not exist."""
        cur = self._conn.cursor()
        # Core tables.
        cur.execute(CREATE_TABLE_PLAYERS)
        cur.execute(CREATE_TABLE_GAMES)
        cur.execute(CREATE_TABLE_RESULTS)
        # Useful indexes for fast lookups and leaderboard queries.
        cur.execute(CREATE_UNIQUE_IDX_PLAYERS_NAME)
        cur.execute(CREATE_IDX_RESULTS_PLAYER)
        cur.execute(CREATE_IDX_RESULTS_GAME)
        # Trigger for enforcing FK-like behavior on other connections (tests)
        cur.execute(CREATE_TRIGGER_RESULTS_FK)
        self._conn.commit()

    # --- Private helpers -----------------------------------------------------

    def _get_or_create_player(self, name: str) -> int:
        """Return the ID of a player, creating it if necessary.

        Player names are normalized by stripping whitespace; blank names are
        stored as ``\"Anonymous\"``.

        This method attempts an UPSERT-first strategy using the SQL statement
        provided in :data:`UPSERT_PLAYER_BY_NAME`. On older SQLite versions
        that do not support ``ON CONFLICT``, it falls back to an
        ``INSERT OR IGNORE`` / ``SELECT`` pattern, and as a last resort
        performs a plain insert.

        Args:
            name: Display name of the player.

        Returns:
            The integer primary key of the player in the ``players`` table.
        """
        name = name.strip() or "Anonymous"
        cur = self._conn.cursor()

        # Try insert with upsert behavior, then select id.
        try:
            cur.execute(UPSERT_PLAYER_BY_NAME, (name,))
        except sqlite3.IntegrityError:
            # Fallback for older SQLite variants; proceed to SELECT below.
            pass
        else:
            # Some drivers do not reliably set rowcount; we still proceed to SELECT.
            if cur.rowcount == -1:
                cur.execute(INSERT_OR_IGNORE_PLAYER, (name,))

        cur.execute(SELECT_PLAYER_ID_BY_NAME, (name,))
        row = cur.fetchone()
        if row:
            self._conn.commit()
            return int(row["id"])

        # As a last resort (should rarely happen), insert plainly.
        cur.execute(PLAIN_INSERT_PLAYER, (name,))
        self._conn.commit()
        return int(cur.lastrowid)

    # --- Public API ----------------------------------------------------------

    def record_game_result(
        self,
        player_name: str,
        board_size: int,
        pool_max: int,
        won: bool,
        draws_count: int,
    ) -> None:
        """Record the outcome of a completed game.

        This method inserts a row into the ``games`` table and a corresponding
        row into the ``results`` table inside a single atomic transaction.

        Args:
            player_name: Name of the player who played the game.
            board_size: Size of the Bingo board (e.g. 3, 4, or 5 for N×N).
            pool_max: Maximum number in the draw pool (e.g. 75).
            won: Whether the player won the game (``True``) or lost (``False``).
            draws_count: Total number of draws that happened in this game.
        """
        player_id = self._get_or_create_player(player_name)

        # Atomic write: both inserts commit or rollback together.
        with self._conn:
            cur = self._conn.cursor()
            cur.execute(INSERT_GAME, (board_size, pool_max))
            game_id = int(cur.lastrowid)
            cur.execute(
                INSERT_RESULT,
                (player_id, game_id, 1 if won else 0, draws_count),
            )

    def get_leaderboard(
        self,
        limit: int = 10,
    ) -> List["BingoRepository.LeaderboardRow"]:
        """Return aggregated leaderboard data.

        The leaderboard is computed from the ``results`` table and typically
        includes, for each player:

        - name
        - games played
        - wins
        - win rate (wins / games played)

        Args:
            limit: Maximum number of players to return. Values less than 1 are
                coerced to 1. If parsing fails, a default of 10 is used.

        Returns:
            A list of :class:`LeaderboardRow` dictionaries ordered by the
            ranking defined in :data:`SELECT_LEADERBOARD`.
        """
        try:
            limit_val = max(1, int(limit))
        except (TypeError, ValueError):
            limit_val = 10

        cur = self._conn.cursor()
        cur.execute(SELECT_LEADERBOARD, (limit_val,))
        rows = cur.fetchall()

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
        """Close the underlying SQLite connection.

        It is safe to call this method multiple times; after the first call
        the internal connection reference is set to ``None``.
        """
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def __enter__(self) -> "BingoRepository":
        """Enter the context manager.

        This allows usage such as:

        .. code-block:: python

            with BingoRepository() as repo:
                repo.record_game_result(...)

        Returns:
            The current :class:`BingoRepository` instance.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit the context manager and close the connection.

        Args:
            exc_type: Optional exception type raised inside the context.
            exc: Optional exception instance.
            tb: Optional traceback object.

        This method always closes the connection by delegating to
        :meth:`close`.
        """
        self.close()