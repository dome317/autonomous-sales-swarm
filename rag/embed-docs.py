"""
Sales Swarm — Document Embedder
Reads .md files from knowledge-base/, chunks them, embeds via OpenAI,
and inserts into Supabase documents table.

Usage:
    pip install openai supabase tiktoken
    python embed-docs.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import tiktoken
from openai import OpenAI
from supabase import create_client, Client


# --- Config ---
CHUNK_SIZE = 500       # tokens per chunk
CHUNK_OVERLAP = 100    # token overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge-base"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://localhost:54322")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY",
    os.environ.get("SUPABASE_ANON_KEY", "")
)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY must be set")
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


def read_markdown_files(base_dir: Path) -> list[dict[str, Any]]:
    """Read all .md files recursively from the knowledge base directory."""
    docs: list[dict[str, Any]] = []
    for md_file in sorted(base_dir.rglob("*.md")):
        relative_path = md_file.relative_to(base_dir)
        content = md_file.read_text(encoding="utf-8")
        docs.append({
            "path": str(relative_path),
            "filename": md_file.name,
            "content": content,
        })
        print(f"  Read: {relative_path} ({len(content)} chars)")
    return docs


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by token count."""
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = enc.decode(chunk_tokens)
        chunks.append(chunk_text_str)
        start += chunk_size - overlap

    return chunks


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenAI embeddings API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def insert_documents(
    supabase: Client,
    chunks: list[dict[str, Any]],
) -> int:
    """Insert document chunks with embeddings into Supabase."""
    inserted = 0
    batch_size = 50

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        rows = [
            {
                "content": chunk["content"],
                "metadata": chunk["metadata"],
                "embedding": chunk["embedding"],
            }
            for chunk in batch
        ]
        supabase.table("documents").insert(rows).execute()
        inserted += len(rows)
        print(f"  Inserted batch: {inserted}/{len(chunks)}")

    return inserted


def main() -> None:
    print("=" * 60)
    print("Sales Swarm — Document Embedder")
    print("=" * 60)

    # 1. Read all markdown files
    print("\n[1/4] Reading knowledge base files...")
    docs = read_markdown_files(KNOWLEDGE_BASE_DIR)
    if not docs:
        print("ERROR: No .md files found in", KNOWLEDGE_BASE_DIR)
        sys.exit(1)
    print(f"  Found {len(docs)} documents")

    # 2. Chunk documents
    print("\n[2/4] Chunking documents...")
    all_chunks: list[dict[str, Any]] = []
    for doc in docs:
        chunks = chunk_text(doc["content"])
        for idx, chunk_content in enumerate(chunks):
            all_chunks.append({
                "content": chunk_content,
                "metadata": {
                    "source": doc["path"],
                    "filename": doc["filename"],
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
                "embedding": None,
            })
        print(f"  {doc['path']}: {len(chunks)} chunks")
    print(f"  Total chunks: {len(all_chunks)}")

    # 3. Generate embeddings
    print("\n[3/4] Generating embeddings...")
    openai_client = get_openai_client()
    texts = [c["content"] for c in all_chunks]

    # Batch in groups of 100 (API limit ~2048 per batch, but 100 is safe)
    batch_size = 100
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = embed_texts(openai_client, batch)
        all_embeddings.extend(embeddings)
        print(f"  Embedded: {len(all_embeddings)}/{len(texts)}")

    for idx, emb in enumerate(all_embeddings):
        all_chunks[idx]["embedding"] = emb

    # 4. Insert into Supabase
    print("\n[4/4] Inserting into Supabase...")
    supabase = get_supabase_client()

    # Clear existing documents (optional — for re-embedding)
    print("  Clearing existing documents...")
    supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    total_inserted = insert_documents(supabase, all_chunks)

    print(f"\nDone! Inserted {total_inserted} chunks into Supabase.")
    print("=" * 60)


if __name__ == "__main__":
    main()
