#!/usr/bin/env bash
# Seed the RAG knowledge base with embedded documents
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing Python dependencies..."
pip3 install --quiet openai supabase tiktoken

echo "Running document embedder..."
python3 "$PROJECT_DIR/rag/embed-docs.py"
