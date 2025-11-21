#!/usr/bin/env python3
"""Unit tests for BingoCard class."""

import re

import pytest

from game.src.bingo_card import BingoCard


class TestBingoCardValidation:
    """Tests for BingoCard input validation."""

    def test_rejects_invalid_size(self):
        """Tests that BingoCard rejects invalid board sizes.

        A valid board size must be in the set {3, 4, 5}. This test ensures that:
            - Creating a card with n=2 triggers ValueError.
            - Creating a card with n=6 triggers ValueError.
        """
        with pytest.raises(ValueError):
            BingoCard(n=2, pool_max=10)

        with pytest.raises(ValueError):
            BingoCard(n=6, pool_max=200)

    def test_rejects_pool_max_too_small(self):
        """Test that BingoCard rejects pool_max smaller than n*n."""
        with pytest.raises(ValueError, match="pool_max must be at least N\\*N"):
            BingoCard(n=5, pool_max=20)  # 20 < 25

    def test_rejects_free_center_with_even_size(self):
        """Test that BingoCard rejects free_center with even-sized boards."""
        with pytest.raises(ValueError, match="Free center is only available for odd-sized boards"):
            BingoCard(n=4, pool_max=60, free_center=True)


class TestBingoCardBasicFunctionality:
    """Tests for basic BingoCard functionality."""

    def test_shape_and_uniqueness(self):
        """Validates the structure and content rules of a BingoCard.

        This test verifies that a generated card:
            - Has dimensions n × n.
            - Contains only unique numbers.
            - Uses values strictly within the range [1, pool_max].
        """
        n = 5
        pool_max = 75
        card = BingoCard(n=n, pool_max=pool_max)

        # shape check
        assert len(card.grid) == n
        assert all(len(row) == n for row in card.grid)

        # flatten values
        vals = [v for row in card.grid for v in row]

        # uniqueness
        assert len(vals) == n * n
        assert len(set(vals)) == n * n

        # range check
        assert all(1 <= v <= pool_max for v in vals)

    def test_auto_mark_and_toggle_mark(self):
        """Tests the marking behavior on a BingoCard.

        This includes:
            - auto_mark_if_present(): marks a number if it exists on the card.
            - toggle_mark(r, c): toggles a cell between marked and unmarked.

        Behaviors validated:
            - A real card number is successfully auto-marked.
            - A non-existing number does not get marked.
            - toggle_mark() correctly flips marked state on/off.
        """
        card = BingoCard(n=3, pool_max=30)

        # Take a known value from the card
        target = card.grid[0][0]

        # auto-mark should succeed
        assert card.auto_mark_if_present(target) is True
        assert (0, 0) in card.marked

        # auto-mark non-existing number
        not_in_card = max(max(row) for row in card.grid) + 1
        assert card.auto_mark_if_present(not_in_card) is False

        # toggle should unmark
        card.toggle_mark(0, 0)
        assert (0, 0) not in card.marked

        # toggle again should mark
        card.toggle_mark(0, 0)
        assert (0, 0) in card.marked

    def test_toggle_mark_out_of_bounds(self):
        """Test that toggle_mark silently ignores out-of-bounds coordinates."""
        card = BingoCard(n=3, pool_max=30)
        initial_marked = card.marked.copy()

        # Try to toggle out-of-bounds coordinates
        card.toggle_mark(-1, 0)  # negative row
        card.toggle_mark(0, -1)  # negative column
        card.toggle_mark(3, 0)   # row too large
        card.toggle_mark(0, 3)   # column too large
        card.toggle_mark(10, 10) # both out of bounds

        # Marked set should be unchanged
        assert card.marked == initial_marked

    def test_render_returns_human_readable_string(self):
        """Ensures render() produces a valid human-readable string.

        Validity criteria:
            - Output must be a multiline string.
            - Output must contain at least one digit.
            - We do not check for ANSI color codes because the color function is optional.
        """
        card = BingoCard(n=4, pool_max=60)
        out = card.render()
        assert isinstance(out, str)
        assert "\n" in out
        assert re.search(r"\d", out) is not None


class TestBingoCardAdvancedFeatures:
    """Tests for advanced BingoCard features like free center and bingo detection."""

    def test_free_center_is_marked_and_rendered(self):
        """Tests correct behavior of free center cells in BingoCard.

        When free_center=True:
            - The center cell must always hold the value 0.
            - The center cell must always remain marked.
            - toggle_mark() must *not* unmark the center.
            - render() should visually indicate the FREE space.
        """
        card = BingoCard(n=5, pool_max=75, free_center=True, seed=123)
        center = card.n // 2

        assert card.grid[center][center] == 0
        assert (center, center) in card.marked

        # toggle should *not* unmark the free center
        card.toggle_mark(center, center)
        assert (center, center) in card.marked

        rendered = card.render()
        assert "FREE" in rendered

    def test_has_bingo_detects_all_patterns(self):
        """Tests that has_bingo() correctly detects all valid bingo patterns.

        Valid patterns include:
            - A complete row.
            - A complete column.
            - A complete main diagonal (top-left → bottom-right).
            - A complete anti-diagonal (top-right → bottom-left).
        """
        n = 5
        card = BingoCard(n=n, pool_max=75)

        # Test row bingo
        card.marked = {(0, c) for c in range(n)}
        assert card.has_bingo is True

        # Test column bingo
        card.marked = {(r, 2) for r in range(n)}
        assert card.has_bingo is True

        # Test main diagonal bingo
        card.marked = {(i, i) for i in range(n)}
        assert card.has_bingo is True

        # Test anti-diagonal bingo
        card.marked = {(i, n - 1 - i) for i in range(n)}
        assert card.has_bingo is True

    def test_has_bingo_no_false_positives(self):
        """Tests that incomplete markings do not produce a bingo.

        Validates that:
            - Partial rows.
            - Partial columns.
            - Partial diagonals.
        do NOT trigger a win.
        """
        n = 5
        card = BingoCard(n=n, pool_max=75)
        card.marked = {(0, 0), (0, 1), (1, 1)}  # Not a full row, column, or diagonal
        assert card.has_bingo is False
