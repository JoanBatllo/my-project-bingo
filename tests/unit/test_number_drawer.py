from src.game.number_drawer import NumberDrawer


def test_drawer_rejects_invalid_pool():
    """Tests that NumberDrawer rejects non-positive pool_max values.

    Valid behavior:
        - pool_max must be strictly positive.
        - Creating a NumberDrawer with pool_max <= 0 should raise ValueError.

    Raises:
        AssertionError: If NumberDrawer does not raise ValueError for invalid input.
    """
    for value in (0, -5):
        try:
            NumberDrawer(pool_max=value)
            assert False, f"Expected ValueError for pool_max={value}"
        except ValueError:
            pass


def test_drawer_draws_without_repetition_and_exhausts():
    """Tests that NumberDrawer draws unique numbers and exhausts properly.

    Validates that:
        - draw() returns each number at most once.
        - draw() eventually returns None when the pool is empty.
        - remaining() correctly tracks how many values are left.

    Raises:
        AssertionError: If duplicate draws occur, pool size is incorrect,
            or exhaustion logic fails.
    """
    drawer = NumberDrawer(pool_max=15)

    seen = set()
    draws = []

    while True:
        x = drawer.draw()
        if x is None:
            break

        # number should never repeat
        assert x not in seen
        seen.add(x)
        draws.append(x)

    # We should have drawn exactly pool_max unique numbers
    assert len(draws) == 15
    assert drawer.remaining() == 0


def test_drawer_reset_restores_full_pool():
    """Tests that reset() restores the drawer to a full fresh state.

    After reset(), the drawer must:
        - Rebuild a full shuffled pile of numbers.
        - Clear the internal `drawn` list.
        - Report remaining() == pool_max.

    Raises:
        AssertionError: If the pile is not fully restored or if state persists
            after the reset.
    """
    drawer = NumberDrawer(pool_max=10)

    # consume some draws
    for _ in range(4):
        _ = drawer.draw()
    assert drawer.remaining() == 6  # 10 - 4

    drawer.reset()

    # after reset, pile is full again
    assert drawer.remaining() == 10
    assert drawer.drawn == []


def test_drawer_seed_allows_reproducible_draws():
    """Tests deterministic behavior when NumberDrawer is initialized with a seed.

    Validates that:
        - Two drawers with the same seed produce the same draw sequence.
        - reset() without changing the seed preserves determinism.
        - Changing the seed results in a different future sequence.

    Raises:
        AssertionError: If deterministic behavior fails or if reseeding
            does not alter the draw order as expected.
    """
    seed = 42
    drawer_a = NumberDrawer(pool_max=20, seed=seed)
    drawer_b = NumberDrawer(pool_max=20, seed=seed)

    draws_a = [drawer_a.draw() for _ in range(10)]
    draws_b = [drawer_b.draw() for _ in range(10)]
    assert draws_a == draws_b

    # Reset without changing the seed keeps determinism aligned.
    drawer_a.reset()
    drawer_b.reset()
    assert [drawer_a.draw() for _ in range(5)] == [drawer_b.draw() for _ in range(5)]

    # Changing the seed should alter the future order.
    drawer_a.reset(seed=seed + 1)
    drawer_b.reset(seed=seed + 1)
    new_draws_a = [drawer_a.draw() for _ in range(5)]
    new_draws_b = [drawer_b.draw() for _ in range(5)]

    assert new_draws_a == new_draws_b
    assert new_draws_a != draws_a[:5]
