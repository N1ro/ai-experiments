# Local RAG Pipeline

FastAPI-based Retrieval-Augmented Generation service using PostgreSQL + pgvector and Ollama.

## Features

- Document ingestion and chunking
- Vector embeddings via Ollama (`nomic-embed-text`)
- LLM-powered answer generation (Qwen3:14b)
- PostgreSQL + pgvector for semantic search
- REST API for all operations

## Setup

See `/SETUP.md` in the root of this repo for local AI environment setup (Ollama, PostgreSQL, Python).

## Quick Start (Local)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start Ollama (separate terminal)
brew services start ollama

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## Quick Start (Docker)

```bash
docker compose up
```

## Endpoints

### POST `/ingest`
Upload documents for indexing.

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@document.txt"
```

### POST `/query`
Query the RAG system.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 3}'
```

### GET `/documents`
List all indexed documents.

```bash
curl "http://localhost:8000/documents"
```

### DELETE `/documents/{doc_id}`
Delete a document.

```bash
curl -X DELETE "http://localhost:8000/documents/abc-123"
```

## Testing

```bash
pytest tests/
```

## Tech Stack

- FastAPI
- PostgreSQL 16 + pgvector
- Ollama (Qwen3:14b, nomic-embed-text)
- LangChain
- SQLAlchemy

## Licence

MIT
