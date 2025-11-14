#!/usr/bin/env python3
from typing import Set, Tuple

def has_bingo(marked: Set[Tuple[int, int]], n: int) -> bool:
    """Check whether a Bingo condition is met.

    This function evaluates whether the set of marked cells contains any
    complete row, column, or diagonal for an ``n × n`` Bingo board. It assumes
    that each marked cell is represented as a ``(row, column)`` tuple.

    Args:
        marked (Set[Tuple[int, int]]): A set of coordinates representing the
            marked cells on the board.
        n (int): The size of the board (e.g., 3, 4, or 5 for Bingo).

    Returns:
        bool: ``True`` if a full row, column, or diagonal is fully marked,
        otherwise ``False``.
    """
    # Check rows
    for r in range(n):
        if all((r, c) in marked for c in range(n)):
            return True

    # Check columns
    for c in range(n):
        if all((r, c) in marked for r in range(n)):
            return True

    # Check main diagonal
    if all((i, i) in marked for i in range(n)):
        return True

    # Check anti-diagonal
    if all((i, n - 1 - i) in marked for i in range(n)):
        return True

    return False
