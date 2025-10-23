"""同期結果値オブジェクトのテスト

TDD準拠テスト:
    - SyncResult


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.value_objects.sync_result import SyncResult

pytestmark = pytest.mark.vo_smoke



class TestSyncResult:
    """SyncResult値オブジェクトのテストクラス"""

    @pytest.fixture
    def successful_sync_result(self) -> SyncResult:
        """成功した同期結果"""
        return SyncResult(
            success=True, updated_fields=["title", "word_count", "status"], error_message=None, backup_created=True
        )

    @pytest.fixture
    def failed_sync_result(self) -> SyncResult:
        """失敗した同期結果"""
        return SyncResult(
            success=False, updated_fields=[], error_message="ファイルが見つかりません", backup_created=False
        )

    @pytest.fixture
    def partial_sync_result(self) -> SyncResult:
        """部分的な同期結果"""
        return SyncResult(
            success=True,
            updated_fields=["word_count"],
            error_message="一部のフィールドの更新に失敗しました",
            backup_created=True,
        )

    def test_sync_result_creation_successful(self, successful_sync_result: SyncResult) -> None:
        """成功した同期結果作成テスト"""
        assert successful_sync_result.success is True
        assert successful_sync_result.updated_fields == ["title", "word_count", "status"]
        assert successful_sync_result.error_message is None
        assert successful_sync_result.backup_created is True

    def test_sync_result_creation_failed(self, failed_sync_result: SyncResult) -> None:
        """失敗した同期結果作成テスト"""
        assert failed_sync_result.success is False
        assert failed_sync_result.updated_fields == []
        assert failed_sync_result.error_message == "ファイルが見つかりません"
        assert failed_sync_result.backup_created is False

    def test_sync_result_creation_partial(self, partial_sync_result: SyncResult) -> None:
        """部分的な同期結果作成テスト"""
        assert partial_sync_result.success is True
        assert partial_sync_result.updated_fields == ["word_count"]
        assert partial_sync_result.error_message == "一部のフィールドの更新に失敗しました"
        assert partial_sync_result.backup_created is True

    def test_sync_result_creation_minimal(self) -> None:
        """最小パラメータでの同期結果作成テスト"""
        result = SyncResult(success=True, updated_fields=["title"])

        assert result.success is True
        assert result.updated_fields == ["title"]
        assert result.error_message is None
        assert result.backup_created is False

    def test_sync_result_creation_empty_updated_fields(self) -> None:
        """空の更新フィールドでの同期結果作成テスト"""
        result = SyncResult(success=False, updated_fields=[], error_message="処理に失敗しました")

        assert result.success is False
        assert result.updated_fields == []
        assert result.error_message == "処理に失敗しました"
        assert result.backup_created is False

    def test_sync_result_is_successful_true(self, successful_sync_result: SyncResult) -> None:
        """成功判定(True)テスト"""
        assert successful_sync_result.is_successful() is True

    def test_sync_result_is_successful_false(self, failed_sync_result: SyncResult) -> None:
        """成功判定(False)テスト"""
        assert failed_sync_result.is_successful() is False

    def test_sync_result_has_error_true(self, failed_sync_result: SyncResult) -> None:
        """エラー有無判定(True)テスト"""
        assert failed_sync_result.has_error() is True

    def test_sync_result_has_error_false(self, successful_sync_result: SyncResult) -> None:
        """エラー有無判定(False)テスト"""
        assert successful_sync_result.has_error() is False

    def test_sync_result_has_error_with_warning(self, partial_sync_result: SyncResult) -> None:
        """警告付きエラー有無判定テスト"""
        # 成功しているが警告メッセージがある場合
        assert partial_sync_result.has_error() is True

    def test_sync_result_get_updated_field_count_multiple(self, successful_sync_result: SyncResult) -> None:
        """更新フィールド数取得(複数)テスト"""
        assert successful_sync_result.get_updated_field_count() == 3

    def test_sync_result_get_updated_field_count_single(self, partial_sync_result: SyncResult) -> None:
        """更新フィールド数取得(単一)テスト"""
        assert partial_sync_result.get_updated_field_count() == 1

    def test_sync_result_get_updated_field_count_zero(self, failed_sync_result: SyncResult) -> None:
        """更新フィールド数取得(0)テスト"""
        assert failed_sync_result.get_updated_field_count() == 0

    def test_sync_result_get_updated_field_count_large(self) -> None:
        """更新フィールド数取得(大量)テスト"""
        large_fields = [f"field_{i}" for i in range(100)]
        result = SyncResult(success=True, updated_fields=large_fields)

        assert result.get_updated_field_count() == 100

    def test_sync_result_success_and_error_combinations(self) -> None:
        """成功・エラーの組み合わせテスト"""
        # 成功 + エラーメッセージなし
        result1 = SyncResult(success=True, updated_fields=["field1"], error_message=None)
        assert result1.is_successful() is True
        assert result1.has_error() is False

        # 成功 + エラーメッセージあり(警告の場合)
        result2 = SyncResult(
            success=True, updated_fields=["field1"], error_message="警告: 一部のデータが古い可能性があります"
        )

        assert result2.is_successful() is True
        assert result2.has_error() is True

        # 失敗 + エラーメッセージあり
        result3 = SyncResult(success=False, updated_fields=[], error_message="致命的エラー")
        assert result3.is_successful() is False
        assert result3.has_error() is True

        # 失敗 + エラーメッセージなし(技術的には可能だが非推奨)
        result4 = SyncResult(success=False, updated_fields=[], error_message=None)
        assert result4.is_successful() is False
        assert result4.has_error() is False

    def test_sync_result_backup_combinations(self) -> None:
        """バックアップ作成の組み合わせテスト"""
        # 成功 + バックアップ作成
        result1 = SyncResult(success=True, updated_fields=["field1"], backup_created=True)
        assert result1.is_successful() is True
        assert result1.backup_created is True

        # 成功 + バックアップ未作成
        result2 = SyncResult(success=True, updated_fields=["field1"], backup_created=False)
        assert result2.is_successful() is True
        assert result2.backup_created is False

        # 失敗 + バックアップ作成(部分的に処理が進んだ場合)
        result3 = SyncResult(success=False, updated_fields=[], error_message="エラー", backup_created=True)
        assert result3.is_successful() is False
        assert result3.backup_created is True

        # 失敗 + バックアップ未作成
        result4 = SyncResult(success=False, updated_fields=[], error_message="エラー", backup_created=False)
        assert result4.is_successful() is False
        assert result4.backup_created is False

    def test_sync_result_updated_fields_types(self) -> None:
        """更新フィールドの種類テスト"""
        # 一般的なフィールド名
        result1 = SyncResult(success=True, updated_fields=["title", "word_count", "status", "tags", "metadata"])
        assert result1.get_updated_field_count() == 5
        assert "title" in result1.updated_fields
        assert "word_count" in result1.updated_fields

        # 特殊な文字を含むフィールド名
        result2 = SyncResult(
            success=True,
            updated_fields=["field_with_underscore", "field-with-dash", "field.with.dot", "日本語フィールド"],
        )

        assert result2.get_updated_field_count() == 4
        assert "日本語フィールド" in result2.updated_fields

        # 空文字列フィールド(技術的には可能)
        result3 = SyncResult(success=True, updated_fields=["", "valid_field", ""])
        assert result3.get_updated_field_count() == 3
        assert "" in result3.updated_fields

    def test_sync_result_error_message_types(self) -> None:
        """エラーメッセージの種類テスト"""
        # 短いエラーメッセージ
        result1 = SyncResult(success=False, updated_fields=[], error_message="Error")
        assert result1.error_message == "Error"
        assert result1.has_error() is True

        # 長いエラーメッセージ
        long_error = "非常に長いエラーメッセージです。" * 10
        result2 = SyncResult(success=False, updated_fields=[], error_message=long_error)
        assert result2.error_message == long_error
        assert result2.has_error() is True

        # 空文字列エラーメッセージ
        result3 = SyncResult(success=False, updated_fields=[], error_message="")
        assert result3.error_message == ""
        assert result3.has_error() is True

        # 多言語エラーメッセージ
        result4 = SyncResult(
            success=False, updated_fields=[], error_message="Error: ファイルが見つかりません / File not found"
        )

        assert "ファイルが見つかりません" in result4.error_message
        assert "File not found" in result4.error_message

    def test_sync_result_is_frozen(self, successful_sync_result: SyncResult) -> None:
        """同期結果オブジェクトの不変性テスト"""
        with pytest.raises(AttributeError, match=".*"):
            successful_sync_result.success = False  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            successful_sync_result.error_message = "変更後"  # type: ignore

    def test_sync_result_equality(self) -> None:
        """同期結果等価性テスト"""
        result1 = SyncResult(success=True, updated_fields=["title", "status"], error_message=None, backup_created=True)

        result2 = SyncResult(success=True, updated_fields=["title", "status"], error_message=None, backup_created=True)

        result3 = SyncResult(success=False, updated_fields=["title", "status"], error_message=None, backup_created=True)

        assert result1 == result2
        assert result1 != result3

    def test_sync_result_hash(self) -> None:
        """同期結果ハッシュテスト"""
        result1 = SyncResult(success=True, updated_fields=["title"], error_message=None, backup_created=False)

        result2 = SyncResult(success=True, updated_fields=["title"], error_message=None, backup_created=False)

        # 同じ内容のオブジェクトは同じハッシュ値を持つ
        assert hash(result1) == hash(result2)

    def test_sync_result_string_representation(self, successful_sync_result: SyncResult) -> None:
        """同期結果文字列表現テスト"""
        str_repr = str(successful_sync_result)

        # 基本的な情報が含まれていることを確認
        assert "SyncResult" in str_repr or "True" in str_repr

    def test_sync_result_repr(self, failed_sync_result: SyncResult) -> None:
        """同期結果repr表現テスト"""
        repr_str = repr(failed_sync_result)

        # SyncResultクラス名が含まれていることを確認
        assert "SyncResult" in repr_str

    def test_sync_result_edge_cases(self) -> None:
        """同期結果エッジケーステスト"""
        # 重複フィールド名
        result1 = SyncResult(success=True, updated_fields=["title", "title", "status", "title"])
        assert result1.get_updated_field_count() == 4  # 重複も含めてカウント
        assert result1.updated_fields.count("title") == 3

        # 非常に長いフィールド名
        long_field_name = "very_long_field_name_" * 10
        result2 = SyncResult(success=True, updated_fields=[long_field_name])
        assert long_field_name in result2.updated_fields

        # 特殊文字を含むエラーメッセージ
        special_error = "エラー: 特殊文字 @#$%^&*()[]{}|\\:;\"'<>?,./`~"
        result3 = SyncResult(success=False, updated_fields=[], error_message=special_error)
        assert result3.error_message == special_error

    def test_sync_result_field_order_preservation(self) -> None:
        """フィールド順序保持テスト"""
        fields_order = ["z_field", "a_field", "m_field", "b_field"]
        result = SyncResult(success=True, updated_fields=fields_order)

        # 順序が保持されることを確認
        assert result.updated_fields == fields_order
        assert result.updated_fields[0] == "z_field"
        assert result.updated_fields[-1] == "b_field"

    def test_sync_result_large_scale(self) -> None:
        """大規模データテスト"""
        # 1000個のフィールド
        large_fields = [f"field_{i:04d}" for i in range(1000)]
        result = SyncResult(
            success=True, updated_fields=large_fields, error_message="大量データ処理完了", backup_created=True
        )

        assert result.get_updated_field_count() == 1000
        assert result.is_successful() is True
        assert result.has_error() is True  # エラーメッセージがあるため
        assert result.backup_created is True

    def test_sync_result_none_field_handling(self) -> None:
        """Noneフィールド処理テスト"""
        # updated_fieldsにNoneを直接含む(技術的には可能だが推奨されない)
        result = SyncResult(
            success=True,
            updated_fields=[None, "valid_field", None],  # type: ignore
        )

        assert result.get_updated_field_count() == 3
        assert None in result.updated_fields  # type: ignore
        assert "valid_field" in result.updated_fields
