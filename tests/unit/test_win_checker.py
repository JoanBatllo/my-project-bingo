from src.game.win_checker import has_bingo


def test_row_column_and_diagonal_bingo():
    """Tests that has_bingo() correctly detects all valid bingo patterns.

    Valid patterns include:
        - A complete row.
        - A complete column.
        - A complete main diagonal (top-left → bottom-right).
        - A complete anti-diagonal (top-right → bottom-left).

    Raises:
        AssertionError: If any valid bingo configuration is not detected.
    """
    n = 5

    # Full row 0
    marked = {(0, c) for c in range(n)}
    assert has_bingo(marked, n) is True

    # Full column 2
    marked = {(r, 2) for r in range(n)}
    assert has_bingo(marked, n) is True

    # Main diagonal
    marked = {(i, i) for i in range(n)}
    assert has_bingo(marked, n) is True

    # Anti-diagonal
    marked = {(i, n - 1 - i) for i in range(n)}
    assert has_bingo(marked, n) is True


def test_no_false_positive_bingo():
    """Tests that incomplete markings do not produce a bingo.

    Validates that:
        - Partial rows.
        - Partial columns.
        - Partial diagonals.
    do NOT trigger a win.

    Raises:
        AssertionError: If has_bingo() incorrectly returns True.
    """
    n = 5
    marked = {(0, 0), (0, 1), (1, 1)}  # Not a full row, column, or diagonal
    assert has_bingo(marked, n) is False
