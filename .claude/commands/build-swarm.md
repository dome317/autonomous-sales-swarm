Build the Autonomous Sales Swarm — a complete multi-agent n8n system for B2B SaaS sales automation. Follow the phased build order defined in CLAUDE.md strictly.

## Execution Strategy

Work through each phase sequentially. After completing each phase, commit with the appropriate convention, verify the output, and only then proceed. Use subagents for parallel research tasks. Use /clear between major phases to keep context fresh.

## Phase 1: Infrastructure (do first, verify before proceeding)

1. Create `infrastructure/docker-compose.yml`:
   - n8n (latest, self-hosted, port 5678)
   - Supabase (postgres with pgvector, port 54322)
   - Redis (for n8n queue mode, optional)
   - Volume mounts for persistence
   - `.env` file reference for all secrets

2. Create `infrastructure/.env.example` with all required variables:
   - N8N_*, SUPABASE_*, OPENAI_API_KEY, ANTHROPIC_API_KEY, HUBSPOT_API_KEY, SLACK_WEBHOOK_URL

3. Create `infrastructure/init-supabase.sql`:
   - Use the rag-architect subagent schema (documents, lead_memory, swarm_learnings tables)
   - Add RLS policies
   - Create match_documents function for similarity search
   - Create match_lead_memory function filtered by lead_id

4. Verify: `docker-compose config` validates, SQL is syntactically correct.

## Phase 2: RAG Knowledge Base

1. Create knowledge base source documents in `rag/knowledge-base/`:
   - `product-features.md` — comprehensive product feature list
   - `conversion-stats.md` — conversion statistics and benchmarks
   - `case-studies/` — sample success stories
   - `gdpr-templates.md` — GDPR-compliant communication templates
   - `compliance-guide.md` — relevant regulations

2. Create `rag/embed-docs.py`:
   - Reads all .md files from knowledge-base/
   - Chunks at 500 tokens with 100-token overlap
   - Embeds via OpenAI text-embedding-3-small
   - Inserts into Supabase documents table with metadata

3. Create `rag/retrieval-config.json`

## Phase 3: System Prompts (use prompt-engineer subagent)

Create all system prompts in `config/prompts/`. Each prompt must follow the structure defined in the prompt-engineer subagent.

1. `supervisor-system.md` — Routes leads to correct specialist agent
2. `lead-intel-system.md` — Researches company website, extracts structured data
3. `qualifier-system.md` — Scores leads using RAG context + weighted criteria
4. `outreach-system.md` — Generates personalized outreach messages
5. `onboarding-system.md` — Creates onboarding checklist and content
6. `support-system.md` — Auto-answers support queries using RAG

## Phase 4: Core Workflows (use n8n-workflow-builder subagent)

Build each workflow as a valid n8n JSON file. Test with `jq . file.json`.

### 4a-4g: Supervisor, Lead Intelligence, Qualification, Outreach, Onboarding, Support, Analytics

## Phase 5: Self-Improvement Loop

After each lead reaches terminal state:
- Collect lead profile, agent decisions, outreach content, outcome
- AI Agent generates learning summary
- Embed and insert into swarm_learnings table

## Phase 6: Scoring Model

Create `scoring/scoring-config.json` and `scoring/lead_scoring_model.py`

## Phase 7: Test Suite (use test-simulator subagent)

1. Generate `tests/test-leads.json`
2. Create `tests/test-supervisor-routing.js`
3. Create `tests/test-scoring-accuracy.py`

## Phase 8: Documentation

1. `docs/architecture.md`
2. `docs/agents.md`
3. `docs/n8n-setup.md`
4. `docs/rag-setup.md`

## Phase 9: Deployment Script

Create `scripts/deploy.sh` — one-command deployment.

---

After completing all phases, provide a summary of what was built, what needs manual configuration (API keys, credentials), and next steps.
