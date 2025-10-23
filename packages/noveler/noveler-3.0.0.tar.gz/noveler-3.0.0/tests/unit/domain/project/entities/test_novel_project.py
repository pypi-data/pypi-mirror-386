#!/usr/bin/env python3
"""小説プロジェクトエンティティのテスト

NovelProjectエンティティの動作を検証するユニットテスト
DDD準拠・パフォーマンス最適化対応版
"""

from datetime import datetime
from pathlib import Path

import pytest
pytestmark = pytest.mark.project

from noveler.domain.entities.novel_project import NovelProject
from noveler.domain.value_objects.project_info import ProjectInfo


class TestNovelProject:
    """NovelProject テストクラス"""

    @pytest.fixture
    def project_info(self):
        """プロジェクト情報の作成"""
        return ProjectInfo(
            title="テストプロジェクト",
            author="Test Author",
            genre="fantasy",
            description="テスト用の小説プロジェクト",
            target_word_count=50000
        )

    @pytest.fixture
    def novel_project(self, project_info):
        """NovelProject インスタンス"""
        return NovelProject(
            name="test_novel",
            project_info=project_info,
            project_path=Path("/test/projects/test_novel")
        )

    @pytest.mark.spec("SPEC-NOVEL_PROJECT-NOVEL_PROJECT_CREATI")
    def test_novel_project_creation(self, novel_project):
        """小説プロジェクト作成テスト"""
        # 検証
        assert novel_project is not None
        assert novel_project.name == "test_novel"
        assert novel_project.project_info.title == "テストプロジェクト"
        assert novel_project.project_info.author == "Test Author"
        assert novel_project.project_path == Path("/test/projects/test_novel")

    @pytest.mark.spec("SPEC-NOVEL_PROJECT-NOVEL_PROJECT_VALIDA")
    def test_novel_project_validation(self, project_info):
        """プロジェクト検証テスト"""
        # 無効な名前でプロジェクト作成を試行
        with pytest.raises(ValueError, match="プロジェクト名が無効です"):
            NovelProject(
                name="",  # 空の名前
                project_info=project_info,
                project_path=Path("/test")
            )

        # 無効なパスでプロジェクト作成を試行
        with pytest.raises(ValueError, match="プロジェクトパスが無効です"):
            NovelProject(
                name="valid_name",
                project_info=project_info,
                project_path=None  # 無効なパス
            )

    @pytest.mark.spec("SPEC-NOVEL_PROJECT-NOVEL_PROJECT_METADA")
    def test_novel_project_metadata(self, novel_project):
        """プロジェクトメタデータテスト"""
        # メタデータの設定
        novel_project.set_metadata("created_at", datetime.now())
        novel_project.set_metadata("version", "1.0.0")

        # 検証
        assert novel_project.get_metadata("created_at") is not None
        assert novel_project.get_metadata("version") == "1.0.0"
        assert novel_project.get_metadata("non_existent") is None

    @pytest.mark.spec("SPEC-NOVEL_PROJECT-NOVEL_PROJECT_CONFIG")
    def test_novel_project_configuration(self, novel_project):
        """プロジェクト設定テスト"""
        # 設定の変更
        novel_project.update_configuration({
            "auto_save": True,
            "backup_interval": 300,
            "quality_check": True
        })

        # 検証
        config = novel_project.get_configuration()
        assert config is not None
        assert config.get("auto_save") is True
        assert config.get("backup_interval") == 300
        assert config.get("quality_check") is True
