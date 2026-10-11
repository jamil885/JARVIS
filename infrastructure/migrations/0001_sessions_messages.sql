-- JARVIS schema v0001. Apply once to a local development database.
BEGIN;

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL CHECK (length(content) BETWEEN 1 AND 20000),
    client_message_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT messages_session_client_id_unique UNIQUE (session_id, client_message_id)
);

CREATE INDEX IF NOT EXISTS messages_session_created_idx
    ON messages (session_id, created_at, id);

COMMIT;
