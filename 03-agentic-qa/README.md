# Agentic QA Workflow

Autonomous AI agent that improves code quality by analyzing repositories and writing tests.

## What This Does

Imagine an AI engineer who can:

1. Clone any GitHub repository
2. Read and understand Python code
3. Identify which functions lack tests
4. Write comprehensive tests automatically
5. Open a pull request with those tests

This agent does exactly that. It demonstrates **agentic workflows** — where an AI makes decisions, uses tools, evaluates results, and iterates toward a goal.

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
- "Is the PR creation working? Try a different branch if needed."

## Overview

This agent orchestrates a complete code quality workflow using Claude (Haiku 4.5) and the Anthropic tool use API:

1. **Clone** GitHub repository
2. **Analyze** Python files and function definitions
3. **Identify** untested functions
4. **Generate** comprehensive tests
5. **Create** pull request with test additions
6. **Iterate** based on results

## Setup

### 1. Install dependencies

```bash
cd 03-agentic-qa
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Authenticate GitHub CLI (for PR creation)

```bash
gh auth login
```

## Usage

```bash
.venv/bin/python main.py https://github.com/owner/repo
```

The agent will:

- Clone the repository to a temp directory
- Scan for Python files
- Extract function definitions
- Write pytest tests for untested functions
- Create a pull request with the new tests

## How It Works

### The Agentic Loop

```
START
  ↓
[1] Claude receives the goal:
    "Improve test coverage for this repo"
  ↓
[2] Claude decides: "I need to clone the repo first"
    → Calls tool: clone_repo
  ↓
[3] Tool result fed back to Claude:
    "Cloned to /tmp/agentic_qa_abc123"
  ↓
[4] Claude decides: "Now I'll find Python files"
    → Calls tool: list_python_files
  ↓
[5] Tool result: ["src/math.py", "src/utils.py", ...]
  ↓
[6] Claude decides: "I'll analyze each file"
    → Calls tool: analyze_functions (per file)
  ↓
[7] Claude evaluates: "Found 8 untested functions"
  ↓
[8] Claude decides: "I'll write tests for each"
    → Calls tool: write_test (multiple times)
  ↓
[9] Claude decides: "Time to create a PR"
    → Calls tool: create_pull_request
  ↓
[10] PR link returned
  ↓
END ✅
```

**Key insight:** At each step, Claude evaluates the tool result and decides the next action. This is what makes it an "agent" rather than a fixed script.

### Tools Available

| Tool                    | Purpose               | What It Does                                    |
| ----------------------- | --------------------- | ----------------------------------------------- |
| **clone_repo**          | Get the code          | Clones a GitHub repository to a temp directory  |
| **list_python_files**   | Find source files     | Lists all `.py` files recursively (up to 20)    |
| **analyze_functions**   | Extract code structure| Parses Python files to find function definitions|
| **write_test**          | Generate tests        | Writes pytest-compatible test code to disk      |
| **create_pull_request** | Submit changes        | Commits tests and opens a GitHub PR             |

### Architecture

```
main.py
    ↓
agent/graph.py — tool definitions + agentic loop
    ↓
Claude Haiku 4.5 with tool use (Anthropic API)
    ↓
External: git clone, file I/O, gh pr create
```

## Requirements

- Python 3.12+
- Anthropic API key (`ANTHROPIC_API_KEY`)
- GitHub CLI (`gh auth login`) — only needed for PR creation
- `git` installed

## Testing

```bash
# Run all tests (no API key or network needed — all mocked)
cd 03-agentic-qa
.venv/bin/pytest tests/ -v
```

Tests cover all 5 tool functions and the agent loop, with subprocess, filesystem, and API calls mocked.

## Example Output

```
$ .venv/bin/python main.py https://github.com/example/mathlib

Starting QA agent for: https://github.com/example/mathlib
------------------------------------------------------------
[Tool: clone_repo]
[Tool: list_python_files]
[Tool: analyze_functions]
[Tool: analyze_functions]
[Tool: write_test]
[Tool: write_test]
[Tool: write_test]
[Tool: create_pull_request]

Agent completed.
------------------------------------------------------------
Repository analyzed: /tmp/agentic_qa_xyz
Functions found: 12
Tests written: /tmp/agentic_qa_xyz/tests/test_math.py
PR created: True
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY=sk-ant-...
echo $ANTHROPIC_API_KEY   # verify
```

### "gh: command not found"

```bash
# macOS
brew install gh
gh auth login
```

### "Error cloning repo"

```bash
# Verify URL format
.venv/bin/python main.py https://github.com/owner/repo

# Check GitHub CLI auth
gh auth status
```

### "Agent stops mid-execution"

- Check `ANTHROPIC_API_KEY` is valid and has quota
- Try a smaller repository (fewer Python files)
- Review stderr output for the full error

### "PR creation fails"

```bash
# Ensure authenticated
gh auth status

# Configure git identity if missing
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## Limitations

**Works well for:**
- Simple utility functions (validation, formatting, math)
- Pure Python with no complex external dependencies
- Small-to-medium repositories (~50 functions)

**Harder cases:**
- Functions with complex external dependencies (database, network)
- Large repositories (token limits, 20-file cap)
- Monorepos with mixed languages

## Licence

MIT
