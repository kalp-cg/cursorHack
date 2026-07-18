-- Auth, conversations, and secure audit linkage (additive migration)
-- Safe to run multiple times (IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS users (
    user_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    TEXT,
    preferred_locale TEXT NOT NULL DEFAULT 'en'
        CHECK (preferred_locale IN ('en', 'hi', 'gu')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (lower(email));

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title           TEXT,
    locale          TEXT NOT NULL DEFAULT 'en'
        CHECK (locale IN ('en', 'hi', 'gu')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS conversation_messages (
    message_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content_text    TEXT NOT NULL,
    payload         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON conversation_messages (conversation_id, created_at ASC);

-- Link anonymous traces to users / conversations when authenticated
ALTER TABLE recommendation_traces
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(user_id) ON DELETE SET NULL;

ALTER TABLE recommendation_traces
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_traces_user ON recommendation_traces (user_id, created_at DESC);
