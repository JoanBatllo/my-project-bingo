#!/usr/bin/env python3
"""HTTP client for interacting with the persistence service."""

from __future__ import annotations

import os
from collections.abc import MutableMapping

import requests


class PersistenceClient:
    """Client wrapper for the persistence API (leaderboard + results).

    Attributes:
        base_url (str): Base URL of the persistence service (e.g., http://persistence:8000).
        timeout (int): Request timeout in seconds.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 5) -> None:
        """Initialize the client.

        Args:
            base_url: Full base URL of the persistence service. If None, uses PERSISTENCE_URL env var.
            timeout: Request timeout in seconds.
        """
        env_url = os.environ.get("PERSISTENCE_URL")
        if base_url is None:
            if not env_url:
                raise RuntimeError("PERSISTENCE_URL is not set and no base_url provided")
            base_url = env_url
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_leaderboard(self, limit: int = 10) -> list[MutableMapping[str, object]]:
        """Fetch leaderboard rows from the persistence service.

        Args:
            limit: Maximum number of rows to retrieve.

        Returns:
            List of leaderboard entries.

        Raises:
            RuntimeError: If the remote call fails.
        """
        resp = requests.get(f"{self.base_url}/leaderboard", params={"limit": limit}, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch leaderboard: {resp.status_code} {resp.text}")
        return resp.json()

    def record_result(
        self,
        player_name: str,
        board_size: int,
        pool_max: int,
        won: bool,
        draws_count: int,
    ) -> None:
        """Send a game result to the persistence service.

        Args:
            player_name: Display name of the player.
            board_size: Board dimension (N for N×N grid).
            pool_max: Maximum number in the draw pool.
            won: Whether the player won.
            draws_count: Number of draws taken.

        Raises:
            RuntimeError: If the remote call fails.
        """
        payload: dict[str, object] = {
            "player_name": player_name,
            "board_size": board_size,
            "pool_max": pool_max,
            "won": won,
            "draws_count": draws_count,
        }
        resp = requests.post(f"{self.base_url}/results", json=payload, timeout=self.timeout)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to save result: {resp.status_code} {resp.text}")
