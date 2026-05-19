"""Agentic QA workflow using LiteLLM for local-first models."""

import litellm
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv
from tree_sitter_languages import get_language, get_parser
from agent.auditor import TreeSitterAuditor

# Load environment variables
load_dotenv()

class AgentState(TypedDict):
    repo_url: str
    repo_path: str
    functions: list[dict]
    test_file: str
    pr_created: bool
    messages: list
    model: str


def initialize_state(repo_url: str, model: str = None) -> AgentState:
    if not model:
        model = os.getenv("LITELLM_MODEL", "ollama/qwen2.5-coder")
    
    return {
        "repo_url": repo_url,
        "repo_path": repo_url if os.path.isdir(repo_url) else "",
        "functions": [],
        "test_file": "",
        "pr_created": False,
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Analyze {repo_url} and improve its test coverage. "
                    "If it is a local path, use it directly. If it is a URL, clone it first. "
                    "Use get_local_diff if it is a local repo to see recent changes. "
                    "Use find_testing_gaps to find missing tests using Tree-sitter, "
                    "then write pytest tests for those gaps."
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


def find_testing_gaps(repo_path: str) -> list[dict]:
    """Use Tree-sitter to find functions in source that are never called in tests."""
    try:
        auditor = TreeSitterAuditor()
        gaps = auditor.find_gaps(repo_path)
        return gaps
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


def get_local_diff(repo_path: str) -> str:
    """Get the git diff of uncommitted changes in a local repository."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error getting diff: {str(e)}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "clone_repo",
            "description": "Clone a GitHub repository to a local temp directory for analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string", "description": "Full GitHub repository URL"}
                },
                "required": ["repo_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_python_files",
            "description": "List all Python (.py) source files in the cloned repository (up to 20)",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Local path to the cloned repository"}
                },
                "required": ["repo_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_testing_gaps",
            "description": "Find all functions and methods in the repository that lack corresponding test calls using Tree-sitter AST analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Local path to the cloned repository"}
                },
                "required": ["repo_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_test",
            "description": "Write a pytest test function for a given Python function into the tests/ directory",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "create_pull_request",
            "description": "Stage, commit, and open a GitHub pull request with all test additions",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Local path to the cloned repository"},
                    "title": {"type": "string", "description": "PR title"},
                    "body": {"type": "string", "description": "PR description summarising what was done"},
                },
                "required": ["repo_path", "title", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_local_diff",
            "description": "Get the git diff of uncommitted changes in the local repository to focus the audit on recent work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Local path to the repository"}
                },
                "required": ["repo_path"],
            },
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

    elif name == "find_testing_gaps":
        gaps = find_testing_gaps(tool_input["repo_path"])
        state["functions"].extend(gaps)
        return json.dumps(gaps), state

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

    elif name == "get_local_diff":
        return get_local_diff(tool_input["repo_path"]), state

    return f"Unknown tool: {name}", state


def run_agent(initial_state: AgentState) -> AgentState:
    """Run the agentic QA loop using LiteLLM (max 10 iterations)."""
    state = initial_state
    messages = list(state["messages"])
    model = state["model"]

    for _ in range(10):
        response = litellm.completion(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            break

        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"[Tool: {name}]", flush=True)
            
            result_str, state = _execute_tool(name, args, state)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": result_str,
            })

    state["messages"] = messages
    return state
