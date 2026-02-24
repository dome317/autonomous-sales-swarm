# Contributing

Thanks for your interest in contributing to the Autonomous Sales Swarm!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/autonomous-sales-swarm.git`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Make your changes
5. Run tests: `node tests/test-supervisor-routing.js && python tests/test-scoring-accuracy.py`
6. Commit with conventional format: `feat(agent-name): description`
7. Push and open a Pull Request

## Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, refactor, docs, test, chore, perf, ci
Scope: agent name or component (supervisor, outreach, scoring, rag, infra)
```

Examples:
```
feat(outreach): add WhatsApp template support
fix(scoring): correct weight normalization
docs: update RAG setup guide
infra: add Redis health check
```

## Adding a New Agent

1. Create the workflow JSON in `workflows/`
2. Add the system prompt in `config/prompts/`
3. Register the route in the supervisor's Switch node
4. Add test cases to `tests/test-supervisor-routing.js`
5. Document in `docs/agents.md`

## Modifying the Scoring Model

1. Edit weights in `scoring/scoring-config.json`
2. Run `python tests/test-scoring-accuracy.py` to validate
3. Check that boundary tests still pass

## RAG Knowledge Base

1. Add `.md` files to `rag/knowledge-base/`
2. Run `bash scripts/seed-rag.sh` to re-embed
3. Test retrieval quality manually

## Code Standards

- **JavaScript** (n8n Code Nodes): ES2022, no external imports
- **Python**: 3.11+, type hints, docstrings
- **Prompts**: Markdown with XML tags for structured sections
- **JSON**: camelCase keys

## Testing

Before submitting a PR:
- `node tests/test-supervisor-routing.js` — all routing tests pass
- `python tests/test-scoring-accuracy.py` — all scoring tests pass
- `jq . workflows/*.json` — all workflow JSON is valid

## Questions?

Open an issue for bugs, feature requests, or questions.
