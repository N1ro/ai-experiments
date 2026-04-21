.PHONY: help setup dev stop clean test

help:
	@echo "AI Experiments — Local Development Setup"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          Install dependencies for projects 01-02"
	@echo "  make dev            Start RAG API + MCP server (requires Ollama running)"
	@echo "  make stop           Stop all services"
	@echo "  make test           Run tests for project 01 (RAG pipeline)"
	@echo "  make clean          Remove virtual environments and caches"
	@echo ""
	@echo "Quick start:"
	@echo "  1. brew services start ollama  # Start Ollama (if not running)"
	@echo "  2. make setup                  # One-time setup"
	@echo "  3. make dev                    # Start both services"

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

test:
	@echo "Running tests for Project 01 (RAG pipeline)..."
	cd 01-local-rag-pipeline && .venv/bin/pytest tests/ -v
	@echo ""
	@echo "Note: Project 02 tests require full integration; Project 03 is not yet complete."

clean:
	@echo "Cleaning up virtual environments and caches..."
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"
