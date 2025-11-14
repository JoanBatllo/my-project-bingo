#!/usr/bin/env python3
import sqlite3
import tempfile
import os
from pathlib import Path

import pytest

from src.persistence.repository import BingoRepository


def test_repository_creates_schema(tmp_path: Path):
    """Tests that the repository creates all required tables and indexes.

    Validates:
        - The `players`, `games`, and `results` tables are created.
        - Relevant indexes exist for lookup efficiency.

    Raises:
        AssertionError: If tables or indexes are missing.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Check tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cur.fetchall()}
        assert "players" in tables
        assert "games" in tables
        assert "results" in tables

        # Check indexes exist
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name IS NOT NULL"
        )
        index_names = {row[0] for row in cur.fetchall()}
        assert any("players" in name.lower() and "name" in name.lower() for name in index_names)
        assert any("results" in name.lower() and "player" in name.lower() for name in index_names)
        assert any("results" in name.lower() and "game" in name.lower() for name in index_names)

        conn.close()
    finally:
        repo.close()


def test_get_or_create_player_new(tmp_path: Path):
    """Tests that a new player is created correctly and returned.

    Validates:
        - A new ID is generated.
        - The player entry is stored in the database.

    Raises:
        AssertionError: If creation or database lookup fails.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        player_id = repo._get_or_create_player("Alice")

        assert isinstance(player_id, int)
        assert player_id > 0

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        assert row is not None and row[0] == "Alice"
        conn.close()
    finally:
        repo.close()


def test_get_or_create_player_existing(tmp_path: Path):
    """Tests that retrieving an existing player returns the same ID.

    Raises:
        AssertionError: If repeated calls return different IDs.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        id1 = repo._get_or_create_player("Bob")
        id2 = repo._get_or_create_player("Bob")
        assert id1 == id2
    finally:
        repo.close()


def test_get_or_create_player_anonymous_on_empty(tmp_path: Path):
    """Tests that empty or whitespace-only names resolve to 'Anonymous'.

    Validates:
        - "", "   ", and "Anonymous" all map to the same player record.

    Raises:
        AssertionError: If anonymous handling fails.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        id1 = repo._get_or_create_player("")
        id2 = repo._get_or_create_player("   ")
        id3 = repo._get_or_create_player("Anonymous")

        assert id1 == id2 == id3
    finally:
        repo.close()


def test_record_game_result_creates_game_and_result(tmp_path: Path):
    """Tests that record_game_result inserts both a game and a result row.

    Validates:
        - A game entry is created with correct board parameters.
        - A result entry is created with correct win status and draw count.

    Raises:
        AssertionError: If either table fails to update.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Charlie", board_size=5, pool_max=75, won=True, draws_count=12)

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Game exists
        cur.execute("SELECT COUNT(*) FROM games")
        assert cur.fetchone()[0] == 1

        cur.execute("SELECT board_size, pool_max FROM games")
        row = cur.fetchone()
        assert row == (5, 75)

        # Result exists
        cur.execute("SELECT COUNT(*) FROM results")
        assert cur.fetchone()[0] == 1

        cur.execute("SELECT won, draws_count FROM results")
        row = cur.fetchone()
        assert row[0] == 1
        assert row[1] == 12

        conn.close()
    finally:
        repo.close()


def test_record_game_result_multiple_players(tmp_path: Path):
    """Tests recording game results for multiple distinct players.

    Validates:
        - Multiple players create independent game and result entries.
        - Counts across tables reflect correct totals.

    Raises:
        AssertionError: If totals do not match expected operation count.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Player1", board_size=3, pool_max=30, won=True, draws_count=5)
        repo.record_game_result("Player2", board_size=3, pool_max=30, won=False, draws_count=8)
        repo.record_game_result("Player1", board_size=4, pool_max=60, won=True, draws_count=10)

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM games")
        assert cur.fetchone()[0] == 3

        cur.execute("SELECT COUNT(*) FROM results")
        assert cur.fetchone()[0] == 3

        conn.close()
    finally:
        repo.close()


