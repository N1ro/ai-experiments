# RAG MCP Server

Model Context Protocol (MCP) server that exposes the local RAG pipeline as tools for Claude.

## Overview

This MCP server wraps the RAG API (Project 1) and makes it available to Claude through the Model Context Protocol. You can now ask Claude questions and have it search your local knowledge base.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag-local": {
      "command": "python",
      "args": ["<path-to>/src/rag_mcp_server.py"]
    }
  }
}
```

Replace `<path-to>` with the full path to this directory.

### 3. Ensure RAG API is running

The RAG API (Project 1) must be running on `http://localhost:8000`:

```bash
cd ../01-local-rag-pipeline
uvicorn app.main:app --reload
```

### 4. Restart Claude Desktop

Restart Claude Desktop to load the new MCP server.

## Tools Exposed

### query_knowledge_base
Search your indexed documents with semantic similarity.

```
Query the knowledge base with a natural language question.
Returns relevant document chunks and an LLM-generated answer.
```

### ingest_document
Add new documents to your knowledge base.

```
Upload documents by URL or direct content.
Documents are chunked, embedded, and indexed.
```

### list_documents
View all indexed documents and their chunk counts.

### delete_document
Remove a document and its embeddings from the knowledge base.

## Usage Example

In Claude Desktop, you can now say:

- "Search my knowledge base for information about machine learning"
- "Add this document to my knowledge base: <URL or content>"
- "What documents do I have indexed?"
- "Delete document XYZ from my knowledge base"

Claude will use the appropriate tool and display the results.

## Testing

```bash
python -m pytest tests/
```

## Architecture

```
Claude Desktop
    ↓
MCP Protocol
    ↓
rag_mcp_server.py (this file)
    ↓
HTTP REST API
    ↓
Project 1: RAG API
    ↓
PostgreSQL + pgvector + Ollama
```

## Licence

MIT
