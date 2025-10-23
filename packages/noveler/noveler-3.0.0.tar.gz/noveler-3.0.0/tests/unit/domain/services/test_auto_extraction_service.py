#!/usr/bin/env python3
"""自動抽出ドメインサービスのテスト

TDD原則に基づく単体テスト


仕様書: SPEC-DOMAIN-SERVICES
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from noveler.domain.entities.file_change_event import FileChangeEvent, FileChangeType
from noveler.domain.entities.proper_noun_collection import ProperNounCollection
from noveler.domain.services.auto_extraction_service import AutoExtractionService, ExtractionResult


class TestExtractionResult:
    """ExtractionResultのテスト"""

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-EXTRACTION_RESULT_SU")
    def test_extraction_result_success_no_errors(self) -> None:
        """成功・エラーなしの抽出結果"""
        terms = ProperNounCollection({"綾瀬カノン", "律", "BUG.CHURCH"})
        result = ExtractionResult(
            success=True,
            extracted_terms=terms,
            processed_files=["キャラクター.yaml", "世界観.yaml"],
            errors=[],
        )

        assert result.success is True
        assert result.has_errors is False
        assert result.partial_success is False
        assert len(result.extracted_terms.to_set()) == 3
        assert len(result.processed_files) == 2
        assert len(result.errors) == 0

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-EXTRACTION_RESULT_SU")
    def test_extraction_result_success_with_errors(self) -> None:
        """成功・エラーありの抽出結果(部分成功)"""
        terms = ProperNounCollection({"綾瀬カノン", "律"})
        result = ExtractionResult(
            success=True,
            extracted_terms=terms,
            processed_files=["キャラクター.yaml"],
            errors=["世界観.yaml: ファイルが見つかりません"],
        )

        assert result.success is True
        assert result.has_errors is True
        assert result.partial_success is True
        assert len(result.extracted_terms.to_set()) == 2
        assert len(result.processed_files) == 1
        assert len(result.errors) == 1

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-EXTRACTION_RESULT_FA")
    def test_extraction_result_failure(self) -> None:
        """失敗の抽出結果"""
        terms = ProperNounCollection(set())
        result = ExtractionResult(
            success=False,
            extracted_terms=terms,
            processed_files=[],
            errors=["キャッシュ操作エラー: 権限がありません"],
        )

        assert result.success is False
        assert result.has_errors is True
        assert result.partial_success is False
        assert len(result.extracted_terms.to_set()) == 0
        assert len(result.processed_files) == 0
        assert len(result.errors) == 1


class TestAutoExtractionService:
    """AutoExtractionServiceのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.settings_repository = Mock()
        self.cache_repository = Mock()
        self.service = AutoExtractionService(self.settings_repository, self.cache_repository)

    def create_file_change_event(self, file_path: str, change_type: FileChangeType) -> FileChangeEvent:
        """ファイル変更イベントを作成"""

        return FileChangeEvent(
            file_path=file_path,
            change_type=change_type.value,
            timestamp=datetime.fromisoformat("2024-07-16T10:00:00"),
        )

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_empty_changes(self) -> None:
        """空の変更リストの処理"""
        # キャッシュされた用語を設定
        cached_terms = ProperNounCollection({"既存の用語"})
        self.cache_repository.get_cached_terms.return_value = cached_terms

        result = self.service.process_file_changes([])

        assert result.success is True
        assert result.extracted_terms == cached_terms
        assert result.processed_files == []
        assert result.errors == []
        assert result.has_errors is False

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_no_extraction_needed(self) -> None:
        """抽出不要な変更の処理"""
        # 抽出不要なイベントを作成
        event = self.create_file_change_event("test.txt", FileChangeType.MODIFIED)

        # requires_extraction() が False を返すようにモック
        with patch.object(event, "requires_extraction", return_value=False):
            cached_terms = ProperNounCollection({"既存の用語"})
            self.cache_repository.get_cached_terms.return_value = cached_terms

            result = self.service.process_file_changes([event])

            assert result.success is True
            assert result.extracted_terms == cached_terms
            assert result.processed_files == []
            assert result.errors == []

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_successful_extraction(self) -> None:
        """成功した抽出処理"""
        # 抽出が必要なイベントを作成
        event = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.MODIFIED)

        # requires_extraction() が True を返すようにモック
        with patch.object(event, "requires_extraction", return_value=True):
            with patch.object(event, "is_deletion", return_value=False):
                # 設定リポジトリから用語抽出
                self.settings_repository.extract_proper_nouns_from_file.return_value = {"綾瀬カノン", "律"}

                # 既存キャッシュ
                cached_terms = ProperNounCollection({"既存用語"})
                self.cache_repository.get_cached_terms.return_value = cached_terms

                result = self.service.process_file_changes([event])

                assert result.success is True
                assert "綾瀬カノン" in result.extracted_terms.to_set()
                assert "律" in result.extracted_terms.to_set()
                assert result.processed_files == ["キャラクター.yaml"]
                assert result.errors == []

                # キャッシュに保存されたことを確認
                self.cache_repository.save_terms.assert_called_once()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_deletion_event(self) -> None:
        """削除イベントの処理"""
        # 削除イベントを作成
        event = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.DELETED)

        with patch.object(event, "requires_extraction", return_value=True):
            with patch.object(event, "is_deletion", return_value=True):
                cached_terms = ProperNounCollection({"既存用語"})
                self.cache_repository.get_cached_terms.return_value = cached_terms

                result = self.service.process_file_changes([event])

                assert result.success is True
                assert result.processed_files == ["キャラクター.yaml (削除)"]
                assert result.errors == []

                # 削除ファイルからは抽出されない
                self.settings_repository.extract_proper_nouns_from_file.assert_not_called()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_extraction_error(self) -> None:
        """抽出エラーの処理"""
        # 抽出が必要なイベントを作成
        event = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.MODIFIED)

        with patch.object(event, "requires_extraction", return_value=True):
            with patch.object(event, "is_deletion", return_value=False):
                # 抽出時にエラーが発生
                self.settings_repository.extract_proper_nouns_from_file.side_effect = Exception(
                    "ファイル読み取りエラー",
                )

                cached_terms = ProperNounCollection({"既存用語"})
                self.cache_repository.get_cached_terms.return_value = cached_terms

                result = self.service.process_file_changes([event])

                assert result.success is True  # 他のファイルは処理されなくてもキャッシュは返される
                assert result.processed_files == []
                assert len(result.errors) == 1
                assert "キャラクター.yaml: ファイル読み取りエラー" in result.errors[0]

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_multiple_files(self) -> None:
        """複数ファイルの処理"""
        # 複数のイベントを作成
        event1 = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.MODIFIED)
        event2 = self.create_file_change_event("30_設定集/世界観.yaml", FileChangeType.MODIFIED)

        with patch.object(event1, "requires_extraction", return_value=True):
            with patch.object(event1, "is_deletion", return_value=False):
                with patch.object(event2, "requires_extraction", return_value=True):
                    with patch.object(event2, "is_deletion", return_value=False):
                        # 各ファイルから異なる用語を抽出
                        def extract_side_effect(file_path):
                            if "キャラクター" in str(file_path):
                                return {"綾瀬カノン", "律"}
                            if "世界観" in str(file_path):
                                return {"BUG.CHURCH", "渋谷"}
                            return set()

                        self.settings_repository.extract_proper_nouns_from_file.side_effect = extract_side_effect

                        cached_terms = ProperNounCollection(set())
                        self.cache_repository.get_cached_terms.return_value = cached_terms

                        result = self.service.process_file_changes([event1, event2])

                        assert result.success is True
                        all_terms = result.extracted_terms.to_set()
                        assert "綾瀬カノン" in all_terms
                        assert "律" in all_terms
                        assert "BUG.CHURCH" in all_terms
                        assert "渋谷" in all_terms
                        assert len(result.processed_files) == 2
                        assert result.errors == []

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-PROCESS_FILE_CHANGES")
    def test_process_file_changes_cache_error(self) -> None:
        """キャッシュエラーの処理"""
        # 抽出が必要なイベントを作成
        event = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.MODIFIED)

        with patch.object(event, "requires_extraction", return_value=True):
            with patch.object(event, "is_deletion", return_value=False):
                # 抽出は成功
                self.settings_repository.extract_proper_nouns_from_file.return_value = {"綾瀬カノン"}

                # キャッシュ取得は成功
                cached_terms = ProperNounCollection(set())
                self.cache_repository.get_cached_terms.return_value = cached_terms

                # キャッシュ保存でエラー
                self.cache_repository.save_terms.side_effect = Exception("キャッシュ書き込みエラー")

                result = self.service.process_file_changes([event])

                assert result.success is True  # 処理は成功
                assert "綾瀬カノン" in result.extracted_terms.to_set()
                assert result.processed_files == ["キャラクター.yaml"]
                assert len(result.errors) == 1
                assert "キャッシュ操作エラー" in result.errors[0]
                assert result.partial_success is True

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-FORCE_EXTRACT_ALL_SU")
    def test_force_extract_all_success(self) -> None:
        """全体抽出の成功"""
        # 全ファイルから抽出される用語
        all_terms = {"綾瀬カノン", "律", "BUG.CHURCH", "渋谷"}
        self.settings_repository.extract_all_proper_nouns.return_value = all_terms

        result = self.service.force_extract_all()

        assert result.success is True
        assert result.extracted_terms.to_set() == all_terms
        assert result.processed_files == ["全設定ファイル"]
        assert result.errors == []

        # キャッシュに保存されたことを確認
        self.cache_repository.save_terms.assert_called_once()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-FORCE_EXTRACT_ALL_FA")
    def test_force_extract_all_failure(self) -> None:
        """全体抽出の失敗"""
        # 抽出時にエラーが発生
        self.settings_repository.extract_all_proper_nouns.side_effect = Exception("権限エラー")

        result = self.service.force_extract_all()

        assert result.success is False
        assert len(result.extracted_terms.to_set()) == 0
        assert result.processed_files == []
        assert len(result.errors) == 1
        assert "全体抽出エラー: 権限エラー" in result.errors[0]

        # キャッシュ保存は呼ばれない
        self.cache_repository.save_terms.assert_not_called()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-GET_CURRENT_TERMS")
    def test_get_current_terms(self) -> None:
        """現在の用語取得"""
        cached_terms = ProperNounCollection({"既存用語1", "既存用語2"})
        self.cache_repository.get_cached_terms.return_value = cached_terms

        result = self.service.get_current_terms()

        assert result == cached_terms
        self.cache_repository.get_cached_terms.assert_called_once()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-CLEAR_CACHE_SUCCESS")
    def test_clear_cache_success(self) -> None:
        """キャッシュクリアの成功"""
        result = self.service.clear_cache()

        assert result is True
        self.cache_repository.clear_cache.assert_called_once()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-CLEAR_CACHE_FAILURE")
    def test_clear_cache_failure(self) -> None:
        """キャッシュクリアの失敗"""
        self.cache_repository.clear_cache.side_effect = Exception("権限エラー")

        result = self.service.clear_cache()

        assert result is False
        self.cache_repository.clear_cache.assert_called_once()

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-COMPLEX_WORKFLOW_SCE")
    def test_complex_workflow_scenario(self) -> None:
        """複雑なワークフローシナリオ"""
        # 複数の変更イベント: 追加、変更、削除
        event1 = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.ADDED)
        event2 = self.create_file_change_event("30_設定集/世界観.yaml", FileChangeType.MODIFIED)
        event3 = self.create_file_change_event("30_設定集/魔法システム.yaml", FileChangeType.DELETED)

        # 各イベントの動作を設定
        with patch.object(event1, "requires_extraction", return_value=True):
            with patch.object(event1, "is_deletion", return_value=False):
                with patch.object(event2, "requires_extraction", return_value=True):
                    with patch.object(event2, "is_deletion", return_value=False):
                        with patch.object(event3, "requires_extraction", return_value=True):
                            with patch.object(event3, "is_deletion", return_value=True):
                                # 抽出結果を設定
                                def extract_side_effect(file_path):
                                    if "キャラクター" in str(file_path):
                                        return {"綾瀬カノン", "律"}
                                    if "世界観" in str(file_path):
                                        return {"BUG.CHURCH", "渋谷"}
                                    return set()

                                self.settings_repository.extract_proper_nouns_from_file.side_effect = (
                                    extract_side_effect
                                )

                                # 既存キャッシュ
                                cached_terms = ProperNounCollection({"既存用語"})
                                self.cache_repository.get_cached_terms.return_value = cached_terms

                                result = self.service.process_file_changes([event1, event2, event3])

                                assert result.success is True

                                # 抽出された用語を確認
                                all_terms = result.extracted_terms.to_set()
                                assert "綾瀬カノン" in all_terms
                                assert "律" in all_terms
                                assert "BUG.CHURCH" in all_terms
                                assert "渋谷" in all_terms

                                # 処理されたファイルを確認
                                assert "キャラクター.yaml" in result.processed_files
                                assert "世界観.yaml" in result.processed_files
                                assert "魔法システム.yaml (削除)" in result.processed_files

                                assert result.errors == []
                                assert result.has_errors is False

    @pytest.mark.spec("SPEC-AUTO_EXTRACTION_SERVICE-MIXED_SUCCESS_AND_FA")
    def test_mixed_success_and_failure_scenario(self) -> None:
        """成功と失敗が混在するシナリオ"""
        # 複数のイベント: 一部成功、一部失敗
        event1 = self.create_file_change_event("30_設定集/キャラクター.yaml", FileChangeType.MODIFIED)
        event2 = self.create_file_change_event("30_設定集/世界観.yaml", FileChangeType.MODIFIED)

        with patch.object(event1, "requires_extraction", return_value=True):
            with patch.object(event1, "is_deletion", return_value=False):
                with patch.object(event2, "requires_extraction", return_value=True):
                    with patch.object(event2, "is_deletion", return_value=False):
                        # 1つ目は成功、2つ目は失敗
                        def extract_side_effect(file_path):
                            if "キャラクター" in str(file_path):
                                return {"綾瀬カノン", "律"}
                            if "世界観" in str(file_path):
                                msg = "ファイル破損"
                                raise Exception(msg)
                            return set()

                        self.settings_repository.extract_proper_nouns_from_file.side_effect = extract_side_effect

                        cached_terms = ProperNounCollection(set())
                        self.cache_repository.get_cached_terms.return_value = cached_terms

                        result = self.service.process_file_changes([event1, event2])

                        assert result.success is True  # 一部成功
                        assert result.has_errors is True
                        assert result.partial_success is True

                        # 成功した分の用語は含まれる
                        all_terms = result.extracted_terms.to_set()
                        assert "綾瀬カノン" in all_terms
                        assert "律" in all_terms

                        # 処理結果を確認
                        assert "キャラクター.yaml" in result.processed_files
                        assert len(result.errors) == 1
                        assert "世界観.yaml: ファイル破損" in result.errors[0]
