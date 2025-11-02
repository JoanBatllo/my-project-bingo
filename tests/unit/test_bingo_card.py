import re
from src.game.bingo_card import BingoCard
from src.game.exceptions import InvalidBoardError


def test_bingo_card_rejects_invalid_size():
    """Card must only allow N in {3,4,5}."""
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
    """
    The card must:
    - have shape n x n
    - contain only unique numbers
    - pull from range 1..pool_max
    """
    n = 5
    pool_max = 75
    card = BingoCard(n=n, pool_max=pool_max)

    # shape
    assert len(card.grid) == n
    assert all(len(row) == n for row in card.grid)

    # flatten values
    vals = [v for row in card.grid for v in row]

    # uniqueness (no repeated numbers in one card)
    assert len(vals) == n * n
    assert len(set(vals)) == n * n

    # values must be in 1..pool_max
    assert all(1 <= v <= pool_max for v in vals)


def test_auto_mark_and_toggle_mark():
    """
    auto_mark_if_present(number) should mark the position if it exists.
    toggle_mark(r,c) should flip mark on/off.
    """
    card = BingoCard(n=3, pool_max=30)

    # Take a known value from the card
    target = card.grid[0][0]

    # auto mark should return True and mark that cell
    assert card.auto_mark_if_present(target) is True
    assert (0, 0) in card.marked

    # auto mark with a number not on the card should return False
    not_in_card = max(max(row) for row in card.grid) + 1
    assert card.auto_mark_if_present(not_in_card) is False

    # toggle should unmark (0,0)
    card.toggle_mark(0, 0)
    assert (0, 0) not in card.marked

    # toggle again should remark it
    card.toggle_mark(0, 0)
    assert (0, 0) in card.marked


def test_render_returns_human_readable_string():
    """
    render() should return a multiline string with digits in it.
    We don't assert ANSI colors because color_fn is optional.
    """
    card = BingoCard(n=4, pool_max=60)
    out = card.render()
    assert isinstance(out, str)
    assert "\n" in out
    # should contain at least one digit
    assert re.search(r"\d", out) is not None