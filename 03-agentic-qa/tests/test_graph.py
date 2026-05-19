"""Unit tests for the agentic QA workflow.

All subprocess, filesystem, and LLM calls are mocked so these tests
run without needing git, gh CLI, or Ollama.
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent.graph import (
    clone_repo,
    create_pull_request,
    initialize_state,
    list_python_files,
    run_agent,
    write_test,
)


# ============= initialize_state =============

def test_initialize_state_defaults():
    state = initialize_state("https://github.com/user/repo")
    assert state["repo_url"] == "https://github.com/user/repo"
    assert state["repo_path"] == ""
    assert state["functions"] == []
    assert state["test_file"] == ""
    assert state["pr_created"] is False
    assert len(state["messages"]) == 1
    assert state["messages"][0]["role"] == "user"


# ============= clone_repo =============

def test_clone_repo_success():
    with patch("agent.graph.tempfile.mkdtemp", return_value="/tmp/agentic_qa_abc"), \
         patch("agent.graph.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = clone_repo("https://github.com/user/repo")
    assert result == "/tmp/agentic_qa_abc"


def test_clone_repo_failure():
    with patch("agent.graph.tempfile.mkdtemp", return_value="/tmp/agentic_qa_abc"), \
         patch("agent.graph.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Repository not found")
        result = clone_repo("https://github.com/invalid/repo")
    assert result.startswith("Error")


def test_clone_repo_exception():
    with patch("agent.graph.tempfile.mkdtemp", return_value="/tmp/agentic_qa_abc"), \
         patch("agent.graph.subprocess.run", side_effect=Exception("timeout")):
        result = clone_repo("https://github.com/user/repo")
    assert "Error cloning repo" in result


# ============= list_python_files =============

def test_list_python_files_returns_py_only():
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "main.py"), "w").close()
        open(os.path.join(tmpdir, "utils.py"), "w").close()
        open(os.path.join(tmpdir, "README.md"), "w").close()

        result = list_python_files(tmpdir)

    assert len(result) == 2
    assert all(f.endswith(".py") for f in result)


def test_list_python_files_skips_git_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        git_dir = os.path.join(tmpdir, ".git")
        os.makedirs(git_dir)
        open(os.path.join(git_dir, "hook.py"), "w").close()
        open(os.path.join(tmpdir, "app.py"), "w").close()

        result = list_python_files(tmpdir)

    assert len(result) == 1
    assert not any(".git" in f for f in result)


def test_list_python_files_caps_at_20():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(25):
            open(os.path.join(tmpdir, f"file{i}.py"), "w").close()
        result = list_python_files(tmpdir)
    assert len(result) == 20


# ============= find_testing_gaps =============

def test_find_testing_gaps_error_path():
    with patch("agent.graph.TreeSitterAuditor") as mock_cls:
        mock_cls.return_value.find_gaps.side_effect = Exception("parser crashed")
        from agent.graph import find_testing_gaps
        result = find_testing_gaps("/some/path")
    assert result == [{"error": "parser crashed"}]


# ============= write_test =============

def test_write_test_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        func = {
            "name": "add",
            "file": os.path.join(tmpdir, "math_utils.py"),
            "line": 1,
            "signature": "def add(a, b):",
        }
        test_code = "def test_add():\n    assert add(1, 2) == 3\n"

        result = write_test(func, test_code)

        assert "Test written to" in result
        expected = os.path.join(tmpdir, "tests", "test_math_utils.py")
        assert os.path.exists(expected)
        assert "test_add" in open(expected).read()


def test_write_test_appends_on_repeated_calls():
    with tempfile.TemporaryDirectory() as tmpdir:
        func = {
            "name": "add",
            "file": os.path.join(tmpdir, "calc.py"),
            "line": 1,
            "signature": "def add(a, b):",
        }
        write_test(func, "def test_add():\n    pass\n")
        write_test(func, "def test_add_negative():\n    pass\n")

        content = open(os.path.join(tmpdir, "tests", "test_calc.py")).read()
        assert "test_add_negative" in content


# ============= create_pull_request =============

def test_create_pull_request_success():
    with patch("agent.graph.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo/pull/1\n",
            stderr="",
        )
        result = create_pull_request("/tmp/repo", "Add tests", "Auto-generated tests")
    assert "PR created" in result
    assert "https://github.com" in result


def test_create_pull_request_gh_failure():
    with patch("agent.graph.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no upstream")
        result = create_pull_request("/tmp/repo", "Add tests", "body")
    assert "Error creating PR" in result


def test_create_pull_request_exception():
    with patch("agent.graph.subprocess.run", side_effect=Exception("gh not installed")):
        result = create_pull_request("/tmp/repo", "Add tests", "body")
    assert result.startswith("Error")


# ============= run_agent =============

def _mock_litellm_response(tool_calls=None):
    """Build a mock litellm ModelResponse."""
    message = MagicMock()
    if tool_calls:
        message.tool_calls = []
        for tc in tool_calls:
            call = MagicMock()
            call.id = f"call_{tc['name']}"
            call.function.name = tc["name"]
            call.function.arguments = json.dumps(tc["input"])
            message.tool_calls.append(call)
    else:
        message.tool_calls = None

    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def test_run_agent_stops_when_no_tool_calls():
    with patch("agent.graph.litellm.completion") as mock_completion:
        mock_completion.return_value = _mock_litellm_response()

        state = initialize_state("https://github.com/user/repo")
        result = run_agent(state)

    assert mock_completion.call_count == 1
    assert result["pr_created"] is False


def test_run_agent_executes_clone_tool():
    tool_resp = _mock_litellm_response(
        tool_calls=[{"name": "clone_repo", "input": {"repo_url": "https://github.com/user/repo"}}]
    )
    end_resp = _mock_litellm_response()

    with patch("agent.graph.litellm.completion") as mock_completion, \
         patch("agent.graph.clone_repo", return_value="/tmp/repo_xyz") as mock_clone:
        mock_completion.side_effect = [tool_resp, end_resp]

        state = initialize_state("https://github.com/user/repo")
        result = run_agent(state)

    mock_clone.assert_called_once_with("https://github.com/user/repo")
    assert result["repo_path"] == "/tmp/repo_xyz"


def test_run_agent_sets_pr_created():
    tool_resp = _mock_litellm_response(
        tool_calls=[{
            "name": "create_pull_request",
            "input": {"repo_path": "/tmp/repo", "title": "Add tests", "body": "body"},
        }]
    )
    end_resp = _mock_litellm_response()

    with patch("agent.graph.litellm.completion") as mock_completion, \
         patch("agent.graph.create_pull_request", return_value="PR created: https://github.com/x/y/pull/1"):
        mock_completion.side_effect = [tool_resp, end_resp]

        state = initialize_state("https://github.com/user/repo")
        result = run_agent(state)

    assert result["pr_created"] is True


def test_run_agent_respects_max_iterations():
    """Agent loop does not exceed 10 iterations."""
    tool_resp = _mock_litellm_response(
        tool_calls=[{"name": "clone_repo", "input": {"repo_url": "https://github.com/user/repo"}}]
    )

    with patch("agent.graph.litellm.completion") as mock_completion, \
         patch("agent.graph.clone_repo", return_value="/tmp/repo"):
        mock_completion.return_value = tool_resp

        state = initialize_state("https://github.com/user/repo")
        run_agent(state)

    assert mock_completion.call_count == 10
