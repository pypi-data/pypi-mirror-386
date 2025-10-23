#!/usr/bin/env python3
"""A31自動修正システムの統合テスト

SPEC-QUALITY-001に基づくA31自動修正システムの統合テスト
"""

import pytest
import yaml

from noveler.application.use_cases.a31_auto_fix_use_case import A31AutoFixUseCase
from noveler.domain.services.a31_auto_fix_service import A31AutoFixService
from noveler.domain.services.a31_evaluation_service import A31EvaluationService
from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.infrastructure.repositories.yaml_a31_checklist_repository import YamlA31ChecklistRepository
from noveler.infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository
from noveler.infrastructure.repositories.yaml_project_repository import YamlProjectRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service
from tests.test_helpers import create_test_project_structure
from tests.unit.infrastructure.test_base import BaseIntegrationTestCase


@pytest.mark.spec("SPEC-QUALITY-001")
class TestA31AutoFixIntegration(BaseIntegrationTestCase):
    """A31自動修正システムの統合テスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        get_common_path_service()
        super().setup_method()

        # プロジェクト構造を作成
        self.guide_root = self.test_root / "guide"
        self.projects_root = self.test_root / "projects"
        self.test_project_root = self.projects_root / "テストプロジェクト"

        # ディレクトリ構造を作成
        self.guide_root.mkdir(parents=True)
        self.test_project_root.mkdir(parents=True)
        create_test_project_structure(self.test_project_root)

        # テンプレートディレクトリとファイルを作成
        templates_dir = self.guide_root / "templates"
        templates_dir.mkdir()

        template_data = {
            "metadata": {
                "checklist_name": "A31_原稿執筆チェックリスト",
                "version": "2.1",
                "target_episode": None,
                "target_title": None,
                "created_date": None,
            },
            "checklist_items": {
                "Phase4_品質チェック段階": [
                    {
                        "id": "A31-045",
                        "item": "段落頭の字下げを確認",
                        "status": False,
                        "required": True,
                        "type": "format_check",
                        "auto_fix_supported": True,
                        "auto_fix_level": "safe",
                        "auto_fix_applied": False,
                        "fix_details": [],
                    },
                    {
                        "id": "A31-035",
                        "item": "三点リーダー、ダッシュの使用法を統一",
                        "status": False,
                        "required": True,
                        "type": "style_consistency",
                        "auto_fix_supported": True,
                        "auto_fix_level": "safe",
                        "auto_fix_applied": False,
                        "fix_details": [],
                    },
                ]
            },
            "validation_summary": {"total_items": 68, "completed_items": 0, "completion_rate": 0.0},
        }

        template_path = templates_dir / "A31_原稿執筆チェックリストテンプレート.yaml"
        with template_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(template_data, f, allow_unicode=True)

        # テスト用エピソードファイルを作成
        from tests.test_helpers import get_test_manuscript_path

        self.episode_file = get_test_manuscript_path(self.test_project_root, 1, "テスト章")
        episode_content = """これは段落です。
これも段落です。
三点リーダーは...で表現されます。
ダッシュは--で表現されます。"""

        with self.episode_file.Path("w").open(encoding="utf-8") as f:
            f.write(episode_content)

        # リポジトリとサービスを初期化
        self.checklist_repository = YamlA31ChecklistRepository(self.guide_root)
        self.episode_repository = YamlEpisodeRepository(self.test_project_root)
        self.project_repository = YamlProjectRepository(self.projects_root)

        self.evaluation_service = A31EvaluationService()
        self.auto_fix_service = A31AutoFixService()

        # ユースケースを初期化（DI拡張版対応）
        from noveler.presentation.shared.shared_utilities import get_logger_service

        self.use_case = A31AutoFixUseCase(
            logger_service=get_logger_service(),
            # console_service: テスト環境ではNoneでフォールバック
            episode_repository=self.episode_repository,
            project_repository=self.project_repository,
            evaluation_service=self.evaluation_service,
            auto_fix_service=self.auto_fix_service,
            a31_checklist_repository=self.checklist_repository,
        )

    def test_end_to_end_safe_level_auto_fix(self) -> None:
        """エンドツーエンド安全レベル自動修正テスト"""
        # Given: 自動修正が必要なエピソード
        project_name = "テストプロジェクト"
        episode_number = 1
        fix_level = FixLevel.SAFE
        items_to_fix = ["A31-045", "A31-035"]

        # テスト用エピソードファイルを作成
        path_service = get_common_path_service()
        episode_file = self.test_project_root / str(path_service.get_manuscript_dir()) / "第001話_テストエピソード.md"
        episode_content = """# 第1話 テストエピソード

 これはテスト用のエピソードです。

「こんにちは」と彼は言った…
彼女は---そう、答えを知っていたのだ。

 段落の始まりです。
