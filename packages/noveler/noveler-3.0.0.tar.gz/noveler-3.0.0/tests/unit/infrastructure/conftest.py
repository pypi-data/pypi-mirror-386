"""Tests.tests.unit.infrastructure.conftest
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from noveler.presentation.shared.shared_utilities import get_common_path_service

#!/usr/bin/env python3
"""Infrastructure層テスト用共通フィクスチャ

リポジトリ実装やアダプターテストで使用する共通フィクスチャ群
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """各テスト用の一時ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="novel_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_project_dir(temp_dir) -> Path:
    """一時プロジェクトディレクトリ"""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()

    # 基本的なプロジェクト構造を作成
    path_service = get_common_path_service()
    (project_dir / str(path_service.get_manuscript_dir())).mkdir()
    (project_dir / "プロジェクト設定.yaml").write_text(
        "title: テストプロジェクト\nauthor: テスト作者\n", encoding="utf-8"
    )

    return project_dir


@pytest.fixture
def yaml_test_data() -> dict[str, Any]:
    """YAML テスト用データ"""
    return {
        "test_episode": {"episode_number": 1, "title": "テストエピソード", "word_count": 3000, "status": "draft"},
        "test_project": {"title": "テストプロジェクト", "author": "テスト作者", "genre": "ファンタジー"},
    }
