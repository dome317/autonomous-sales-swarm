-- ============================================================
-- Sales Swarm — Supabase pgvector Schema
-- Run once on fresh database: psql -f init-supabase.sql
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --- Documents table (RAG knowledge base) ---
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding VECTOR(1536),  -- text-embedding-3-small dimension
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_embedding
  ON documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_documents_metadata
  ON documents USING gin (metadata);

-- --- Lead Memory table (per-lead context) ---
CREATE TABLE IF NOT EXISTS lead_memory (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id TEXT NOT NULL,
  memory_type TEXT NOT NULL CHECK (memory_type IN (
    'enrichment', 'scoring', 'outreach', 'interaction', 'outcome'
  )),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lead_memory_lead_id
  ON lead_memory (lead_id);

CREATE INDEX IF NOT EXISTS idx_lead_memory_embedding
  ON lead_memory USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_lead_memory_type
  ON lead_memory (memory_type);

-- --- Swarm Learnings table (self-improvement loop) ---
CREATE TABLE IF NOT EXISTS swarm_learnings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category TEXT NOT NULL CHECK (category IN (
    'outreach_effectiveness', 'scoring_accuracy',
    'channel_preference', 'objection_handling',
    'segment_insight', 'process_improvement'
  )),
  insight TEXT NOT NULL,
  supporting_data JSONB DEFAULT '{}'::jsonb,
  embedding VECTOR(1536),
  confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
  times_validated INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_swarm_learnings_embedding
  ON swarm_learnings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_swarm_learnings_category
  ON swarm_learnings (category);

-- --- Similarity search: documents ---
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.78,
  match_count INT DEFAULT 5,
  filter_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.content,
    d.metadata,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE
    1 - (d.embedding <=> query_embedding) > match_threshold
    AND (filter_metadata = '{}'::jsonb OR d.metadata @> filter_metadata)
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- --- Similarity search: lead memory (filtered by lead) ---
CREATE OR REPLACE FUNCTION match_lead_memory(
  query_embedding VECTOR(1536),
  p_lead_id TEXT,
  match_threshold FLOAT DEFAULT 0.75,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  lead_id TEXT,
  memory_type TEXT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    lm.id,
    lm.lead_id,
    lm.memory_type,
    lm.content,
    lm.metadata,
    1 - (lm.embedding <=> query_embedding) AS similarity
  FROM lead_memory lm
  WHERE
    lm.lead_id = p_lead_id
    AND 1 - (lm.embedding <=> query_embedding) > match_threshold
  ORDER BY lm.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- --- Similarity search: swarm learnings ---
CREATE OR REPLACE FUNCTION match_swarm_learnings(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.75,
  match_count INT DEFAULT 5,
  p_category TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  category TEXT,
  insight TEXT,
  supporting_data JSONB,
  confidence FLOAT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sl.id,
    sl.category,
    sl.insight,
    sl.supporting_data,
    sl.confidence,
    1 - (sl.embedding <=> query_embedding) AS similarity
  FROM swarm_learnings sl
  WHERE
    1 - (sl.embedding <=> query_embedding) > match_threshold
    AND (p_category IS NULL OR sl.category = p_category)
  ORDER BY sl.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- --- Row Level Security ---
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE swarm_learnings ENABLE ROW LEVEL SECURITY;

-- Service role has full access (n8n connects as service role)
CREATE POLICY "Service role full access on documents"
  ON documents FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on lead_memory"
  ON lead_memory FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on swarm_learnings"
  ON swarm_learnings FOR ALL
  USING (auth.role() = 'service_role');

-- Anon can read documents (for RAG retrieval)
CREATE POLICY "Anon read access on documents"
  ON documents FOR SELECT
  USING (auth.role() = 'anon');
