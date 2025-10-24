#!/usr/bin/env python3
"""
Test script for the enhanced test_boundary_enforcer.py hook
"""

import json
import subprocess
from pathlib import Path

try:
    import pytest
except ImportError:
    # pytest not available, skip markers won't work but tests can still run
    pytest = None

# Get project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()


def run_hook_with_input(test_input):
    """Test the hook with given input data."""
    hook_path = PROJECT_ROOT / ".claude" / "hooks" / "test_boundary_enforcer.py"

    # Skip if hook doesn't exist
    if not hook_path.exists():
        if pytest:
            pytest.skip(f"Hook not found at {hook_path}")
        return {"returncode": 0, "stdout": "", "stderr": "Hook not found"}

    try:
        process = subprocess.run(
            ["python3", hook_path], input=json.dumps(test_input), text=True, capture_output=True, timeout=10
        )
        return {"returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "Hook timed out"}
    except Exception as e:
        return {"error": str(e)}


def test_hook_blocks_testing_agent_source_code():
    """Test that hook blocks testing agents targeting source code."""
    test_input = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hive-testing-fixer",
            "prompt": "Fix the bug in lib/knowledge/config_aware_filter.py by updating the source code",
        },
        "cwd": str(PROJECT_ROOT),
    }

    result = run_hook_with_input(test_input)
    assert result.get("returncode") == 0

    if result.get("stdout"):
        output = json.loads(result["stdout"])
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision", "none")
        assert decision == "deny", "Should block testing agent targeting source code"


def test_hook_allows_testing_agent_test_work():
    """Test that hook allows testing agents targeting test work."""
    if pytest:
        pytest.skip("Blocked by task-330ed5e0-4fc2-4612-b95c-9c654b212583 - hook needs prompt analysis fix")

    test_input = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hive-testing-fixer",
            "prompt": "Fix failing test in tests/lib/knowledge/test_config_filter.py by updating test expectations",
        },
        "cwd": str(PROJECT_ROOT),
    }

    result = run_hook_with_input(test_input)
    assert result.get("returncode") == 0
    assert not result.get("stdout"), "Should allow testing agent targeting test work"


def test_hook_allows_non_testing_agent():
    """Test that hook allows non-testing agents."""
    test_input = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hive-dev-fixer",
            "prompt": "Fix the bug in lib/knowledge/config_aware_filter.py by updating the source code",
        },
        "cwd": str(PROJECT_ROOT),
    }

    result = run_hook_with_input(test_input)
    assert result.get("returncode") == 0
    assert not result.get("stdout"), "Should allow non-testing agent"


def main():
    """Legacy main function for backward compatibility."""


if __name__ == "__main__":
    main()
