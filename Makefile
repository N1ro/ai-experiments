.PHONY: help setup dev stop clean test ingest-samples delete-all reset setup-03 deploy-agents

help:
	@echo "AI Experiments — Local Development Setup"
	@echo ""
	@echo "Usage:"
	@echo "  make setup           Install dependencies for projects 01-02 (local/offline)"
	@echo "  make dev             Start RAG API (auto-ingests samples if KB is empty)"
	@echo "  make stop            Stop all services"
	@echo "  make reset           Wipe all docs and reload sample documents"
	@echo "  make ingest-samples  Ingest sample documents into the knowledge base"
	@echo "  make delete-all      Wipe all documents from the knowledge base"
	@echo "  make test            Run tests for all projects"
	@echo "  make setup-03        Install dependencies for project 03 (needs ANTHROPIC_API_KEY)"
	@echo "  make deploy-agents   Install QA agents globally (~/.claude/agents/)"
	@echo "  make clean           Remove virtual environments and caches"
	@echo ""
	@echo "Quick start:"
	@echo "  1. brew services start ollama  # Start Ollama (if not running)"
	@echo "  2. make setup                  # One-time dependency install"
	@echo "  3. make dev                    # Start RAG API + auto-ingest samples"
	@echo ""
	@echo "After a test session with added docs:"
	@echo "  make reset                     # Wipe and reload just the sample docs"
	@echo ""
	@echo "On a new machine (e.g. tech test):"
	@echo "  1. git clone git@github.com:N1ro/ai-experiments.git"
	@echo "  2. make deploy-agents          # Install Claude Code agents globally"

setup:
	@echo "Installing dependencies for Project 01 (RAG) and Project 02 (MCP Server)..."
	cd 01-local-rag-pipeline && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd 02-mcp-server && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "✓ Setup complete. Run 'make dev' to start the RAG API."

setup-03:
	@echo "Installing dependencies for Project 03 (Agentic QA)..."
	cd 03-agentic-qa && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "✓ Project 03 setup complete."
	@echo "  Set ANTHROPIC_API_KEY and run: 03-agentic-qa/.venv/bin/python main.py <github-url>"

dev:
	@echo "Starting RAG API (Project 01)..."
	@echo "  RAG API: http://localhost:8000"
	@echo ""
	@echo "Note: The MCP server (Project 02) is started automatically by Claude Desktop."
	@echo ""
	@echo "To stop, press Ctrl+C or run 'make stop' in another terminal"
	cd 01-local-rag-pipeline && .venv/bin/uvicorn app.main:app --reload --port 8000 &
	@sleep 3
	@DOC_COUNT=$$(curl -s http://localhost:8000/documents | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null); \
	if [ "$$DOC_COUNT" = "0" ]; then \
		echo ""; \
		echo "Knowledge base is empty — ingesting sample documents..."; \
		$(MAKE) ingest-samples; \
	else \
		echo ""; \
		echo "Knowledge base already has $$DOC_COUNT document(s) — skipping sample ingest."; \
		echo "Run 'make reset' to wipe and reload sample docs."; \
	fi
	@wait

stop:
	@echo "Stopping RAG API..."
	pkill -f "uvicorn app.main:app" || true
	@echo "✓ Stopped"

reset:
	@echo "Resetting knowledge base to sample documents only..."
	@if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✗ RAG API is not running. Start it first with: make dev"; \
		exit 1; \
	fi
	@$(MAKE) delete-all
	@$(MAKE) ingest-samples
	@echo "✓ Knowledge base reset to sample documents."

ingest-samples:
	@if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✗ RAG API is not running. Start it first with: make dev"; \
		exit 1; \
	fi
	@echo "Ingesting sample documents..."
	@for f in sample-docs/*.txt; do \
		curl -s -X POST http://localhost:8000/ingest -F "files=@$$f" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓', d['documents'][0]['filename'])"; \
	done
	@echo "✓ Done."

delete-all:
	@if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✗ RAG API is not running. Start it first with: make dev"; \
		exit 1; \
	fi
	@curl -s -X DELETE http://localhost:8000/documents > /dev/null
	@echo "✓ All documents deleted."

test:
	@echo "Running tests for Project 01 (RAG pipeline)..."
	cd 01-local-rag-pipeline && .venv/bin/pytest tests/ -v
	@echo ""
	@echo "Running tests for Project 02 (MCP server)..."
	cd 02-mcp-server && .venv/bin/pytest tests/ -v
	@echo ""
	@echo "Running tests for Project 03 (Agentic QA)..."
	cd 03-agentic-qa && .venv/bin/pytest tests/ -v

deploy-agents:
	@echo "Installing QA agents to ~/.claude/agents/ ..."
	@bash qa-tooling/deploy.sh
	@echo ""
	@echo "Installed agents:"
	@ls ~/.claude/agents/*.md 2>/dev/null | xargs -I{} basename {} || echo "  (none found)"

clean:
	@echo "Cleaning up virtual environments and caches..."
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"
