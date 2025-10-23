import shutil
from pathlib import Path

import pytest

from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
from noveler.domain.services.progressive_write_runtime_deps import NullPathService, ProgressiveWriteRuntimeDeps


class _StubArtifactStore:
    """Minimal artifact store returning fixed metadata for tests."""

    def __init__(self, artifacts: list[dict[str, str]]) -> None:
        self._artifacts = list(artifacts)
        self._metadata = {item["artifact_id"]: item["metadata"] for item in artifacts}

    def list_artifacts(self) -> list[dict[str, str]]:
        return list(self._artifacts)

    def get_metadata(self, artifact_id: str) -> dict[str, str]:
        return self._metadata.get(artifact_id, {})

    def fetch(self, artifact_id: str) -> str | None:
        entry = self._metadata.get(artifact_id, {})
        return entry.get("content") if isinstance(entry, dict) else None


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    source = Path(__file__).with_name("sample_project")
    destination = tmp_path / "project"
    shutil.copytree(source, destination)
    return destination


def _build_write_manager(project_root: Path) -> ProgressiveWriteManager:
    artifacts = [
        {
            "artifact_id": "summary-ep1",
            "metadata": {"tags": {"episode": "1", "type": "summary"}, "content": "要約テキスト"},
        },
        {
            "artifact_id": "world-ep1",
            "metadata": {"tags": {"episode": "1", "type": "world_settings"}, "content": "世界設定メモ"},
        },
    ]

    def artifact_store_factory(*, storage_dir: Path, **_: object) -> _StubArtifactStore:
        return _StubArtifactStore(artifacts)

    deps = ProgressiveWriteRuntimeDeps(
        artifact_store_factory=artifact_store_factory,
        path_service_factory=lambda root: NullPathService(root),
    )

    manager = ProgressiveWriteManager(project_root=str(project_root), episode_number=1, deps=deps)
    manager.prompt_templates_dir = project_root / "templates"
    return manager


def test_generate_enhanced_instruction_matches_golden(sample_project: Path) -> None:
    manager = _build_write_manager(sample_project)
    current_task = manager._get_task_by_id(manager.tasks_config["tasks"], 1)
    assert current_task is not None
    instruction = manager._generate_enhanced_llm_instruction(current_task, [current_task])

    golden_path = Path(__file__).with_name("golden_step01_instruction.txt")
    expected = golden_path.read_text(encoding="utf-8")
    assert instruction == expected

