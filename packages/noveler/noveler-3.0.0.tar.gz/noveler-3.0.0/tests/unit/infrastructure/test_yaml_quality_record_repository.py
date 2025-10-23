#!/usr/bin/env python3
# File: tests/unit/infrastructure/test_yaml_quality_record_repository.py
# Purpose: Verify YAML-based quality repositories manage persistence paths,
#          backups, and transaction orchestration correctly.
# Context: Unit test suite covering infrastructure repositories used by MCP
#          and CLI flows. Exercises path resolution via PathService adapters.
"""Unit tests for YAML-backed quality repositories and transaction helpers."""

from datetime import timedelta

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.domain.entities.quality_record import QualityRecord
from noveler.domain.exceptions import QualityRecordError
from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_check_result import (
    AutoFix,
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.repositories.yaml_quality_record_repository import (
    YamlEpisodeManagementRepository,
    YamlQualityRecordRepository,
    YamlRecordTransactionManager,
    YamlRevisionHistoryRepository,
)


class TestYamlQualityRecordRepository:
    """YAML品質記録リポジトリのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.repository = YamlQualityRecordRepository(self.test_dir)

    def teardown_method(self) -> None:
        """テストクリーンアップ"""
        self.temp_dir.cleanup()

    def create_sample_quality_record(self, project_name: str = "test_project") -> QualityRecord:
        """テスト用品質記録作成"""
        record = QualityRecord(project_name)

        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[QualityError(type="punctuation", message="記号エラー", line_number=10)],
            warnings=[],
            auto_fixes=[AutoFix(type="punctuation_fix", description="記号修正", count=1)],
        )

        record.add_quality_check_result(result)
        return record

    def test_find_by_project_file_not_exists(self) -> None:
        """存在しないプロジェクトファイルの場合はNoneを返す"""
        result = self.repository.find_by_project("nonexistent_project")
        assert result is None

    def test_save_new_quality_record(self) -> None:
        """新規品質記録の保存"""
        record = self.create_sample_quality_record()

        # 保存実行
        self.repository.save(record)

        # ファイルが作成されたことを確認
        path_service = create_path_service(self.test_dir / "test_project")
        file_path = path_service.get_quality_record_file()
        assert file_path.exists()

        # ファイル内容の確認
        with Path(file_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["metadata"]["project_name"] == "test_project"
        assert data["metadata"]["entry_count"] == 1
        assert len(data["quality_checks"]) == 1
        assert data["quality_checks"][0]["episode_number"] == 1

    def test_find_by_project_existing_file(self) -> None:
        """既存ファイルから品質記録を読み込み"""
        # まず保存
        original_record = self.create_sample_quality_record()
        self.repository.save(original_record)

        # 読み込み
        loaded_record = self.repository.find_by_project("test_project")

        assert loaded_record is not None
        assert loaded_record.project_name == "test_project"
        assert loaded_record.entry_count == 1

        # エントリ内容の確認
        latest_entry = loaded_record.get_latest_for_episode(1)
        assert latest_entry is not None
        assert latest_entry.quality_result.episode_number == 1

    def test_save_update_existing_record(self) -> None:
        """既存記録の更新"""
        # 初回保存
        record = self.create_sample_quality_record()
        self.repository.save(record)

        # 新しい結果を追加
        new_result = QualityCheckResult(
            episode_number=2,
            timestamp=project_now().datetime + timedelta(minutes=1),
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(87.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        record.add_quality_check_result(new_result)

        # 更新保存
        self.repository.save(record)

        # 再読み込みして確認
        loaded_record = self.repository.find_by_project("test_project")
        assert loaded_record.entry_count == 2
        assert loaded_record.get_latest_for_episode(2) is not None

    def test_file_permission_error_handling(self) -> None:
        """ファイル権限エラーの処理"""
        record = self.create_sample_quality_record()

        # ディレクトリを読み取り専用に設定(Windows環境での権限制御をシミュレート)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(QualityRecordError, match="Failed to save quality record"):
                self.repository.save(record)

    def test_yaml_parsing_error_handling(self) -> None:
        """不正なYAMLファイルの処理"""
        # 不正なYAMLファイルを作成
        path_service = create_path_service(self.test_dir / "test_project")
        file_path = path_service.get_quality_record_file()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with Path(file_path).open("w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [unclosed")

        # パースエラーが適切に処理されることを確認
        with pytest.raises(QualityRecordError, match="Failed to parse quality record file"):
            self.repository.find_by_project("test_project")

    def test_backup_creation_on_save(self) -> None:
        """保存時のバックアップ作成"""
        record = self.create_sample_quality_record()

        # 初回保存
        self.repository.save(record)

        # ファイルを変更して再保存
        new_result = QualityCheckResult(
            episode_number=2,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(87.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        record.add_quality_check_result(new_result)

        # 再保存(バックアップが作成される)
        self.repository.save(record)

        # バックアップファイルの存在確認
        path_service = create_path_service(self.test_dir / "test_project")
        backup_dir = path_service.get_management_dir() / ".backup"
        backup_files = list(backup_dir.glob("品質記録_*.yaml"))
        assert len(backup_files) >= 1


class TestYamlEpisodeManagementRepository:
    """YAML話数管理リポジトリのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.repository = YamlEpisodeManagementRepository()

    def teardown_method(self) -> None:
        """テストクリーンアップ"""
        self.temp_dir.cleanup()

    def test_update_episode_status_new_episode(self) -> None:
        """新規エピソードの状態更新"""
        project_path = self.test_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        path_service = create_path_service(project_path)
        episode_file = path_service.get_episode_management_file()
        episode_file.parent.mkdir(parents=True, exist_ok=True)

        # 初期ファイル作成
        initial_data = {
            "episodes": [],
            "metadata": {"last_updated": project_now().datetime.isoformat(), "total_episodes": 0},
        }

        with Path(episode_file).open("w", encoding="utf-8") as f:
            yaml.dump(initial_data, f, default_flow_style=False, allow_unicode=True)

        # 品質チェック結果
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        # 更新実行
        self.repository.update_quality_scores(project_path, 1, quality_result)

        # 結果確認
        with Path(episode_file).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["episodes"]) == 1
        assert data["episodes"][0]["episode_number"] == 1
        assert data["episodes"][0]["quality_score"] == 83.75  # 平均
        assert data["metadata"]["total_episodes"] == 1

    def test_update_episode_status_existing_episode(self) -> None:
        """既存エピソードの状態更新"""
        project_path = self.test_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        path_service = create_path_service(project_path)
        episode_file = path_service.get_episode_management_file()
        episode_file.parent.mkdir(parents=True, exist_ok=True)

        # 既存データ
        existing_data = {
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "テストエピソード",
                    "quality_score": 80.0,
                    "last_check": (project_now().datetime - timedelta(days=1)).isoformat(),
                    "status": "draft",
                }
            ],
            "metadata": {"last_updated": (project_now().datetime - timedelta(days=1)).isoformat(), "total_episodes": 1},
        }

        with Path(episode_file).open("w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True)

        # 新しい品質チェック結果
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(87.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        # 更新実行
        self.repository.update_quality_scores(project_path, 1, quality_result)

        # 結果確認
        with Path(episode_file).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["episodes"]) == 1
        assert data["episodes"][0]["quality_score"] == 87.5  # 新しい平均
        assert data["metadata"]["total_episodes"] == 1


class TestYamlRevisionHistoryRepository:
    """YAML改訂履歴リポジトリのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.repository = YamlRevisionHistoryRepository()

    def teardown_method(self) -> None:
        """テストクリーンアップ"""
        self.temp_dir.cleanup()

    def test_add_quality_check_revision_new_file(self) -> None:
        """新規改訂履歴の追加"""
        project_path = self.test_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        path_service = create_path_service(project_path)
        revision_file = path_service.get_revision_history_file()

        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[QualityError(type="punctuation", message="記号エラー", line_number=10)],
            warnings=[],
            auto_fixes=[AutoFix(type="punctuation_fix", description="記号修正", count=1)],
        )

        # 改訂履歴追加
        self.repository.add_quality_revision(project_path, quality_result)

        # 結果確認
        assert revision_file.exists()

        with Path(revision_file).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["revisions"]) == 1
        revision = data["revisions"][0]
        assert revision["episode_number"] == 1
        assert revision["revision_type"] == "quality_check"
        assert revision["quality_score"] == 83.75
        assert revision["error_count"] == 1
        assert revision["auto_fix_count"] == 1

    def test_add_quality_check_revision_existing_file(self) -> None:
        """既存改訂履歴への追加"""
        project_path = self.test_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        path_service = create_path_service(project_path)
        revision_file = path_service.get_revision_history_file()
        revision_file.parent.mkdir(parents=True, exist_ok=True)

        # 既存データ
        existing_data = {
            "revisions": [
                {
                    "id": "rev-001",
                    "timestamp": (project_now().datetime - timedelta(days=1)).isoformat(),
                    "episode_number": 1,
                    "revision_type": "manual_edit",
                    "description": "手動編集",
                }
            ],
            "metadata": {
                "total_revisions": 1,
                "last_updated": (project_now().datetime - timedelta(days=1)).isoformat(),
            },
        }

        with Path(revision_file).open("w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True)

        quality_result = QualityCheckResult(
            episode_number=2,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(87.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        # 新しい改訂履歴追加
        self.repository.add_quality_revision(project_path, quality_result)

        # 結果確認
        with Path(revision_file).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["revisions"]) == 2
        assert data["metadata"]["total_revisions"] == 2

        # 新しい改訂履歴が先頭に追加されることを確認
        latest_revision = data["revisions"][0]
        assert latest_revision["episode_number"] == 2
        assert latest_revision["revision_type"] == "quality_check"


class TestYamlRecordTransactionManager:
    """YAML記録トランザクションマネージャーのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        self.quality_repo = Mock()
        self.episode_repo = Mock()
        self.revision_repo = Mock()

        self.transaction_manager = YamlRecordTransactionManager(
            quality_record_repository=self.quality_repo,
            episode_management_repository=self.episode_repo,
            revision_history_repository=self.revision_repo,
        )

    def teardown_method(self) -> None:
        """テストクリーンアップ"""
        self.temp_dir.cleanup()

    def test_successful_transaction(self) -> None:
        """正常なトランザクション実行"""
        record = QualityRecord("test_project")
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        project_path = self.test_dir / "test_project"

        # トランザクション実行
        with self.transaction_manager.begin_transaction() as transaction:
            transaction.update_quality_record(record)
            transaction.update_episode_management(project_path, 1, quality_result)
            transaction.update_revision_history(project_path, quality_result)
            transaction.commit()

        # リポジトリメソッドが呼ばれたことを確認
        self.quality_repo.save.assert_called_once_with(record)
        self.episode_repo.update_quality_scores.assert_called_once_with(project_path, 1, quality_result)
        self.revision_repo.add_quality_revision.assert_called_once_with(project_path, quality_result)

    def test_transaction_rollback_on_error(self) -> None:
        """エラー時のトランザクションロールバック"""
        record = QualityRecord("test_project")
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        project_path = self.test_dir / "test_project"

        # episode_repoでエラーを発生させる
        self.episode_repo.update_quality_scores.side_effect = Exception("Episode update failed")

        # トランザクション実行(エラーが発生)
        with pytest.raises(Exception, match="Episode update failed"):
            with self.transaction_manager.begin_transaction() as transaction:
                transaction.update_quality_record(record)
                transaction.update_episode_management(project_path, 1, quality_result)
                transaction.update_revision_history(project_path, quality_result)
                transaction.commit()

        # ロールバックにより、他の操作も実行されないことを確認
        self.revision_repo.add_quality_revision.assert_not_called()

    def test_transaction_context_manager(self) -> None:
        """トランザクションのコンテキストマネージャー機能"""
        record = QualityRecord("test_project")

        # 正常終了の場合
        with self.transaction_manager.begin_transaction() as transaction:
            transaction.update_quality_record(record)
            # コミットを明示的に呼ばない場合、自動コミット

        self.quality_repo.save.assert_called_once()

    def test_transaction_explicit_rollback(self) -> None:
        """明示的なロールバック"""
        record = QualityRecord("test_project")

        with self.transaction_manager.begin_transaction() as transaction:
            transaction.update_quality_record(record)
            # 何らかの理由でロールバック
            transaction.rollback()

        # ロールバック後は実際の保存操作は行われない
        self.quality_repo.save.assert_not_called()
