import importlib
from pathlib import Path

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "module_path",
    [
        "noveler.infrastructure.mcp.handlers",
        "noveler.presentation.mcp.adapters.handlers",
    ],
)
async def test_status_avoids_manuscript_dir_creation(module_path: str, tmp_path, monkeypatch):
    """Ensure the status handler inspects manuscripts without creating directories."""

    module = importlib.import_module(module_path)

    calls: list[bool] = []

    class StubPathService:
        def __init__(self, project_root: Path):
            self.project_root = project_root

        def get_manuscript_dir(self, *, create: bool = True) -> Path:
            calls.append(create)
            if create:
                raise AssertionError("status should not create manuscript directories")
            return Path("40_原稿")

    resolver_attr = "resolve_path_service"
    if not hasattr(module, resolver_attr):
        resolver_attr = "_resolve_path_service"

    def _fake_resolve(*_args, **_kwargs):
        return StubPathService(tmp_path)

    monkeypatch.setattr(module, resolver_attr, _fake_resolve)

    result = await module.status({"project_root": str(tmp_path)})

    assert result["success"] is True
    assert calls == [False]
    assert not (tmp_path / "40_原稿").exists()
