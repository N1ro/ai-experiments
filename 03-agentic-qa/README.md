# Agentic QA Workflow

Multi-step agent that autonomously analyzes GitHub repositories, identifies untested functions, writes tests, and creates pull requests.

## Overview

This agent uses Claude (Opus 4.7) with LangGraph to orchestrate a complete testing workflow:

1. Clone GitHub repository
2. Scan for Python files
3. Extract function definitions
4. Identify untested functions
5. Generate comprehensive tests
6. Create a PR with test additions

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

### Agent Loop

```
1. Initial Request
    ↓
2. Claude analyzes repo structure
    ↓
3. Uses tools to:
    - Clone repo
    - List Python files
    - Extract functions
    - Write tests
    - Create PR
    ↓
4. Tool results fed back to Claude
    ↓
5. Repeat until complete (max 10 iterations)
```

### Tools Available

- **clone_repo** — Clone GitHub repo
- **list_python_files** — Find all Python files
- **analyze_functions** — Extract function definitions
- **write_test** — Generate and write test code
- **create_pull_request** — Create PR with changes

## Requirements

- Python 3.12+
- Anthropic API key
- GitHub CLI (`gh`)
- Git

## Testing

```bash
pytest tests/
```

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

```
Starting QA agent for: https://github.com/example/project
------------------------------------------------------------

[Agent analyzing repository...]
[Cloning repository...]
[Scanning for Python files...]
[Identifying untested functions...]
[Writing tests for 5 functions...]
[Creating pull request...]

Agent completed.
------------------------------------------------------------
Repository analyzed: /tmp/repo
Functions found: 24
Tests written: 5
PR created: True
```

## Limitations

- Works best with small-to-medium repositories
- Test quality depends on Claude's analysis
- Requires GitHub CLI for PR creation
- No dependency analysis (doesn't handle complex imports)

## Future Enhancements

- Support for other languages (TypeScript, Go, etc.)
- Parallel function analysis
- Integration test generation
- Custom test templates
- Coverage metrics

## Licence

MIT
