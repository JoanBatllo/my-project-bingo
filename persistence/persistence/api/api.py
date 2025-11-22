#!/usr/bin/env python3
"""FastAPI application for Bingo persistence service."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from persistence.api.models import GameHistoryEntry, GameResultRequest, StatusResponse
from persistence.core.repository import BingoRepository


def _db_path() -> str:
    """Resolve the database path from environment or fall back to default.

    Returns:
        str: Absolute database file path, or ":memory:" when requested.
    """
    env_path = os.environ.get("BINGO_DB_PATH")
    if env_path:
        if env_path == ":memory:":
            return ":memory:"
        return str(Path(env_path).resolve())
    # Default to data/bingo.db relative to the persistence directory
    default_path = Path(__file__).parent.parent.parent / "data" / "bingo.db"
    return str(default_path.resolve())


app = FastAPI(title="Bingo Persistence API", version="0.1.0")

@app.get("/health", response_model=StatusResponse)
def health_check() -> StatusResponse:
    """Report service health.

    Returns:
        StatusResponse: Static ok status payload.
    """
    return StatusResponse(status="ok")


@app.get("/leaderboard")
def get_leaderboard(limit: int = 10) -> list[dict]:
    """Return leaderboard entries.

    Args:
        limit (int): Maximum number of entries to return (default 10).

    Returns:
        list[dict]: Rows with name, wins, games_played, and win_rate.
    """
    db_path = _db_path()
    repo = BingoRepository(db_path)
    try:
        leaderboard = repo.get_leaderboard(limit=limit)
        return leaderboard
    finally:
        repo.close()


@app.get("/history", response_model=list[GameHistoryEntry])
def get_history(limit: int = 200) -> list[dict]:
    """Return recent game history rows for analytics.

    Args:
        limit (int): Maximum number of rows to return (default 200).

    Returns:
        list[dict]: History rows ordered newest first.
    """
    db_path = _db_path()
    repo = BingoRepository(db_path)
    try:
        return repo.get_game_history(limit=limit)
    finally:
        repo.close()


@app.post("/results", status_code=201, response_model=StatusResponse)
def record_result(result: GameResultRequest) -> StatusResponse:
    """Record a game result.

    Args:
        result (GameResultRequest): Game result data payload.

    Returns:
        StatusResponse: Success indicator.

    Raises:
        HTTPException: Raised when the result cannot be persisted.
    """
    db_path = _db_path()
    repo = BingoRepository(db_path)
    try:
        repo.record_game_result(
            player_name=result.player_name,
            board_size=result.board_size,
            pool_max=result.pool_max,
            won=result.won,
            draws_count=result.draws_count,
        )
        return StatusResponse(status="ok")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        repo.close()
