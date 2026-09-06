CREATE TABLE IF NOT EXISTS rami_accounts (
    id BIGSERIAL PRIMARY KEY,
    google_sub TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT NOT NULL DEFAULT 'Joueur',
    elo INTEGER NOT NULL DEFAULT 100 CHECK (elo >= 0),
    games_played INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rami_rooms (
    id BIGSERIAL PRIMARY KEY,
    creator_account_id BIGINT NOT NULL REFERENCES rami_accounts(id) ON DELETE CASCADE,
    target_players INTEGER NOT NULL CHECK (target_players BETWEEN 2 AND 4),
    base_elo INTEGER NOT NULL CHECK (base_elo >= 0),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','full','started','closed','cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS rami_room_players (
    room_id BIGINT NOT NULL REFERENCES rami_rooms(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES rami_accounts(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    seat_index INTEGER NOT NULL,
    PRIMARY KEY (room_id, account_id),
    UNIQUE (room_id, seat_index)
);

CREATE TABLE IF NOT EXISTS rami_matches (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT UNIQUE REFERENCES rami_rooms(id) ON DELETE SET NULL,
    target_players INTEGER NOT NULL CHECK (target_players BETWEEN 2 AND 4),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','finished','cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS rami_match_players (
    match_id BIGINT NOT NULL REFERENCES rami_matches(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES rami_accounts(id) ON DELETE CASCADE,
    seat_index INTEGER NOT NULL,
    elo_before INTEGER NOT NULL,
    elo_after INTEGER,
    placement INTEGER,
    disconnected BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (match_id, account_id),
    UNIQUE (match_id, seat_index)
);

CREATE INDEX IF NOT EXISTS idx_rami_rooms_open_size_elo
    ON rami_rooms(status, target_players, base_elo, created_at);
CREATE INDEX IF NOT EXISTS idx_rami_room_players_account
    ON rami_room_players(account_id);
CREATE INDEX IF NOT EXISTS idx_rami_match_players_account
    ON rami_match_players(account_id);
