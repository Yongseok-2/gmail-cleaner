CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS emails_raw (
    id BIGSERIAL PRIMARY KEY,
    gmail_message_id TEXT UNIQUE NOT NULL,
    gmail_thread_id TEXT,
    subject TEXT,
    from_email TEXT,
    to_email TEXT,
    date_header TEXT,
    snippet TEXT,
    internal_date TEXT,
    label_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(768),
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
