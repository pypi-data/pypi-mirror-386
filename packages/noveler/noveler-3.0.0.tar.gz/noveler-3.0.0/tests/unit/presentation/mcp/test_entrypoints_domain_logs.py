from __future__ import annotations

import pytest

from noveler.domain.utils import domain_console
from noveler.presentation.mcp.entrypoints import _safe_async


class DummyDelegate:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.messages.append(" ".join(str(arg) for arg in args))


@pytest.mark.asyncio
async def test_safe_async_captures_domain_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    delegate = DummyDelegate()
    console_wrapper = domain_console.DomainConsole(delegate)
    monkeypatch.setattr(domain_console, "console", console_wrapper)
    monkeypatch.setattr(domain_console, "get_console", lambda: console_wrapper)

    async def handler(arguments):  # type: ignore[no-untyped-def]
        domain_console.console.print("hello from domain")
        return {"success": True, "metadata": {}}

    result = await _safe_async("dummy", handler, {})
    assert result["metadata"]["domain_logs"] == [
        {"level": "info", "message": "hello from domain"}
    ]
    assert delegate.messages == []  # suppressed during capture


@pytest.mark.asyncio
async def test_safe_async_logs_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    delegate = DummyDelegate()
    console_wrapper = domain_console.DomainConsole(delegate)
    monkeypatch.setattr(domain_console, "console", console_wrapper)
    monkeypatch.setattr(domain_console, "get_console", lambda: console_wrapper)

    async def handler(arguments):  # type: ignore[no-untyped-def]
        domain_console.console.print("before failure")
        raise RuntimeError("boom")

    result = await _safe_async("dummy", handler, {"foo": "bar"}, include_arguments=True)
    assert result["success"] is False
    assert result["error"] == "boom"
    assert result["arguments"] == {"foo": "bar"}
    assert result["domain_logs"] == [
        {"level": "info", "message": "before failure"}
    ]
    assert delegate.messages == []
