"""Agentic QA workflow using Anthropic tool use."""

import anthropic
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict


class AgentState(TypedDict):
    repo_url: str
    repo_path: str
    functions: list[dict]
    test_file: str
    pr_created: bool
    messages: list


def initialize_state(repo_url: str) -> AgentState:
    return {
        "repo_url": repo_url,
        "repo_path": "",
        "functions": [],
        "test_file": "",
        "pr_created": False,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Analyze {repo_url} and improve its test coverage. "
                    "Clone the repo, find Python files, analyze functions, "
                    "write pytest tests for untested functions, then create a PR."
                ),
            }
        ],
    }


def clone_repo(repo_url: str) -> str:
    """Clone a GitHub repository to a temp directory."""
    dest = tempfile.mkdtemp(prefix="agentic_qa_")
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, dest],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return dest
        return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error cloning repo: {str(e)}"


def list_python_files(repo_path: str) -> list[str]:
    """List Python files in a repository (up to 20, skipping common non-source dirs)."""
    skip = {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules", "dist", "build"}
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in filenames:
            if f.endswith(".py"):
                files.append(os.path.join(root, f))
    return files[:20]


def analyze_functions(file_path: str) -> list[dict]:
    """Extract function definitions from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        functions = []
        for i, line in enumerate(content.split("\n"), start=1):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("async def "):
                name = stripped.split("def ")[1].split("(")[0].strip()
                functions.append({
                    "name": name,
                    "file": file_path,
                    "line": i,
                    "signature": stripped,
                })
        return functions
    except Exception as e:
        return [{"error": str(e)}]


def write_test(function: dict, test_code: str) -> str:
    """Append test code for a function to the appropriate test file."""
    try:
        test_dir = os.path.join(os.path.dirname(function["file"]), "tests")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, f"test_{Path(function['file']).stem}.py")
        with open(test_file, "a", encoding="utf-8") as f:
            f.write("\n\n" + test_code)
        return f"Test written to {test_file}"
    except Exception as e:
        return f"Error writing test: {str(e)}"


def create_pull_request(repo_path: str, title: str, body: str) -> str:
    """Commit test changes and open a GitHub pull request."""
    try:
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", title],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return f"PR created: {result.stdout.strip()}"
        return f"Error creating PR: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"


TOOLS = [
    {
        "name": "clone_repo",
        "description": "Clone a GitHub repository to a local temp directory for analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "Full GitHub repository URL"}
            },
            "required": ["repo_url"],
        },
    },
    {
        "name": "list_python_files",
        "description": "List all Python (.py) source files in the cloned repository (up to 20)",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Local path to the cloned repository"}
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "analyze_functions",
        "description": "Extract all function definitions (name, file, line number, signature) from a Python file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to a Python source file"}
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write_test",
        "description": "Write a pytest test function for a given Python function into the tests/ directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "function": {
                    "type": "object",
                    "description": "Function metadata dict with keys: name, file, line, signature",
                },
                "test_code": {
                    "type": "string",
                    "description": "Complete, runnable pytest test code (including imports if needed)",
                },
            },
            "required": ["function", "test_code"],
        },
    },
    {
        "name": "create_pull_request",
        "description": "Stage, commit, and open a GitHub pull request with all test additions",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Local path to the cloned repository"},
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR description summarising what was done"},
            },
            "required": ["repo_path", "title", "body"],
        },
    },
]


def _execute_tool(name: str, tool_input: dict, state: AgentState) -> tuple[str, AgentState]:
    if name == "clone_repo":
        result = clone_repo(tool_input["repo_url"])
        if not result.startswith("Error"):
            state["repo_path"] = result
        return result, state

    elif name == "list_python_files":
        files = list_python_files(tool_input["repo_path"])
        return json.dumps(files), state

    elif name == "analyze_functions":
        functions = analyze_functions(tool_input["file_path"])
        state["functions"].extend(f for f in functions if "error" not in f)
        return json.dumps(functions), state

    elif name == "write_test":
        result = write_test(tool_input["function"], tool_input["test_code"])
        if result.startswith("Test written to "):
            state["test_file"] = result.split("Test written to ", 1)[-1]
        return result, state

    elif name == "create_pull_request":
        result = create_pull_request(
            tool_input["repo_path"],
            tool_input["title"],
            tool_input["body"],
        )
        if "PR created" in result:
            state["pr_created"] = True
        return result, state

    return f"Unknown tool: {name}", state


def run_agent(initial_state: AgentState) -> AgentState:
    """Run the agentic QA loop (max 10 iterations)."""
    client = anthropic.Anthropic()
    state = initial_state
    messages = list(state["messages"])

    for _ in range(10):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=(
                "You are an expert QA engineer. Your job is to improve test coverage for Python repositories. "
                "Follow this order: clone_repo → list_python_files → analyze_functions (for each file) → "
                "write_test (for each untested function) → create_pull_request. "
                "Write complete, runnable pytest test functions including any necessary imports."
            ),
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[Tool: {block.name}]", flush=True)
                result_str, state = _execute_tool(block.name, block.input, state)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    state["messages"] = messages
    return state
