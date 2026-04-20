"""LangGraph-based agentic workflow for automated QA."""

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Annotated, TypedDict, Any
from langchain_core.messages import AnyMessage, BaseMessage, HumanMessage
from langchain_core.tools import tool
import anthropic
import json
import subprocess
import os
from pathlib import Path

class AgentState(TypedDict):
    """State for the QA agent."""
    repo_url: str
    repo_path: str
    functions: list[dict]
    test_file: str
    pr_created: bool
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]

def initialize_state(repo_url: str) -> AgentState:
    """Initialize agent state."""
    return {
        "repo_url": repo_url,
        "repo_path": "",
        "functions": [],
        "test_file": "",
        "pr_created": False,
        "messages": [HumanMessage(content=f"Analyze {repo_url} and write tests for untested functions")],
    }

@tool
def clone_repo(repo_url: str) -> str:
    """Clone a GitHub repository."""
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, "/tmp/repo"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return "/tmp/repo"
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Error cloning repo: {str(e)}"

@tool
def list_python_files(repo_path: str) -> list[str]:
    """List all Python files in a repository."""
    try:
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache", "venv", ".venv"]]
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
        return files[:20]  # Limit to first 20 files
    except Exception as e:
        return [f"Error: {str(e)}"]

@tool
def analyze_functions(file_path: str) -> list[dict]:
    """Extract function definitions from a Python file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        functions = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                func_name = line.split("def ")[1].split("(")[0]
                functions.append({
                    "name": func_name,
                    "file": file_path,
                    "line": i + 1,
                    "signature": line.strip()
                })
        return functions
    except Exception as e:
        return [{"error": str(e)}]

@tool
def write_test(function: dict, test_code: str) -> str:
    """Write a test for a function."""
    try:
        test_dir = os.path.join(os.path.dirname(function["file"]), "tests")
        os.makedirs(test_dir, exist_ok=True)

        test_file = os.path.join(test_dir, f"test_{Path(function['file']).stem}.py")

        with open(test_file, "a") as f:
            f.write("\n\n" + test_code)

        return f"Test written to {test_file}"
    except Exception as e:
        return f"Error writing test: {str(e)}"

@tool
def create_pull_request(repo_path: str, title: str, body: str) -> str:
    """Create a pull request with test changes."""
    try:
        # Git add and commit
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", title],
            cwd=repo_path,
            check=True
        )

        # Use gh CLI to create PR
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return f"PR created: {result.stdout}"
        else:
            return f"Error creating PR: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

def process_agent_response(response: dict, state: AgentState) -> AgentState:
    """Process Claude's response and update state."""
    if "functions" in response:
        state["functions"] = response["functions"]
    if "tests_written" in response:
        state["test_file"] = response.get("tests_written", "")
    if "pr_created" in response:
        state["pr_created"] = response["pr_created"]
    return state

def run_agent(initial_state: AgentState) -> AgentState:
    """Run the QA agent."""
    client = anthropic.Anthropic()
    state = initial_state

    tools = [
        {
            "name": "clone_repo",
            "description": "Clone a GitHub repository to analyze",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string", "description": "GitHub repository URL"}
                },
                "required": ["repo_url"]
            }
        },
        {
            "name": "list_python_files",
            "description": "List Python files in the repository",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Path to the repository"}
                },
                "required": ["repo_path"]
            }
        },
        {
            "name": "analyze_functions",
            "description": "Extract function definitions from a Python file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file"}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "write_test",
            "description": "Write a test for a function",
            "input_schema": {
                "type": "object",
                "properties": {
                    "function": {"type": "object", "description": "Function metadata"},
                    "test_code": {"type": "string", "description": "Test code to write"}
                },
                "required": ["function", "test_code"]
            }
        },
        {
            "name": "create_pull_request",
            "description": "Create a PR with test changes",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["repo_path", "title", "body"]
            }
        }
    ]

    messages = state["messages"]

    # Run agent loop
    for _ in range(10):  # Max 10 iterations
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system="You are an expert QA engineer. Analyze GitHub repos and write comprehensive tests for untested functions. Use the provided tools to clone repos, analyze code, write tests, and create PRs.",
            tools=tools,
            messages=messages
        )

        # Add assistant response
        messages.append({"role": "assistant", "content": response.content})

        # Check if done
        if response.stop_reason == "end_turn":
            break

        # Process tool uses
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input

                # Execute tool
                if tool_name == "clone_repo":
                    result = clone_repo(tool_input["repo_url"])
                    state["repo_path"] = result
                elif tool_name == "list_python_files":
                    result = json.dumps(list_python_files(tool_input["repo_path"]))
                elif tool_name == "analyze_functions":
                    result = json.dumps(analyze_functions(tool_input["file_path"]))
                elif tool_name == "write_test":
                    result = write_test(tool_input["function"], tool_input["test_code"])
                elif tool_name == "create_pull_request":
                    result = create_pull_request(
                        tool_input["repo_path"],
                        tool_input["title"],
                        tool_input["body"]
                    )
                    state["pr_created"] = True
                else:
                    result = f"Unknown tool: {tool_name}"

                # Add tool result
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result)
                        }
                    ]
                })

    state["messages"] = messages
    return state
