import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from noveler.application.mcp_services import writing as writing_module
from noveler.application.mcp_services.writing import WritingToolService


class DummyBatchProcessor:
    def __init__(self) -> None:
        self.created = []
        self.executed = []

    def create_batch_job(self, episode_numbers, step_ids, job_name):
        self.created.append((episode_numbers, step_ids, job_name))
        return "job-001"

    async def execute_batch_job(self, job_id):
        self.executed.append(job_id)

        class Result:
            total_episodes = 2
            successful_episodes = 2
            failed_episodes = 0
            total_steps = 36
            successful_steps = 36
            failed_steps = 0
            execution_time = 1.2
            start_time = datetime(2025, 9, 27, 12, 0)
            end_time = datetime(2025, 9, 27, 12, 1)
            detailed_results = {}
            errors = []

        return Result()

    def get_batch_status(self, job_id):
        return {"job_id": job_id, "status": "active"}


class DummyPathService:
    def __init__(self, plot_path: Path) -> None:
        self._plot_path = plot_path

    def get_episode_plot_path(self, episode_number: int) -> Path:
        return self._plot_path

    @property
    def project_root(self) -> Path:
        return self._plot_path.parent


class DummyManuscriptPathService:
    def __init__(self, base: Path) -> None:
        self._base = base

    def get_manuscript_path(self, episode_number: int) -> Path:
        return self._base / f"EP{episode_number:03d}.md"


class DummyArtifactStore:
    def __init__(self) -> None:
        self.records = []

    def store(self, content, content_type, description, source_file=None):
        artifact_id = f"artifact-{len(self.records)+1:03d}"
        self.records.append(
            {
                "content": content,
                "content_type": content_type,
                "description": description,
                "source_file": source_file,
                "id": artifact_id,
            }
        )
        return artifact_id


def _patch_project_now(monkeypatch):
    class _Now:
        def __init__(self) -> None:
            self.datetime = datetime(2025, 9, 27, 12, 0)

    monkeypatch.setattr(writing_module, "project_now", lambda: _Now())


@pytest.mark.asyncio
async def test_create_batch_job_expands_ranges(monkeypatch):
    service = WritingToolService()
    processor = DummyBatchProcessor()
    monkeypatch.setattr(service, "_get_batch_processor", lambda root: processor)

    result = await service.create_batch_job(
        episode_numbers=[1, 2],
        step_ranges=[{"start": 1, "end": 3}],
        job_name="demo",
        project_root=None,
    )

    assert result["job_id"] == "job-001"
    assert processor.created[0][1] == list(range(1, 4))


@pytest.mark.asyncio
async def test_execute_batch_job_returns_serialized_result(monkeypatch):
    service = WritingToolService()
    processor = DummyBatchProcessor()
    monkeypatch.setattr(service, "_get_batch_processor", lambda root: processor)

    result = await service.execute_batch_job(job_id="job-001", dry_run=False, project_root=None)

    assert result["success"] is True
    assert result["result"]["total_episodes"] == 2
    assert processor.executed == ["job-001"]


@pytest.mark.asyncio
async def test_get_batch_status_uses_processor(monkeypatch):
    service = WritingToolService()
    processor = DummyBatchProcessor()
    monkeypatch.setattr(service, "_get_batch_processor", lambda root: processor)

    status = await service.get_batch_status(job_id="job-001", project_root=None)

    assert status == {"success": True, "status": {"job_id": "job-001", "status": "active"}}


@pytest.mark.asyncio
async def test_write_with_claude_generates_prompt(tmp_path, monkeypatch):
    plot_file = tmp_path / "plot" / "EP001_plot.md"
    plot_file.parent.mkdir(parents=True, exist_ok=True)
    plot_file.write_text("タイトル: テストタイトル", encoding="utf-8")

    manuscript_dir = tmp_path / "manuscripts"
    manuscript_dir.mkdir()

    monkeypatch.setattr(writing_module, "create_mcp_aware_path_service", lambda: DummyPathService(plot_file))
    monkeypatch.setattr(writing_module, "create_path_service", lambda: DummyManuscriptPathService(manuscript_dir))
    _patch_project_now(monkeypatch)

    service = WritingToolService()

    result = await service.write_with_claude(episode_number=1, dry_run=False)

    assert result["success"] is True
    assert "テストタイトル" in result.get("plot_title", "") or result["plot_title"] is None
    assert result["manuscript_path"].endswith("EP001.md")


@pytest.mark.asyncio
async def test_write_manuscript_draft_uses_artifact_store(monkeypatch):
    store = DummyArtifactStore()
    monkeypatch.setattr(writing_module, "create_artifact_store", lambda storage_dir: store)
    monkeypatch.setattr(writing_module, "create_mcp_aware_path_service", lambda: DummyPathService(Path("/tmp")))
    _patch_project_now(monkeypatch)

    service = WritingToolService()

    result = await service.write_manuscript_draft(
        episode_number=1,
        plot_analysis={"content": "テストプロット"},
        writing_settings={"word_count_target": 3200},
    )

    assert result["success"] is True
    assert store.records[0]["description"].startswith("第001話")
    assert result["plot_artifact_id"] == "artifact-001"
