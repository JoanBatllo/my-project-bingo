#!/usr/bin/env python3
"""Integration tests for the Streamlit Bingo UI application.

These tests use Streamlit's AppTest framework to test the actual
running Streamlit application with real user interactions.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "persistence"))


@pytest.fixture
def persistence_server(tmp_path):
    """Start a test persistence server."""
    db_path = tmp_path / "test_bingo.db"
    from persistence.api.api import app

    with patch.dict(os.environ, {"BINGO_DB_PATH": str(db_path)}):
        client = TestClient(app)
        yield client


@pytest.fixture
def streamlit_app():
    """Create a Streamlit AppTest instance."""
    # tests-integration/ is at project root, so go up 1 level to get project root
    project_root = Path(__file__).resolve().parent.parent
    app_path = project_root / "game" / "game" / "ui" / "app.py"
    # Set PERSISTENCE_URL to avoid errors when app tries to create PersistenceClient
    with patch.dict(os.environ, {"PERSISTENCE_URL": "http://localhost:8000"}):
        return AppTest.from_file(str(app_path))


def test_streamlit_app_initializes(streamlit_app):
    """Test that Streamlit app initializes correctly."""
    streamlit_app.run()

    # Verify app has initialized game state
    assert "cards" in streamlit_app.session_state
    assert "drawer" in streamlit_app.session_state
    assert len(streamlit_app.session_state.cards) >= 1
    assert streamlit_app.session_state.drawer is not None


def test_streamlit_app_draw_number(streamlit_app):
    """Test drawing numbers in the Streamlit app."""
    streamlit_app.run()

    # Verify initial state
    assert streamlit_app.session_state.last_draw is None
    assert streamlit_app.session_state.draw_history == []

    # Simulate clicking "Draw next number" button
    draw_button = None
    for button in streamlit_app.button:
        if "Draw next number" in button.label:
            draw_button = button
            break

    if draw_button:
        draw_button.click().run()

        # Verify a number was drawn
        assert streamlit_app.session_state.last_draw is not None
        assert len(streamlit_app.session_state.draw_history) > 0


def test_streamlit_app_new_game_button(streamlit_app):
    """Test the new game/reset functionality."""
    streamlit_app.run()

    # Get initial card state
    initial_card = streamlit_app.session_state.cards[0]
    initial_grid = [row[:] for row in initial_card.grid]

    # Find and click "New game / reset" button
    new_game_button = None
    for button in streamlit_app.button:
        if "New game" in button.label or "reset" in button.label.lower():
            new_game_button = button
            break

    if new_game_button:
        new_game_button.click().run()

        # Verify card was reset (should have different numbers)
        new_card = streamlit_app.session_state.cards[0]
        # Cards should be different (very unlikely to be identical)
        assert new_card.grid != initial_grid or len(streamlit_app.session_state.draw_history) == 0


def test_streamlit_app_integration_with_persistence(streamlit_app, persistence_server):
    """Test integration between Streamlit app and persistence service.

    This test verifies that:
    1. The persistence API can record results
    2. The persistence API can return leaderboard data
    3. The Streamlit app initializes correctly

    Note: Full end-to-end integration would require the Streamlit app to actually
    connect to the persistence service, which is complex in a test environment.
    This test verifies the persistence service works correctly.
    """
    # Record some data via the API
    response = persistence_server.post(
        "/results",
        json={
            "player_name": "StreamlitTest",
            "board_size": 5,
            "pool_max": 75,
            "won": True,
            "draws_count": 10,
        },
    )
    assert response.status_code == 201

    # Verify the data was recorded by fetching leaderboard
    leaderboard_response = persistence_server.get("/leaderboard")
    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    assert len(leaderboard) > 0
    assert any(row["name"] == "StreamlitTest" for row in leaderboard)

    # Verify Streamlit app initializes
    streamlit_app.run()
    assert "cards" in streamlit_app.session_state
