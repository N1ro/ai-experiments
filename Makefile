.PHONY: help setup dev stop clean install test

help:
	@echo "AI Experiments — Local Development Setup"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          Install all dependencies"
	@echo "  make dev            Start RAG API + MCP server (requires Ollama running)"
	@echo "  make stop           Stop all services"
	@echo "  make clean          Remove virtual environments and caches"
	@echo "  make test           Run all tests"
	@echo ""
	@echo "Quick start:"
	@echo "  1. brew services start ollama  # Start Ollama (if not running)"
	@echo "  2. make setup                  # One-time setup"
	@echo "  3. make dev                    # Start both services"

setup:
	@echo "Installing dependencies..."
	cd 01-local-rag-pipeline && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd 02-mcp-server && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd 03-agentic-qa && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "✓ Setup complete. Run 'make dev' to start services."

dev:
	@echo "Starting services..."
	@echo "  1. RAG API (http://localhost:8000)"
	@echo "  2. MCP Server (configured in Claude Desktop)"
	@echo ""
	@echo "To stop services, press Ctrl+C or run 'make stop' in another terminal"
	@echo ""
	@trap 'make stop' EXIT; \
	cd 01-local-rag-pipeline && .venv/bin/uvicorn app.main:app --reload --port 8000 &
	RAG_PID=$$!; \
	sleep 3; \
	cd 02-mcp-server && .venv/bin/python src/rag_mcp_server.py &
	MCP_PID=$$!; \
	wait

stop:
	@echo "Stopping services..."
	pkill -f "uvicorn app.main:app" || true
	pkill -f "python.*rag_mcp_server.py" || true
	@echo "✓ Services stopped"

test:
	@echo "Running tests for all projects..."
	cd 01-local-rag-pipeline && .venv/bin/pytest tests/ -v || true
	cd 02-mcp-server && .venv/bin/pytest tests/ -v || true
	cd 03-agentic-qa && .venv/bin/pytest tests/ -v || true

clean:
	@echo "Cleaning up..."
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"
