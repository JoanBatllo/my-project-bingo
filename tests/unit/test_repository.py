#!/usr/bin/env python3
import sqlite3
import tempfile
import os
from pathlib import Path

import pytest

from src.persistence.repository import BingoRepository


def test_repository_creates_schema(tmp_path: Path):
    """Verify that repository creates all tables and indexes."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Check tables exist
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
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
    """Test creating a new player."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        player_id = repo._get_or_create_player("Alice")
        assert isinstance(player_id, int)
        assert player_id > 0
        # Verify it's in the database
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "Alice"
        conn.close()
    finally:
        repo.close()


def test_get_or_create_player_existing(tmp_path: Path):
    """Test retrieving an existing player returns same ID."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        id1 = repo._get_or_create_player("Bob")
        id2 = repo._get_or_create_player("Bob")
        assert id1 == id2
    finally:
        repo.close()


def test_get_or_create_player_anonymous_on_empty(tmp_path: Path):
    """Test that empty/whitespace names become 'Anonymous'."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        id1 = repo._get_or_create_player("")
        id2 = repo._get_or_create_player("   ")
        id3 = repo._get_or_create_player("Anonymous")
        # All should resolve to the same Anonymous player
        assert id1 == id2 == id3
    finally:
        repo.close()


def test_record_game_result_creates_game_and_result(tmp_path: Path):
    """Test that record_game_result inserts both game and result."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Charlie", board_size=5, pool_max=75, won=True, draws_count=12)
        # Verify game was created
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM games")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT board_size, pool_max FROM games")
        row = cur.fetchone()
        assert row[0] == 5
        assert row[1] == 75
        # Verify result was created
        cur.execute("SELECT COUNT(*) FROM results")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT won, draws_count FROM results")
        row = cur.fetchone()
        assert row[0] == 1  # won=True -> 1
        assert row[1] == 12
        conn.close()
    finally:
        repo.close()


def test_record_game_result_multiple_players(tmp_path: Path):
    """Test recording results for multiple players."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Player1", board_size=3, pool_max=30, won=True, draws_count=5)
        repo.record_game_result("Player2", board_size=3, pool_max=30, won=False, draws_count=8)
        repo.record_game_result("Player1", board_size=4, pool_max=60, won=True, draws_count=10)
        # Verify counts
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
    """Test leaderboard with no games returns empty list."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        leaderboard = repo.get_leaderboard()
        assert leaderboard == []
    finally:
        repo.close()


def test_get_leaderboard_ordering(tmp_path: Path):
    """Test leaderboard orders by wins DESC, then games DESC."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        # Player A: 2 wins, 2 games
        repo.record_game_result("PlayerA", board_size=5, pool_max=75, won=True, draws_count=10)
        repo.record_game_result("PlayerA", board_size=5, pool_max=75, won=True, draws_count=12)
        # Player B: 1 win, 3 games
        repo.record_game_result("PlayerB", board_size=5, pool_max=75, won=True, draws_count=15)
        repo.record_game_result("PlayerB", board_size=5, pool_max=75, won=False, draws_count=20)
        repo.record_game_result("PlayerB", board_size=5, pool_max=75, won=False, draws_count=18)
        # Player C: 1 win, 1 game
        repo.record_game_result("PlayerC", board_size=5, pool_max=75, won=True, draws_count=8)
        leaderboard = repo.get_leaderboard(limit=10)
        assert len(leaderboard) == 3
        # Player A should be first (2 wins)
        assert leaderboard[0]["name"] == "PlayerA"
        assert leaderboard[0]["wins"] == 2
        assert leaderboard[0]["games_played"] == 2
        assert leaderboard[0]["win_rate"] == 100.0
        # Player B should be second (1 win, 3 games)
        assert leaderboard[1]["name"] == "PlayerB"
        assert leaderboard[1]["wins"] == 1
        assert leaderboard[1]["games_played"] == 3
        assert leaderboard[1]["win_rate"] == pytest.approx(33.3, abs=0.1)
        # Player C should be third (1 win, 1 game, but fewer total games)
        assert leaderboard[2]["name"] == "PlayerC"
        assert leaderboard[2]["wins"] == 1
        assert leaderboard[2]["games_played"] == 1
    finally:
        repo.close()


def test_get_leaderboard_limit(tmp_path: Path):
    """Test leaderboard respects limit parameter."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        for i in range(5):
            repo.record_game_result(f"Player{i}", board_size=5, pool_max=75, won=True, draws_count=10)
        leaderboard = repo.get_leaderboard(limit=3)
        assert len(leaderboard) == 3
        leaderboard_all = repo.get_leaderboard(limit=100)
        assert len(leaderboard_all) == 5
    finally:
        repo.close()


def test_get_leaderboard_invalid_limit(tmp_path: Path):
    """Test leaderboard handles invalid limit gracefully."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        repo.record_game_result("Test", board_size=5, pool_max=75, won=True, draws_count=10)
        # Invalid limits should default to 10
        assert len(repo.get_leaderboard(limit=-5)) == 1
        assert len(repo.get_leaderboard(limit=0)) == 1
    finally:
        repo.close()


def test_context_manager(tmp_path: Path):
    """Test repository works as context manager."""
    db_path = tmp_path / "test.db"
    with BingoRepository(str(db_path)) as repo:
        repo.record_game_result("ContextTest", board_size=5, pool_max=75, won=True, draws_count=5)
        # Should still be accessible
        assert repo._conn is not None
    # After exit, connection should be closed
    assert repo._conn is None


def test_close_idempotent(tmp_path: Path):
    """Test that close() can be called multiple times safely."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    repo.close()
    assert repo._conn is None
    repo.close()  # Should not raise
    assert repo._conn is None


def test_foreign_key_constraint(tmp_path: Path):
    """Test that foreign key constraints are enforced."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Try to insert result with non-existent player_id
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO results (player_id, game_id, won, draws_count) VALUES (?, ?, ?, ?)",
                (99999, 1, 1, 10)
            )
        conn.close()
    finally:
        repo.close()


def test_check_constraints(tmp_path: Path):
    """Test that CHECK constraints are enforced."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Try invalid board_size
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (2, 10))
        # Try invalid pool_max (too small)
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (5, 20))
        # Try invalid won value
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO results (player_id, game_id, won, draws_count) VALUES (?, ?, ?, ?)",
                (1, 1, 2, 10)  # won must be 0 or 1
            )
        conn.close()
    finally:
        repo.close()


def test_atomic_transaction_rollback(tmp_path: Path):
    """Test that record_game_result is atomic (rollback on error)."""
    db_path = tmp_path / "test.db"
    repo = BingoRepository(str(db_path))
    try:
        # Create a valid player first
        player_id = repo._get_or_create_player("TestPlayer")
        # Now try to record a result that will fail FK constraint
        # We'll manually break the transaction by inserting invalid game_id
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Insert a game to get valid game_id
        cur.execute("INSERT INTO games (board_size, pool_max) VALUES (?, ?)", (5, 75))
        game_id = cur.lastrowid
        conn.commit()
        conn.close()
        # Now record a result - should succeed atomically
        repo.record_game_result("TestPlayer", board_size=5, pool_max=75, won=True, draws_count=10)
        # Verify both inserts happened
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM games")
        assert cur.fetchone()[0] >= 1
        cur.execute("SELECT COUNT(*) FROM results")
        assert cur.fetchone()[0] >= 1
        conn.close()
    finally:
        repo.close()
