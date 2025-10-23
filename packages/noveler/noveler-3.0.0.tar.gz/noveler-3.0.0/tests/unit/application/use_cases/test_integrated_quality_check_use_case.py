"""Tests.tests.unit.application.use_cases.test_integrated_quality_check_use_case
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import time

import pytest

# IntegratedQualityCheckUseCaseのテスト
#
# TDD+DDD原則に基づくユースケースのテスト
# 仕様書: integrated_quality_check_use_case.spec.md

import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

from noveler.application.use_cases.integrated_quality_check_use_case import (
    IntegratedQualityCheckUseCase,
    QualityCheckRequest,
)
from noveler.domain.entities.quality_check_session import (
    CheckType,
)


class TestIntegratedQualityCheckUseCase:
    """IntegratedQualityCheckUseCaseのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドごとの初期設定"""
        self.quality_evaluation_service = Mock()

        # モックチェッカーの設定
        self.mock_checker = Mock()
        self.mock_checker.execute.return_value = {
            "score": 85.0,
            "issues": [
                {
                    "type": "punctuation",
                    "message": "句読点の重複があります",
                    "severity": "warning",
                    "line_number": 5,
                    "position": 10,
                    "suggestion": "。。 → 。",
                    "auto_fixable": True,
                }
            ],
            "metadata": {"check_duration": 0.5},
            "execution_time": 0.5,
        }

        self.checker_registry = {CheckType.BASIC_STYLE: self.mock_checker}

        self.use_case = IntegratedQualityCheckUseCase(
            quality_evaluation_service=self.quality_evaluation_service, checker_registry=self.checker_registry
        )

    # -----------------------------------------------------------------
    # RED Phase: 失敗するテストを先に書く
    # -----------------------------------------------------------------

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_FILE_N")
    def test_check_quality_file_not_found(self) -> None:
        """TDD RED: ファイル不在エラーのテスト

        存在しないファイルに対してエラーが返されることを確認
        """
        # Given: 存在しないファイルパス
        request = QualityCheckRequest(project_id="test-project", filepath=Path("/nonexistent/file.md"))

        # When: 品質チェックを実行
        response = self.use_case.check_quality(request)

        # Then: エラーレスポンスを返す
        assert response.success is False
        assert response.error_message == "ファイルが見つかりません: /nonexistent/file.md"
        assert response.session_id is None
        assert response.total_score is None

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_SUCCES")
    def test_check_quality_success_basic_flow(self) -> None:
        """TDD RED→GREEN: 基本的な品質チェック成功のテスト

        正常な入力で品質チェックが成功することを確認
        """
        # Given: 一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("これはテスト用の小説原稿です。\n主人公は朝早く起きました。")
            temp_path = Path(f.name)

        try:
            # Given: 品質チェックリクエスト
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=[CheckType.BASIC_STYLE], verbose=True
            )

            # Given: セッション作成のモック
            with patch("uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = uuid.UUID("12345678-1234-5678-9abc-123456789abc")

                # When: 品質チェックを実行
                response = self.use_case.check_quality(request)

            # Then: 成功レスポンスを返す
            assert response.success is True
            assert response.session_id == "12345678-1234-5678-9abc-123456789abc"
            assert response.total_score is not None
            assert response.grade is not None
            assert response.check_results is not None
            assert len(response.check_results) == 1
            assert response.issues is not None
            assert response.error_message is None

            # Then: チェッカーが呼ばれた
            self.mock_checker.execute.assert_called_once()
            call_args = self.mock_checker.execute.call_args[0][0]
            assert "これはテスト用の小説原稿です。" in call_args["content"]
            assert call_args["filepath"] == str(temp_path)

        finally:
            # クリーンアップ
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_WITH_A")
    def test_check_quality_with_auto_fix(self) -> None:
        """TDD RED: 自動修正機能のテスト

        auto_fix=Trueの場合に修正後内容が返されることを確認
        """
        # Given: 修正対象を含む一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("句読点の重複テストです。。\n")
            temp_path = Path(f.name)

        try:
            # Given: 自動修正付きリクエスト
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=[CheckType.BASIC_STYLE], auto_fix=True
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 自動修正後の内容が返される
            assert response.success is True
            assert response.auto_fixed_content is not None
            assert "。。" not in response.auto_fixed_content  # 重複句読点が修正されている
            assert response.auto_fixed_content == "句読点の重複テストです。\n"

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_MULTIP")
    def test_check_quality_multiple_check_types(self) -> None:
        """TDD RED: 複数チェックタイプのテスト

        複数のチェッカーが実行されることを確認
        """
        # Given: 複数チェッカーの設定
        mock_structure_checker = Mock()
        mock_structure_checker.execute.return_value = {
            "score": 75.0,
            "issues": [
                {"type": "composition", "message": "起承転結が不明確です", "severity": "info", "auto_fixable": False}
            ],
            "execution_time": 0.3,
        }

        self.checker_registry[CheckType.COMPOSITION] = mock_structure_checker

        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("複数チェックのテスト原稿です。")
            temp_path = Path(f.name)

        try:
            # Given: 複数チェックタイプのリクエスト
            request = QualityCheckRequest(
                project_id="test-project",
                filepath=temp_path,
                check_types=[CheckType.BASIC_STYLE, CheckType.COMPOSITION],
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 両方のチェッカーが実行される
            assert response.success is True
            assert len(response.check_results) == 2

            # Then: 各チェッカーが呼ばれた
            self.mock_checker.execute.assert_called_once()
            mock_structure_checker.execute.assert_called_once()

            # Then: 問題が両方から集約されている
            assert len(response.issues) == 2
            issue_types = {issue["type"] for issue in response.issues}
            assert "punctuation" in issue_types
            assert "composition" in issue_types

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_CHECKE")
    def test_check_quality_checker_error_handling(self) -> None:
        """TDD RED: チェッカーエラーのハンドリングテスト

        個別チェッカーでエラーが発生しても処理が継続されることを確認
        """
        # Given: エラーを発生させるチェッカー
        error_checker = Mock()
        error_checker.execute.side_effect = Exception("チェッカー内部エラー")
        self.checker_registry[CheckType.COMPOSITION] = error_checker

        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("エラーハンドリングテスト原稿")
            temp_path = Path(f.name)

        try:
            # Given: 複数チェックタイプのリクエスト
            request = QualityCheckRequest(
                project_id="test-project",
                filepath=temp_path,
                check_types=[CheckType.BASIC_STYLE, CheckType.COMPOSITION],
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 成功レスポンス(部分的な失敗でも継続)
            assert response.success is True
            assert len(response.check_results) == 2

            # Then: エラーチェッカーの結果にエラー情報が含まれる
            error_result = None
            for result in response.check_results:
                if result["check_type"] == "composition":
                    error_result = result
                    break

            assert error_result is not None
            assert error_result["score"] == 0.0
            assert len(error_result["issues"]) == 1
            assert "チェッカーエラー" in error_result["issues"][0]["message"]

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_NO_CHE")
    def test_check_quality_no_check_types_specified(self) -> None:
        """TDD RED: チェックタイプ未指定時のテスト

        check_typesがNoneの場合、全チェックタイプが実行されることを確認
        """
        # Given: 全チェックタイプのチェッカーを設定
        for check_type in CheckType:
            if check_type not in self.checker_registry:
                mock_checker = Mock()
                mock_checker.execute.return_value = {"score": 80.0, "issues": [], "execution_time": 0.1}
                self.checker_registry[check_type] = mock_checker

        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("全チェックタイプテスト原稿")
            temp_path = Path(f.name)

        try:
            # Given: チェックタイプ未指定のリクエスト
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=None
            )  # 全チェックタイプ実行

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 全チェックタイプが実行される
            assert response.success is True
            assert len(response.check_results) == len(CheckType)

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-GET_SESSION_SUMMARY_")
    def test_get_session_summary_success(self) -> None:
        """TDD RED: セッションサマリー取得のテスト

        有効なセッションIDでサマリーが取得できることを確認
        """
        # Given: 品質チェックを実行してセッション作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("セッションテスト原稿")
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(project_id="test-project", filepath=temp_path)

            response = self.use_case.check_quality(request)
            session_id = response.session_id

            # When: セッションサマリーを取得
            summary = self.use_case.get_session_summary(session_id)

            # Then: サマリーが取得できる
            assert summary is not None
            assert isinstance(summary, dict)

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-GET_SESSION_SUMMARY_")
    def test_get_session_summary_not_found(self) -> None:
        """TDD RED: 存在しないセッションIDのテスト

        存在しないセッションIDでNoneが返されることを確認
        """
        # Given: 存在しないセッションID
        nonexistent_session_id = "nonexistent-session-id"

        # When: セッションサマリーを取得
        summary = self.use_case.get_session_summary(nonexistent_session_id)

        # Then: Noneが返される
        assert summary is None

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-BULK_CHECK_SUCCESS")
    def test_bulk_check_success(self) -> None:
        """TDD RED: 一括チェック成功のテスト

        複数ファイルの一括チェックが正常に動作することを確認
        """
        # Given: 複数の一時ファイルを作成
        temp_files = []
        temp_dir = Path(tempfile.mkdtemp())

        try:
            for i in range(3):
                temp_file = temp_dir / f"test_{i}.md"
                temp_file.write_text(f"一括テスト原稿{i}", encoding="utf-8")
                temp_files.append(temp_file)

            # Given: ファイルパターン
            file_patterns = [str(temp_dir / "*.md")]

            # When: 一括チェックを実行
            with patch.object(Path, "glob") as mock_glob:
                mock_glob.return_value = temp_files
                responses = self.use_case.bulk_check(project_id="test-project", file_patterns=file_patterns)

            # Then: 全ファイルの結果が返される
            assert len(responses) == 3
            for response in responses:
                assert response.success is True
                assert response.session_id is not None

        finally:
            # クリーンアップ
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            temp_dir.rmdir()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-BULK_CHECK_EMPTY_PAT")
    def test_bulk_check_empty_patterns(self) -> None:
        """TDD RED: 空のファイルパターンのテスト

        空のファイルパターンで空リストが返されることを確認
        """
        # Given: 空のファイルパターン
        file_patterns = []

        # When: 一括チェックを実行
        responses = self.use_case.bulk_check(project_id="test-project", file_patterns=file_patterns)

        # Then: 空リストが返される
        assert responses == []

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CHECK_QUALITY_WITH_C")
    def test_check_quality_with_config(self) -> None:
        """TDD RED: 設定付きチェックのテスト

        設定がチェッカーに正しく渡されることを確認
        """
        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("設定テスト原稿")
            temp_path = Path(f.name)

        try:
            # Given: 設定付きリクエスト
            config = {"strict_mode": True, "threshold": 80}
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=[CheckType.BASIC_STYLE], config=config
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 設定がチェッカーに渡される
            assert response.success is True
            call_args = self.mock_checker.execute.call_args[0][0]
            assert hasattr(call_args, "config")
            assert call_args.config == config

        finally:
            temp_path.unlink()

    # -----------------------------------------------------------------
    # GREEN Phase: テストを通す最小実装(実装は既存コードで対応)
    # -----------------------------------------------------------------

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-SCORE_CALCULATION_WE")
    def test_score_calculation_weighted_average(self) -> None:
        """TDD GREEN: スコア計算のテスト

        仕様書通りの重み付け平均でスコアが計算されることを確認
        """
        # Given: 複数チェッカーの設定(異なるスコア)
        mock_structure_checker = Mock()
        mock_structure_checker.execute.return_value = {
            "score": 90.0,  # STORY_STRUCTURE(重み2.0)
            "issues": [],
            "execution_time": 0.2,
        }
        self.checker_registry[CheckType.COMPOSITION] = mock_structure_checker

        # mock_checker(BASIC_STYLEは85.0(重み1.5)
        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("スコア計算テスト原稿")
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(
                project_id="test-project",
                filepath=temp_path,
                check_types=[CheckType.BASIC_STYLE, CheckType.COMPOSITION],
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 重み付け平均でスコアが計算される
            # 期待値: (85.0 * 1.5 + 90.0 * 2.0) / (1.5 + 2.0) = 87.86...
            assert response.success is True
            assert response.total_score is not None
            assert 87.0 <= response.total_score <= 88.0  # 重み付け平均の範囲

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-GRADE_DETERMINATION")
    def test_grade_determination(self) -> None:
        """TDD GREEN: グレード判定のテスト

        仕様書通りのグレード判定が行われることを確認
        """
        # Given: 高スコアのチェッカー設定
        self.mock_checker.execute.return_value = {
            "score": 96.0,  # Sグレード相当
            "issues": [],
            "execution_time": 0.1,
        }

        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("グレードテスト原稿")
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=[CheckType.BASIC_STYLE]
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 適切なグレードが判定される
            assert response.success is True
            assert response.total_score >= 95.0
            assert response.grade == "S"  # 95-100点でSグレード

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-ISSUES_FORMATTING")
    def test_issues_formatting(self) -> None:
        """TDD GREEN: 問題リストフォーマットのテスト

        問題リストが仕様書通りの形式でフォーマットされることを確認
        """
        # Given: 詳細な問題情報を含むチェッカー
        self.mock_checker.execute.return_value = {
            "score": 75.0,
            "issues": [
                {
                    "type": "punctuation",
                    "message": "句読点の重複があります",
                    "severity": "warning",
                    "line_number": 3,
                    "position": 15,
                    "suggestion": "。。 → 。",
                    "auto_fixable": True,
                },
                {
                    "type": "readability",
                    "message": "長すぎる文章です",
                    "severity": "info",
                    "line_number": 7,
                    "auto_fixable": False,
                },
            ],
            "execution_time": 0.3,
        }

        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("問題フォーマットテスト原稿")
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(
                project_id="test-project", filepath=temp_path, check_types=[CheckType.BASIC_STYLE]
            )

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 問題が適切にフォーマットされる
            assert response.success is True
            assert len(response.issues) == 2

            issue1 = response.issues[0]
            assert issue1["type"] == "punctuation"
            assert issue1["message"] == "句読点の重複があります"
            assert issue1["severity"] == "warning"
            assert issue1["line_number"] == 3
            assert issue1["position"] == 15
            assert issue1["suggestion"] == "。。 → 。"
            assert issue1["auto_fixable"] is True

            issue2 = response.issues[1]
            assert issue2["type"] == "readability"
            assert issue2["auto_fixable"] is False

        finally:
            temp_path.unlink()

    # -----------------------------------------------------------------
    # REFACTOR Phase: より良い設計へ
    # -----------------------------------------------------------------

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-PERFORMANCE_REQUIREM")
    def test_performance_requirements_single_file(self) -> None:
        """TDD REFACTOR: パフォーマンス要件のテスト

        仕様書の実行時間制限(10秒以内)を満たすことを確認
        """
        # Given: 一時ファイル
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("パフォーマンステスト原稿" * 1000)  # やや大きめのファイル
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(project_id="test-project", filepath=temp_path)

            start_time = time.time()

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            execution_time = time.time() - start_time

            # Then: 10秒以内に完了する
            assert response.success is True
            assert execution_time < 10.0  # 仕様書の制限時間

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-AUTO_FIX_COMPREHENSI")
    def test_auto_fix_comprehensive(self) -> None:
        """TDD REFACTOR: 包括的な自動修正テスト

        仕様書記載の各種自動修正が適用されることを確認
        """
        # Given: 各種修正対象を含むコンテンツ
        content_with_issues = """
        句読点の重複テストです。。
        全角スペースの重複  テスト
        正常な文章も含まれています。
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content_with_issues)
            temp_path = Path(f.name)

        try:
            # Given: 自動修正可能な問題を返すチェッカー
            self.mock_checker.execute.return_value = {
                "score": 70.0,
                "issues": [
                    {
                        "type": "punctuation",
                        "message": "句読点の重複",
                        "severity": "warning",
                        "auto_fixable": True,
                        "suggestion": "。。 → 。",
                    },
                    {
                        "type": "space",
                        "message": "全角スペースの重複",
                        "severity": "warning",
                        "auto_fixable": True,
                        "suggestion": "   →  ",
                    },
                ],
                "execution_time": 0.2,
            }

            request = QualityCheckRequest(project_id="test-project", filepath=temp_path, auto_fix=True)

            # When: 自動修正付きチェックを実行
            response = self.use_case.check_quality(request)

            # Then: 各種修正が適用される
            assert response.success is True
            assert response.auto_fixed_content is not None

            fixed_content = response.auto_fixed_content
            assert "。。" not in fixed_content  # 句読点重複が修正
            assert "  " not in fixed_content  # 全角スペース重複が修正
            assert "正常な文章も含まれています。" in fixed_content  # 正常部分は保持

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-MEMORY_USAGE_WITHIN_")
    def test_memory_usage_within_limits(self) -> None:
        """TDD REFACTOR: メモリ使用量制限のテスト

        仕様書のメモリ制限(100MB/セッション)を満たすことを確認
        """
        # Given: 適度なサイズのファイル(メモリ使用量テスト)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            # 約1MBのコンテンツ
            large_content = "メモリテスト用長文。" * 50000
            f.write(large_content)
            temp_path = Path(f.name)

        try:
            request = QualityCheckRequest(project_id="test-project", filepath=temp_path)

            # When: 品質チェックを実行
            response = self.use_case.check_quality(request)

            # Then: 正常に処理完了(メモリエラーなし)
            assert response.success is True
            assert response.session_id is not None

            # メモリ使用量の詳細測定は統合テストで実施

        finally:
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INTEGRATED_QUALITY_CHECK_USE_CASE-CONCURRENT_SESSIONS_")
    def test_concurrent_sessions_handling(self) -> None:
        """TDD REFACTOR: 同時セッション処理のテスト

        複数セッションが同時に動作することを確認
        """
        # Given: 複数の一時ファイル
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
            temp_file.write(f"同時セッションテスト{i}")
            temp_file.close()
            temp_files.append(Path(temp_file.name))

        try:
            # When: 複数のセッションを作成
            session_ids = []
            for temp_path in temp_files:
                request = QualityCheckRequest(project_id="test-project", filepath=temp_path)
                response = self.use_case.check_quality(request)
                assert response.success is True
                session_ids.append(response.session_id)

            # Then: 全セッションが独立して管理される
            assert len(set(session_ids)) == 3  # 全て異なるセッションID

            # Then: 各セッションのサマリーが取得できる
            for session_id in session_ids:
                summary = self.use_case.get_session_summary(session_id)
                assert summary is not None

        finally:
            for temp_path in temp_files:
                temp_path.unlink()
