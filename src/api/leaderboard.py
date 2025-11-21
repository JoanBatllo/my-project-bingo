"""FastAPI service for exposing leaderboard data."""

from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, Query

from src.persistence.repository import BingoRepository

app = FastAPI(title="Bingo Leaderboard API", version="0.1.0")


def get_repository() -> BingoRepository:
    """Provide the shared repository instance."""

    repo: BingoRepository = app.state.repo  # type: ignore[attr-defined]
    return repo


@app.on_event("startup")
def startup() -> None:
    app.state.repo = BingoRepository()


@app.on_event("shutdown")
def shutdown() -> None:
    repo: BingoRepository = app.state.repo  # type: ignore[attr-defined]
    repo.close()


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/leaderboard", tags=["leaderboard"])
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    repo: BingoRepository = Depends(get_repository),
) -> List[BingoRepository.LeaderboardRow]:
    return repo.get_leaderboard(limit=limit)

