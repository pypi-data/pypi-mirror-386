#!/usr/bin/env python3
"""UnifiedSessionExecutor単体テスト"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from noveler.domain.value_objects.five_stage_writing_execution import ExecutionStage, FiveStageWritingRequest
from noveler.infrastructure.services.unified_session_executor import (
    SessionState,
    TurnAllocation,
    UnifiedSessionExecutor,
)


@pytest.fixture
def mock_claude_service():
    """Claude Codeサービスのモック"""
    service = Mock()
    service.execute_with_turn_limit = AsyncMock(
        return_value={"output": "テスト出力", "turns_used": 2, "success": True}
    )
    return service


@pytest.fixture
def mock_validation_service():
    """検証サービスのモック"""
    service = Mock()
    service.validate = AsyncMock(
        return_value=Mock(is_valid=True, errors=[], warnings=[], cleaned_content="クリーニング済み出力")
    )
    return service


@pytest.fixture
def sample_request():
    """サンプルリクエスト"""
    return FiveStageWritingRequest(
        episode_number=1,
        project_root=Path("/test/project"),
        debug_mode=False,
        dry_run=False,
    )


class TestUnifiedSessionExecutor:
    """UnifiedSessionExecutor単体テスト"""

    def test_session_state_initialization(self):
        """セッション状態の初期化テスト"""
        state = SessionState(session_id="test_session")

        assert state.session_id == "test_session"
        assert state.total_turns_available == 30
        assert state.turns_used == 0
        assert state.remaining_turns == 30
        assert state.can_continue() is True

    def test_turn_allocation_initialization(self):
        """ターン配分の初期化テスト"""
        allocation = TurnAllocation(stage=ExecutionStage.INITIAL_WRITING, min_turns=5, max_turns=10, priority=5)

        assert allocation.stage == ExecutionStage.INITIAL_WRITING
        assert allocation.min_turns == 5
        assert allocation.max_turns == 10
        assert allocation.priority == 5
        assert allocation.actual_turns == 0

    @pytest.mark.asyncio
    async def test_executor_initialization(self, mock_claude_service):
        """実行サービスの初期化テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        assert executor.claude_service == mock_claude_service
        assert executor.validation_service is not None
        assert len(executor.default_allocations) == 5

    def test_complexity_estimation(self, mock_claude_service, sample_request):
        """複雑度推定テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        # デフォルト複雑度
        complexity = executor._estimate_complexity(sample_request)
        assert 0.0 <= complexity <= 1.0

        # エピソード番号による複雑度変化
        sample_request.episode_number = 100
        complexity_high = executor._estimate_complexity(sample_request)
        assert complexity_high >= complexity

    def test_turn_allocation_calculation(self, mock_claude_service, sample_request):
        """ターン配分計算テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        allocations = executor._calculate_turn_allocations(sample_request)

        # 全段階の配分が存在
        assert len(allocations) == 5

        # 総ターン数が制限内
        total_max = sum(a.max_turns for a in allocations.values())
        assert total_max <= 30

        # 各段階の配分が妥当
        for allocation in allocations.values():
            assert allocation.min_turns <= allocation.max_turns
            assert allocation.min_turns > 0

    @pytest.mark.asyncio
    async def test_unified_session_execution_basic(self, mock_claude_service, mock_validation_service, sample_request):
        """基本的な統一セッション実行テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service, mock_validation_service)

        # モックの設定
        mock_claude_service.execute_with_turn_limit.return_value = {
            "output": "第001話\n\n本文内容...",
            "turns_used": 3,
            "success": True,
        }

        response = await executor.execute_unified_session(sample_request)

        # 基本的な応答検証
        assert response is not None
        assert response.session_id.startswith("unified_001_")
        assert "unified_session" in response.metadata

    def test_json_metadata_removal(self, mock_claude_service):
        """JSONメタデータ除去テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        test_text = """
        第001話 テストタイトル

        {"metadata": {"stage": "writing"}}

        実際の本文内容です。

        ```json
        {"version": "1.0"}
        ```
        """

        cleaned = executor._remove_json_metadata(test_text)

        assert "metadata" not in cleaned
        assert "stage" not in cleaned
        assert "実際の本文内容です。" in cleaned
        assert "第001話" in cleaned

    def test_prompt_contamination_removal(self, mock_claude_service):
        """プロンプト混入除去テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        test_text = """
        ## 指示: 以下の要件に従って執筆してください

        第001話 テストタイトル

        実際の本文内容です。

        ## 注意事項: 必ず含めてください
        """

        cleaned = executor._remove_prompt_contamination(test_text)

        assert "指示:" not in cleaned
        assert "注意事項:" not in cleaned
        assert "第001話" in cleaned
        assert "実際の本文内容です。" in cleaned

    def test_manuscript_text_extraction(self, mock_claude_service):
        """原稿テキスト抽出テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        test_text = """
        前置きテキスト

        第001話 テストタイトル

        実際の原稿内容です。

        後続テキスト
        """

        extracted = executor._extract_manuscript_text(test_text)

        assert extracted.startswith("第001話")
        assert "実際の原稿内容です。" in extracted
        assert "前置きテキスト" not in extracted


@pytest.mark.spec("SPEC-FIVE-STAGE-002")
class TestSessionManagement:
    """セッション管理のテスト"""

    def test_session_state_turn_tracking(self):
        """セッション状態のターン追跡テスト"""
        state = SessionState("test", total_turns_available=10)

        # 初期状態
        assert state.remaining_turns == 10
        assert state.can_continue() is True

        # ターン消費
        state.turns_used = 5
        assert state.remaining_turns == 5
        assert state.can_continue() is True

        # ターン枯渇
        state.turns_used = 10
        assert state.remaining_turns == 0
        assert state.can_continue() is False

        # エラー累積
        state.turns_used = 5
        state.error_count = 3
        assert state.can_continue() is False


@pytest.mark.spec("SPEC-FIVE-STAGE-003")
class TestContentValidation:
    """コンテンツ検証のテスト"""

    @pytest.mark.asyncio
    async def test_validation_with_errors(self, mock_claude_service):
        """エラーありコンテンツの検証テスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        # JSON混入コンテンツ
        content_with_json = """
        第001話 テスト
        {"metadata": "test"}
        本文
        """

        cleaned = await executor._validate_and_clean_output(content_with_json, ExecutionStage.INITIAL_WRITING)

        # JSONが除去されている
        assert "metadata" not in cleaned
        assert "本文" in cleaned

    def test_auto_cleaning_comprehensive(self, mock_claude_service):
        """包括的自動クリーニングテスト"""
        executor = UnifiedSessionExecutor(mock_claude_service)

        dirty_content = """
        ## 指示: 執筆してください

        [System] Starting execution

        第001話 テスト

        {"metadata": {"stage": "writing"}}

        ```json
        {"config": "test"}
        ```

        実際の内容です。

        DEBUG: Processing complete
        """

        cleaned = executor._auto_clean_content(dirty_content)

        # 各種不要要素が除去されている
        assert "指示:" not in cleaned
        assert "[System]" not in cleaned
        assert "metadata" not in cleaned
        assert "```json" not in cleaned
        assert "DEBUG:" not in cleaned

        # 必要な内容は残っている
        assert "第001話" in cleaned
        assert "実際の内容です。" in cleaned
