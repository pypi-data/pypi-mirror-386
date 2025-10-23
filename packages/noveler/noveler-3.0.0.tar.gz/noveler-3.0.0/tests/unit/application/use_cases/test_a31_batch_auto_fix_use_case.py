#!/usr/bin/env python3

"""Tests.tests.unit.application.use_cases.test_a31_batch_auto_fix_use_case
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

"""A31バッチ自動修正ユースケースのテストケース(TDD実装)

SPEC-A31-001準拠のバッチ処理機能のアプリケーション層テスト。
"""


from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.a31_batch_auto_fix_use_case import (
    A31BatchAutoFixUseCase,
    A31BatchRequest,
    A31BatchResponse,
)
from noveler.application.use_cases.a31_complete_check_use_case import A31CompleteCheckUseCase
from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31CompleteCheckRequest,
    A31CompleteCheckResponse,
    A31EvaluationBatch,
    A31EvaluationCategory,
    A31EvaluationResult,
)


@pytest.mark.spec("SPEC-A31-001")
class TestA31BatchAutoFixUseCase:
    """A31バッチ自動修正ユースケースのテストクラス"""

    @pytest.fixture
    def episode_repository(self) -> Mock:
        """エピソードリポジトリのモック"""
        mock = Mock()

        # 複数エピソードの内容を返すように設定
        def get_episode_content(project_name: str, episode_number: int) -> str:
            if episode_number in [1, 2, 3]:
                return f"""# 第{episode_number:03d}話 テストエピソード{episode_number}

 これは第{episode_number}話のテスト内容です。

「テストです」と彼は言った。

 風が頬を撫でていく。
