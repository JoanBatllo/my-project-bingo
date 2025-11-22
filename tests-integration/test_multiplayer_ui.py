#!/usr/bin/env python3
"""Integration-style checks for the Streamlit multiplayer UI."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "persistence"))


@pytest.fixture
def streamlit_app():
    """Create a Streamlit AppTest instance with mocked persistence URL."""
    app_path = project_root / "game" / "game" / "ui" / "app.py"
    with patch.dict(os.environ, {"PERSISTENCE_URL": "http://localhost:8000"}):
        yield AppTest.from_file(str(app_path))


def _find_by_label(widgets, text):
    return next(widget for widget in widgets if text in widget.label)


def test_multiplayer_creates_two_cards_and_names(streamlit_app):
    """Enabling multiplayer should create two cards and store both player names."""
    apptest = streamlit_app.run()

    # Enable multiplayer
    multiplayer_checkbox = _find_by_label(apptest.checkbox, "Multiplayer mode")
    apptest = multiplayer_checkbox.set_value(True).run()

    # Set both player names
    p1_input = _find_by_label(apptest.text_input, "Player 1 name")
    apptest = p1_input.set_value("Alice").run()
    p2_input = _find_by_label(apptest.text_input, "Player 2 name")
    apptest = p2_input.set_value("Bob").run()

    # Reset to apply settings and create fresh cards
    reset_button = _find_by_label(
        apptest.button, "New game / reset"
    )
    apptest = reset_button.click().run()

    assert apptest.session_state["multiplayer"] is True
    assert len(apptest.session_state.cards) == 2
    assert apptest.session_state.player_names == ["Alice", "Bob"]
    assert apptest.session_state.winner_name is None
