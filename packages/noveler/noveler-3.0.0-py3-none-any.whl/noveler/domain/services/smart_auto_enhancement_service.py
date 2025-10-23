"""Smart Auto-Enhancement Domain Service

SPEC-SAE-002: Smart Auto-Enhancement ドメインサービス仕様
- 複数の品質チェック段階を統合実行するドメインサービス
- 既存のA31評価、Claude分析サービスを協調させる
- DDD原則に基づくドメインロジックの実装
"""

import time
from typing import Protocol

from noveler.domain.entities.smart_auto_enhancement import (
    EnhancementRequest,
    EnhancementResult,
    EnhancementStage,
    SmartAutoEnhancement,
)
from noveler.domain.value_objects.quality_score import QualityScore


class BasicQualityChecker(Protocol):
    """基本品質チェッカー インターフェース"""

    def check_quality(self, episode_content: str) -> tuple[QualityScore, list[str]]:
        """基本品質チェックを実行"""
        ...


class A31Evaluator(Protocol):
    """A31評価器 インターフェース"""

    async def evaluate(self, project_name: str, episode_number: int, episode_content: str) -> tuple[QualityScore, dict]:
        """A31評価を実行"""
        ...


class ClaudeAnalyzer(Protocol):
    """Claude分析器 インターフェース"""

    async def analyze(self, project_name: str, episode_number: int, a31_results: dict) -> tuple[QualityScore, dict]:
        """Claude分析を実行"""
        ...


