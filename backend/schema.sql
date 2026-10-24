-- =============================================================================
-- Wayhall Municipal Knowledge Assistant — Database Schema & RPC Functions
-- Run this script in the Supabase SQL Editor to initialize the database.
-- =============================================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Document chunks table (PDF Knowledge Base)
CREATE TABLE IF NOT EXISTS document_chunks (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chunk_id    TEXT UNIQUE NOT NULL,
    text        TEXT NOT NULL,
    embedding   VECTOR(768),                         -- 768-dimensional embeddings (Gemini embedding-001)
    source      TEXT NOT NULL,                       -- Original PDF filename
    page        INTEGER NOT NULL,                    -- 1-indexed original page number
    section     TEXT,                                -- Detected section heading
    doc_label   TEXT NOT NULL,                       -- "permits" | "bylaws" | "service_requests"
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Full-text search column & index
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_chunks' AND column_name = 'fts_vector'
    ) THEN
        ALTER TABLE document_chunks
            ADD COLUMN fts_vector TSVECTOR
            GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS document_chunks_fts_idx 
    ON document_chunks USING GIN(fts_vector);

CREATE INDEX IF NOT EXISTS document_chunks_label_idx 
    ON document_chunks(doc_label);

-- Vector similarity index (cosine)
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 3. Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    summary     TEXT
);

-- 4. Chat messages table (conversation history)
CREATE TABLE IF NOT EXISTS chat_messages (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    citations   JSONB DEFAULT '[]'::JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chat_messages_session_idx
    ON chat_messages(session_id, created_at);

-- 5. RPC Function: Dense Vector Similarity Search (768d cosine)
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(768),
    match_count int,
    doc_label_filter text DEFAULT NULL
)
RETURNS TABLE (
    chunk_id text,
    text text,
    source text,
    page integer,
    section text,
    doc_label text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        dc.chunk_id,
        dc.text,
        dc.source,
        dc.page,
        dc.section,
        dc.doc_label,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE (doc_label_filter IS NULL OR dc.doc_label = doc_label_filter)
      AND dc.embedding IS NOT NULL
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 6. RPC Function: Full-Text Search (BM25/ts_rank)
CREATE OR REPLACE FUNCTION search_chunks_fts(
    query_text text,
    match_count int,
    doc_label_filter text DEFAULT NULL
)
RETURNS TABLE (
    chunk_id text,
    text text,
    source text,
    page integer,
    section text,
    doc_label text,
    rank float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        dc.chunk_id,
        dc.text,
        dc.source,
        dc.page,
        dc.section,
        dc.doc_label,
        ts_rank(dc.fts_vector, plainto_tsquery('english', query_text)) AS rank
    FROM document_chunks dc
    WHERE (doc_label_filter IS NULL OR dc.doc_label = doc_label_filter)
      AND dc.fts_vector @@ plainto_tsquery('english', query_text)
    ORDER BY rank DESC
    LIMIT match_count;
$$;

-- 7. Permissions for client access
GRANT ALL ON document_chunks TO anon, authenticated, service_role;
GRANT ALL ON chat_sessions TO anon, authenticated, service_role;
GRANT ALL ON chat_messages TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION match_chunks TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION search_chunks_fts TO anon, authenticated, service_role;
