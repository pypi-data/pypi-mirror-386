import json
from datetime import datetime, timedelta, timezone

import pytest

from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager


class _DummyProjectTime:
    def __init__(self, dt: datetime) -> None:
        self.datetime = dt


@pytest.fixture
def write_manager_stub(tmp_path):
    manager = ProgressiveWriteManager.__new__(ProgressiveWriteManager)
    manager.project_root = tmp_path
    manager.episode_number = 3
    manager.session_id = "EP0003_WRITE_SEED"
    manager.session_start_ts = None
    manager.session_start_iso = None
    manager._session_meta_path = tmp_path / ".noveler" / "writes" / "session_meta.json"
    return manager


def test_write_manager_ensure_session_start_ts_persists_meta(write_manager_stub, monkeypatch):
    manager = write_manager_stub

    jst = timezone(timedelta(hours=9))
    monkeypatch.setattr(
        "noveler.domain.services.progressive_write_manager.project_now",
        lambda: _DummyProjectTime(datetime(2025, 10, 4, 15, 30, tzinfo=jst)),
    )

    ts1, iso1 = manager._ensure_session_start_ts()

    assert ts1 == "202510041530"
    assert iso1.startswith("2025-10-04T15:30:00")

    meta = json.loads(manager._session_meta_path.read_text(encoding="utf-8"))
    assert meta["session_id"] == manager.session_id
    assert meta["first_step_started_at"]["compact"] == ts1

    manager.session_start_ts = None
    manager.session_start_iso = None

    ts2, iso2 = manager._ensure_session_start_ts()

    assert ts2 == ts1
    assert iso2 == iso1
