#!/usr/bin/env python3
"""Pydantic models for the persistence API."""

from __future__ import annotations

from pydantic import BaseModel, Field


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


class GameHistoryEntry(BaseModel):
    """Response model for a single game history row."""

    id: int
    name: str
    board_size: int
    pool_max: int
    won: bool
    draws_count: int
    played_at: str
