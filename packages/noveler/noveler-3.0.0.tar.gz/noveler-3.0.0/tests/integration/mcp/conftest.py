#!/usr/bin/env python3

"""Tests.tests.integration.mcp.conftest
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import pytest


@pytest.fixture
def temp_project(temp_project_dir):
    """Alias fixture to match tests expecting `temp_project`.

    Reuses the session-scoped `temp_project_dir` from the root tests conftest.
    """
    return temp_project_dir


@pytest.fixture
async def mcp_server(mcp_server_instance):
    """Alias fixture for backward compatibility.

    Some tests request a `mcp_server` fixture, while this suite provides
    `mcp_server_instance`. This fixture bridges the naming difference.
    """
    return mcp_server_instance


@pytest.fixture
def mcp_test_project(temp_project_dir):
    """Fixture providing a temporary project root for MCP integration tests.

    Provides the common `mcp_test_project` fixture that automatically
    constructs temporary project root and manages environment variables/caches.
    Reuses the session-scoped `temp_project_dir` from root tests conftest.
    """
    return temp_project_dir
