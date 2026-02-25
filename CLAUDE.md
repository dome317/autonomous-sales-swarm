# Autonomous Sales Swarm — Claude Code Project Config

## WHAT: Project Overview

A **fully autonomous multi-agent sales pipeline** using n8n workflows. Supervisor orchestration, agentic RAG, tool-calling, persistent memory per lead, and a closed-loop self-improvement system.

### Tech Stack
- **Orchestration**: n8n (self-hosted, Docker)
- **LLMs**: Claude Sonnet 4 (primary), GPT-4o (fallback), Groq (speed tasks)
- **Embeddings**: OpenAI text-embedding-3-small (1536-dim, for RAG query embedding in WF02, WF03, WF05)
- **Vector DB**: Supabase (pgvector extension)
- **CRM**: HubSpot (native n8n nodes)
- **Comms**: Gmail/SendGrid, WhatsApp Business API, Slack
- **Code Nodes**: JavaScript (n8n native), Python (data transforms)

### Project Structure
```
autonomous-sales-swarm/
├── CLAUDE.md                          # This file
├── .claude/
│   ├── agents/                        # Sub-agents for specialized tasks
│   ├── skills/                        # Domain knowledge & patterns
│   └── commands/                      # Custom slash commands
├── infrastructure/
│   ├── docker-compose.yml             # n8n + Supabase + Redis
│   ├── .env.example                   # Environment variables template
│   └── init-supabase.sql              # Vector DB schema + RLS policies
├── workflows/
│   ├── 00-supervisor.json             # Master orchestrator
│   ├── 01-lead-intelligence.json      # Lead research sub-workflow
│   ├── 02-qualification-scoring.json  # RAG-based scoring
│   ├── 03-outreach-orchestrator.json  # Multi-channel outreach
│   ├── 04-onboarding-executor.json    # Post-sale automation
│   ├── 05-support-guardian.json       # Auto-support with RAG
│   └── 06-analytics-reporter.json     # AI-generated summaries
├── config/prompts/                    # Agent system prompts
├── agents/                            # Claude Code agent definitions
├── skills/                            # Claude Code skill definitions
├── rag/
│   ├── knowledge-base/                # Source docs for RAG embedding
│   ├── embed-docs.py                  # Embedding script
│   └── retrieval-config.json          # Multi-query RAG config
├── scoring/
│   ├── lead_scoring_model.py          # Weighted scoring logic
│   └── scoring-config.json            # Weights + thresholds
├── tests/                             # Test suite
├── docs/                              # Documentation
└── scripts/                           # Deployment & utility scripts
```

## HOW: Development Workflow

### Build Order (STRICT)
1. **Infrastructure** → Docker, Supabase, n8n running
2. **RAG Knowledge Base** → Documents embedded, retrieval working
3. **Supervisor Workflow** → Routing logic with Switch nodes
4. **Lead Intelligence Agent** → Website scraping + enrichment
5. **Qualification Agent** → RAG scoring + CRM update
6. **Outreach Agent** → Email generation + send
7. **Onboarding Agent** → Post-sale automation
8. **Support Agent** → RAG auto-responses
9. **Analytics Reporter** → Daily summaries
10. **Self-Improvement Loop** → Outcome → embedding → RAG update
11. **Testing** → End-to-end with simulated leads

### n8n Workflow JSON Standards
- Every workflow gets a descriptive `name` and `tags`
- Node IDs: `{workflow-abbrev}-{function}` (e.g., `sup-route-switch`)
- AI Agent Nodes: `@n8n/n8n-nodes-langchain.agent` with explicit `systemMessage`
- Sub-workflow calls: `n8n-nodes-base.executeWorkflow` with `workflowId`
- Error handling: try/catch → Slack alert fallback
- Webhook nodes: Header Auth or Basic
- Credentials: placeholder names `{{HUBSPOT_CRED}}`, `{{SUPABASE_CRED}}`, `{{OPENAI_CRED}}`, `{{ANTHROPIC_CRED}}`

### Code Conventions
- JavaScript in n8n Code Nodes: ES2022, no external imports (n8n sandbox)
- Python scripts: 3.11+, type hints, docstrings
- System prompts: Markdown with XML tags for structured sections
- JSON configs: camelCase keys

### Testing & Validation
- Validate workflow JSON: `jq . workflow.json`
- Test each agent independently before connecting to supervisor
- Use `tests/test-leads.json` for consistent test data

### Commit Convention
```
feat(agent-name): description    — new agent or major feature
fix(agent-name): description     — bug fix
docs: description                — documentation only
infra: description               — Docker, deployment, config
test: description                — test additions/fixes
refactor(agent-name): description — code restructuring
```

## CRITICAL CONSTRAINTS

- **GDPR**: No PII in logs, vector DB stores only anonymized summaries
- **n8n Version**: Target n8n 1.70+ (AI Agent Nodes with LangChain, Sub-Workflows)
- **Cost Control**: Claude Sonnet (not Opus) for agents, Supabase free tier
- **Idempotency**: Workflows must handle duplicate webhook triggers gracefully
- **Rate Limits**: Respect HubSpot API (100 calls/10sec), Claude API (varies by tier)
