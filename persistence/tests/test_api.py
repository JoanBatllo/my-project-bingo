#!/usr/bin/env python3
"""Tests for the persistence API endpoints."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from persistence.api.api import _db_path, app


class TestDatabasePathConfiguration:
    """Tests for database path configuration."""

    def test_db_path_from_env(self):
        """Test that _db_path uses BINGO_DB_PATH environment variable."""
        with patch.dict(os.environ, {"BINGO_DB_PATH": "/custom/path/db.db"}):
            path = _db_path()
            assert path == str(Path("/custom/path/db.db").resolve())

    def test_db_path_default(self):
        """Test that _db_path uses default when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            path = _db_path()
            assert "data/bingo.db" in path or "bingo.db" in path

    def test_db_path_memory(self):
        """Test that _db_path returns :memory: when specified."""
        with patch.dict(os.environ, {"BINGO_DB_PATH": ":memory:"}):
            path = _db_path()
            assert path == ":memory:"


class TestAPIEndpoints:
    """Tests for API endpoint functionality."""

    @pytest.fixture
    def test_client(self, tmp_path):
        """Create a test client with a temporary database."""
        db_path = tmp_path / "test.db"
        with patch.dict(os.environ, {"BINGO_DB_PATH": str(db_path)}):
            yield TestClient(app)

    def test_health_endpoint(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_leaderboard_endpoint(self, test_client):
        """Test the leaderboard endpoint with and without limit parameter."""
        # Test without limit (default)
        response = test_client.get("/leaderboard")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        # Test with custom limit
        response = test_client.get("/leaderboard?limit=5")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_record_result_endpoint(self, test_client):
        """Test the record result endpoint with win and loss scenarios."""
        # Test recording a win
        response = test_client.post(
            "/results",
            json={
                "player_name": "Alice",
                "board_size": 5,
                "pool_max": 75,
                "won": True,
                "draws_count": 10,
            },
        )
        assert response.status_code == 201
        assert response.json() == {"status": "ok"}

        # Test recording a loss
        response = test_client.post(
            "/results",
            json={
                "player_name": "Bob",
                "board_size": 3,
                "pool_max": 30,
                "won": False,
                "draws_count": 15,
            },
        )
        assert response.status_code == 201
        assert response.json() == {"status": "ok"}

    def test_leaderboard_after_recording(self, test_client):
        """Test that leaderboard shows recorded results."""
        # Record a result
        test_client.post(
            "/results",
            json={
                "player_name": "Alice",
                "board_size": 5,
                "pool_max": 75,
                "won": True,
                "draws_count": 10,
            },
        )
        # Get leaderboard
        response = test_client.get("/leaderboard")
        assert response.status_code == 200
        leaderboard = response.json()
        assert len(leaderboard) > 0
        assert any(row["name"] == "Alice" for row in leaderboard)

    def test_history_endpoint(self, test_client):
        """Test the history endpoint returns recent games with required fields."""
        test_client.post(
            "/results",
            json={
                "player_name": "HistoryUser",
                "board_size": 3,
                "pool_max": 30,
                "won": False,
                "draws_count": 7,
            },
        )

        response = test_client.get("/history?limit=5")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)
        assert len(payload) >= 1
        assert {"id", "name", "board_size", "pool_max", "won", "draws_count", "played_at"} <= payload[0].keys()