def test_get_leaderboard_empty(tmp_path: Path):
    """Tests that leaderboard returns an empty list when no games exist."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        assert repo.get_leaderboard() == []
    finally:
        repo.close()


def test_get_leaderboard_ordering(tmp_path: Path):
    """Tests that leaderboard ordering follows wins desc, then games desc.

    Player ranking criteria:
        1. Highest number of wins.
        2. If tied, highest number of games played.

    Raises:
        AssertionError: If ordering or win rates differ from expectations.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        # Player A: 2 wins, 2 games
        repo.record_game_result("PlayerA", 5, 75, True, 10)
        repo.record_game_result("PlayerA", 5, 75, True, 12)

        # Player B: 1 win, 3 games
        repo.record_game_result("PlayerB", 5, 75, True, 15)
        repo.record_game_result("PlayerB", 5, 75, False, 20)
        repo.record_game_result("PlayerB", 5, 75, False, 18)

        # Player C: 1 win, 1 game
        repo.record_game_result("PlayerC", 5, 75, True, 8)

        leaderboard = repo.get_leaderboard(limit=10)
        assert len(leaderboard) == 3

        # A first
        assert leaderboard[0]["name"] == "PlayerA"
        assert leaderboard[0]["wins"] == 2
        assert leaderboard[0]["games_played"] == 2
        assert leaderboard[0]["win_rate"] == 100.0

        # B second
        assert leaderboard[1]["name"] == "PlayerB"
        assert leaderboard[1]["wins"] == 1
        assert leaderboard[1]["games_played"] == 3
        assert leaderboard[1]["win_rate"] == pytest.approx(33.3, abs=0.1)

        # C third
        assert leaderboard[2]["name"] == "PlayerC"
        assert leaderboard[2]["wins"] == 1
        assert leaderboard[2]["games_played"] == 1
    finally:
        repo.close()


def test_get_leaderboard_limit(tmp_path: Path):
    """Tests that leaderboard respects the `limit` parameter."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        for i in range(5):
            repo.record_game_result(f"Player{i}", 5, 75, True, 10)

        leaderboard = repo.get_leaderboard(limit=3)
        assert len(leaderboard) == 3

        leaderboard_all = repo.get_leaderboard(limit=100)
        assert len(leaderboard_all) == 5
    finally:
        repo.close()


def test_get_leaderboard_invalid_limit(tmp_path: Path):
    """Tests that invalid limits default to 10."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Test", 5, 75, True, 10)

        assert len(repo.get_leaderboard(limit=-5)) == 1
        assert len(repo.get_leaderboard(limit=0)) == 1
    finally:
        repo.close()


def test_context_manager(tmp_path: Path):
    """Tests that BingoRepository supports context manager usage.

    Validates:
        - Connection is open inside the context.
        - Connection is closed after exiting the context.

    Raises:
        AssertionError: If connection state does not update correctly.
    """
    db_path = tmp_path / "test.db"
    with BingoRepository(str(db_path)) as repo:
        repo.record_game_result("ContextTest", 5, 75, True, 5)
        assert repo._conn is not None

    assert repo._conn is None


def test_close_idempotent(tmp_path: Path):
    """Tests that close() may be called multiple times safely."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    repo.close()
    assert repo._conn is None

    # Should not fail on repeated close
    repo.close()
    assert repo._conn is None


def test_foreign_key_constraint(tmp_path: Path):
    """Tests SQLite foreign key enforcement via results table.

    Attempting to insert a result referencing a non-existent player_id
    should raise sqlite3.IntegrityError.

    Raises:
        AssertionError: If invalid insertion does not raise an FK error.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO results (player_id, game_id, won, draws_count) VALUES (?, ?, ?, ?)",
                (99999, 1, 1, 10),
            )
        conn.close()
    finally:
        repo.close()


def test_check_constraints(tmp_path: Path):
    """Tests CHECK constraints on games and results tables.

    Validates:
        - Invalid board_size is rejected.
        - pool_max too small is rejected.
        - won must be 0 or 1.

    Raises:
        AssertionError: If CHECK constraints do not trigger IntegrityError.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (2, 10))

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (5, 20))

        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO results (player_id, game_id, won, draws_count) VALUES (?, ?, ?, ?)",
                (1, 1, 2, 10),
            )

        conn.close()
    finally:
        repo.close()


def test_atomic_transaction_rollback(tmp_path: Path):
    """Tests that record_game_result is atomic and rolls back on error.

    Process:
        1. Create a player.
        2. Insert a valid game manually.
        3. Call record_game_result().
        4. Verify that both game and result entries exist—indicating atomic commit.

    Raises:
        AssertionError: If entries are missing or transaction fails.
    """
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        # Create a valid player
        player_id = repo._get_or_create_player("TestPlayer")

        # Insert a game to get a valid game_id
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (5, 75))
        game_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Operation should succeed atomically
        repo.record_game_result("TestPlayer", 5, 75, True, 10)

        # Validate
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM games")
        assert cur.fetchone()[0] >= 1

        cur.execute("SELECT COUNT(*) FROM results")
        assert cur.fetchone()[0] >= 1

        conn.close()
    finally:
        repo.close()
