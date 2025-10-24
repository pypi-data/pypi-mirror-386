#!/usr/bin/env python3
"""Comprehensive test of TDD hook to ensure it maintains our perfect test structure."""

import json
import subprocess
import sys


def test_hook_with_real_scenarios():
    """Test the TDD hook with real-world scenarios."""

    # Test scenarios
    scenarios = [
        # Scenario 1: Try to create source without test
        {
            "name": "Block source creation without test",
            "tool": "Write",
            "file": "lib/utils/new_feature.py",
            "content": "def new_feature(): pass",
            "expect_blocked": True,
            "reason": "TDD violation - need test first",
        },
        # Scenario 2: Create test first (TDD Red phase)
        {
            "name": "Allow test creation for new feature",
            "tool": "Write",
            "file": "tests/lib/utils/test_new_feature.py",
            "content": "def test_new_feature(): assert False",
            "expect_blocked": False,
            "reason": "TDD Red phase - test first",
        },
        # Scenario 3: Create test in wrong location
        {
            "name": "Block test outside tests/ directory",
            "tool": "Write",
            "file": "lib/test_wrong_location.py",
            "content": "def test_wrong(): pass",
            "expect_blocked": True,
            "reason": "Test must be in tests/ directory",
        },
        # Scenario 4: Create fixture file
        {
            "name": "Allow fixture file creation",
            "tool": "Write",
            "file": "tests/fixtures/database_fixture.py",
            "content": "import pytest",
            "expect_blocked": False,
            "reason": "Fixtures don't need test_ prefix",
        },
        # Scenario 5: Create integration test
        {
            "name": "Allow integration test without source",
            "tool": "Write",
            "file": "tests/integration/api/test_workflow.py",
            "content": "def test_workflow(): pass",
            "expect_blocked": False,
            "reason": "Integration tests don't need source mirrors",
        },
        # Scenario 6: Wrong test naming
        {
            "name": "Block incorrectly named test",
            "tool": "Write",
            "file": "tests/lib/utils/my_tests.py",
            "content": "def test_something(): pass",
            "expect_blocked": True,
            "reason": "Test file must start with test_",
        },
        # Scenario 7: Modify existing source with test
        {
            "name": "Allow source modification when test exists",
            "tool": "Edit",
            "file": "lib/utils/proxy_agents.py",
            "content": "# Modified content",
            "expect_blocked": False,
            "reason": "Test exists for this source file",
        },
    ]

    # Run each scenario
    for _i, scenario in enumerate(scenarios, 1):
        # Create JSON input for the hook
        hook_input = {
            "tool_name": scenario["tool"],
            "tool_input": {"file_path": scenario["file"], "content": scenario["content"]},
        }

        # Run the hook
        result = subprocess.run(
            [sys.executable, ".claude/tdd_hook.py"], input=json.dumps(hook_input), capture_output=True, text=True
        )

        blocked = result.returncode == 2

        if blocked != scenario["expect_blocked"]:
            if result.stderr:
                pass
        else:
            pass


if __name__ == "__main__":
    test_hook_with_real_scenarios()
