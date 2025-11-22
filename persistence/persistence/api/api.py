#!/usr/bin/env python3
"""FastAPI application for Bingo persistence service."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from persistence.core.repository import BingoRepository


def _db_path() -> str:
    """Get database path from environment or use default.

    Returns:
        Database file path, or ":memory:" if specified in env.
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


class GameResultRequest(BaseModel):
    """Request model for recording a game result."""

    player_name: str = Field(..., description="Display name of the player")
    board_size: int = Field(..., ge=3, description="Board dimension (N for N×N grid)")
    pool_max: int = Field(..., ge=1, description="Maximum number in the draw pool")
    won: bool = Field(..., description="Whether the player won")
    draws_count: int = Field(..., ge=0, description="Number of draws taken")


class StatusResponse(BaseModel):
    """Response model for status endpoints."""

    status: str


@app.get("/health", response_model=StatusResponse)
def health_check() -> StatusResponse:
    """Health check endpoint."""
    return StatusResponse(status="ok")


@app.get("/leaderboard")
def get_leaderboard(limit: int = 10) -> list[dict]:
    """Get leaderboard entries.

    Args:
        limit: Maximum number of entries to return (default: 10).

    Returns:
        List of leaderboard entries with name, wins, games_played, and win_rate.
    """
    db_path = _db_path()
    repo = BingoRepository(db_path)
    try:
        leaderboard = repo.get_leaderboard(limit=limit)
        return leaderboard
    finally:
        repo.close()


@app.post("/results", status_code=201, response_model=StatusResponse)
def record_result(result: GameResultRequest) -> StatusResponse:
    """Record a game result.

    Args:
        result: Game result data.

    Returns:
        Status response indicating success.

    Raises:
        HTTPException: If recording fails.
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
