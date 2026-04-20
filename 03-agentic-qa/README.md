# Agentic QA Workflow 🤖

Autonomous AI agent that improves code quality by analyzing repositories and writing tests.

## What This Does

Imagine an AI engineer who can:
1. Clone any GitHub repository
2. Read and understand Python code
3. Identify which functions lack tests
4. Write comprehensive tests automatically
5. Open a pull request with those tests

This agent does exactly that. It demonstrates **agentic workflows**—where an AI makes decisions, uses tools, evaluates results, and iterates toward a goal.

```
You:     "https://github.com/user/repo"
    ↓
Agent clones repo
    ↓
Agent reads Python files
    ↓
Agent analyzes functions
    ↓
Agent asks: "Which functions need tests?"
    ↓
Agent writes tests
    ↓
Agent creates PR
    ↓
Done ✅
```

## Understanding Agentic Workflows

Unlike a simple script (which follows fixed steps), an **agent**:
- Makes decisions based on observed state
- Uses tools to gather information
- Evaluates results and adapts
- Repeats until the goal is reached

Example decision points in this agent:
- "Did the repo clone successfully? If not, handle the error."
- "How many untested functions? Should I write tests for all?"
- "Did the tests run without syntax errors? If not, fix them."
- "Is the PR creation working? Try a different branch if needed."

## Overview

This agent orchestrates a complete code quality workflow using Claude (Opus 4.7) and LangGraph:

1. **Clone** GitHub repository
2. **Analyze** Python files and function definitions
3. **Identify** untested functions
4. **Generate** comprehensive tests
5. **Create** pull request with test additions
6. **Iterate** based on results

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Authenticate with GitHub (for PR creation)

```bash
gh auth login
```

### 3. Set ANTHROPIC_API_KEY

```bash
export ANTHROPIC_API_KEY=your_api_key
```

## Usage

```bash
python main.py https://github.com/user/repo
```

The agent will:
- Clone the repository locally
- Analyze the codebase
- Write comprehensive tests
- Commit changes and create a PR

## How It Works

### The Agentic Loop

```
START
  ↓
[1] Claude reads your goal:
    "Improve test coverage for this repo"
  ↓
[2] Claude decides: "I need to clone the repo first"
    → Calls tool: clone_repo
  ↓
[3] Tool result fed back to Claude:
    "Cloned to /tmp/repo_xyz"
  ↓
[4] Claude decides: "Now I'll find Python files"
    → Calls tool: list_python_files
  ↓
[5] Tool result: "Found 24 Python files"
  ↓
[6] Claude decides: "I'll analyze these for untested functions"
    → Calls tool: analyze_functions
  ↓
[7] Claude evaluates results:
    "Found 8 untested functions"
  ↓
[8] Claude decides: "I'll write tests for each"
    → Calls tool: write_test (multiple times)
  ↓
[9] Claude verifies: "All tests written and valid"
  ↓
[10] Claude decides: "Time to create a PR"
     → Calls tool: create_pull_request
  ↓
[11] Tool returns PR link
  ↓
END ✅
```

**Key insight:** At each step, Claude evaluates results and decides the next action. This is what makes it an "agent" rather than a simple script.

### Tools Available

| Tool | Purpose | What It Does |
|------|---------|-------------|
| **clone_repo** | Get the code | Clones GitHub repository locally |
| **list_python_files** | Find source files | Lists all `.py` files recursively |
| **analyze_functions** | Extract code structure | Parses Python AST to find function definitions |
| **write_test** | Generate tests | Uses Claude to write pytest-compatible test code |
| **create_pull_request** | Submit changes | Creates PR on GitHub with test additions |

## Why This Matters for Your Portfolio

This project demonstrates:

1. **Agentic Design** — Understanding how AI systems make decisions and iterate
2. **Tool Integration** — Building interfaces between AI and external systems (Git, GitHub API)
3. **Error Handling** — Real agents must handle tool failures gracefully
4. **LangGraph** — Industry-standard framework for agent orchestration
5. **Real-World Value** — Actually improves code quality (not just a toy example)

For interviews: This shows you understand autonomous AI systems, a core pattern in modern AI engineering. You're not just calling APIs; you're building systems that can reason and act.

## Requirements

