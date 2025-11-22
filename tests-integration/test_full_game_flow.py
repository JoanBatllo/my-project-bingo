"""
Integration test for the full game flow of the Bingo application.

This test simulates a mini game loop without using real CLI input. It verifies
that the BingoCard, NumberDrawer, and win-checking logic work together
correctly as an integrated system.
"""

from game.core.bingo_card import BingoCard
from game.core.number_drawer import NumberDrawer


def test_full_game_flow_reaches_bingo():
    """Runs an end-to-end integration test of the Bingo game flow.

    This test performs the following steps:
        1. Creates a BingoCard and a NumberDrawer.
        2. Repeatedly draws numbers from the drawer.
        3. Automatically marks numbers on the card when drawn.
        4. Checks for a bingo condition after each draw.
        5. Ensures that the loop terminates either by achieving bingo or by
           exhausting the number pool.

    The purpose is to confirm that the core mechanics—number drawing, card
    marking, and bingo detection—function correctly together.

    Raises:
        AssertionError: If the loop exceeds a safe iteration limit
            (indicating a possible infinite loop).
        AssertionError: If the game fails to produce a bingo by the time all
            card numbers could have been drawn.
    """
    # Use a small board so test finishes fast
    n = 3
    pool_max = 30

    card = BingoCard(n=n, pool_max=pool_max)
    drawer = NumberDrawer(pool_max=pool_max)

    bingo = False
    safety_counter = 0

    while drawer.remaining() > 0 and not bingo:
        number = drawer.draw()
        if number is None:
            break

        # Mark card if that number is on it
        card.auto_mark_if_present(number)

        # Check win condition after each draw
        if card.has_bingo:
            bingo = True
            break

        safety_counter += 1
        assert safety_counter < 500, "Something is wrong, infinite loop?"

    # We expect a bingo on a 3x3 by the time enough numbers are drawn.
    assert bingo is True, (
        "End-to-end game flow should eventually produce a bingo"
    )
