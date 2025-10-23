"""Tests for ProgressiveCheckManager template fallback search order."""
from __future__ import annotations

from pathlib import Path

import pytest

from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager


@pytest.fixture()
def manager(tmp_path: Path) -> ProgressiveCheckManager:
    project_config = tmp_path / "プロジェクト設定.yaml"
    default_config = '\n'.join([
        'writing:',
        '  episode:',
        '    target_length:',
        '      min: 6000',
        '      max: 10000',
    ]) + '\n'
    project_config.write_text(default_config, encoding='utf-8')

    mgr = ProgressiveCheckManager(project_root=tmp_path, episode_number=1)
    mgr.prompt_templates_dir = tmp_path
    mgr.template_source_log.clear()
    return mgr


def _write_template(root: Path, relative_parts: list[str], filename: str, content: str) -> None:
    target_dir = root
    for part in relative_parts:
        target_dir = target_dir / part
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_text(content, encoding="utf-8")


def test_primary_directory_preferred(manager: ProgressiveCheckManager, tmp_path: Path) -> None:
    filename = "check_step01_typo_check.yaml"
    _write_template(tmp_path, ["quality", "checks"], filename, "metadata: {}\n")
    _write_template(tmp_path, ["quality", "checks", "backup"], filename, "metadata: {}\n")

    template = manager._load_prompt_template(1)  # noqa: SLF001 (private for test)

    assert isinstance(template, dict)
    source_meta = manager.template_source_log.get(1)
    assert isinstance(source_meta, dict)
    assert source_meta.get("source") == "checks"


def test_fallback_to_backup_directory(manager: ProgressiveCheckManager, tmp_path: Path) -> None:
    filename = "check_step01_typo_check.yaml"
    _write_template(tmp_path, ["quality", "checks", "backup"], filename, "metadata: {}\n")

    template = manager._load_prompt_template(1)  # noqa: SLF001

    assert isinstance(template, dict)
    source_meta = manager.template_source_log.get(1)
    assert isinstance(source_meta, dict)
    assert source_meta.get("source") == "checks_backup"


def test_fallback_to_writing_directory(manager: ProgressiveCheckManager, tmp_path: Path) -> None:
    filename = "check_step01_typo_check.yaml"
    _write_template(tmp_path, ["writing"], filename, "metadata: {}\n")

    template = manager._load_prompt_template(1)  # noqa: SLF001

    assert isinstance(template, dict)
    source_meta = manager.template_source_log.get(1)
    assert isinstance(source_meta, dict)
    assert source_meta.get("source") == "writing"
