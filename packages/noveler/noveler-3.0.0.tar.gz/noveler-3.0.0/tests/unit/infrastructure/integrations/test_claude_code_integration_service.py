#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.integrations.test_claude_code_integration_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import pytest

from noveler.infrastructure.integrations.claude_code_integration_service import (
    ClaudeCodeIntegrationConfig,
    ClaudeCodeIntegrationService,
)
from noveler.domain.value_objects.claude_code_execution import (
    ClaudeCodeExecutionRequest,
)


@pytest.mark.asyncio
async def test_validate_environment_non_mcp(monkeypatch):
    # Arrange
    from noveler.infrastructure.integrations import claude_code_integration_service as mod

    monkeypatch.setattr(mod, "is_mcp_environment", lambda: False)
    cfg = ClaudeCodeIntegrationConfig(claude_executable_path="claude")
    svc = ClaudeCodeIntegrationService(cfg)

    # Act
    ok = await svc.validate_environment()

    # Assert
    assert ok is True


@pytest.mark.asyncio
async def test_validate_environment_mcp(monkeypatch):
    # Arrange
    from noveler.infrastructure.integrations import claude_code_integration_service as mod

    monkeypatch.setattr(mod, "is_mcp_environment", lambda: True)
    cfg = ClaudeCodeIntegrationConfig(claude_executable_path="claude")
    svc = ClaudeCodeIntegrationService(cfg)

    # Act
    ok = await svc.validate_environment()

    # Assert
    assert ok is False


@pytest.mark.asyncio
async def test_execute_prompt_normalization_success(monkeypatch):
    # Arrange
    from noveler.infrastructure.integrations import claude_code_integration_service as mod

    monkeypatch.setattr(mod, "is_mcp_environment", lambda: False)
    cfg = ClaudeCodeIntegrationConfig()
    svc = ClaudeCodeIntegrationService(cfg)

    req = ClaudeCodeExecutionRequest(prompt_content="hello")

    # Act
    resp = await svc.execute_prompt(req)

    # Assert
    assert resp.success is True
    assert resp.response_content == "実行完了"
    # 後方互換フィールド（動的付与）
    assert getattr(resp, "result") == resp.response_content
    assert resp.error_message in (None, "")
    assert resp.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_execute_prompt_mcp_fallback(monkeypatch):
    # Arrange
    from noveler.infrastructure.integrations import claude_code_integration_service as mod

    monkeypatch.setattr(mod, "is_mcp_environment", lambda: True)
    cfg = ClaudeCodeIntegrationConfig()
    svc = ClaudeCodeIntegrationService(cfg)
    req = ClaudeCodeExecutionRequest(prompt_content="dummy")

    # Act
    resp = await svc.execute_prompt(req)

    # Assert
    assert resp.success is True
    assert resp.response_content == "MCP環境用フォールバック結果"
    # メタデータはフォールバックフラグを含む
    meta = getattr(resp, "metadata", {})
    assert meta.get("fallback") is True
