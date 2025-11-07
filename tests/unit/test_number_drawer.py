from src.game.number_drawer import NumberDrawer


def test_drawer_rejects_invalid_pool():
    """pool_max must be positive."""
    for value in (0, -5):
        try:
            NumberDrawer(pool_max=value)
            assert False, f"Expected ValueError for pool_max={value}"
        except ValueError:
            pass


def test_drawer_draws_without_repetition_and_exhausts():
    """
    NumberDrawer should:
    - draw numbers without repeating
    - eventually return None when empty
    - track how many are left
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
    """
    After drawing some numbers, reset() should:
    - reshuffle a full new pile
    - clear 'drawn'
    - restore remaining() == pool_max
    """
    drawer = NumberDrawer(pool_max=10)

    # consume some draws
    for _ in range(4):
        _ = drawer.draw()
    assert drawer.remaining() == 6  # 10-4

    drawer.reset()

    # after reset, pile is full again
    assert drawer.remaining() == 10
    assert drawer.drawn == []


def test_drawer_seed_allows_reproducible_draws():
    """Providing the same seed should reproduce the exact draw order."""
    seed = 42
    drawer_a = NumberDrawer(pool_max=20, seed=seed)
    drawer_b = NumberDrawer(pool_max=20, seed=seed)

    draws_a = [drawer_a.draw() for _ in range(10)]
    draws_b = [drawer_b.draw() for _ in range(10)]
    assert draws_a == draws_b

    # Reset without changing the seed keeps the determinism aligned.
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
