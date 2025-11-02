#!/usr/bin/env python3
import random
from typing import List, Optional

class NumberDrawer:
    """Handles the number pool from 1 to pool_max without repetition."""
    def __init__(self, pool_max: int):
        self.pool_max = int(pool_max)
        self._pile: List[int] = []
        self.drawn: List[int] = []
        self.reset()

    def reset(self) -> None:
        self._pile = list(range(1, self.pool_max + 1))
        random.shuffle(self._pile)
        self.drawn.clear()

    def draw(self) -> Optional[int]:
        while self._pile:
            x = self._pile.pop()
            if x not in self.drawn:
                self.drawn.append(x)
                return x
        return None

    def remaining(self) -> int:
        return len(self._pile)
