#!/usr/bin/env bash
# ============================================================
# Sales Swarm — Deployment Script
# One-command deployment from zero to running
# Usage: bash scripts/deploy.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_DIR/infrastructure"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# --- Pre-flight Checks ---
log "Running pre-flight checks..."

command -v docker >/dev/null 2>&1 || error "Docker is not installed"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose is not installed"
command -v python3 >/dev/null 2>&1 || error "Python 3 is not installed"
command -v node >/dev/null 2>&1 || error "Node.js is not installed"

if [ ! -f "$INFRA_DIR/.env" ]; then
  warn ".env file not found, copying from .env.example"
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  warn "Please edit infrastructure/.env with your actual API keys!"
  warn "Press Enter to continue or Ctrl+C to abort..."
  read -r
fi

# --- Step 1: Start Docker Services ---
log "Step 1/6: Starting Docker services..."
cd "$INFRA_DIR"
docker compose up -d

log "Waiting for services to be healthy..."
sleep 10

# Check services
if docker compose ps | grep -q "unhealthy\|Exit"; then
  error "Some services failed to start. Run 'docker compose ps' for details."
fi
log "All services running."

# --- Step 2: Verify Database ---
log "Step 2/6: Verifying database schema..."

# Source .env for DB credentials
set -a
source "$INFRA_DIR/.env"
set +a

TABLES=$(docker exec swarm-postgres psql \
  -U "${SUPABASE_DB_USER:-postgres}" \
  -d "${SUPABASE_DB_NAME:-swarm}" \
  -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")

TABLES=$(echo "$TABLES" | tr -d ' ')
if [ "$TABLES" -ge 3 ]; then
  log "Database initialized with $TABLES tables."
else
  warn "Database tables not found. Running init script manually..."
  docker exec -i swarm-postgres psql \
    -U "${SUPABASE_DB_USER:-postgres}" \
    -d "${SUPABASE_DB_NAME:-swarm}" \
    < "$INFRA_DIR/init-supabase.sql"
  log "Database initialized."
fi

# --- Step 3: Seed RAG Knowledge Base ---
log "Step 3/6: Seeding RAG knowledge base..."

cd "$PROJECT_DIR"
if pip3 install --quiet openai supabase tiktoken 2>/dev/null; then
  python3 rag/embed-docs.py && log "RAG knowledge base seeded." || warn "RAG seeding failed. Run manually: python3 rag/embed-docs.py"
else
  warn "Could not install Python dependencies. Run manually:"
  warn "  pip install openai supabase tiktoken && python3 rag/embed-docs.py"
fi

# --- Step 4: Import Workflows ---
log "Step 4/6: Importing workflows to n8n..."

N8N_URL="${WEBHOOK_URL:-http://localhost:5678}"

# Check if n8n API is available
if curl -s "$N8N_URL/healthz" >/dev/null 2>&1; then
  warn "n8n is running. Workflow import requires API key."
  warn "To import manually:"
  warn "  1. Open $N8N_URL in your browser"
  warn "  2. Go to Settings > API > Create API Key"
  warn "  3. Run:"
  warn "     for f in workflows/*.json; do"
  warn "       curl -X POST $N8N_URL/api/v1/workflows \\"
  warn "         -H 'X-N8N-API-KEY: your-key' \\"
  warn "         -H 'Content-Type: application/json' \\"
  warn "         -d @\"\$f\""
  warn "     done"
else
  warn "n8n API not yet available. Import workflows after setup."
fi

# --- Step 5: Run Tests ---
log "Step 5/6: Running test suite..."

echo ""
node tests/test-supervisor-routing.js
echo ""

if python3 -c "import json, sys; sys.path.insert(0,'scoring')" 2>/dev/null; then
  python3 tests/test-scoring-accuracy.py || warn "Scoring tests had failures."
else
  warn "Skipping scoring tests (missing dependencies)."
fi

# --- Step 6: Status Summary ---
log "Step 6/6: Deployment summary"

echo ""
echo "============================================================"
echo "  Autonomous Sales Swarm — Deployment Complete"
echo "============================================================"
echo ""
echo "  Services:"
docker compose -f "$INFRA_DIR/docker-compose.yml" ps --format "    {{.Name}}: {{.Status}}" 2>/dev/null || docker compose -f "$INFRA_DIR/docker-compose.yml" ps
echo ""
echo "  URLs:"
echo "    n8n:      $N8N_URL"
echo "    Postgres: localhost:${SUPABASE_DB_PORT:-54322}"
echo "    Redis:    localhost:${REDIS_PORT:-6379}"
echo ""
echo "  Next Steps:"
echo "    1. Open $N8N_URL and create your account"
echo "    2. Set up credentials (Anthropic, HubSpot, Gmail, Slack)"
echo "    3. Import workflows from workflows/*.json"
echo "    4. Update sub-workflow IDs in Execute Workflow nodes"
echo "    5. Activate workflows (supervisor LAST)"
echo "    6. Send a test lead to the webhook"
echo ""
echo "  See docs/n8n-setup.md for detailed instructions."
echo "============================================================"
