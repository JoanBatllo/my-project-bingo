#!/usr/bin/env python3
import random
from typing import List, Set, Tuple, Optional

from .exceptions import InvalidBoardError

class BingoCard:
    """Genera y gestiona un cartón N×N con números únicos."""
    def __init__(self, n: int, pool_max: int):
        if n not in (3, 4, 5):
            raise InvalidBoardError("Board size N must be 3, 4, or 5")
        if pool_max < n * n:
            raise InvalidBoardError("pool_max must be at least N*N to ensure unique values.")
        self.n = n
        self.pool_max = pool_max
        self.grid: List[List[int]] = []
        self.marked: Set[Tuple[int, int]] = set()
        self._generate()

    def _generate(self) -> None:
        nums = random.sample(range(1, self.pool_max + 1), self.n * self.n)
        self.grid = [nums[i * self.n:(i + 1) * self.n] for i in range(self.n)]
        self.marked.clear()

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
        """Devuelve una representación de texto; color_fn(text, name)->str (opcional)."""
        if color_fn is None:
            color_fn = lambda s, _name=None: s
        max_num = max(max(row) for row in self.grid)
        w = max(2, len(str(max_num)))
        lines = []
        header = "   " + " ".join(color_fn(f"{c:>{w}}", "dim") for c in range(self.n))
        lines.append(header)
        for r in range(self.n):
            row_repr = []
            for c in range(self.n):
                num = self.grid[r][c]
                cell = f"{num:>{w}}"
                if (r, c) in self.marked:
                    cell = color_fn(cell, "green")
                row_repr.append(cell)
            lines.append(color_fn(f"{r:>2}", "dim") + " " + " ".join(row_repr))
        return "\n".join(lines)
