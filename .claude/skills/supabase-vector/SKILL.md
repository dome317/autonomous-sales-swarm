---
description: Supabase pgvector setup patterns for n8n RAG workflows. Auto-loads when working with vector databases, embeddings, or similarity search.
---

# Supabase pgvector for n8n RAG

## Setup Checklist
1. Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Create tables with VECTOR columns
3. Create similarity search functions
4. Create IVFFlat indexes (after inserting initial data)
5. Set up RLS policies
6. Test with n8n Supabase Vector Store node

## Similarity Search Function (required by n8n)

```sql
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.78,
  match_count INT DEFAULT 5,
  filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
  id BIGINT,
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
  WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
    AND (filter = '{}' OR d.metadata @> filter)
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

## Lead Memory Search (filtered by lead_id)

```sql
CREATE OR REPLACE FUNCTION match_lead_memory (
  query_embedding VECTOR(1536),
  p_lead_id TEXT,
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  memory_type TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    lm.id,
    lm.content,
    lm.memory_type,
    1 - (lm.embedding <=> query_embedding) AS similarity
  FROM lead_memory lm
  WHERE lm.lead_id = p_lead_id
    AND 1 - (lm.embedding <=> query_embedding) > match_threshold
  ORDER BY lm.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

## n8n Connection
- Credential type: Supabase API
- URL: your Supabase project URL
- Service Role Key: for insert operations (bypasses RLS)
- Anon Key: for read-only operations