"""
            msg = f"Episode {episode_number} not found"
            raise FileNotFoundError(msg)

        mock.get_episode_content.side_effect = get_episode_content
        return mock

    @pytest.fixture
    def project_repository(self) -> Mock:
        """プロジェクトリポジトリのモック"""
        mock = Mock()
        mock.get_project_config.return_value = {
            "quality_threshold": 70.0,
            "characters": {"主人公": {"口調": "丁寧語"}},
            "terminology": {"魔法": "マジック"},
        }
        return mock

    @pytest.fixture
    def a31_checklist_repository(self) -> Mock:
        """A31チェックリストリポジトリのモック"""
        mock = Mock()
        mock.save_evaluation_results.return_value = Path("test_checklist.yaml")
        return mock

    @pytest.fixture
    def complete_check_use_case(self) -> Mock:
        """完全チェックユースケースのモック"""
        mock = Mock()

        def execute_check(request: A31CompleteCheckRequest) -> A31CompleteCheckResponse:
            # エピソード番号に応じて結果を変える
            if request.episode_number == 1:
                # 成功ケース
                return A31CompleteCheckResponse(
                    success=True,
                    project_name=request.project_name,
                    episode_number=request.episode_number,
                    evaluation_batch=A31EvaluationBatch(
                        results={
                            "A31-045": A31EvaluationResult(
                                item_id="A31-045",
                                category=A31EvaluationCategory.FORMAT_CHECK,
                                score=95.0,
                                passed=True,
                                details="段落字下げ適正",
                                execution_time_ms=50.0,
                            )
                        },
                        total_items=1,
                        evaluated_items=1,
                        execution_time_ms=50.0,
                    ),
                    total_items_checked=1,
                )

            if request.episode_number == 2:
                # 部分的成功ケース
                return A31CompleteCheckResponse(
                    success=True,
                    project_name=request.project_name,
                    episode_number=request.episode_number,
                    evaluation_batch=A31EvaluationBatch(
                        results={
                            "A31-022": A31EvaluationResult(
                                item_id="A31-022",
                                category=A31EvaluationCategory.CONTENT_BALANCE,
                                score=25.0,
                                passed=False,
                                details="会話比率不足",
                                execution_time_ms=30.0,
                            )
                        },
                        total_items=1,
                        evaluated_items=1,
                        execution_time_ms=30.0,
                    ),
                    total_items_checked=1,
                )

            # 失敗ケース
            return A31CompleteCheckResponse(
                success=False,
                project_name=request.project_name,
                episode_number=request.episode_number,
                evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                error_message=f"エピソード {request.episode_number} の処理に失敗しました",
            )

        mock.execute.side_effect = execute_check
        return mock

    @pytest.fixture
    def logger_service(self) -> Mock:
        """ロガーサービスのモック"""
        mock = Mock()
        mock.info.return_value = None
        mock.debug.return_value = None
        mock.error.return_value = None
        mock.warning.return_value = None
        return mock

    @pytest.fixture
    def unit_of_work(self) -> Mock:
        """ユニットオブワークのモック"""
        mock = Mock()
        mock.__enter__ = Mock(return_value=mock)
        mock.__exit__ = Mock(return_value=False)
        return mock

    @pytest.fixture
    def use_case(
        self,
        logger_service: Mock,
        unit_of_work: Mock,
        episode_repository: Mock,
        project_repository: Mock,
        a31_checklist_repository: Mock,
        complete_check_use_case: Mock,
    ) -> A31BatchAutoFixUseCase:
        """テスト対象のバッチユースケース"""
        use_case = A31BatchAutoFixUseCase(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            episode_repository=episode_repository,
            project_repository=project_repository,
            a31_checklist_repository=a31_checklist_repository,
            complete_check_use_case=complete_check_use_case,
        )

        # 実装ではDIコンテナ経由で設定される内部依存をテスト用に明示設定
        use_case._episode_repository = episode_repository
        use_case._project_repository = project_repository
        use_case._a31_checklist_repository = a31_checklist_repository
        use_case._complete_check_use_case = complete_check_use_case

        return use_case

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-USE_CASE_INITIALIZAT")
    def test_use_case_initialization(self, use_case: A31BatchAutoFixUseCase) -> None:
        """ユースケースの初期化テスト"""
        assert use_case is not None
        assert use_case._episode_repository is not None
        assert use_case._project_repository is not None
        assert use_case._a31_checklist_repository is not None
        assert use_case._complete_check_use_case is not None

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-SUCCESSFUL_BATCH_PRO")
    @pytest.mark.asyncio
    async def test_successful_batch_processing_multiple_episodes(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """複数エピソードの成功バッチ処理テスト"""
        # Setup
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2],
            target_categories=[A31EvaluationCategory.FORMAT_CHECK, A31EvaluationCategory.CONTENT_BALANCE],
            include_auto_fix=True,
            fix_level="safe",
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.project_name == "テストプロジェクト"
        assert response.total_episodes == 2
        assert response.processed_episodes == 2
        assert response.successful_episodes == 2  # 両方とも成功(エラーでない)
        assert response.failed_episodes == 0
        assert len(response.episode_responses) == 2
        assert 1 in response.episode_responses
        assert 2 in response.episode_responses
        assert response.execution_time_ms > 0

        # 個別エピソードの結果確認
        assert response.episode_responses[1].success is True
        assert response.episode_responses[2].success is True

        # complete_check_use_caseが2回呼ばれることを確認
        assert complete_check_use_case.execute.call_count == 2

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-BATCH_REQUEST_VALIDA")
    def test_batch_request_validation(self) -> None:
        """バッチリクエストの検証テスト"""
        # 空のエピソード番号リスト
        with pytest.raises(ValueError, match="エピソード番号リストが空です"):
            A31BatchRequest(project_name="テストプロジェクト", episode_numbers=[])

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-EPISODE_VALIDATION_N")
    @pytest.mark.asyncio
    async def test_episode_validation_non_existent_episodes(
        self, use_case: A31BatchAutoFixUseCase, episode_repository: Mock
    ) -> None:
        """存在しないエピソードの検証テスト"""
        # Setup - エピソード5は存在しない
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[5, 6, 7],  # 全て存在しない
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is False
        assert "処理可能なエピソードが見つかりません" in response.error_message
        assert response.processed_episodes == 0

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-PARTIAL_EPISODE_AVAI")
    @pytest.mark.asyncio
    async def test_partial_episode_availability(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """一部のエピソードのみ存在する場合のテスト"""
        # Setup - エピソード1,2は存在、3以降は存在しない
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2, 5, 6],  # 1,2は存在、5,6は存在しない
            include_auto_fix=True,
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.total_episodes == 4
        assert response.processed_episodes == 2  # 存在する1,2のみ処理
        assert len(response.episode_responses) == 2
        assert 1 in response.episode_responses
        assert 2 in response.episode_responses
        assert 5 not in response.episode_responses
        assert 6 not in response.episode_responses

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-STOP_ON_ERROR_BEHAVI")
    @pytest.mark.asyncio
    async def test_stop_on_error_behavior(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """エラー時停止動作のテスト"""
        # Setup - エピソード3で失敗するように設定
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 3, 2],  # 3で失敗するので2は処理されない
            stop_on_error=True,
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is True  # バッチ自体は成功(一部処理済み)
        assert response.processed_episodes <= 2  # 3で止まるので最大2つ
        # complete_check_use_caseの呼び出し回数を確認(エラーで停止)
        assert complete_check_use_case.execute.call_count <= 2

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-SEQUENTIAL_EXECUTION")
    @pytest.mark.asyncio
    async def test_sequential_execution_mode(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """順次実行モードのテスト"""
        # Setup
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2],
            max_parallel_jobs=1,  # 順次実行を強制
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.processed_episodes == 2
        assert complete_check_use_case.execute.call_count == 2

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-BATCH_SUMMARY_GENERA")
    def test_batch_summary_generation_success(self, use_case: A31BatchAutoFixUseCase) -> None:
        """バッチサマリー生成のテスト(成功ケース)"""
        # Setup
        successful_response = A31BatchResponse(
            success=True,
            project_name="テストプロジェクト",
            total_episodes=2,
            processed_episodes=2,
            successful_episodes=2,
            failed_episodes=0,
            episode_responses={
                1: A31CompleteCheckResponse(
                    success=True,
                    project_name="テストプロジェクト",
                    episode_number=1,
                    evaluation_batch=A31EvaluationBatch(
                        results={
                            "A31-045": A31EvaluationResult(
                                item_id="A31-045",
                                category=A31EvaluationCategory.FORMAT_CHECK,
                                score=95.0,
                                passed=True,
                                details="テスト",
                                execution_time_ms=50.0,
                            )
                        },
                        total_items=1,
                        evaluated_items=1,
                        execution_time_ms=50.0,
                    ),
                    total_items_checked=1,
                ),
                2: A31CompleteCheckResponse(
                    success=True,
                    project_name="テストプロジェクト",
                    episode_number=2,
                    evaluation_batch=A31EvaluationBatch(
                        results={
                            "A31-022": A31EvaluationResult(
                                item_id="A31-022",
                                category=A31EvaluationCategory.CONTENT_BALANCE,
                                score=25.0,
                                passed=False,
                                details="テスト",
                                execution_time_ms=30.0,
                            )
                        },
                        total_items=1,
                        evaluated_items=1,
                        execution_time_ms=30.0,
                    ),
                    total_items_checked=1,
                ),
            },
            execution_time_ms=100.0,
        )

        # Execute
        summary = use_case.get_batch_summary(successful_response)

        # Assert
        assert summary["success"] is True
        assert summary["project_name"] == "テストプロジェクト"
        assert summary["total_episodes"] == 2
        assert summary["processed_episodes"] == 2
        assert summary["success_rate"] == 1.0
        assert summary["total_items_checked"] == 2
        assert "performance_metrics" in summary
        assert summary["performance_metrics"]["episodes_per_second"] > 0

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-BATCH_SUMMARY_GENERA")
    def test_batch_summary_generation_failure(self, use_case: A31BatchAutoFixUseCase) -> None:
        """バッチサマリー生成のテスト(失敗ケース)"""
        # Setup
        failed_response = A31BatchResponse(
            success=False,
            project_name="テストプロジェクト",
            total_episodes=2,
            processed_episodes=0,
            successful_episodes=0,
            failed_episodes=0,
            episode_responses={},
            execution_time_ms=0.0,
            error_message="テストエラー",
        )

        # Execute
        summary = use_case.get_batch_summary(failed_response)

        # Assert
        assert summary["success"] is False
        assert summary["error"] == "テストエラー"

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-BATCH_RESPONSE_CALCU")
    def test_batch_response_calculations(self) -> None:
        """バッチレスポンスの計算メソッドテスト"""
        # Setup
        episode_responses = {
            1: A31CompleteCheckResponse(
                success=True,
                project_name="テスト",
                episode_number=1,
                evaluation_batch=A31EvaluationBatch(
                    results={
                        "A31-045": A31EvaluationResult(
                            item_id="A31-045",
                            category=A31EvaluationCategory.FORMAT_CHECK,
                            score=100.0,
                            passed=True,
                            details="テスト",
                            execution_time_ms=50.0,
                        )
                    },
                    total_items=1,
                    evaluated_items=1,
                    execution_time_ms=50.0,
                ),
                total_items_checked=1,
            ),
            2: A31CompleteCheckResponse(
                success=False,
                project_name="テスト",
                episode_number=2,
                evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                error_message="テストエラー",
            ),
        }

        response = A31BatchResponse(
            success=True,
            project_name="テスト",
            total_episodes=2,
            processed_episodes=2,
            successful_episodes=1,
            failed_episodes=1,
            episode_responses=episode_responses,
            execution_time_ms=100.0,
        )

        # Execute & Assert
        assert response.get_overall_success_rate() == 0.5  # 1/2
        assert response.get_failed_episode_numbers() == [2]
        assert response.get_total_items_checked() == 1  # 成功したエピソードのみ
        assert response.get_overall_pass_rate() == 1.0  # 成功したエピソードの平均

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-CATEGORY_FILTERING_I")
    @pytest.mark.asyncio
    async def test_category_filtering_in_batch(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """バッチ処理でのカテゴリフィルタリングテスト"""
        # Setup
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2],
            target_categories=[A31EvaluationCategory.FORMAT_CHECK],  # フォーマットのみ
            include_auto_fix=False,
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        assert response.success is True

        # complete_check_use_caseに渡されたリクエストの確認
        call_args_list = complete_check_use_case.execute.call_args_list
        for call_args in call_args_list:
            request_arg = call_args[0][0]  # 第1引数(A31CompleteCheckRequest)
            assert request_arg.target_categories == [A31EvaluationCategory.FORMAT_CHECK]

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-ERROR_HANDLING_DURIN")
    @pytest.mark.asyncio
    async def test_error_handling_during_batch_processing(
        self, use_case: A31BatchAutoFixUseCase, complete_check_use_case: Mock
    ) -> None:
        """バッチ処理中のエラーハンドリングテスト"""
        # Setup - complete_check_use_caseが失敗レスポンスを返すよう設定
        def failing_execute(request: A31CompleteCheckRequest) -> A31CompleteCheckResponse:
            return A31CompleteCheckResponse(
                success=False,
                project_name=request.project_name,
                episode_number=request.episode_number,
                evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                error_message="評価エンジンエラー",
            )

        complete_check_use_case.execute.side_effect = failing_execute

        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2],
            stop_on_error=False,  # エラーでも継続
        )
        request.show_progress = False

        # Execute
        response = await use_case.execute(request)

        # Assert
        # バッチ処理自体は成功(個々のエピソードでエラーが発生しても継続処理)
        assert response.success is True
        assert response.successful_episodes == 0  # 全てのエピソードが失敗
        assert response.failed_episodes == 2
        # 個々のエピソードのエラーメッセージを確認
        for episode_response in response.episode_responses.values():
            assert episode_response.success is False
        assert episode_response.error_message == "評価エンジンエラー"


@pytest.mark.spec("SPEC-A31-001")
class TestA31BatchRequest:
    """A31バッチリクエストのテストクラス"""

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-VALID_BATCH_REQUEST_")
    def test_valid_batch_request_creation(self) -> None:
        """有効なバッチリクエストの作成テスト"""
        request = A31BatchRequest(
            project_name="テストプロジェクト",
            episode_numbers=[1, 2, 3],
            target_categories=[A31EvaluationCategory.FORMAT_CHECK],
            include_auto_fix=True,
            fix_level="standard",
            max_parallel_jobs=2,
            stop_on_error=True,
        )

        assert request.project_name == "テストプロジェクト"
        assert request.episode_numbers == [1, 2, 3]
        assert request.target_categories == [A31EvaluationCategory.FORMAT_CHECK]
        assert request.include_auto_fix is True
        assert request.fix_level == "standard"
        assert request.max_parallel_jobs == 2
        assert request.stop_on_error is True

    @pytest.mark.spec("SPEC-A31_BATCH_AUTO_FIX_USE_CASE-DEFAULT_VALUES_IN_BA")
    def test_default_values_in_batch_request(self) -> None:
        """バッチリクエストのデフォルト値テスト"""
        request = A31BatchRequest(project_name="テストプロジェクト", episode_numbers=[1, 2])

        assert request.target_categories == list(A31EvaluationCategory)
        assert request.include_auto_fix is True
        assert request.fix_level == "safe"
        assert request.max_parallel_jobs == 3
        assert request.stop_on_error is False
