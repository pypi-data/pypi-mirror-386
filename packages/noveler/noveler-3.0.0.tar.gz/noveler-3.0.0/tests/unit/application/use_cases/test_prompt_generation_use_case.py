#!/usr/bin/env python3
"""
プロンプト生成ユースケースのユニットテスト

SPEC-PROMPT-003: プロンプト生成アプリケーションサービス
DDD設計に基づくプロンプト生成ユースケースの動作を検証する。
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.prompt_generation_use_case import (
    PromptGenerationUseCase,
    PromptGenerationUseCaseRequest,
)
from noveler.domain.entities.prompt_generation import (
    A24Stage,
    OptimizationTarget,
    PromptGenerationSession,
)


class TestPromptGenerationUseCaseRequest:
    """PromptGenerationUseCaseRequest データクラステスト"""

    @pytest.mark.spec("SPEC-PROMPT-003-001")
    def test_request_creation_with_defaults(self) -> None:
        """デフォルト値でのリクエスト作成テスト"""
        request = PromptGenerationUseCaseRequest(episode_number=12, project_name="テストプロジェクト")

        assert request.episode_number == 12
        assert request.project_name == "テストプロジェクト"
        assert request.context_level == "基本"
        assert request.include_foreshadowing is True
        assert request.include_important_scenes is True
        assert request.optimization_target == OptimizationTarget.CLAUDE_CODE
        assert request.project_root_path is None

    @pytest.mark.spec("SPEC-PROMPT-003-002")
    def test_request_creation_with_custom_values(self) -> None:
        """カスタム値でのリクエスト作成テスト"""
        project_path = Path("/test/path")
        request = PromptGenerationUseCaseRequest(
            episode_number=5,
            project_name="カスタムプロジェクト",
            context_level="拡張",
            include_foreshadowing=False,
            include_important_scenes=True,
            optimization_target=OptimizationTarget.CHATGPT,
            project_root_path=project_path,
        )

        assert request.episode_number == 5
        assert request.project_name == "カスタムプロジェクト"
        assert request.context_level == "拡張"
        assert request.include_foreshadowing is False
        assert request.include_important_scenes is True
        assert request.optimization_target == OptimizationTarget.CHATGPT
        assert request.project_root_path == project_path


class TestPromptGenerationUseCase:
    """PromptGenerationUseCase アプリケーションサービステスト"""

    @pytest.fixture
    def mock_prompt_service(self) -> Mock:
        """プロンプトサービスモック"""
        service = Mock()

        def mock_generate_prompt(session: PromptGenerationSession) -> None:
            # 成功ケースのセッション状態設定
            session.final_prompt = "生成されたプロンプト"
            session.token_estimate = 1500
            session.completed_stages = list(A24Stage)  # 全段階完了
            session.warnings = ["テスト警告"]

        service.generate_prompt_for_episode = mock_generate_prompt
        return service

    @pytest.fixture
    def use_case(self, mock_prompt_service: Mock) -> PromptGenerationUseCase:
        """プロンプト生成ユースケース"""
        return PromptGenerationUseCase(mock_prompt_service)

    @pytest.fixture
    def valid_request(self) -> PromptGenerationUseCaseRequest:
        """有効なリクエスト"""
        return PromptGenerationUseCaseRequest(
            episode_number=12,
            project_name="テストプロジェクト",
            context_level="基本",
            include_foreshadowing=True,
            include_important_scenes=True,
            optimization_target=OptimizationTarget.CLAUDE_CODE,
        )

    @pytest.mark.spec("SPEC-PROMPT-003-003")
    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """正常実行テスト"""
        response = await use_case.execute(valid_request)

        assert response.success is True
        assert response.generated_prompt == "生成されたプロンプト"
        assert response.token_estimate == 1500
        assert response.generation_time_ms > 0
        assert response.completion_rate == 1.0
        assert len(response.warnings) > 0
        assert response.error_message is None

        # セッションIDが設定されていることを確認
        assert response.session_id != ""
        assert len(response.session_id) > 0

    @pytest.mark.spec("SPEC-PROMPT-003-004")
    @pytest.mark.asyncio
    async def test_execute_invalid_episode_number(self, use_case: PromptGenerationUseCase) -> None:
        """無効なエピソード番号でのテスト"""
        invalid_request = PromptGenerationUseCaseRequest(
            episode_number=0,  # 無効な値
            project_name="テストプロジェクト",
        )

        response = await use_case.execute(invalid_request)

        assert response.success is False
        assert "エピソード番号は1以上である必要があります" in response.error_message
        assert response.generated_prompt == ""
        assert response.token_estimate == 0
        assert response.generation_time_ms >= 0

    @pytest.mark.spec("SPEC-PROMPT-003-005")
    @pytest.mark.asyncio
    async def test_execute_empty_project_name(self, use_case: PromptGenerationUseCase) -> None:
        """空のプロジェクト名でのテスト"""
        invalid_request = PromptGenerationUseCaseRequest(
            episode_number=5,
            project_name="",  # 空のプロジェクト名
        )

        response = await use_case.execute(invalid_request)

        assert response.success is False
        assert "プロジェクト名は必須です" in response.error_message

    @pytest.mark.spec("SPEC-PROMPT-003-006")
    @pytest.mark.asyncio
    async def test_execute_invalid_context_level(self, use_case: PromptGenerationUseCase) -> None:
        """無効なコンテキストレベルでのテスト"""
        invalid_request = PromptGenerationUseCaseRequest(
            episode_number=5,
            project_name="テストプロジェクト",
            context_level="無効レベル",  # 無効なレベル
        )

        response = await use_case.execute(invalid_request)

        assert response.success is False
        assert "コンテキストレベルは次のいずれかである必要があります" in response.error_message

    @pytest.mark.spec("SPEC-PROMPT-003-007")
    @pytest.mark.asyncio
    async def test_execute_nonexistent_project_path(self, use_case: PromptGenerationUseCase) -> None:
        """存在しないプロジェクトパスでのテスト"""
        invalid_request = PromptGenerationUseCaseRequest(
            episode_number=5,
            project_name="テストプロジェクト",
            project_root_path=Path("/nonexistent/path"),  # 存在しないパス
        )

        response = await use_case.execute(invalid_request)

        assert response.success is False
        assert "指定されたプロジェクトルートが存在しません" in response.error_message

    @pytest.mark.spec("SPEC-PROMPT-003-008")
    @pytest.mark.asyncio
    async def test_execute_prompt_service_runtime_error(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """プロンプトサービスランタイムエラーテスト"""
        mock_prompt_service.generate_prompt_for_episode.side_effect = RuntimeError("サービスエラー")

        response = await use_case.execute(valid_request)

        assert response.success is False
        assert "プロンプト生成エラー: サービスエラー" in response.error_message
        assert response.generated_prompt == ""

    @pytest.mark.spec("SPEC-PROMPT-003-009")
    @pytest.mark.asyncio
    async def test_execute_prompt_service_value_error(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """プロンプトサービス値エラーテスト"""
        mock_prompt_service.generate_prompt_for_episode.side_effect = ValueError("値エラー")

        response = await use_case.execute(valid_request)

        assert response.success is False
        assert "要求パラメータエラー: 値エラー" in response.error_message

    @pytest.mark.spec("SPEC-PROMPT-003-010")
    @pytest.mark.asyncio
    async def test_execute_unexpected_error(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """予期せぬエラーテスト"""
        mock_prompt_service.generate_prompt_for_episode.side_effect = Exception("予期せぬエラー")

        response = await use_case.execute(valid_request)

        assert response.success is False
        assert "内部エラー: 予期せぬエラー" in response.error_message

    @pytest.mark.spec("SPEC-PROMPT-003-011")
    @pytest.mark.asyncio
    async def test_execute_partial_success(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """部分的成功テスト（警告あり）"""

        def mock_generate_prompt_with_warnings(session: PromptGenerationSession) -> None:
            session.final_prompt = "部分的プロンプト"
            session.token_estimate = 800
            session.completed_stages = [A24Stage.SKELETON, A24Stage.THREE_ACT]  # 2段階のみ完了
            session.warnings = ["段階未完了の警告", "コンテキスト不足の警告"]
            session.errors = []  # エラーなし

        mock_prompt_service.generate_prompt_for_episode = mock_generate_prompt_with_warnings

        response = await use_case.execute(valid_request)

        # セッション成功判定は3段階以上完了が必要なため、失敗となる
        assert response.success is False
        assert response.generated_prompt == "部分的プロンプト"
        assert response.completion_rate == 0.5  # 2/4 = 0.5
        assert len(response.warnings) == 2
        assert "部分的プロンプト" in response.error_message or response.error_message is None

    @pytest.mark.spec("SPEC-PROMPT-003-012")
    @pytest.mark.asyncio
    async def test_execute_with_errors_in_session(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """セッションエラーありテスト"""

        def mock_generate_prompt_with_errors(session: PromptGenerationSession) -> None:
            session.final_prompt = "エラー付きプロンプト"
            session.token_estimate = 1200
            session.completed_stages = list(A24Stage)
            session.errors = ["エラー1", "エラー2"]
            session.warnings = ["警告"]

        mock_prompt_service.generate_prompt_for_episode = mock_generate_prompt_with_errors

        response = await use_case.execute(valid_request)

        assert response.success is False
        assert "エラー1; エラー2" in response.error_message
        assert len(response.warnings) == 1

    @pytest.mark.spec("SPEC-PROMPT-003-013")
    def test_validate_request_all_valid_context_levels(self, use_case: PromptGenerationUseCase) -> None:
        """全有効コンテキストレベルのバリデーションテスト"""
        valid_levels = ["基本", "拡張", "完全"]

        for level in valid_levels:
            request = PromptGenerationUseCaseRequest(episode_number=1, project_name="テスト", context_level=level)

            # 例外が発生しないことを確認
            use_case._validate_request(request)

    @pytest.mark.spec("SPEC-PROMPT-003-014")
    def test_create_session_mapping(self, use_case: PromptGenerationUseCase) -> None:
        """セッション作成でのマッピングテスト"""
        request = PromptGenerationUseCaseRequest(
            episode_number=8,
            project_name="マッピングテスト",
            context_level="拡張",
            include_foreshadowing=False,
            include_important_scenes=True,
            optimization_target=OptimizationTarget.CHATGPT,
        )

        session = use_case._create_session(request)

        assert session.context_level == "拡張"
        assert session.optimization_target == OptimizationTarget.CHATGPT
        assert session.include_foreshadowing is False
        assert session.include_important_scenes is True

    @pytest.mark.spec("SPEC-PROMPT-003-015")
    def test_create_error_response(self, use_case: PromptGenerationUseCase) -> None:
        """エラーレスポンス作成テスト"""
        error_message = "テストエラーメッセージ"
        generation_time = 1500

        response = use_case._create_error_response(error_message, generation_time)

        assert response.success is False
        assert response.error_message == error_message
        assert response.generation_time_ms == generation_time
        assert response.generated_prompt == ""
        assert response.token_estimate == 0
        assert response.context_elements_count == 0
        assert response.session_id == ""
        assert response.completion_rate == 0.0
        assert len(response.context_summary) == 0
        assert len(response.warnings) == 0

    @pytest.mark.spec("SPEC-PROMPT-003-016")
    @pytest.mark.asyncio
    async def test_execute_performance_timing(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """実行時間計測テスト"""

        def slow_mock_generate_prompt(session: PromptGenerationSession) -> None:
            # 100msの遅延をシミュレート
            import time

            time.sleep(0.1)
            session.final_prompt = "遅延プロンプト"
            session.token_estimate = 1000
            session.completed_stages = list(A24Stage)

        mock_prompt_service.generate_prompt_for_episode = slow_mock_generate_prompt

        response = await use_case.execute(valid_request)

        assert response.success is True
        assert response.generation_time_ms >= 100  # 少なくとも100ms以上
        assert response.generation_time_ms < 1000  # 1秒未満であることを確認

    @pytest.mark.spec("SPEC-PROMPT-003-017")
    @pytest.mark.asyncio
    async def test_execute_context_summary_mapping(
        self,
        use_case: PromptGenerationUseCase,
        valid_request: PromptGenerationUseCaseRequest,
        mock_prompt_service: Mock,
    ) -> None:
        """コンテキストサマリマッピングテスト"""
        from noveler.domain.entities.prompt_generation import ContextElement, ContextElementType

        def mock_generate_with_context(session: PromptGenerationSession) -> None:
            # テストコンテキスト要素追加
            foreshadowing = ContextElement(
                element_type=ContextElementType.FORESHADOWING,
                content="伏線",
                priority=0.8,
                integration_stage=A24Stage.TECH_INTEGRATION,
            )

            scene = ContextElement(
                element_type=ContextElementType.IMPORTANT_SCENE,
                content="シーン",
                priority=0.9,
                integration_stage=A24Stage.SCENE_DETAIL,
            )

            session.add_context_element(foreshadowing)
            session.add_context_element(scene)

            session.final_prompt = "コンテキスト付きプロンプト"
            session.token_estimate = 1800
            session.completed_stages = list(A24Stage)

        mock_prompt_service.generate_prompt_for_episode = mock_generate_with_context

        response = await use_case.execute(valid_request)

        assert response.success is True
        assert response.context_elements_count == 2
        assert response.context_summary["伏線要素"] == 1
        assert response.context_summary["重要シーン"] == 1
        assert response.context_summary["章間連携"] == 0
        assert response.context_summary["技術要素"] == 0
