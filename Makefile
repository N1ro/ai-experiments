.PHONY: help setup dev stop clean test ingest-samples delete-all

help:
	@echo "AI Experiments — Local Development Setup"
	@echo ""
	@echo "Usage:"
	@echo "  make setup           Install dependencies for projects 01-02"
	@echo "  make dev             Start RAG API (requires Ollama running)"
	@echo "  make stop            Stop all services"
	@echo "  make ingest-samples  Ingest sample documents into the knowledge base"
	@echo "  make delete-all      Wipe all documents from the knowledge base"
	@echo "  make test            Run tests for project 01 (RAG pipeline)"
	@echo "  make clean           Remove virtual environments and caches"
	@echo ""
	@echo "Quick start:"
	@echo "  1. brew services start ollama  # Start Ollama (if not running)"
	@echo "  2. make setup                  # One-time dependency install"
	@echo "  3. make dev                    # Start RAG API"
	@echo "  4. make ingest-samples         # Load sample documents"

setup:
	@echo "Installing dependencies for Project 01 (RAG) and Project 02 (MCP Server)..."
	cd 01-local-rag-pipeline && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd 02-mcp-server && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "✓ Setup complete. Run 'make dev' to start services."

dev:
	@echo "Starting RAG API (Project 01)..."
	@echo "  RAG API: http://localhost:8000"
	@echo ""
	@echo "Note: The MCP server (Project 02) is started automatically by Claude Desktop."
	@echo "      Configure it in Claude Desktop settings, then restart Claude Desktop."
	@echo ""
	@echo "To stop, press Ctrl+C or run 'make stop' in another terminal"
	cd 01-local-rag-pipeline && .venv/bin/uvicorn app.main:app --reload --port 8000

stop:
	@echo "Stopping RAG API..."
	pkill -f "uvicorn app.main:app" || true
	@echo "✓ Stopped"

ingest-samples:
	@echo "Ingesting sample documents into the knowledge base..."
	@if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✗ RAG API is not running. Start it first with: make dev"; \
		exit 1; \
	fi
	@for f in sample-docs/*.txt; do \
		echo "  Ingesting $$f..."; \
		curl -s -X POST http://localhost:8000/ingest -F "files=@$$f" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓', d['documents'][0]['filename'])"; \
	done
	@echo "✓ Sample documents ingested. Run 'make dev' and query via Claude Desktop."

delete-all:
	@echo "Deleting all documents from the knowledge base..."
	@if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✗ RAG API is not running. Start it first with: make dev"; \
		exit 1; \
	fi
	curl -s -X DELETE http://localhost:8000/documents
	@echo "✓ All documents deleted."

test:
	@echo "Running tests for Project 01 (RAG pipeline)..."
	cd 01-local-rag-pipeline && .venv/bin/pytest tests/ -v
	@echo ""
	@echo "Running tests for Project 02 (MCP server)..."
	cd 02-mcp-server && .venv/bin/pytest tests/ -v

clean:
	@echo "Cleaning up virtual environments and caches..."
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"
