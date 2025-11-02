#!/usr/bin/env python3
import random
from typing import List, Optional

class NumberDrawer:
    """Handles the number pool from 1 to pool_max without repetition."""
    def __init__(self, pool_max: int, *, seed: Optional[int] = None):
        pool_max = int(pool_max)
        if pool_max < 1:
            raise ValueError("pool_max must be at least 1.")
        self.pool_max = pool_max
        self._pile: List[int] = []
        self.drawn: List[int] = []
        self._rng = random.Random(seed)
        self._seed = seed
        self.reset()

    def reset(self, *, seed: Optional[int] = None) -> None:
        if seed is not None:
            self._rng.seed(seed)
            self._seed = seed
        self._pile = list(range(1, self.pool_max + 1))
        self._rng.shuffle(self._pile)
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
