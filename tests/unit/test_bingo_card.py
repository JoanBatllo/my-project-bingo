import re
from src.game.bingo_card import BingoCard
from src.game.exceptions import InvalidBoardError


def test_bingo_card_rejects_invalid_size():
    """Tests that BingoCard rejects invalid board sizes.

    A valid board size must be in the set {3, 4, 5}. This test ensures that:
        - Creating a card with n=2 triggers an InvalidBoardError.
        - Creating a card with n=6 triggers an InvalidBoardError.

    Raises:
        AssertionError: If an invalid size does not raise InvalidBoardError.
    """
    try:
        _ = BingoCard(n=2, pool_max=10)
        assert False, "Expected InvalidBoardError for N=2"
    except InvalidBoardError:
        assert True

    try:
        _ = BingoCard(n=6, pool_max=200)
        assert False, "Expected InvalidBoardError for N=6"
    except InvalidBoardError:
        assert True


def test_bingo_card_shape_and_uniqueness():
    """Validates the structure and content rules of a BingoCard.

    This test verifies that a generated card:
        - Has dimensions n × n.
        - Contains only unique numbers.
        - Uses values strictly within the range [1, pool_max].

    Raises:
        AssertionError: If the grid has an incorrect shape, repeated numbers,
            or values outside the allowed range.
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


def test_auto_mark_and_toggle_mark():
    """Tests the marking behavior on a BingoCard.

    This includes:
        - auto_mark_if_present(): marks a number if it exists on the card.
        - toggle_mark(r, c): toggles a cell between marked and unmarked.

    Behaviors validated:
        - A real card number is successfully auto-marked.
        - A non-existing number does not get marked.
        - toggle_mark() correctly flips marked state on/off.

    Raises:
        AssertionError: If marking or toggling behavior deviates from expected.
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


def test_render_returns_human_readable_string():
    """Ensures render() produces a valid human-readable string.

    Validity criteria:
        - Output must be a multiline string.
        - Output must contain at least one digit.
        - We do not check for ANSI color codes because the color function is optional.

    Raises:
        AssertionError: If render() output is not a string, not multiline,
            or contains no numeric characters.
    """
    card = BingoCard(n=4, pool_max=60)
    out = card.render()
    assert isinstance(out, str)
    assert "\n" in out
    assert re.search(r"\d", out) is not None


def test_free_center_is_marked_and_rendered():
    """Tests correct behavior of free center cells in BingoCard.

    When free_center=True:
        - The center cell must always hold the value 0.
        - The center cell must always remain marked.
        - toggle_mark() must *not* unmark the center.
        - render() should visually indicate the FREE space.

    Raises:
        AssertionError: If the free center is not marked, becomes unmarked,
            or the rendered output does not include the FREE label.
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
