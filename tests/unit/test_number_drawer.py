from src.game.number_drawer import NumberDrawer


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
