#!/usr/bin/env python3
"""Persistence service exposing leaderboard endpoints over HTTP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, List

from fastapi import Depends, FastAPI, Query

from .repository import BingoRepository

app = FastAPI(title="Bingo Persistence API", version="0.2.0")


def _db_path() -> str:
    """Resolve the SQLite database path.

    Returns:
        str: Expanded path to the SQLite database, or ":memory:" for ephemeral DB.
    """
    raw = os.environ.get("BINGO_DB_PATH", "data/bingo.db")
    if raw == ":memory:":
        return raw
    return str(Path(raw).expanduser().resolve())


def _repository_dependency() -> Generator[BingoRepository, None, None]:
    """Open a repository for the duration of a request.

    Yields:
        BingoRepository: Repository instance bound to the configured database path.
    """
    repo = BingoRepository(_db_path())
    try:
        yield repo
    finally:
        repo.close()


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Health check endpoint for orchestration and monitoring.

    Returns:
        dict[str, str]: Simple status payload.
    """
    return {"status": "ok"}


@app.get("/leaderboard", tags=["leaderboard"])
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    repo: BingoRepository = Depends(_repository_dependency),
) -> List[BingoRepository.LeaderboardRow]:
    """Fetch leaderboard entries ordered by win ratio and games played.

    Args:
        limit (int): Maximum number of rows to return (1–100).
        repo (BingoRepository): Repository dependency for DB access.

    Returns:
        List[BingoRepository.LeaderboardRow]: Leaderboard rows from persistence.
    """
    return repo.get_leaderboard(limit=limit)


@app.post("/results", tags=["leaderboard"], status_code=201)
def record_result(
    player_name: str,
    board_size: int,
    pool_max: int,
    won: bool,
    draws_count: int,
    repo: BingoRepository = Depends(_repository_dependency),
) -> dict[str, str]:
    """Persist a game result.

    Args:
        player_name (str): Display name of the player.
        board_size (int): Board dimension (N for N×N grid).
        pool_max (int): Maximum number in the draw pool.
        won (bool): Whether the player won.
        draws_count (int): Number of draws taken in the game.
        repo (BingoRepository): Repository dependency for DB access.

    Returns:
        dict[str, str]: Confirmation payload.
    """
    repo.record_game_result(
        player_name=player_name,
        board_size=board_size,
        pool_max=pool_max,
        won=won,
        draws_count=draws_count,
    )
    return {"status": "ok"}
