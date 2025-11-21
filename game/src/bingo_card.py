#!/usr/bin/env python3
import random
from typing import List, Optional, Set, Tuple


class BingoCard:
    """Generates and manages an N×N bingo card with unique, non-repeating numbers."""

    def __init__(self, n: int, pool_max: int, *, free_center: bool = False, seed: Optional[int] = None):
        if n not in (3, 4, 5):
            raise ValueError("Board size N must be 3, 4, or 5")
        if pool_max < n * n:
            raise ValueError("pool_max must be at least N*N to ensure unique values.")
        if free_center and n % 2 == 0:
            raise ValueError("Free center is only available for odd-sized boards.")
        self.n = n
        self.pool_max = pool_max
        self.free_center = bool(free_center) and n % 2 == 1
        self._center = (n // 2, n // 2) if n % 2 == 1 else None
        self._rng = random.Random(seed)
        self.grid: List[List[int]] = []
        self.marked: Set[Tuple[int, int]] = set()
        self._generate()

    def _generate(self) -> None:
        nums = self._rng.sample(range(1, self.pool_max + 1), self.n * self.n)
        self.grid = [nums[i * self.n:(i + 1) * self.n] for i in range(self.n)]
        self.marked.clear()
        if self.free_center and self._center is not None:
            r, c = self._center
            self.grid[r][c] = 0  # sentinel value for the free slot
            self.marked.add((r, c))

    def find(self, number: int) -> Optional[Tuple[int, int]]:
        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] == number:
                    return (r, c)
        return None

    def toggle_mark(self, r: int, c: int) -> None:
        if not (0 <= r < self.n and 0 <= c < self.n):
            return
        pos = (r, c)
        if self.free_center and self._center == pos:
            # Free center stays marked; ignore manual toggles.
            self.marked.add(pos)
            return
        if pos in self.marked:
            self.marked.remove(pos)
        else:
            self.marked.add(pos)

    def auto_mark_if_present(self, number: int) -> bool:
        loc = self.find(number)
        if loc is not None:
            self.marked.add(loc)
            return True
        return False

    def render(self, color_fn=None) -> str:
        """Returns a text representation; color_fn(text, name) -> str (optional)."""
        if color_fn is None:
            color_fn = lambda s, _name=None: s
        max_num = max(max(row) for row in self.grid)
        w = max(2, len(str(max_num)), len("FREE"))
        lines = []
        header = "   " + " ".join(color_fn(f"{c:>{w}}", "dim") for c in range(self.n))
        lines.append(header)
        for r in range(self.n):
            row_repr = []
            for c in range(self.n):
                num = self.grid[r][c]
                if self.free_center and self._center == (r, c):
                    cell_value = "FREE"
                else:
                    cell_value = f"{num}"
                cell = f"{cell_value:>{w}}"
                if (r, c) in self.marked:
                    cell = color_fn(cell, "green")
                row_repr.append(cell)
            lines.append(color_fn(f"{r:>2}", "dim") + " " + " ".join(row_repr))
        return "\n".join(lines)

    @property
    def has_bingo(self) -> bool:
        """Whether the current marked set contains a winning line."""
        # Rows
        for r in range(self.n):
            if all((r, c) in self.marked for c in range(self.n)):
                return True
        # Columns
        for c in range(self.n):
            if all((r, c) in self.marked for r in range(self.n)):
                return True
        # Diagonals
        if all((i, i) in self.marked for i in range(self.n)):
            return True
        if all((i, self.n - 1 - i) in self.marked for i in range(self.n)):
            return True
        return False
