from src.persistence.repository import BingoRepository

def test_record_and_leaderboard(tmp_path):
    db_path = tmp_path / "test_bingo.db"
    repo = BingoRepository(str(db_path))

    repo.record_game_result("Alice", 5, 75, True, 10)
    repo.record_game_result("Alice", 5, 75, False, 12)
    repo.record_game_result("Bob", 3, 30, True, 8)

    lb = repo.get_leaderboard(limit=10)

    assert {row["name"] for row in lb} == {"Alice", "Bob"}

    alice = next(r for r in lb if r["name"] == "Alice")
    bob = next(r for r in lb if r["name"] == "Bob")

    assert alice["wins"] == 1
    assert alice["games_played"] == 2
    assert bob["wins"] == 1
    assert bob["games_played"] == 1