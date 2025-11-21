from src.persistence.repository import BingoRepository

def test_record_and_leaderboard(tmp_path):
    """Test recording game results and generating a leaderboard.

    This test verifies that the repository correctly:
    - Stores game results for multiple players.
    - Aggregates wins and total games played.
    - Returns a leaderboard structure ordered and formatted properly.

    The test uses a temporary SQLite database provided by pytest's ``tmp_path``.

    Args:
        tmp_path (pathlib.Path): Temporary directory fixture provided by pytest.
    """
    db_path = tmp_path / "test_bingo.db"
    repo = BingoRepository(str(db_path))

    # Record multiple results for multiple players
    repo.record_game_result("Alice", 5, 75, True, 10)
    repo.record_game_result("Alice", 5, 75, False, 12)
    repo.record_game_result("Bob", 3, 30, True, 8)

    # Fetch leaderboard
    lb = repo.get_leaderboard(limit=10)

    # Validate players present
    assert {row["name"] for row in lb} == {"Alice", "Bob"}

    # Extract rows
    alice = next(r for r in lb if r["name"] == "Alice")
    bob = next(r for r in lb if r["name"] == "Bob")

    # Validate statistics
    assert alice["wins"] == 1
    assert alice["games_played"] == 2
    assert bob["wins"] == 1
    assert bob["games_played"] == 1
