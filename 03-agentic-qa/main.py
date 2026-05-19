#!/usr/bin/env python3
"""CLI for running the agentic QA workflow."""

import sys
import asyncio
from agent.graph import initialize_state, run_agent

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <github-repo-url> [model-name]")
        print("Example: python main.py https://github.com/user/repo ollama/qwen2.5-coder")
        sys.exit(1)

    repo_url = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Starting QA agent for: {repo_url}")
    if model:
        print(f"Using model: {model}")
    print("-" * 60)

    # Initialize and run agent
    state = initialize_state(repo_url, model=model)
    final_state = run_agent(state)

    print("\nAgent completed.")
    print("-" * 60)
    print(f"Repository analyzed: {final_state['repo_path']}")
    print(f"Functions found: {len(final_state['functions'])}")
    print(f"Tests written: {final_state['test_file']}")
    print(f"PR created: {final_state['pr_created']}")

if __name__ == "__main__":
    main()
