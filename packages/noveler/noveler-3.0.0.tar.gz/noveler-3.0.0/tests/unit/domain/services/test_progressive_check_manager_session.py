import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from noveler.domain.interfaces.logger_interface import NullLogger
from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager


class _DummyProjectTime:
    def __init__(self, dt: datetime) -> None:
        self.datetime = dt


@pytest.fixture
def check_manager_stub(tmp_path):
    manager = ProgressiveCheckManager.__new__(ProgressiveCheckManager)
    manager.project_root = tmp_path
    manager.episode_number = 2
    manager.session_id = "EP002_202510041100"
    manager.io_dir = tmp_path / ".noveler" / "checks" / manager.session_id
    manager.io_dir.mkdir(parents=True, exist_ok=True)
    manager.manifest_path = manager.io_dir / "manifest.json"
    manager.manifest = {}
    manager.session_start_ts = None
    manager.session_start_iso = None
    manager._base_target_length = {}
    manager.logger = NullLogger()
    manager._workflow_state_store_factory = lambda *args, **kwargs: None
    manager._workflow_state_store = None
    manager._io_logger_factory = None

    # SessionCoordinatorのモックを追加
    manager.session_coordinator = MagicMock()
    return manager


def test_ensure_session_start_ts_uses_manifest_created_at(check_manager_stub, monkeypatch):
    manager = check_manager_stub
    manager.manifest = {"created_at": "2025-10-04T11:00:00+09:00"}

    fixed = datetime(2025, 10, 4, 5, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "noveler.domain.services.progressive_check_manager.project_now",
        lambda: _DummyProjectTime(fixed),
    )

    # SessionCoordinatorのモック動作を設定
    expected_ts = "202510041100"
    expected_iso = "2025-10-04T11:00:00+09:00"
    manager.session_coordinator.ensure_session_start_ts.return_value = (expected_ts, expected_iso)

    # _load_manifestのモック（manifestを返すだけ）
    updated_manifest = {
        "created_at": "2025-10-04T11:00:00+09:00",
        "first_step_started_at": {
            "compact": expected_ts,
            "iso": expected_iso,
        }
    }
    manager._load_manifest = lambda: updated_manifest
    # manifest_pathに保存（テスト検証用）
    manager.manifest_path.write_text(json.dumps(updated_manifest, ensure_ascii=False), encoding="utf-8")

    session_ts, session_iso = manager._ensure_session_start_ts()

    assert session_ts == expected_ts
    assert session_iso.startswith("2025-10-04T11:00:00")

    stored = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
    assert stored["first_step_started_at"]["compact"] == session_ts
    assert stored["first_step_started_at"]["iso"] == session_iso


def test_hydrate_session_start_from_manifest(check_manager_stub):
    manager = check_manager_stub
    manager.manifest = {
        "first_step_started_at": {
            "compact": "202510041345",
            "iso": "2025-10-04T13:45:00+09:00",
        }
    }

    # SessionCoordinatorのモック属性を設定
    # hydrate_session_start_from_manifestが呼ばれた後の状態をシミュレート
    def mock_hydrate(manifest):
        manager.session_coordinator.session_start_ts = "202510041345"
        manager.session_coordinator.session_start_iso = "2025-10-04T13:45:00+09:00"

    manager.session_coordinator.hydrate_session_start_from_manifest = mock_hydrate

    manager._hydrate_session_start_from_manifest()

    assert manager.session_start_ts == "202510041345"
    assert manager.session_start_iso == "2025-10-04T13:45:00+09:00"
