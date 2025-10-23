#!/usr/bin/env python3
"""YamlA31ChecklistRepositoryのユニットテスト

SPEC-QUALITY-001に基づくYAML A31チェックリストリポジトリのテスト
"""

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from noveler.domain.entities.a31_checklist_item import ChecklistItemType
from noveler.domain.entities.auto_fix_session import AutoFixSession
from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_fix_result import FixResult
from noveler.domain.value_objects.a31_session_id import SessionId
from noveler.domain.value_objects.a31_threshold import ThresholdType
from noveler.infrastructure.repositories.yaml_a31_checklist_repository import YamlA31ChecklistRepository


@pytest.mark.spec("SPEC-QUALITY-001")
class TestYamlA31ChecklistRepository:
    """YamlA31ChecklistRepositoryのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        # テンポラリディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_dir = self.temp_dir / "templates"
        self.template_dir.mkdir(exist_ok=True)

        # テンプレートファイルを作成
        self.template_path = self.template_dir / "A31_原稿執筆チェックリストテンプレート.yaml"
        self.sample_template = {
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
                        "id": "A31-042",
                        "item": "品質スコア70点以上を達成",
                        "status": False,
                        "required": True,
                        "type": "quality_threshold",
                        "auto_fix_supported": True,
                        "auto_fix_level": "standard",
                    },
                ]
            },
            "validation_summary": {"total_items": 68, "completed_items": 0, "completion_rate": 0.0},
        }

        with self.template_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(self.sample_template, f, allow_unicode=True)

        self.repository = YamlA31ChecklistRepository(self.temp_dir)

    def teardown_method(self) -> None:
        """テスト後処理"""
        # import shutil # Moved to top-level
        shutil.rmtree(self.temp_dir)

    def test_load_template_success(self) -> None:
        """テンプレート読み込み成功テスト"""
        # When: テンプレートを読み込み
        template = self.repository.load_template()

        # Then: 正しく読み込まれることを確認
        assert template["metadata"]["checklist_name"] == "A31_原稿執筆チェックリスト"
        assert template["metadata"]["version"] == "2.1"
        assert "checklist_items" in template
        assert "validation_summary" in template

    def test_load_template_file_not_found(self) -> None:
        """テンプレートファイル未存在テスト"""
        # Given: 存在しないテンプレートパス
        invalid_repo = YamlA31ChecklistRepository(Path("/nonexistent"))

        # When & Then: FileNotFoundErrorが発生することを確認
        with pytest.raises(FileNotFoundError, match="テンプレートファイルが見つかりません"):
            invalid_repo.load_template()

    def test_create_episode_checklist(self) -> None:
        """エピソード用チェックリスト作成テスト"""
        # Given: プロジェクトルートディレクトリ
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        episode_number = 1
        episode_title = "冒険の始まり"

        # When: エピソード用チェックリストを作成
        checklist_path = self.repository.create_episode_checklist(episode_number, episode_title, project_root)

        # Then: ファイルが作成されることを確認
        assert checklist_path.exists()
        assert checklist_path.name == "A31_チェックリスト_第001話_冒険の始まり.yaml"

        # 内容の確認
        with checklist_path.Path("r").open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["metadata"]["target_episode"] == 1
        assert data["metadata"]["target_title"] == "冒険の始まり"
        assert data["metadata"]["created_date"] is not None

    def test_create_episode_checklist_with_invalid_title(self) -> None:
        """不正なタイトルを含むエピソード用チェックリスト作成テスト"""
        # Given: 不正な文字を含むタイトル
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        episode_number = 1
        episode_title = "冒険<>の?始まり"  # 不正な文字を含む

        # When: エピソード用チェックリストを作成
        checklist_path = self.repository.create_episode_checklist(episode_number, episode_title, project_root)

        # Then: 安全な文字に置換されてファイルが作成される
        assert checklist_path.exists()
        assert checklist_path.name == "A31_チェックリスト_第001話_冒険__の_始まり.yaml"

    def test_save_results(self) -> None:
        """修正結果保存テスト"""
        # Given: エピソード用チェックリストファイルを作成
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        checklist_path = self.repository.create_episode_checklist(1, "テストエピソード", project_root)

        # 修正セッションの準備
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/episode.md"),
            fix_level=FixLevel.SAFE,
            items_to_fix=["A31-045"],
        )

        fix_result = FixResult.create_successful_fix(
            item_id="A31-045",
            fix_type="format_indentation",
            changes_made=["段落頭に全角スペース追加: 5箇所"],
            before_score=50.0,
            after_score=100.0,
        )

        session.add_result(fix_result)

        # When: 修正結果を保存
        self.repository.save_results(session, checklist_path)

        # Then: ファイルが更新されることを確認
        with checklist_path.Path("r").open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # A31-045項目の状態が更新されていることを確認
        phase_items = data["checklist_items"]["Phase4_品質チェック段階"]
        a31_045_item = next(item for item in phase_items if item["id"] == "A31-045")

        assert a31_045_item["status"] is True
        assert a31_045_item["auto_fix_applied"] is True
        assert len(a31_045_item["fix_details"]) == 1
        assert "fix_history" in a31_045_item

    def test_get_checklist_items(self) -> None:
        """チェックリスト項目取得テスト"""
        # Given: 取得する項目IDのリスト
        item_ids = ["A31-045", "A31-042"]

        # When: チェックリスト項目を取得
        items = self.repository.get_checklist_items("test_project", item_ids)

        # Then: 指定した項目が取得される
        assert len(items) == 2
        assert items[0].item_id == "A31-045"
        assert items[0].title == "段落頭の字下げを確認"
        assert items[0].item_type == ChecklistItemType.FORMAT_CHECK
        assert items[0].threshold.threshold_type == ThresholdType.PERCENTAGE
        assert items[0].threshold.value == 100.0

    def test_get_all_items(self) -> None:
        """全チェックリスト項目取得テスト"""
        # When: 全チェックリスト項目を取得
        items = self.repository.get_all_items()

        # Then: テンプレートの全項目が取得される
        assert len(items) == 2  # サンプルテンプレートには2項目
        item_ids = [item.item_id for item in items]
        assert "A31-045" in item_ids
        assert "A31-042" in item_ids

    def test_get_all_checklist_items(self) -> None:
        """全チェックリスト項目取得(プロジェクト依存版)テスト"""
        # When: プロジェクト名を指定して全チェックリスト項目を取得
        items = self.repository.get_all_checklist_items("test_project")

        # Then: 全項目が取得される(現在の実装では get_all_items() と同じ)
        assert len(items) == 2
        item_ids = [item.item_id for item in items]
        assert "A31-045" in item_ids
        assert "A31-042" in item_ids

    def test_save_evaluation_results(self) -> None:
        """評価結果保存テスト"""
        # Given: 評価バッチ結果をモック
        from unittest.mock import Mock

        # モック評価結果
        mock_result_1 = Mock()
        mock_result_1.to_dict.return_value = {
            "item_id": "A31-045",
            "category": "format_check",
            "score": 95.0,
            "passed": True,
            "details": "段落字下げ適正",
            "execution_time_ms": 50.0,
        }

        mock_result_2 = Mock()
        mock_result_2.to_dict.return_value = {
            "item_id": "A31-042",
            "category": "quality_threshold",
            "score": 75.0,
            "passed": True,
            "details": "品質スコア達成",
            "execution_time_ms": 30.0,
        }

        # モック評価バッチ
        mock_evaluation_batch = Mock()
        mock_evaluation_batch.total_items = 2
        mock_evaluation_batch.evaluated_items = 2
        mock_evaluation_batch.execution_time_ms = 80.0
        mock_evaluation_batch.get_average_score.return_value = 85.0
        mock_evaluation_batch.get_pass_rate.return_value = 1.0
        mock_evaluation_batch.get_category_statistics.return_value = {
            Mock(value="format_check"): {"count": 1, "pass_rate": 1.0, "average_score": 95.0},
            Mock(value="quality_threshold"): {"count": 1, "pass_rate": 1.0, "average_score": 75.0},
        }
        mock_evaluation_batch.results = {"A31-045": mock_result_1, "A31-042": mock_result_2}

        # When: 評価結果を保存
        saved_path = self.repository.save_evaluation_results("テストプロジェクト", 1, mock_evaluation_batch)

        # Then: ファイルが保存される
        assert saved_path.exists()
        assert "A31_evaluation_" in saved_path.name
        assert "episode_001" in saved_path.name
        assert saved_path.suffix == ".yaml"

        # 保存内容の確認
        with saved_path.Path("r").open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["metadata"]["project_name"] == "テストプロジェクト"
        assert data["metadata"]["episode_number"] == 1
        assert data["metadata"]["total_items"] == 2
        assert data["metadata"]["evaluated_items"] == 2
        assert data["evaluation_results"]["average_score"] == 85.0
        assert data["evaluation_results"]["pass_rate"] == 1.0
        assert "A31-045" in data["evaluation_results"]["item_results"]
        assert "A31-042" in data["evaluation_results"]["item_results"]

    def test_save_evaluation_results_with_invalid_project_name(self) -> None:
        """不正なプロジェクト名での評価結果保存テスト"""
        # Given: 不正な文字を含むプロジェクト名
        from unittest.mock import Mock

        mock_evaluation_batch = Mock()
        mock_evaluation_batch.total_items = 1
        mock_evaluation_batch.evaluated_items = 1
        mock_evaluation_batch.execution_time_ms = 50.0
        mock_evaluation_batch.get_average_score.return_value = 80.0
        mock_evaluation_batch.get_pass_rate.return_value = 1.0
        mock_evaluation_batch.get_category_statistics.return_value = {}
        mock_evaluation_batch.results = {}

        # When: 不正な文字を含むプロジェクト名で保存
        saved_path = self.repository.save_evaluation_results("テスト<>プロジェクト?", 1, mock_evaluation_batch)

        # Then: 安全な文字に置換されてファイルが保存される
        assert saved_path.exists()
        assert "テスト__プロジェクト_" in saved_path.name

    def test_get_auto_fixable_items(self) -> None:
        """自動修正可能項目取得テスト"""
        # When: safe レベルの自動修正可能項目を取得
        safe_items = self.repository.get_auto_fixable_items("safe")

        # Then: safe レベルの項目のみ取得される
        assert len(safe_items) == 1
        assert safe_items[0].item_id == "A31-045"

        # When: standard レベルの自動修正可能項目を取得
        standard_items = self.repository.get_auto_fixable_items("standard")

        # Then: safe + standard レベルの項目が取得される
        assert len(standard_items) == 2
        item_ids = [item.item_id for item in standard_items]
        assert "A31-045" in item_ids
        assert "A31-042" in item_ids

    def test_validate_checklist_structure_valid(self) -> None:
        """チェックリスト構造検証(正常)テスト"""
        # Given: 正常なチェックリストファイル
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        checklist_path = self.repository.create_episode_checklist(1, "テストエピソード", project_root)

        # When: 構造を検証
        is_valid = self.repository.validate_checklist_structure(checklist_path)

        # Then: 有効と判定される
        assert is_valid is True

    def test_validate_checklist_structure_invalid(self) -> None:
        """チェックリスト構造検証(異常)テスト"""
        # Given: 不正な構造のファイル
        invalid_file = self.temp_dir / "invalid.yaml"
        with invalid_file.Path("w").open(encoding="utf-8") as f:
            yaml.dump({"invalid": "structure"}, f)

        # When: 構造を検証
        is_valid = self.repository.validate_checklist_structure(invalid_file)

        # Then: 無効と判定される
        assert is_valid is False

    def test_backup_checklist(self) -> None:
        """チェックリストバックアップテスト"""
        # Given: チェックリストファイル
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        checklist_path = self.repository.create_episode_checklist(1, "テストエピソード", project_root)

        # When: バックアップを作成
        backup_path = self.repository.backup_checklist(checklist_path)

        # Then: バックアップファイルが作成される
        assert backup_path.exists()
        assert "backup_" in backup_path.name
        assert backup_path.suffix == ".yaml"

    def test_restore_checklist(self) -> None:
        """チェックリスト復元テスト"""
        # Given: オリジナルファイルとバックアップファイル
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()

        original_path = self.repository.create_episode_checklist(1, "テストエピソード", project_root)

        backup_path = self.repository.backup_checklist(original_path)

        # オリジナルファイルを変更
        with original_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump({"modified": "content"}, f)

        # When: バックアップから復元
        success = self.repository.restore_checklist(backup_path, original_path)

        # Then: 復元が成功し、元の内容に戻る
        assert success is True

        with original_path.Path("r").open(encoding="utf-8") as f:
            restored_data = yaml.safe_load(f)

        assert "metadata" in restored_data
        assert restored_data["metadata"]["target_episode"] == 1

    def test_backup_checklist_file_not_found(self) -> None:
        """存在しないファイルのバックアップテスト"""
        # Given: 存在しないファイルパス
        nonexistent_path = self.temp_dir / "nonexistent.yaml"

        # When & Then: FileNotFoundErrorが発生することを確認
        with pytest.raises(FileNotFoundError, match="バックアップ対象ファイルが見つかりません"):
            self.repository.backup_checklist(nonexistent_path)

    def test_restore_checklist_backup_not_found(self) -> None:
        """存在しないバックアップからの復元テスト"""
        # Given: 存在しないバックアップファイル
        nonexistent_backup = self.temp_dir / "nonexistent_backup.yaml"
        target_path = self.temp_dir / "target.yaml"

        # When: 復元を試行
        success = self.repository.restore_checklist(nonexistent_backup, target_path)

        # Then: 復元が失敗する
        assert success is False
