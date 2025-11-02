"""
Integration test:
Simulates a mini game loop without using the real CLI input().
We:
1. Create a BingoCard and a NumberDrawer.
2. Repeatedly draw numbers.
3. Auto-mark any numbers that match the card.
4. Stop when we detect bingo with has_bingo().
This proves that the full core loop (card + drawing + marking + win check) works together.
"""

from src.game.bingo_card import BingoCard
from src.game.number_drawer import NumberDrawer
from src.game.win_checker import has_bingo


def test_full_game_flow_reaches_bingo():
    # Use a small board so test finishes fast
    n = 3
    pool_max = 30

    card = BingoCard(n=n, pool_max=pool_max)
    drawer = NumberDrawer(pool_max=pool_max)

    # simulate gameplay: draw numbers, auto-mark matches
    bingo = False
    safety_counter = 0

    while drawer.remaining() > 0 and not bingo:
        number = drawer.draw()
        if number is None:
            break

        # mark card if that number is on it
        card.auto_mark_if_present(number)

        # check win condition after each draw
        if has_bingo(card.marked, card.n):
            bingo = True
            break

        safety_counter += 1
        # sanity stop to avoid infinite loop in case of bug
        assert safety_counter < 500, "Something is wrong, infinite loop?"

    # By the time we've drawn enough numbers,
    # we EXPECT to have achieved bingo on a 3x3.
    # (Worst case: after we have drawn all 9 numbers that were on the card.)
    assert bingo is True, "End-to-end game flow should eventually produce a bingo"