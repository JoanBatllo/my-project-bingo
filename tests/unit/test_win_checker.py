from src.game.win_checker import has_bingo


def test_row_column_and_diagonal_bingo():
    """
    has_bingo(marked, n) should detect:
    - complete row
    - complete column
    - main diagonal
    - anti-diagonal
    """
    n = 5

    # Full row 0
    marked = {(0, c) for c in range(n)}
    assert has_bingo(marked, n) is True

    # Full column 2
    marked = {(r, 2) for r in range(n)}
    assert has_bingo(marked, n) is True

    # Main diagonal (0,0) (1,1) (2,2) ...
    marked = {(i, i) for i in range(n)}
    assert has_bingo(marked, n) is True

    # Anti-diagonal (0,n-1) (1,n-2) ...
    marked = {(i, n - 1 - i) for i in range(n)}
    assert has_bingo(marked, n) is True


def test_no_false_positive_bingo():
    """
    Partial markings should NOT count as a win.
    """
    n = 5
    marked = {(0, 0), (0, 1), (1, 1)}  # not a full row / col / diag
    assert has_bingo(marked, n) is False
