# Agentic QA: The Auditor (Local-First)

Autonomous AI auditor that identifies "The Silent Gaps" in test coverage using Tree-sitter and writes tests locally using open-source models.

## What This Does

Unlike general AI coding assistants that wait for instructions, **The Auditor** is a proactive pipeline that:

1.  **Context-Aware Analysis:** Identifies local paths or clones remote GitHub repositories.
2.  **Structural Audit:** Uses **Tree-sitter AST analysis** to find "Silent Gaps" (functions defined in source but never called in tests).
3.  **Local PR Mode:** Uses `git diff` to focus specifically on uncommitted or newly changed code.
4.  **Local Intelligence:** Generates targeted tests using **local models** (via LiteLLM/Ollama) to ensure zero data exfiltration.
5.  **Automated Submissions:** Commits changes and opens pull requests (for remote repos) or updates local files directly.

## The Architecture: Tree-sitter vs. LLM

Most AI tools ask the LLM to "find gaps," which is prone to hallucinations. **The Auditor** uses deterministic static analysis first:

```
[Tree-sitter] -> "Function 'logout' is defined in auth.py but never called in tests/"
      ↓
[LiteLLM]     -> "I know for a fact this is missing. Write a pytest test for it."
```

This approach is faster, cheaper, and 100% accurate at identifying what needs to be tested.

## Setup

### 1. Install dependencies

```bash
cd 03-agentic-qa
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Configure your local model (Ollama)

Ensure Ollama is running, then create a `.env` file from the example:

```bash
cp .env.example .env
# Default is LITELLM_MODEL=ollama/qwen2.5-coder:32b
```

### 3. Requirements
- **Git** (for cloning and diffing)
- **GitHub CLI (`gh`)** (optional, only for remote PR creation)
- **Ollama** (for local-first model execution)

## Usage

### Audit a Local Project (e.g., vibe-align)
Run the auditor against your current working directory to find gaps in your latest changes:

```bash
.venv/bin/python main.py /Users/niro/projects/vibe-align
```

### Audit a Remote Repository
```bash
.venv/bin/python main.py https://github.com/owner/repo [model-name]
```

## How It Works

### The Auditor Loop
1.  **Initialize:** Detects if the target is local or remote.
2.  **Local PR Check:** If local, runs `get_local_diff` to understand the developer's recent focus.
3.  **Gap Analysis:** Runs the `TreeSitterAuditor` to map every function definition in `src/` and every call expression in `tests/`.
4.  **Targeted Generation:** LiteLLM routes the "Missing Functions" to your local model.
5.  **Verification:** Writes the generated tests directly to the codebase.

## Tools Available

| Tool | Purpose | What It Does |
| :--- | :--- | :--- |
| **find_testing_gaps** | Proactive Audit | Uses Tree-sitter to find untested symbols. |
| **get_local_diff** | Local PR Mode | Identifies uncommitted changes to focus the audit. |
| **write_test** | Generate Tests | Writes pytest-compatible test code to the appropriate file. |
| **clone_repo** | Remote Access | Clones GitHub repositories for analysis. |
| **create_pull_request** | Submission | Commits and opens a GitHub PR (for remote targets). |

## Security & Privacy

- **Zero Data Exfiltration:** By using LiteLLM + Ollama, your source code is processed entirely on your local machine.
- **Deterministic Logic:** Structural gaps are found via AST parsing, not LLM guessing, reducing the risk of "hallucinated" code review comments.

## Licence

MIT