class SmartAutoEnhancementService:
    """Smart Auto-Enhancement ドメインサービス

    複数の品質チェック段階を統合実行し、結果を統合するドメインサービス。
    既存のサービスを協調させ、Smart Auto-Enhancement のビジネスロジックを実装。
    """

    def __init__(
        self, basic_checker: BasicQualityChecker, a31_evaluator: A31Evaluator, claude_analyzer: ClaudeAnalyzer
    ) -> None:
        self._basic_checker = basic_checker
        self._a31_evaluator = a31_evaluator
        self._claude_analyzer = claude_analyzer

    async def execute_enhancement(
        self, enhancement: SmartAutoEnhancement, episode_content: str
    ) -> SmartAutoEnhancement:
        """拡張チェックを実行

        Args:
            enhancement: 拡張エンティティ
            episode_content: エピソード内容

        Returns:
            実行結果が反映された拡張エンティティ
        """
        try:
            # 段階1: 基本品質チェック
            if enhancement.should_execute_stage(EnhancementStage.BASIC_CHECK):
                await self._execute_basic_check(enhancement, episode_content)
                # 失敗した場合は以降の段階をスキップ
                if enhancement.current_stage == EnhancementStage.FAILED:
                    return enhancement

            # 段階2: A31評価
            if enhancement.should_execute_stage(EnhancementStage.A31_EVALUATION):
                await self._execute_a31_evaluation(enhancement, episode_content)
                # 失敗した場合は以降の段階をスキップ
                if enhancement.current_stage == EnhancementStage.FAILED:
                    return enhancement

            # 段階3: Claude分析
            if enhancement.should_execute_stage(EnhancementStage.CLAUDE_ANALYSIS):
                await self._execute_claude_analysis(enhancement)
                # 失敗した場合は完了処理をスキップ
                if enhancement.current_stage == EnhancementStage.FAILED:
                    return enhancement

            # 完了状態に移行
            enhancement.advance_to_stage(EnhancementStage.COMPLETED)

        except Exception as e:
            # エラー時は失敗状態に移行
            error_result = EnhancementResult(
                stage=EnhancementStage.FAILED,
                basic_score=None,
                a31_score=None,
                claude_score=None,
                execution_time_ms=enhancement.get_execution_duration_ms(),
                improvements_count=0,
                error_message=str(e),
            )

            enhancement.add_stage_result(EnhancementStage.FAILED, error_result)

        return enhancement

    async def _execute_basic_check(self, enhancement: SmartAutoEnhancement, episode_content: str) -> None:
        """基本品質チェックを実行"""

        start_time = time.time()

        try:
            score, issues = self._basic_checker.check_quality(episode_content)

            result = EnhancementResult(
                stage=EnhancementStage.BASIC_CHECK,
                basic_score=score,
                a31_score=None,
                claude_score=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=len(issues),
                error_message=None,
                analysis_data=None,
            )

            enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, result)
            # 結果が成功の場合のみ次の段階に進む
            if result.is_success():
                enhancement.advance_to_stage(EnhancementStage.A31_EVALUATION)

        except Exception as e:
            result = EnhancementResult(
                stage=EnhancementStage.BASIC_CHECK,
                basic_score=None,
                a31_score=None,
                claude_score=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=0,
                error_message=f"基本チェックエラー: {e!s}",
                analysis_data=None,
            )

            enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, result)
            # 基本チェックでエラーが発生した場合は失敗状態に移行
            enhancement.advance_to_stage(EnhancementStage.FAILED)
            return

    async def _execute_a31_evaluation(self, enhancement: SmartAutoEnhancement, episode_content: str) -> None:
        """A31評価を実行"""

        start_time = time.time()

        try:
            score, a31_results = await self._a31_evaluator.evaluate(
                enhancement.request.project_info.name, enhancement.request.episode_number.value, episode_content
            )

            # A31結果の改善提案数を計算
            improvements_count = self._count_a31_improvements(a31_results)

            result = EnhancementResult(
                stage=EnhancementStage.A31_EVALUATION,
                basic_score=None,
                a31_score=score,
                claude_score=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=improvements_count,
                error_message=None,
                analysis_data=None,
            )

            enhancement.add_stage_result(EnhancementStage.A31_EVALUATION, result)
            # 結果が成功の場合のみ次の段階に進む
            if result.is_success():
                enhancement.advance_to_stage(EnhancementStage.CLAUDE_ANALYSIS)

        except Exception as e:
            result = EnhancementResult(
                stage=EnhancementStage.A31_EVALUATION,
                basic_score=None,
                a31_score=None,
                claude_score=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=0,
                error_message=f"A31評価エラー: {e!s}",
                analysis_data=None,
            )

            enhancement.add_stage_result(EnhancementStage.A31_EVALUATION, result)
            # A31評価でエラーが発生した場合は失敗状態に移行
            enhancement.advance_to_stage(EnhancementStage.FAILED)
            return

    async def _execute_claude_analysis(self, enhancement: SmartAutoEnhancement) -> None:
        """Claude分析を実行"""

        start_time = time.time()

        try:
            # A31結果を取得
            a31_result = enhancement.get_stage_result(EnhancementStage.A31_EVALUATION)
            if not a31_result:
                msg = "A31評価結果が見つかりません"
                raise ValueError(msg)

            # A31結果からデータを取得（実装依存）
            a31_results = {}  # 実際の実装では適切なデータを取得

            score, claude_results = await self._claude_analyzer.analyze(
                enhancement.request.project_info.name, enhancement.request.episode_number.value, a31_results
            )

            # Claude結果の改善提案数を計算
            improvements_count = self._count_claude_improvements(claude_results)

            result = EnhancementResult(
                stage=EnhancementStage.CLAUDE_ANALYSIS,
                basic_score=None,
                a31_score=None,
                claude_score=score,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=improvements_count,
                error_message=None,
                analysis_data=claude_results,  # Claude分析結果の詳細データを保存
            )

            enhancement.add_stage_result(EnhancementStage.CLAUDE_ANALYSIS, result)

        except Exception as e:
            result = EnhancementResult(
                stage=EnhancementStage.CLAUDE_ANALYSIS,
                basic_score=None,
                a31_score=None,
                claude_score=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                improvements_count=0,
                error_message=f"Claude分析エラー: {e!s}",
                analysis_data=None,
            )

            enhancement.add_stage_result(EnhancementStage.CLAUDE_ANALYSIS, result)
            # Claude分析でエラーが発生した場合は失敗状態に移行
            enhancement.advance_to_stage(EnhancementStage.FAILED)
            return

    def _count_a31_improvements(self, a31_results: dict) -> int:
        """A31結果から改善提案数を計算"""
        # 実装依存：A31結果の構造に基づいて改善提案数を計算
        return 0

    def _count_claude_improvements(self, claude_results: dict) -> int:
        """Claude結果から改善提案数を計算"""
        # 実装依存：Claude結果の構造に基づいて改善提案数を計算
        return 0

    def should_enable_smart_auto_mode(self, request: EnhancementRequest) -> bool:
        """Smart Auto-Enhancement モードの有効性判定

        ビジネスルール:
        - リクエストがSMART_AUTOモードまたはENHANCEDモード
        - 全段階スキップではない
        - プロジェクト情報が有効
        """
        if request.mode.value in ["smart_auto", "enhanced"]:
            return True

        # 従来の判定ロジック: 全段階が有効な場合
        return bool(not (request.skip_basic and request.skip_a31 and request.skip_claude))

    def determine_display_mode(self, enhancement: SmartAutoEnhancement) -> str:
        """表示モードの決定

        Smart Auto-Enhancement では詳細表示を標準とする
        """
        if enhancement.is_smart_auto_mode or enhancement.is_enhanced_mode:
            return "detailed"

        if enhancement.request.show_detailed_review:
            return "detailed"

        return "standard"
