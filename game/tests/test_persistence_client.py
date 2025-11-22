#!/usr/bin/env python3
"""Tests for the persistence client."""

import os
from unittest.mock import Mock, patch

import pytest

from game.clients.persistence_client import PersistenceClient


class TestPersistenceClientInitialization:
    """Tests for PersistenceClient initialization."""

    def test_init_with_base_url(self):
        """Test client initialization with explicit base_url."""
        client = PersistenceClient(base_url="http://localhost:8000")
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 5

    def test_init_with_env_var(self):
        """Test client initialization using PERSISTENCE_URL environment variable."""
        with patch.dict(os.environ, {"PERSISTENCE_URL": "http://test:8000"}):
            client = PersistenceClient()
            assert client.base_url == "http://test:8000"

    def test_init_without_url_raises(self):
        """Test that client raises RuntimeError when no URL is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="PERSISTENCE_URL is not set"):
                PersistenceClient()

    def test_init_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base_url."""
        client = PersistenceClient(base_url="http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"

    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = PersistenceClient(base_url="http://localhost:8000", timeout=10)
        assert client.timeout == 10


class TestPersistenceClientLeaderboard:
    """Tests for leaderboard fetching functionality."""

    @pytest.fixture
    def client(self):
        """Create a PersistenceClient instance for testing."""
        return PersistenceClient(base_url="http://localhost:8000")

    @patch("game.clients.persistence_client.requests.get")
    def test_fetch_leaderboard_success(self, mock_get, client):
        """Test successful leaderboard fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "Alice", "wins": 5, "games_played": 10},
            {"name": "Bob", "wins": 3, "games_played": 8},
        ]
        mock_get.return_value = mock_response

        result = client.fetch_leaderboard(limit=10)

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        mock_get.assert_called_once_with(
            "http://localhost:8000/leaderboard",
            params={"limit": 10},
            timeout=5,
        )

    @patch("game.clients.persistence_client.requests.get")
    def test_fetch_leaderboard_default_limit(self, mock_get, client):
        """Test leaderboard fetch with default limit."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client.fetch_leaderboard()

        mock_get.assert_called_once_with(
            "http://localhost:8000/leaderboard",
            params={"limit": 10},
            timeout=5,
        )

    @patch("game.clients.persistence_client.requests.get")
    def test_fetch_leaderboard_error(self, mock_get, client):
        """Test leaderboard fetch with error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to fetch leaderboard: 500"):
            client.fetch_leaderboard()


class TestPersistenceClientRecordResult:
    """Tests for result recording functionality."""

    @pytest.fixture
    def client(self):
        """Create a PersistenceClient instance for testing."""
        return PersistenceClient(base_url="http://localhost:8000")

    @patch("game.clients.persistence_client.requests.post")
    def test_record_result_success(self, mock_post, client):
        """Test successful result recording."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        client.record_result(
            player_name="Alice",
            board_size=5,
            pool_max=75,
            won=True,
            draws_count=10,
        )

        mock_post.assert_called_once_with(
            "http://localhost:8000/results",
            json={
                "player_name": "Alice",
                "board_size": 5,
                "pool_max": 75,
                "won": True,
                "draws_count": 10,
            },
            timeout=5,
        )

    @patch("game.clients.persistence_client.requests.post")
    def test_record_result_success_200(self, mock_post, client):
        """Test result recording with 200 status code (also acceptable)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client.record_result(
            player_name="Bob",
            board_size=3,
            pool_max=30,
            won=False,
            draws_count=15,
        )

        mock_post.assert_called_once()

    @patch("game.clients.persistence_client.requests.post")
    def test_record_result_error(self, mock_post, client):
        """Test result recording with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to save result: 400"):
            client.record_result(
                player_name="Alice",
                board_size=5,
                pool_max=75,
                won=True,
                draws_count=10,
            )
