# Agent Reference

## Overview

The swarm consists of 7 autonomous agents, each a separate n8n workflow connected via the supervisor.

---

## 00 — Supervisor Agent

**File**: `workflows/00-supervisor.json`
**Prompt**: `config/prompts/supervisor-system.md`

**Role**: Central router that classifies incoming lead data and dispatches to the correct specialist.

**Input**: Webhook payload or CRM trigger with lead data
**Output**: Routing decision → Execute Sub-Workflow

**Routes**:
| Decision | Target |
|----------|--------|
| `research` | 01 — Lead Intelligence |
| `qualify` | 02 — Qualification Scoring |
| `outreach` | 03 — Outreach Orchestrator |
| `onboard` | 04 — Onboarding Executor |
| `support` | 05 — Support Guardian |
| `report` | 06 — Analytics Reporter |
| `nurture` | Low-touch email sequence |
| `escalate` | Slack notification to sales team |

---

## 01 — Lead Intelligence Agent

**File**: `workflows/01-lead-intelligence.json`
**Prompt**: `config/prompts/lead-intel-system.md`

**Role**: Researches and enriches lead data by scraping websites, analyzing company profiles, and updating CRM.

**Tools**:
- HTTP Request (website scraping)
- HubSpot (create/update contact)
- Supabase (store enrichment in lead_memory)

**Output**: Enriched lead profile with company size, tech stack, pain indicators.

---

## 02 — Qualification Scoring Agent

**File**: `workflows/02-qualification-scoring.json`
**Prompt**: `config/prompts/qualifier-system.md`

**Role**: Scores leads using the weighted model + RAG context from similar past leads.

**Tools**:
- Supabase Vector Store (retrieve similar leads)
- Code Node (run scoring model)
- HubSpot (update lead score + tier)

**Scoring Model**: See `scoring/scoring-config.json` for weights and thresholds.

**Output**: Score (0-100), tier (hot/warm/cold), detailed breakdown.

---

## 03 — Outreach Orchestrator Agent

**File**: `workflows/03-outreach-orchestrator.json`
**Prompt**: `config/prompts/outreach-system.md`

**Role**: Generates hyper-personalized outreach sequences based on lead profile, score tier, and RAG context.

**Tools**:
- Supabase Vector Store (retrieve product knowledge)
- Gmail / SendGrid (send emails)
- WhatsApp Business API (direct messages)
- HubSpot (log activities)

**Channels**: Email (primary), WhatsApp (high-intent), Slack (internal alerts)

**Output**: Personalized message sent + activity logged in CRM.

---

## 04 — Onboarding Executor Agent

**File**: `workflows/04-onboarding-executor.json`
**Prompt**: `config/prompts/onboarding-system.md`

**Role**: Automates post-sale onboarding — welcome emails, calendar invites, documentation setup.

**Tools**:
- Gmail (welcome sequence)
- Google Calendar (kickoff meeting)
- Notion (create onboarding page)
- HubSpot (update deal stage)

**Output**: Complete onboarding package delivered to new customer.

---

## 05 — Support Guardian Agent

**File**: `workflows/05-support-guardian.json`
**Prompt**: `config/prompts/support-system.md`

**Role**: Auto-answers support queries using RAG knowledge base. Escalates complex issues to humans.

**Tools**:
- Supabase Vector Store (search knowledge base)
- Gmail (send response)
- Slack (escalation alerts)
- HubSpot (log ticket)

**Target**: Resolve 70%+ of queries automatically.

**Output**: AI response or escalation with context summary.

---

## 06 — Analytics Reporter Agent

**File**: `workflows/06-analytics-reporter.json`
**Prompt**: N/A (uses inline system message)

**Role**: Generates daily/weekly performance summaries with AI analysis.

**Data Sources**:
- HubSpot (pipeline metrics)
- Supabase (agent activity logs)
- Swarm learnings table

**Output**: Formatted Slack message with KPIs, trends, and AI recommendations.

---

## Adding a New Agent

1. Create workflow JSON in `workflows/`
2. Write system prompt in `config/prompts/`
3. Add route in supervisor's Switch node
4. Add test cases in `tests/test-supervisor-routing.js`
5. Document here
