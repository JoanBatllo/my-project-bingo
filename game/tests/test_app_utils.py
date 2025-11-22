#!/usr/bin/env python3
"""Unit tests for Streamlit app utility functions."""

from game.ui.app import DEFAULT_POOL_BY_SIZE, _default_pool_max


def test_default_pool_max():
    """Test that _default_pool_max returns correct values for different board sizes."""
    assert _default_pool_max(3) == 30
    assert _default_pool_max(4) == 60
    assert _default_pool_max(5) == 75
    assert _default_pool_max(6) == 36  # Fallback for unsupported sizes
    assert DEFAULT_POOL_BY_SIZE == {3: 30, 4: 60, 5: 75}
