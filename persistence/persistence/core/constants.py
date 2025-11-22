#!/usr/bin/env python3
"""SQL query constants for the Bingo repository."""

# PRAGMA statements
PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON"
PRAGMA_JOURNAL_MODE_WAL = "PRAGMA journal_mode = WAL"
PRAGMA_TABLE_INFO_RESULTS = "PRAGMA table_info(results)"

# Schema creation statements
CREATE_TABLE_PLAYERS = """
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
"""

CREATE_TABLE_GAMES = """
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_size INTEGER NOT NULL CHECK (board_size >= 3),
        pool_max INTEGER NOT NULL CHECK (pool_max >= board_size * board_size)
    )
"""

CREATE_TABLE_RESULTS = """
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        won INTEGER NOT NULL CHECK (won IN (0, 1)),
        draws_count INTEGER NOT NULL,
        played_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (game_id) REFERENCES games(id)
    )
"""

# Index creation statements
CREATE_INDEX_PLAYERS_NAME = """
    CREATE INDEX IF NOT EXISTS idx_players_name ON players(name)
"""

CREATE_INDEX_RESULTS_PLAYER_ID = """
    CREATE INDEX IF NOT EXISTS idx_results_player_id ON results(player_id)
"""

CREATE_INDEX_RESULTS_GAME_ID = """
    CREATE INDEX IF NOT EXISTS idx_results_game_id ON results(game_id)
"""

# Player queries
SELECT_PLAYER_BY_NAME = "SELECT id FROM players WHERE name = ?"
INSERT_PLAYER = "INSERT INTO players (name) VALUES (?)"

# Game queries
INSERT_GAME = "INSERT INTO games (board_size, pool_max) VALUES (?, ?)"

# Result queries
INSERT_RESULT = "INSERT INTO results (player_id, game_id, won, draws_count, played_at) VALUES (?, ?, ?, ?, datetime('now'))"
DELETE_ZERO_DRAW_WINS = "DELETE FROM results WHERE won = 1 AND draws_count <= 0"
ALTER_RESULTS_ADD_PLAYED_AT = "ALTER TABLE results ADD COLUMN played_at TEXT"
BACKFILL_PLAYED_AT = "UPDATE results SET played_at = datetime('now') WHERE played_at IS NULL"

# Leaderboard query
SELECT_LEADERBOARD = """
    SELECT
        p.name,
        COUNT(CASE WHEN r.won = 1 THEN 1 END) AS wins,
        COUNT(r.id) AS games_played,
        CASE
            WHEN COUNT(r.id) > 0
            THEN CAST(COUNT(CASE WHEN r.won = 1 THEN 1 END) AS REAL) / COUNT(r.id)
            ELSE 0.0
        END AS win_rate
    FROM players p
    LEFT JOIN results r ON p.id = r.player_id
    GROUP BY p.id, p.name
    HAVING COUNT(r.id) > 0
    ORDER BY wins DESC, games_played DESC
    LIMIT ?
"""

# Recent game history query (newest first)
SELECT_GAME_HISTORY = """
    SELECT
        r.id,
        p.name,
        g.board_size,
        g.pool_max,
        r.won,
        r.draws_count,
        COALESCE(r.played_at, datetime('now')) AS played_at
    FROM results r
    JOIN players p ON r.player_id = p.id
    JOIN games g ON r.game_id = g.id
    ORDER BY r.played_at DESC, r.id DESC
    LIMIT ?
"""

# Test/utility queries
SELECT_PLAYER_BY_ID = "SELECT name FROM players WHERE id = ?"
SELECT_COUNT_GAMES = "SELECT COUNT(*) FROM games"
SELECT_COUNT_RESULTS = "SELECT COUNT(*) FROM results"
SELECT_GAME_FIELDS = "SELECT board_size, pool_max FROM games"
SELECT_RESULT_FIELDS = "SELECT won, draws_count FROM results"
