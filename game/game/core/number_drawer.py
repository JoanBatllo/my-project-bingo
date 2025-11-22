#!/usr/bin/env python3
import random


class NumberDrawer:
    """Manages a pool of numbers from 1 to ``pool_max`` and draws them without repetition.

    This class provides deterministic randomness when given a seed, supports resetting
    the pool at any time, and tracks both remaining and already drawn numbers.
    """

    def __init__(self, pool_max: int, *, seed: int | None = None):
        """Initialize a NumberDrawer instance.

        Args:
            pool_max (int): The highest number in the draw pool (must be >= 1).
            seed (Optional[int]): Optional seed for deterministic draws.

        Raises:
            ValueError: If ``pool_max`` is less than 1.
        """
        pool_max = int(pool_max)
        if pool_max < 1:
            raise ValueError("pool_max must be at least 1.")

        self.pool_max = pool_max
        self._pile: list[int] = []
        self.drawn: list[int] = []
        self._rng = random.Random(seed)
        self._seed = seed
        self.reset()

    def reset(self, *, seed: int | None = None) -> None:
        """Reset the draw pile to its initial state.

        This recreates the list from 1 to ``pool_max`` and shuffles it.
        If a seed is provided, the internal RNG is reseeded for deterministic behavior.

        Args:
            seed (Optional[int]): A new seed to override the current one.
        """
        if seed is not None:
            self._rng.seed(seed)
            self._seed = seed

        self._pile = list(range(1, self.pool_max + 1))
        self._rng.shuffle(self._pile)
        self.drawn.clear()

    def draw(self) -> int | None:
        """Draw the next number from the pool.

        Returns:
            Optional[int]: The drawn number, or ``None`` if no numbers remain.
        """
        while self._pile:
            x = self._pile.pop()
            if x not in self.drawn:
                self.drawn.append(x)
                return x
        return None

    def remaining(self) -> int:
        """Return the number of undrawn numbers remaining in the pool.

        Returns:
            int: Count of numbers still available to draw.
        """
        return len(self._pile)
