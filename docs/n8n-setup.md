# n8n Setup Guide

## Prerequisites

- n8n 1.70+ (for AI Agent Nodes with LangChain support)
- Docker & Docker Compose
- API keys ready: Anthropic, OpenAI, HubSpot

## Step 1: Start Infrastructure

```bash
cd infrastructure
cp .env.example .env
# Edit .env with your actual API keys
docker compose up -d
```

Verify all services are running:
```bash
docker compose ps
```

Expected: `swarm-n8n`, `swarm-postgres`, `swarm-redis` all healthy.

## Step 2: Access n8n

Open `http://localhost:5678` in your browser and create your admin account.

## Step 3: Configure Credentials

In n8n, go to **Settings > Credentials** and create:

| Credential | Type | Notes |
|-----------|------|-------|
| Anthropic API | Header Auth | Your Claude API key |
| OpenAI API | Header Auth | For embeddings |
| HubSpot | OAuth2 or API Key | CRM access |
| Gmail | OAuth2 | Email sending |
| Supabase | Header Auth | `SUPABASE_SERVICE_ROLE_KEY` |
| Slack | OAuth2 | Team notifications |

## Step 4: Import Workflows

### Option A: Manual Import (Recommended)

1. In n8n, click **Add Workflow** > **Import from File**
2. Import each file from `workflows/` in order:
   - `01-lead-intelligence.json`
   - `02-qualification-scoring.json`
   - `03-outreach-orchestrator.json`
   - `04-onboarding-executor.json`
   - `05-support-guardian.json`
   - `06-analytics-reporter.json`
   - `00-supervisor.json` (LAST — it references the others)

### Option B: API Import

```bash
N8N_URL="http://localhost:5678"
API_KEY="your-n8n-api-key"  # Settings > API > Create Key

for f in workflows/0{1,2,3,4,5,6}*.json workflows/00*.json; do
  curl -X POST "$N8N_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$f"
done
```

## Step 5: Update Sub-Workflow IDs

After import, each workflow gets a new ID. You need to update the supervisor:

1. Open each imported sub-workflow and note its ID (visible in the URL)
2. Open `00 — Supervisor` workflow
3. Find each **Execute Workflow** node
4. Update the `workflowId` to match the actual imported IDs

| Node | Points To |
|------|-----------|
| Execute Lead Intelligence | 01 workflow ID |
| Execute Qualification | 02 workflow ID |
| Execute Outreach | 03 workflow ID |
| Execute Onboarding | 04 workflow ID |
| Execute Support | 05 workflow ID |
| Execute Analytics | 06 workflow ID |

## Step 6: Update Credentials

In each workflow, update credential references:
- Replace `{{HUBSPOT_CRED}}` with your HubSpot credential name
- Replace `{{SUPABASE_CRED}}` with your Supabase credential name
- Replace `{{ANTHROPIC_CRED}}` with your Anthropic credential name
- And so on for Gmail, Slack, etc.

## Step 7: Activate Workflows

Activate in this order:
1. Sub-workflows first (01 through 06)
2. Supervisor (00) **last**

## Step 8: Test

Send a test webhook:

```bash
curl -X POST http://localhost:5678/webhook/swarm-lead-intake \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Lead",
    "email": "test@example.com",
    "company": "Test GmbH",
    "team_size": 5,
    "message": "Interested in your product"
  }'
```

Check:
- Supervisor receives and routes correctly
- Lead appears in HubSpot
- Slack notification sent (if configured)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Webhook returns 404 | Ensure supervisor workflow is active |
| AI Agent timeout | Check Anthropic API key and rate limits |
| Sub-workflow not found | Verify workflow IDs in Execute Workflow nodes |
| Database connection error | Check Supabase credentials and `init-supabase.sql` was run |
| Redis connection error | Verify Redis container is running: `docker compose ps` |
