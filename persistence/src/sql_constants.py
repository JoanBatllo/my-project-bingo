#!/usr/bin/env python3

# --- Schema ---
CREATE_TABLE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_TABLE_GAMES = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_size INTEGER NOT NULL
        CHECK (board_size IN (3,4,5)),
    pool_max INTEGER NOT NULL
        CHECK (pool_max >= board_size * board_size),
    finished_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_TABLE_RESULTS = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    won INTEGER NOT NULL
        CHECK (won IN (0,1)),
    draws_count INTEGER NOT NULL
        CHECK (draws_count >= 0),
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
)
"""

# Trigger to enforce foreign key-like behaviour even if PRAGMA foreign_keys
# is not enabled on a different SQLite connection (like in the test).
CREATE_TRIGGER_RESULTS_FK = """
CREATE TRIGGER IF NOT EXISTS fk_results_player_game
BEFORE INSERT ON results
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'foreign key constraint failed')
    WHERE (SELECT id FROM players WHERE id = NEW.player_id) IS NULL
       OR (SELECT id FROM games   WHERE id = NEW.game_id)   IS NULL;
END;
"""

# --- Indexes ---
CREATE_UNIQUE_IDX_PLAYERS_NAME = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players(name);
"""
CREATE_IDX_RESULTS_PLAYER = """
CREATE INDEX IF NOT EXISTS idx_results_player ON results(player_id);
"""
CREATE_IDX_RESULTS_GAME = """
CREATE INDEX IF NOT EXISTS idx_results_game ON results(game_id);
"""

# --- Player helpers ---
UPSERT_PLAYER_BY_NAME = """
INSERT INTO players (name) VALUES (?) ON CONFLICT(name) DO NOTHING;
"""
INSERT_OR_IGNORE_PLAYER = """
INSERT OR IGNORE INTO players (name) VALUES (?);
"""
SELECT_PLAYER_ID_BY_NAME = """
SELECT id FROM players WHERE name = ?;
"""
PLAIN_INSERT_PLAYER = """
INSERT INTO players (name) VALUES (?);
"""

# --- Game/Result writes ---
INSERT_GAME = """
INSERT INTO games (board_size, pool_max) VALUES (?, ?);
"""
INSERT_RESULT = """
INSERT INTO results (player_id, game_id, won, draws_count) VALUES (?, ?, ?, ?);
"""

# --- Leaderboard ---
SELECT_LEADERBOARD = """
SELECT
    p.name AS name,
    COUNT(*) AS games_played,
    SUM(CASE WHEN r.won = 1 THEN 1 ELSE 0 END) AS wins,
    ROUND(
        100.0 * SUM(CASE WHEN r.won = 1 THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS win_rate
FROM results r
JOIN players p ON p.id = r.player_id
GROUP BY p.id, p.name
ORDER BY wins DESC, games_played DESC
LIMIT ?;
"""