"""
        episode_file.write_text(episode_content, encoding="utf-8")

        # エピソード管理データを作成
        path_service = get_common_path_service()
        episode_management_file = self.test_project_root / str(path_service.get_management_dir()) / "話数管理.yaml"
        episode_management_data = {
            "project_name": project_name,
            "metadata": {"last_updated": "2025-07-28T20:00:00", "total_episodes": 1, "current_phase": "執筆中"},
            "episodes": [
                {
                    "number": 1,
                    "title": "テストエピソード",
                    "status": "draft",
                    "word_count": 100,
                    "created_at": "2025-07-28T20:00:00",
                    "updated_at": "2025-07-28T20:00:00",
                }
            ],
        }
        episode_management_file.write_text(yaml.dump(episode_management_data, allow_unicode=True), encoding="utf-8")

        # When: 自動修正を実行
        session = self.use_case.execute(
            project_name=project_name, episode_number=episode_number, fix_level=fix_level, items_to_fix=items_to_fix
        )

        # Then: 修正セッションが作成される
        assert session is not None
        assert session.fix_level == FixLevel.SAFE
        assert len(session.items_to_fix) == 2

        # エピソード用チェックリストが作成されることを確認
        path_service = get_common_path_service()
        checklist_dir = self.test_project_root / str(path_service.get_management_dir()) / "A31_チェックリスト"
        assert checklist_dir.exists()

        checklist_files = list(checklist_dir.glob("A31_チェックリスト_第001話_*.yaml"))
        assert len(checklist_files) > 0

        # チェックリストファイルの内容を確認
        with checklist_files[0].Path("r").open(encoding="utf-8") as f:
            checklist_data = yaml.safe_load(f)

        assert checklist_data["metadata"]["target_episode"] == 1
        assert checklist_data["metadata"]["target_title"] is not None

    def test_create_episode_checklist_workflow(self) -> None:
        """エピソード用チェックリスト作成ワークフローテスト"""
        # Given: エピソード情報
        episode_number = 2
        episode_title = "新しい冒険"

        # When: エピソード用チェックリストを作成
        checklist_path = self.checklist_repository.create_episode_checklist(
            episode_number, episode_title, self.test_project_root
        )

        # Then: チェックリストファイルが作成される
        assert checklist_path.exists()
        assert f"第{episode_number:03d}話" in checklist_path.name
        assert episode_title in checklist_path.name

        with checklist_path.Path("r").open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["metadata"]["target_episode"] == episode_number
        assert data["metadata"]["target_title"] == episode_title
        assert data["metadata"]["created_date"] is not None

    def test_auto_fixable_items_filtering(self) -> None:
        """自動修正可能項目のフィルタリングテスト"""
        # When: 各レベルの自動修正可能項目を取得
        safe_items = self.checklist_repository.get_auto_fixable_items("safe")
        standard_items = self.checklist_repository.get_auto_fixable_items("standard")
        interactive_items = self.checklist_repository.get_auto_fixable_items("interactive")

        # Then: レベルに応じて適切な項目が取得される
        assert len(safe_items) == 2  # A31-045, A31-035
        assert len(standard_items) == 2  # safe項目 + standard項目
        assert len(interactive_items) == 2  # safe + standard + interactive項目

        # 項目IDの確認
        safe_item_ids = [item.item_id for item in safe_items]
        assert "A31-045" in safe_item_ids
        assert "A31-035" in safe_item_ids

    def test_backup_and_restore_workflow(self) -> None:
        """バックアップ・復元ワークフローテスト"""
        # Given: エピソード用チェックリストを作成
        checklist_path = self.checklist_repository.create_episode_checklist(
            1, "テストエピソード", self.test_project_root
        )

        original_content = checklist_path.read_text(encoding="utf-8")

        # When: バックアップを作成
        backup_path = self.checklist_repository.backup_checklist(checklist_path)

        # Then: バックアップファイルが存在する
        assert backup_path.exists()
        assert "backup_" in backup_path.name

        # チェックリストを変更
        with checklist_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump({"modified": "content"}, f)

        # When: バックアップから復元
        success = self.checklist_repository.restore_checklist(backup_path, checklist_path)

        # Then: 復元が成功し、元の内容に戻る
        assert success is True
        restored_content = checklist_path.read_text(encoding="utf-8")
        assert restored_content == original_content

    def test_project_repository_integration(self) -> None:
        """プロジェクトリポジトリ統合テスト"""
        # Given: プロジェクト名と項目ID
        project_name = "テストプロジェクト"
        item_ids = ["A31-045", "A31-035"]

        # When: プロジェクトリポジトリ経由でチェックリスト項目を取得
        items = self.project_repository.get_checklist_items(project_name, item_ids)

        # Then: 適切な項目が取得される
        assert len(items) == 2
        assert items[0].item_id in item_ids
        assert items[1].item_id in item_ids

    def test_checklist_structure_validation(self) -> None:
        """チェックリスト構造検証テスト"""
        # Given: 正常なチェックリスト
        valid_checklist_path = self.checklist_repository.create_episode_checklist(
            1, "テストエピソード", self.test_project_root
        )

        # When: 構造を検証
        is_valid = self.checklist_repository.validate_checklist_structure(valid_checklist_path)

        # Then: 有効と判定される
        assert is_valid is True

        # Given: 不正な構造のファイル
        invalid_path = self.test_project_root / "invalid.yaml"
        with invalid_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump({"invalid": "structure"}, f)

        # When: 不正な構造を検証
        is_invalid = self.checklist_repository.validate_checklist_structure(invalid_path)

        # Then: 無効と判定される
        assert is_invalid is False

    def test_all_items_retrieval(self) -> None:
        """全項目取得テスト"""
        # When: 全チェックリスト項目を取得
        all_items = self.checklist_repository.get_all_items()

        # Then: テンプレートの全項目が取得される
        assert len(all_items) == 2
        item_ids = [item.item_id for item in all_items]
        assert "A31-045" in item_ids
        assert "A31-035" in item_ids

        # 各項目の詳細を確認
        for item in all_items:
            assert item.item_id.startswith("A31-")
            assert len(item.title) > 0
            assert item.threshold is not None
            assert item.auto_fix_strategy is not None
