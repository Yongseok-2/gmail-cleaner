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

CREATE TABLE IF NOT EXISTS email_analysis (
    id BIGSERIAL PRIMARY KEY,
    gmail_message_id TEXT UNIQUE NOT NULL REFERENCES emails_raw(gmail_message_id) ON DELETE CASCADE,
    sender_email TEXT,
    category TEXT NOT NULL,
    urgency_score INT NOT NULL DEFAULT 0,
    summary TEXT NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    analysis_source TEXT NOT NULL DEFAULT 'rules',
    review_required BOOLEAN NOT NULL DEFAULT false,
    draft_reply_context TEXT,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE email_analysis ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.0;
ALTER TABLE email_analysis ADD COLUMN IF NOT EXISTS analysis_source TEXT NOT NULL DEFAULT 'rules';
ALTER TABLE email_analysis ADD COLUMN IF NOT EXISTS review_required BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_email_analysis_category ON email_analysis(category);
CREATE INDEX IF NOT EXISTS idx_email_analysis_urgency ON email_analysis(urgency_score DESC);
CREATE INDEX IF NOT EXISTS idx_email_analysis_analyzed_at ON email_analysis(analyzed_at DESC);

CREATE TABLE IF NOT EXISTS reply_memory (
    id BIGSERIAL PRIMARY KEY,
    from_email TEXT,
    intent TEXT,
    user_reply TEXT NOT NULL,
    reply_embedding vector(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
