"""Tests.unit.presentation.mcp.test_io_adapter
Where: Automated test module.
What: Unit tests for presentation-layer I/O helpers.
Why: Guard the thin adapter behavior as we thin the server.
"""

from __future__ import annotations

from typing import Any

from noveler.presentation.mcp.adapters.io import (
    apply_path_fallback_from_locals,
    resolve_path_service,
)


class DummyPS:
    def __init__(self, events: list[dict] | None = None) -> None:
        self._events = list(events or [])

    def get_and_clear_fallback_events(self) -> list[dict]:
        ev, self._events = self._events, []
        return ev


def test_apply_path_fallback_from_locals_attaches_events() -> None:
    payload: dict[str, Any] = {"ok": True}
    ctx = {"ps": DummyPS([{"path": "/tmp", "reason": "fallback"}])}
    out = apply_path_fallback_from_locals(payload, ctx)
    assert out.get("path_fallback_used") is True
    assert isinstance(out.get("path_fallback_events"), list)


def test_resolve_path_service_safe_when_factory_missing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Monkeypatch import to simulate missing factory module
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name.startswith("noveler.infrastructure.factories.path_service_factory"):
            raise ImportError("factory missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    ps = resolve_path_service(None)
    assert ps is None

