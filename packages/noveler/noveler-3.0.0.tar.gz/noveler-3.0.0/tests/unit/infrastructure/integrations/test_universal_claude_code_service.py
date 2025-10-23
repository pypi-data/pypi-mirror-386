#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.integrations.test_universal_claude_code_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from dataclasses import dataclass
from pathlib import Path

import pytest

from noveler.domain.value_objects.universal_prompt_execution import (
    PromptType,
    ProjectContext,
    UniversalPromptRequest,
)
from noveler.infrastructure.integrations.claude_code_integration_service import (
    ClaudeCodeIntegrationConfig,
    ClaudeCodeIntegrationService,
)
from noveler.infrastructure.integrations.universal_claude_code_service import (
    UniversalClaudeCodeService,
)

@dataclass
class _DummyConsole:
    messages: list[str]

    def print(self, msg: str) -> None:
        self.messages.append(msg)


@pytest.mark.asyncio
async def test_universal_execute_writing_success(tmp_path, monkeypatch):
    # Arrange: 非MCP環境に固定
    from noveler.infrastructure.integrations import claude_code_integration_service as mod

    monkeypatch.setattr(mod, "is_mcp_environment", lambda: False)

    project_root = tmp_path
    project_root.mkdir(exist_ok=True)

    ctx = ProjectContext(project_root=project_root)
    req = UniversalPromptRequest(
        prompt_content="テストプロンプト",
        prompt_type=PromptType.WRITING,
        project_context=ctx,
    )

    base_cfg = ClaudeCodeIntegrationConfig()
    base_svc = ClaudeCodeIntegrationService(base_cfg)
    dummy_console = _DummyConsole(messages=[])

    universal = UniversalClaudeCodeService(config=base_cfg, logger_service=None, console_service=dummy_console)
    # base_serviceを差し替え（DIの簡易版）
    universal.base_service = base_svc

    # Act
    resp = await universal.execute_universal_prompt(req)

    # Assert
    assert resp.success is True
    assert resp.prompt_type == PromptType.WRITING
    assert resp.execution_time_ms >= 0
    # コンソール出力が呼ばれている（少なくとも1件）
    assert any("プロンプト実行成功" in m for m in dummy_console.messages)