- Python 3.12+
- Anthropic API key (set `ANTHROPIC_API_KEY`)
- GitHub CLI (`gh auth login`)
- Git

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_graph.py -v

# Run with coverage
pytest tests/ --cov=agent
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
**Problem:** Missing API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Verify it's set
echo $ANTHROPIC_API_KEY
```

### "gh: command not found"
**Problem:** GitHub CLI not installed
```bash
# macOS
brew install gh

# Linux
sudo apt install gh

# Then authenticate
gh auth login
```

### "Error: repository not found"
**Problem:** Invalid GitHub URL or no access
```bash
# Verify URL format
python main.py https://github.com/owner/repo

# Check GitHub CLI auth
gh auth status
```

### "Agent stops mid-execution"
**Problem:** LLM hit token limit or API error
- Check `ANTHROPIC_API_KEY` is valid
- Check network connectivity
- Try a smaller repository first
- Check logs for full error context

### "PR creation fails"
**Problem:** GitHub CLI permissions or git config
```bash
# Ensure you're authenticated
gh auth status

# Configure git locally
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Try manually creating a PR to test
gh pr create --title "test" --body "test" --draft
```

### "Agent loops forever"
**Problem:** Agent not converging to goal
- Max iterations set to 10 to prevent this
- Check logs to see what decision it's stuck on
- Try a simpler repository (fewer functions)

## Architecture

```
main.py
    ↓
agent/graph.py (LangGraph agent definition)
    ↓
Claude (Opus 4.7) with tool use
    ↓
Tool execution (git, file operations)
```

## Example Output

When you run the agent, you'll see something like:

```
$ python main.py https://github.com/example/mathlib

Starting agentic QA workflow for: https://github.com/example/mathlib
============================================================

[Agent is thinking...]
[Tool call: clone_repo → Cloning repository]
[Tool call: list_python_files → Found 12 Python files]
[Tool call: analyze_functions → Extracted 34 function definitions]

Agent analysis:
  ✓ Functions with tests: 26
  ✓ Functions without tests: 8
  → Planning to write tests for: add(), multiply(), divide(), normalize()

[Tool call: write_test → Generated tests for add()]
[Tool call: write_test → Generated tests for multiply()]
[Tool call: write_test → Generated tests for divide()]
[Tool call: write_test → Generated tests for normalize()]

[Verifying generated tests...]
✓ All tests valid (syntax checked)

[Tool call: create_pull_request → PR #42 created]

============================================================
Agent completed successfully! 🎉

Summary:
  Repository: /tmp/mathlib_xyz
  Functions analyzed: 34
  Functions without tests: 8
  Tests written: 4
  PR created: https://github.com/example/mathlib/pull/42

The maintainers will see a PR with your test additions!
```

## How It Fits Into Your Portfolio

This project completes the AI stack:

| Project | Purpose | Technology |
|---------|---------|-----------|
| Project 1: RAG | Personal search engine | Vector DB + Embeddings + LLM |
| Project 2: MCP Server | LLM integration | Protocol + API integration |
| **Project 3: Agentic QA** | **Autonomous workflows** | **Decision-making + Tool use** |

Together, they show:
- ✅ Local LLM usage (Ollama)
- ✅ Semantic search (embeddings + vectors)
- ✅ LLM integration (MCP protocol)
- ✅ Autonomous systems (agents)
- ✅ Real-world value (actually improves code)

## Limitations & Realistic Expectations

**What works well:**
- Simple utility functions (validation, formatting, parsing)
- Pure Python without complex dependencies
- Small-to-medium repositories (~50 functions)

**What's harder:**
- Complex business logic (requires deep understanding)
- Heavy dependency chains (import resolution tricky)
- Large repositories (token limits kick in)

**Why these limitations matter:**
- Shows you understand where AI excels (pattern matching) vs. struggles (complex reasoning)
- Real for interviews: "AI is great at test generation, but here are the edge cases"

## Future Enhancements

- **Parallelization** — Analyze multiple functions simultaneously
- **Test templates** — Let user customize generated test style
- **Coverage metrics** — Report on improved coverage %
- **Multi-language** — Support TypeScript, Go, etc.
- **Integration tests** — Not just unit tests
- **Smart retries** — When tests fail, fix them automatically

## Licence

MIT
