# Architecture Overview

## System Design

The Autonomous Sales Swarm uses a **supervisor pattern** where a central orchestrator routes incoming leads to specialized sub-agents based on context analysis.

## Core Principles

1. **Autonomy**: Each agent operates independently with its own tools and RAG context
2. **Specialization**: Agents are purpose-built for one phase of the sales cycle
3. **Memory**: Persistent lead memory in Supabase enables context across interactions
4. **Self-Improvement**: Outcome feedback is embedded back into the knowledge base

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ENTRY POINTS                          │
│  Webhook (lead form)  │  CRM Trigger  │  Scheduled       │
└──────────┬────────────┴───────┬───────┴──────┬──────────┘
           │                    │              │
           ▼                    ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              00 — SUPERVISOR AGENT                        │
│  Claude AI → intent classification → Switch router       │
│  Routes: research | qualify | outreach | onboard |       │
│          support | nurture | escalate | report           │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│ 01 │ │ 02 │ │ 03 │ │ 04 │ │ 05 │ │ 06 │ │Slk │
│Lead│ │Qual│ │Out-│ │On- │ │Sup-│ │Ana-│ │Esc │
│Intl│ │ify │ │rch │ │brd │ │port│ │lyts│ │alat│
└─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └────┘
  │       │      │      │      │      │
  ▼       ▼      ▼      ▼      ▼      ▼
┌─────────────────────────────────────────────────────────┐
│                 SHARED INFRASTRUCTURE                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Supabase │  │ HubSpot  │  │  Redis   │               │
│  │ pgvector │  │   CRM    │  │  Cache   │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              SELF-IMPROVEMENT LOOP                        │
│  Outcome → Analyze → Embed Learning → swarm_learnings    │
│  Future queries use learnings for better decisions        │
└─────────────────────────────────────────────────────────┘
```

## Data Model

### Supabase Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `documents` | RAG knowledge base | content, metadata, embedding (vector 1536) |
| `lead_memory` | Per-lead interaction history | lead_id, agent, action, context, embedding |
| `swarm_learnings` | Self-improvement data | learning_type, insight, outcome, embedding |

### Lead Lifecycle

```
New Lead → Research → Score → Route
  │
  ├─ Hot (≥75)  → Personalized outreach → Follow-up → Close → Onboard
  ├─ Warm (≥45) → Nurture sequence → Re-score → Re-route
  └─ Cold (<45) → Low-touch nurture → Periodic re-evaluation
```

## Scoring Model

Five weighted criteria:

| Criterion | Weight | What It Measures |
|-----------|--------|-----------------|
| Company Size | 25% | Team count → revenue potential |
| Pain Match | 30% | How well problems match our solution |
| Digital Readiness | 20% | Likelihood of adopting SaaS |
| Region Fit | 15% | Proximity to target markets |
| Source Quality | 10% | Lead origin reliability |

Thresholds: **Hot** ≥ 75 | **Warm** ≥ 45 | **Cold** < 45

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | n8n | Visual workflows, AI Agent Nodes, self-hostable |
| Primary LLM | Claude Sonnet 4 | Best reasoning + native German |
| Vector DB | Supabase pgvector | Free tier, Postgres ecosystem, RLS |
| CRM | HubSpot | Native n8n integration, free tier |
| Cache | Redis | Rate limiting, temp state, fast lookups |

## Error Handling

Every critical path follows this pattern:

```
Agent Node → Try/Catch
  ├─ Success → Continue pipeline
  └─ Error → Log to Supabase → Slack alert → Graceful fallback
```

Fallbacks include:
- LLM timeout → retry with shorter prompt or fallback model
- CRM API error → queue for retry via Redis
- RAG empty results → proceed without context, flag for review
