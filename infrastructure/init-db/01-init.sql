-- ===========================================================================
-- InferFlow — Database Initialization
-- ===========================================================================
-- This script runs automatically when the PostgreSQL container is first created.
-- It sets up the initial schema structure.
--
-- Schema design decisions:
--   - conversations: lightweight container for grouping messages
--   - messages: individual user/assistant messages within a conversation
--   - inference_logs: normalized inference telemetry (separated from messages)
--
-- Why separate messages and inference_logs?
--   Messages are user-facing content. Inference logs capture operational
--   telemetry (latency, token usage, model, etc.) that would bloat the
--   messages table and serve a different query pattern.
--
-- Why JSONB metadata?
--   Flexible key-value storage for provider-specific data without
--   schema migrations. Useful for A/B testing, feature flags, and
--   provider-specific response metadata.
-- ===========================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------
-- Conversations
-- -----------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB DEFAULT '{}'::jsonb
);

-- -----------------------------------
-- Messages
-- -----------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- -----------------------------------
-- Inference Logs
-- -----------------------------------
-- Normalized inference telemetry, one row per LLM inference event.
-- Separated from messages to keep operational data independent
-- of user-facing content.
--
-- Idempotency: (request_id, event_type) is UNIQUE. The ingestion worker uses
-- ON CONFLICT (request_id, event_type) DO NOTHING to safely handle Redis
-- Streams replays without dropping subsequent events for the same request.
CREATE TABLE IF NOT EXISTS inference_logs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id        UUID NOT NULL,
    conversation_id   UUID NOT NULL,
    event_type        TEXT NOT NULL,
    provider          TEXT NOT NULL,
    model             TEXT NOT NULL,
    status            TEXT,
    ttft_ms           INTEGER,
    total_latency_ms  INTEGER,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    input_preview     TEXT,
    output_preview    TEXT,
    error             TEXT,
    event_timestamp   TIMESTAMPTZ NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata          JSONB DEFAULT '{}'::jsonb,
    UNIQUE(request_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_inference_logs_request_id ON inference_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_inference_logs_conversation_id ON inference_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_inference_logs_event_type ON inference_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_inference_logs_model ON inference_logs(model);
CREATE INDEX IF NOT EXISTS idx_inference_logs_created_at ON inference_logs(created_at);

