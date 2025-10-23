#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.adapters.test_path_service_adapter_side_effects
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import os
from pathlib import Path

import pytest

from noveler.domain.value_objects.path_configuration import PathConfiguration
from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter


@pytest.mark.unit
def test_get_manuscript_dir_creates_directory(tmp_path: Path):
    # Arrange: 空のプロジェクトルートを用意（プロジェクト設定なし → デフォルトPathConfiguration）
    project_root = tmp_path
    adapter = PathServiceAdapter(project_root)

    # Act
    path = adapter.get_manuscript_dir()

    # Assert
    assert path == project_root / "40_原稿"
    assert path.exists() and path.is_dir()


@pytest.mark.unit
def test_get_management_dir_creates_directory(tmp_path: Path):
    project_root = tmp_path
    adapter = PathServiceAdapter(project_root)

    path = adapter.get_management_dir()

    config = PathConfiguration()
    assert path == project_root / config.management
    assert path.exists() and path.is_dir()


@pytest.mark.unit
def test_get_backup_plots_prompts_quality_reports_create_directories(tmp_path: Path):
    project_root = tmp_path
    adapter = PathServiceAdapter(project_root)

    config = PathConfiguration()
    expected = {
        "backup": project_root / config.backup,
        "plots": project_root / config.plots,
        "prompts": project_root / config.prompts,
        "quality": project_root / config.quality,
        "reports": project_root / config.reports,
    }

    created = {
        "backup": adapter.get_backup_dir(),
        "plots": adapter.get_plots_dir(),
        "prompts": adapter.get_prompts_dir(),
        "quality": adapter.get_quality_dir(),
        "reports": adapter.get_reports_dir(),
    }

    for name, path in created.items():
        assert path == expected[name]
        assert path.exists() and path.is_dir(), f"{name} should be created"
        assert path.is_relative_to(project_root)


@pytest.mark.unit
def test_configuration_overrides_directory_names(tmp_path: Path):
    # Arrange: プロジェクト設定ファイル（プロジェクト直下: プロジェクト設定.yaml）を作成
    project_root = tmp_path
    config = {
        "directory_structure": {
            "manuscript_dir": "40_原稿_CUSTOM",
            "management_dir": "50_管理資料",
            "plot_dir": "20_プロット",
        }
    }
    (project_root / "プロジェクト設定.yaml").write_text(
        __import__("yaml").safe_dump(config, allow_unicode=True), encoding="utf-8"
    )

    adapter = PathServiceAdapter(project_root)

    # Act
    manuscript = adapter.get_manuscript_dir()
    management = adapter.get_management_dir()
    plots = adapter.get_plots_dir()

    # Assert: 反映されたパス名＆ディレクトリ生成の副作用
    assert manuscript == project_root / "40_原稿_CUSTOM"
    assert manuscript.exists() and manuscript.is_dir()

    assert management == project_root / "50_管理資料"
    assert management.exists() and management.is_dir()

    assert plots == project_root / "20_プロット"
    assert plots.exists() and plots.is_dir()


@pytest.mark.unit
def test_get_project_config_file_uses_template(tmp_path: Path):
    """PathServiceAdapter should honour file_templates overrides for project config files."""
    (tmp_path / '.novelerrc.yaml').write_text(
        'file_templates:\n  project_config: custom_project.yaml\n',
        encoding='utf-8',
    )
    custom_config = tmp_path / 'custom_project.yaml'
    custom_config.write_text('title: カスタム作品', encoding='utf-8')

    adapter = PathServiceAdapter(tmp_path)

    assert adapter.get_project_config_file() == custom_config
