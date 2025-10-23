import pytest

from noveler.domain.exceptions import MissingProjectRootError
from noveler.infrastructure.adapters.path_service_adapter import (
    PathServiceAdapter,
    create_path_service,
)


def test_get_step_output_file_path_uses_session_format(tmp_path):
    adapter = PathServiceAdapter(tmp_path)
    path = adapter.get_step_output_file_path(
        episode_number=2,
        step_number=7,
        timestamp="20251004120030",
        session_start_ts="202510041200",
        session_id="EP0002_checks",
    )
    expected = tmp_path / ".noveler" / "checks" / "episode002_202510041200_EP0002_checks_step07.json"
    assert path == expected


def test_get_step_output_file_path_sanitizes_session_id(tmp_path):
    adapter = PathServiceAdapter(tmp_path)
    path = adapter.get_step_output_file_path(
        episode_number=1,
        step_number=3,
        timestamp="20251004120030",
        session_start_ts="202510041201",
        session_id="session id!*",
    )
    assert path.name == "episode001_202510041201_session-id_step03.json"


def test_get_step_output_file_path_falls_back_without_session(tmp_path):
    adapter = PathServiceAdapter(tmp_path)
    path = adapter.get_step_output_file_path(episode_number=4, step_number=5, timestamp="20251004100533")
    assert path.name == "EP0004_step05_20251004100533.json"


def test_get_write_step_output_file_path_uses_session_format(tmp_path):
    adapter = PathServiceAdapter(tmp_path)
    path = adapter.get_write_step_output_file_path(
        episode_number=3,
        step_number=9,
        timestamp="20251004141500",
        session_start_ts="202510041410",
        session_id="write-session",
    )
    expected = tmp_path / ".noveler" / "writes" / "episode003_202510041410_write-session_step09.json"
    assert path == expected


def test_create_path_service_enables_strict_mode_from_error_env(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVELER_STRICT_PATH", "error")
    monkeypatch.delenv("NOVELER_STRICT_PATHS", raising=False)

    captured: dict[str, object] = {}

    class DummyAdapter:
        def __init__(self, project_root, config_repository=None, strict=None):
            captured["project_root"] = project_root
            captured["strict"] = strict

    monkeypatch.setattr(
        "noveler.infrastructure.adapters.path_service_adapter.PathServiceAdapter",
        DummyAdapter,
    )

    create_path_service(tmp_path)

    assert captured["project_root"] == tmp_path
    assert captured["strict"] is True


def test_create_path_service_raises_when_strict_and_root_missing(monkeypatch):
    monkeypatch.setenv("NOVELER_STRICT_PATH", "error")
    monkeypatch.delenv("NOVELER_STRICT_PATHS", raising=False)
    monkeypatch.setattr(
        "noveler.infrastructure.adapters.path_service_adapter.detect_project_root",
        lambda: None,
    )

    with pytest.raises(MissingProjectRootError):
        create_path_service(project_root=None)
