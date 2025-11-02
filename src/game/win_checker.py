#!/usr/bin/env python3
from typing import Set, Tuple

def has_bingo(marked: Set[Tuple[int, int]], n: int) -> bool:
    """Validates rows, columns, and diagonals based on the set of marked cells."""
    # Rows
    for r in range(n):
        if all((r, c) in marked for c in range(n)):
            return True
    # Columns
    for c in range(n):
        if all((r, c) in marked for r in range(n)):
            return True
    # Diagonals
    if all((i, i) in marked for i in range(n)):
        return True
    if all((i, n - 1 - i) in marked for i in range(n)):
        return True
    return False
