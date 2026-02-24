# RAG Setup Guide

## Overview

The swarm uses Retrieval-Augmented Generation (RAG) with Supabase pgvector to give agents access to domain knowledge, lead history, and self-improvement data.

## Architecture

```
Knowledge Base (.md files)
        │
        ▼
   embed-docs.py
   (chunk → embed via OpenAI)
        │
        ▼
  ┌─────────────┐
  │  Supabase    │
  │  pgvector    │
  │              │
  │  documents   │ ← Product knowledge, case studies, compliance
  │  lead_memory │ ← Per-lead interaction history
  │  swarm_learn │ ← Self-improvement insights
  └─────────────┘
        │
        ▼
  n8n Vector Store Node
  (similarity search at query time)
```

## Database Schema

The schema is defined in `infrastructure/init-supabase.sql`. Three tables:

### `documents`
Stores embedded knowledge base chunks.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| content | TEXT | Chunk text |
| metadata | JSONB | Source file, chunk index |
| embedding | vector(1536) | OpenAI embedding |

### `lead_memory`
Stores per-lead context across agent interactions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| lead_id | TEXT | CRM lead identifier |
| agent | TEXT | Which agent wrote this |
| action | TEXT | What was done |
| context | JSONB | Structured context data |
| embedding | vector(1536) | Searchable embedding |

### `swarm_learnings`
Stores outcome-based insights for self-improvement.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| learning_type | TEXT | Type of insight |
| insight | TEXT | What was learned |
| outcome | TEXT | What happened |
| embedding | vector(1536) | Searchable embedding |

## Setup Steps

### 1. Initialize Database

The database is auto-initialized when Docker starts (via `init-supabase.sql`). To verify:

```bash
docker exec swarm-postgres psql -U postgres -d swarm \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
```

Expected: 3+ tables.

### 2. Add Knowledge Base Documents

Place `.md` files in `rag/knowledge-base/`:

```
rag/knowledge-base/
├── product-features.md      # Your product documentation
├── conversion-stats.md      # Industry conversion benchmarks
├── gdpr-templates.md        # GDPR compliance templates
├── compliance-guide.md      # Regulatory information
└── case-studies/
    ├── berlin-techstart.md  # Customer success story
    └── muenchen-enterprise.md
```

### 3. Embed Documents

```bash
# Set environment variables
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="http://localhost:54322"
export SUPABASE_SERVICE_ROLE_KEY="your-key"

# Run embedder
pip install openai supabase tiktoken
python rag/embed-docs.py
```

Or use the convenience script:
```bash
bash scripts/seed-rag.sh
```

### 4. Verify Embeddings

```bash
docker exec swarm-postgres psql -U postgres -d swarm \
  -c "SELECT count(*), avg(char_length(content)) FROM documents;"
```

## Embedding Configuration

Configured in `rag/embed-docs.py`:

| Setting | Value | Notes |
|---------|-------|-------|
| Model | `text-embedding-3-small` | Cost-effective, 1536 dims |
| Chunk size | 500 tokens | Balances context vs precision |
| Chunk overlap | 100 tokens | Prevents context loss at boundaries |
| Batch size | 100 | Per API call |

## Retrieval Configuration

Configured in `rag/retrieval-config.json`:

| Setting | Value | Notes |
|---------|-------|-------|
| Top K | 5 | Number of chunks returned |
| Similarity threshold | 0.7 | Minimum relevance score |
| Strategy | Multi-query | Generates multiple search queries |

## n8n Integration

In n8n workflows, agents access RAG via the **Supabase Vector Store** node:

1. Add a **Vector Store** tool to your AI Agent node
2. Configure with Supabase credentials
3. Set table name (`documents`, `lead_memory`, or `swarm_learnings`)
4. The agent automatically queries relevant context

## Self-Improvement Loop

The swarm improves over time:

1. **Outreach agent** sends message → tracks outcome
2. **Outcome** (replied, converted, ignored) is recorded
3. **Learning** is extracted: "What worked? What didn't?"
4. **Embedding** is generated and stored in `swarm_learnings`
5. **Future queries** include these learnings as context

This creates a flywheel: more interactions → better context → better decisions.

## Re-embedding

To update the knowledge base after adding/changing documents:

```bash
# This clears existing documents and re-embeds everything
python rag/embed-docs.py
```

The script automatically clears the `documents` table before inserting.
