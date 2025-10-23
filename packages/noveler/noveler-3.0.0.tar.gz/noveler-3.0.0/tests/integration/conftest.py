#!/usr/bin/env python3
"""Integration層テスト用共通フィクスチャ

統合テストで使用する共通フィクスチャ群
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from noveler.infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository
from noveler.infrastructure.repositories.yaml_project_info_repository import YamlProjectInfoRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.fixture
def integration_temp_dir() -> Generator[Path, None, None]:
    """統合テスト用一時ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="integration_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def integration_project_setup(integration_temp_dir) -> Any:
    """統合テスト用プロジェクトセットアップ"""
    project_path = integration_temp_dir / "integration_project"
    project_path.mkdir()

    # プロジェクト構造作成
    path_service = get_common_path_service()
    manuscript_dir = project_path / str(path_service.get_manuscript_dir())
    manuscript_dir.mkdir()

    config_file = project_path / "プロジェクト設定.yaml"
    config_file.write_text(
        """
title: "統合テストプロジェクト"
author: "統合テスト作者"
genre: "テストジャンル"
start_date: "2024-01-01"
status: "執筆中"
""",
        encoding="utf-8",
    )

    character_file = project_path / "キャラクター設定.yaml"
    character_file.write_text(
        """
characters:
  テスト太郎:
    attributes:
      hair_color: "黒髪"
      personality: "真面目"
      age: "16歳"
""",
        encoding="utf-8",
    )

    return project_path


@pytest.fixture
def real_yaml_episode_repository(integration_project_setup) -> Any:
    """実際のYAMLエピソードリポジトリ"""
    return YamlEpisodeRepository(integration_project_setup)


@pytest.fixture
def real_yaml_project_repository(integration_project_setup) -> Any:
    """実際のYAMLプロジェクト情報リポジトリ"""
    return YamlProjectInfoRepository(integration_project_setup)
