PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    hero TEXT,
    duration_minutes REAL NOT NULL DEFAULT 0.0,
    deaths INTEGER NOT NULL DEFAULT 0,
    ult_efficiency_score INTEGER NOT NULL DEFAULT 0,
    raw_event_json TEXT NOT NULL DEFAULT '{}',
    feedback_given_json TEXT NOT NULL DEFAULT '{}',
    player_response TEXT,
    map TEXT,
    game_result TEXT,
    allies_json TEXT NOT NULL DEFAULT '[]',
    enemies_json TEXT NOT NULL DEFAULT '[]',
    your_comp TEXT,
    enemy_comp TEXT
);

CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    mistake_type TEXT NOT NULL,
    ability TEXT,
    timestamp_in_session REAL NOT NULL DEFAULT 0.0,
    context_json TEXT NOT NULL DEFAULT '{}',
    severity TEXT NOT NULL DEFAULT 'improvement',
    recurrence_count INTEGER NOT NULL DEFAULT 1,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL,
    improvement_trajectory TEXT NOT NULL DEFAULT 'stable',
    feedback_given TEXT,
    was_acted_on INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_mistakes_session ON mistakes(session_id);
CREATE INDEX IF NOT EXISTS idx_mistakes_type ON mistakes(mistake_type);

CREATE TABLE IF NOT EXISTS player_model (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    updated_at REAL NOT NULL,
    pressure_profile_json TEXT NOT NULL DEFAULT '{}',
    learning_velocity_json TEXT NOT NULL DEFAULT '{}',
    persistent_patterns_json TEXT NOT NULL DEFAULT '{}',
    coaching_style_preference TEXT NOT NULL DEFAULT 'direct',
    current_focus_areas_json TEXT NOT NULL DEFAULT '[]',
    sessions_until_improvement_json TEXT NOT NULL DEFAULT '{}'
);

INSERT OR IGNORE INTO player_model (id, updated_at) VALUES (1, 0.0);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    match_index INTEGER NOT NULL,
    started_at REAL NOT NULL,
    ended_at REAL,
    duration_seconds REAL NOT NULL DEFAULT 0.0,
    map_name TEXT,
    result TEXT NOT NULL DEFAULT 'unknown',
    hero TEXT,
    allies_json TEXT NOT NULL DEFAULT '[]',
    enemies_json TEXT NOT NULL DEFAULT '[]',
    your_comp TEXT,
    enemy_comp TEXT,
    deaths INTEGER NOT NULL DEFAULT 0,
    ult_efficiency_score INTEGER NOT NULL DEFAULT 0,
    aim_on_target_pct REAL NOT NULL DEFAULT 0.0,
    raw_event_json TEXT NOT NULL DEFAULT '{}',
    feedback_given_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_matches_session ON matches(session_id);
CREATE INDEX IF NOT EXISTS idx_matches_hero ON matches(hero);
CREATE INDEX IF NOT EXISTS idx_matches_map ON matches(map_name);

CREATE TABLE IF NOT EXISTS vod_reviews (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT,
    ingested_at REAL NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0.0,
    transcript_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS vod_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    start_seconds REAL NOT NULL,
    end_seconds REAL NOT NULL,
    text TEXT NOT NULL,
    heroes_json TEXT NOT NULL DEFAULT '[]',
    abilities_json TEXT NOT NULL DEFAULT '[]',
    concepts_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (review_id) REFERENCES vod_reviews(id)
);

CREATE INDEX IF NOT EXISTS idx_vod_quotes_review ON vod_quotes(review_id);

CREATE TABLE IF NOT EXISTS vod_correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    quote_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_timestamp REAL NOT NULL,
    score REAL NOT NULL,
    delta_seconds REAL NOT NULL,
    context_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (review_id) REFERENCES vod_reviews(id),
    FOREIGN KEY (quote_id) REFERENCES vod_quotes(id)
);

CREATE INDEX IF NOT EXISTS idx_vod_correlations_event ON vod_correlations(event_type);
CREATE INDEX IF NOT EXISTS idx_vod_correlations_quote ON vod_correlations(quote_id);
