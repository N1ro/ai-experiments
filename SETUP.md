# Local AI Setup Guide — M3 Max (64GB)

This guide sets up your local AI environment from scratch. Designed to be run via Gemini CLI or manually terminal by terminal.

---

## Prerequisites

Check these exist first:

```bash
# Check Homebrew
brew --version

# Check Python
python3 --version    # need 3.11+

# Check Docker
docker --version
```

If Homebrew is missing:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## Step 1 — Install Ollama

Ollama runs local AI models. Think of it like Docker, but for AI models.

```bash
brew install ollama
```

Verify:
```bash
ollama --version
```

---

## Step 2 — Pull the Models

This is a one-time download. Total ~52GB. Use a good WiFi connection.

```bash
# Qwen3 14B — latest Qwen (April 2025), excellent for code generation
# Hybrid thinking/non-thinking mode, Apache 2.0 licence
ollama pull qwen3:14b

# Llama 3.3 70B — Meta, best dense reasoning model locally
# Runs fully offline, no telemetry, open weights
ollama pull llama3.3:70b
```

Check what you have:
```bash
ollama list
```

---

## Step 3 — Run Both Models Simultaneously

By default Ollama loads one model at a time. To keep both in memory on your 64GB machine:

```bash
# Add to your shell profile (~/.zshrc)
echo 'export OLLAMA_MAX_LOADED_MODELS=2' >> ~/.zshrc
source ~/.zshrc

# Start Ollama server
ollama serve
```

Leave this terminal open. Ollama runs on `http://localhost:11434`.

---

## Step 4 — Test the Models

Open a new terminal:

```bash
# Quick test — Qwen3 (coding)
ollama run qwen3:14b "Write a Python function that chunks text into overlapping windows"

# Quick test — Llama (reasoning)
ollama run llama3.3:70b "Explain RAG architecture in 3 sentences"

# Exit the interactive prompt
/bye
```

---

## Step 5 — OpenAI-Compatible API

Ollama exposes an OpenAI-compatible REST API. This means any code written for OpenAI or Azure OpenAI works with your local models by changing one URL.

```bash
# Test the API directly
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:14b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

In Python (same interface as Azure OpenAI):
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # placeholder, not validated locally
)

response = client.chat.completions.create(
    model="qwen3:14b",
    messages=[{"role": "user", "content": "Write a FastAPI health endpoint"}]
)
print(response.choices[0].message.content)
```

---

## Step 6 — Install PostgreSQL + pgvector

pgvector adds vector similarity search to PostgreSQL. Used in Project 1 (RAG pipeline).

```bash
# Install PostgreSQL 16
brew install postgresql@16

# Start PostgreSQL
brew services start postgresql@16

# Install pgvector extension
brew install pgvector

# Add PostgreSQL to PATH (add to ~/.zshrc too)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Create the project database:
```bash
createdb ai_experiments
psql ai_experiments -c "CREATE EXTENSION vector;"
psql ai_experiments -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
# Should print: 0.8.x
```

---

## Step 7 — Python Environment

```bash
# Install pyenv for managing Python versions
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python 3.12
pyenv install 3.12.4
pyenv global 3.12.4
python3 --version  # should print 3.12.4
```

Core AI packages:
```bash
pip install \
  fastapi uvicorn \
  sqlalchemy psycopg2-binary pgvector \
  langchain langchain-community langchain-ollama \
  langgraph \
  anthropic \
  mcp \
  pytest pytest-asyncio httpx \
  python-dotenv
```

---

## Step 8 — Docker (for project containers)

```bash
brew install --cask docker
```

Open Docker Desktop app once to complete installation, then:

```bash
docker --version
docker compose version
```

The projects use Docker Compose to spin up PostgreSQL + pgvector + the app together. One command: `docker compose up`.

---

## Step 9 — Verify Everything Works

Run this checklist:

```bash
# Ollama running
curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep name

# PostgreSQL running
psql ai_experiments -c "SELECT version();"

# pgvector loaded
psql ai_experiments -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"

# Python packages
python3 -c "import langchain, anthropic, mcp, pgvector; print('All packages OK')"

# Docker
docker run --rm hello-world
```

All green = ready to build.

---

## Step 10 — Connect Cursor / VS Code to Local Models

In Cursor settings, add a custom model provider:
```
Provider: OpenAI-compatible
Base URL: http://localhost:11434/v1
API Key:  ollama
Model:    qwen3:14b
```

Use Qwen3:14b for autocomplete and boilerplate. Switch to Claude for architecture and review.

---

## Model Reference

| Model | Pull command | Use for | RAM |
|---|---|---|---|
| Qwen3 14B | `ollama pull qwen3:14b` | Code generation, tests, boilerplate | ~9GB |
| Llama 3.3 70B | `ollama pull llama3.3:70b` | Reasoning, architecture, explanation | ~43GB |
| nomic-embed-text | `ollama pull nomic-embed-text` | Generating embeddings for RAG | ~300MB |

Pull `nomic-embed-text` before starting Project 1:
```bash
ollama pull nomic-embed-text
```

---

## Troubleshooting

**Ollama not starting:**
```bash
pkill ollama
ollama serve
```

**PostgreSQL not found after install:**
```bash
source ~/.zshrc
which psql
```

**pgvector install fails:**
```bash
# Try building from source
pip install pgvector --no-binary pgvector
```

**Models loading slowly:**
Normal on first load — model is being mapped into memory. Subsequent calls are fast.

**Out of memory running both models:**
Use `qwen3:14b` alone (9GB). Only pull in `llama3.3:70b` when you need deep reasoning.
