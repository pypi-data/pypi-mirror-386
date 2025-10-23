#!/usr/bin/env python3

"""Application.use_cases.stepwise_writing_use_case
Where: Application use case supporting stepwise writing sessions.
What: Advances the author through planning, drafting, and review steps interactively.
Why: Helps writers progress methodically without missing key steps or checks.
"""

from __future__ import annotations


import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:

    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from pathlib import Path

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.services.step_output_manager import StepOutputManager

# ステップサービスのインポート
from noveler.domain.services.step_selector_service import StepSelectorService
from noveler.domain.services.work_file_manager import WorkFileManager
from noveler.domain.services.writing_steps.character_consistency_service import CharacterConsistencyService
from noveler.domain.services.writing_steps.dialogue_designer_service import DialogueDesignerService
from noveler.domain.services.writing_steps.emotion_curve_designer_service import EmotionCurveDesignerService
from noveler.domain.services.writing_steps.logic_validator_service import LogicValidatorService
from noveler.domain.services.writing_steps.manuscript_generator_service import ManuscriptGeneratorService
from noveler.domain.services.writing_steps.phase_structure_designer_service import PhaseStructureDesignerService
from noveler.domain.services.writing_steps.props_world_building_service import PropsWorldBuildingService
from noveler.domain.services.writing_steps.publishing_preparation_service import PublishingPreparationService
from noveler.domain.services.writing_steps.quality_certification_service import QualityCertificationService
from noveler.domain.services.writing_steps.quality_gate_service import QualityGateService
from noveler.domain.services.writing_steps.readability_optimizer_service import ReadabilityOptimizerService
from noveler.domain.services.writing_steps.scene_designer_service import SceneDesignerService
from noveler.domain.services.writing_steps.scene_setting_service import SceneSettingService
from noveler.domain.services.writing_steps.scope_definer_service import ScopeDefinerService
from noveler.domain.services.writing_steps.section_balance_optimizer_service import SectionBalanceOptimizerService

# A38準拠：追加実装済みサービス
from noveler.domain.services.writing_steps.story_structure_designer_service import StoryStructureDesignerService
from noveler.domain.services.writing_steps.text_length_optimizer_service import TextLengthOptimizerService
from noveler.domain.services.writing_steps.theme_uniqueness_validator_service import ThemeUniquenessValidatorService


@dataclass
class StepwiseWritingRequest:
    """ステップワイズ執筆リクエスト"""

    # 基本設定
    project_root: Path
    episode_number: int

    # ステップ制御
    step_pattern: str = "all"  # "all", "0-5", "scope", ".*optimizer", etc.
    resume_from_cache: bool = True
    save_intermediate_results: bool = True

    # 実行設定
    parallel_execution: bool = False
    max_retry_count: int = 2
    timeout_seconds: int = 300

    # 出力制御
    verbose_logging: bool = False
    generate_reports: bool = True

    # カスタマイズ
    custom_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepExecutionResult:
    """ステップ実行結果"""

    step_number: int
    step_name: str
    success: bool
    execution_time_ms: float = 0.0

    # 結果データ
    result_data: Any | None = None
    error_message: str | None = None

    # メタデータ
    retry_count: int = 0
    cached_result: bool = False
    performance_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepwiseWritingResponse:
    """ステップワイズ執筆レスポンス"""

    success: bool
    episode_number: int
    project_root: Path

    # 実行結果
    executed_steps: list[int] = field(default_factory=list)
    step_results: dict[int, StepExecutionResult] = field(default_factory=dict)

    # 全体統計
    total_execution_time_ms: float = 0.0
    successful_steps: int = 0
    failed_steps: int = 0
    cached_steps: int = 0

    # 最終状態
    final_manuscript_path: Path | None = None
    quality_score: float | None = None
    approval_status: str = "pending"

    # ログ・レポート
    execution_log: list[str] = field(default_factory=list)
    error_summary: list[str] = field(default_factory=list)
    report_path: Path | None = None


class StepwiseWritingUseCase(AbstractUseCase[StepwiseWritingRequest, StepwiseWritingResponse]):
    """ステップワイズ執筆ユースケース

    15ステップの段階的執筆プロセスを統合管理し、
    効率的で高品質な小説執筆を支援する統合システム。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWork = None,
        path_service: IPathService = None,
        **kwargs: Any
    ) -> None:
        """ステップワイズ執筆ユースケース初期化

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            path_service: パスサービス
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)

        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        self._path_service = path_service

        # コアサービス初期化
        self._step_selector = StepSelectorService()
        self._work_file_manager = WorkFileManager()

        # A38ステップ出力保存サービス初期化
        self._step_output_manager = StepOutputManager(path_service) if path_service else None

        # ステップサービス初期化
        self._step_services = self._initialize_step_services()

    def _initialize_step_services(self) -> dict[int, Any]:
        """A38ガイド準拠：全ステップサービス初期化（STEP2.5→STEP3へ統一）"""
        return {
            # 構造設計フェーズ（小数ステップを整数に統一）
            0: ScopeDefinerService(
                logger=self._logger_service if hasattr(self, "_logger_service") else None,
                path_service=self._path_service,
            ),
            1: StoryStructureDesignerService(),
            2: PhaseStructureDesignerService(),
            3: ThemeUniquenessValidatorService(),          # 旧2.5 → 3
            4: SectionBalanceOptimizerService(),
            5: SceneDesignerService(),
            6: LogicValidatorService(),
            7: CharacterConsistencyService(),
            8: DialogueDesignerService(),
            9: EmotionCurveDesignerService(),
            10: SceneSettingService(),

            # 執筆実装フェーズ
            11: ManuscriptGeneratorService(
                logger_service=self._logger_service,
                path_service=self._path_service
            ),
            12: PropsWorldBuildingService(),
            13: ManuscriptGeneratorService(
                logger_service=self._logger_service,
                path_service=self._path_service
            ),              # 従来の初稿生成位置は維持
            14: TextLengthOptimizerService(),
            15: ReadabilityOptimizerService(),

            # 品質保証・公開フェーズ
            16: QualityGateService(),
            17: QualityCertificationService(),
            18: PublishingPreparationService()
        }

    async def execute(self, request: StepwiseWritingRequest) -> StepwiseWritingResponse:
        """ステップワイズ執筆実行

        Args:
            request: 実行リクエスト

        Returns:
            StepwiseWritingResponse: 実行結果
        """
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(
                    f"ステップワイズ執筆開始: エピソード={request.episode_number}, "
                    f"パターン={request.step_pattern}"
                )

            # 1. 実行ステップ決定
            target_steps = self._step_selector.parse_step_pattern(request.step_pattern)

            if not target_steps:
                return self._create_error_response(
                    request, "有効なステップパターンが指定されていません", start_time
                )

            # 2. キャッシュ・作業ファイル準備
            work_context = await self._prepare_work_context(request, target_steps)

            # 3. ステップ実行
            step_results = {}
            execution_log = []

            if request.parallel_execution and len(target_steps) > 1:
                # 並列実行（依存関係を考慮）
                step_results = await self._execute_steps_parallel(
                    target_steps, request, work_context, execution_log
                )
            else:
                # 順次実行
                step_results = await self._execute_steps_sequential(
                    target_steps, request, work_context, execution_log
                )

            # 4. 結果統合・保存
            if request.save_intermediate_results:
                await self._save_intermediate_results(request, step_results)

            # 5. 最終状態評価
            final_manuscript_path, quality_score, approval_status = \
                await self._evaluate_final_state(request, step_results)

            # 6. レポート生成
            report_path = None
            if request.generate_reports:
                report_path = await self._generate_execution_report(
                    request, step_results, execution_log
                )

            # 7. 成功レスポンス作成
            total_time = (time.time() - start_time) * 1000
            successful_steps = sum(1 for result in step_results.values() if result.success)
            failed_steps = len(step_results) - successful_steps
            cached_steps = sum(1 for result in step_results.values() if result.cached_result)

            return StepwiseWritingResponse(
                success=True,
                episode_number=request.episode_number,
                project_root=request.project_root,
                executed_steps=target_steps,
                step_results=step_results,
                total_execution_time_ms=total_time,
                successful_steps=successful_steps,
                failed_steps=failed_steps,
                cached_steps=cached_steps,
                final_manuscript_path=final_manuscript_path,
                quality_score=quality_score,
                approval_status=approval_status,
                execution_log=execution_log,
                report_path=report_path
            )

        except Exception as e:
            return self._create_error_response(request, str(e), start_time)

    async def _prepare_work_context(
        self,
        request: StepwiseWritingRequest,
        target_steps: list[int]
    ) -> dict[str, Any]:
        """作業コンテキスト準備"""
        work_context = {
            "episode_number": request.episode_number,
            "project_root": request.project_root,
            "target_steps": target_steps,
            "cached_results": {},
            "work_files": {}
        }

        # キャッシュから既存結果を読み込み
        if request.resume_from_cache:
            for step_num in target_steps:
                try:
                    cached_result = await self._work_file_manager.load_work_file(
                        request.episode_number, step_num
                    )
                    if cached_result:
                        work_context["cached_results"][step_num] = cached_result

                        if self._logger_service:
                            self._logger_service.debug(f"キャッシュからSTEP {step_num}の結果を復元")

                except Exception as e:
                    if self._logger_service:
                        self._logger_service.warning(f"STEP {step_num}のキャッシュ読み込み失敗: {e}")

        return work_context

    async def _execute_steps_sequential(
        self,
        target_steps: list[int],
        request: StepwiseWritingRequest,
        work_context: dict[str, Any],
        execution_log: list[str]
    ) -> dict[int, StepExecutionResult]:
        """順次ステップ実行"""
        step_results = {}
        previous_results = {}

        for step_num in sorted(target_steps):
            # キャッシュチェック
            if step_num in work_context["cached_results"]:
                cached_result = work_context["cached_results"][step_num]
                step_results[step_num] = StepExecutionResult(
                    step_number=step_num,
                    step_name=cached_result.step_name if hasattr(cached_result, "step_name") else f"step_{step_num}",
                    success=True,
                    execution_time_ms=0.0,
                    result_data=cached_result,
                    cached_result=True
                )
                previous_results[step_num] = cached_result
                execution_log.append(f"STEP {step_num}: キャッシュから復元")
                continue

            # ステップ実行
            step_start = time.time()
            execution_log.append(f"STEP {step_num}: 実行開始")

            try:
                # リトライ実行
                result_data = None
                error_msg = None
                retry_count = 0

                for attempt in range(request.max_retry_count + 1):
                    try:
                        result_data = await self._execute_single_step(
                            step_num, request.episode_number, previous_results
                        )
                        break

                    except Exception as e:
                        retry_count = attempt
                        error_msg = str(e)

                        if attempt < request.max_retry_count:
                            execution_log.append(f"STEP {step_num}: リトライ {attempt + 1}")
                            await self._wait_before_retry(attempt)
                        else:
                            execution_log.append(f"STEP {step_num}: 最大リトライ回数に達したため失敗")

                step_time = (time.time() - step_start) * 1000

                if result_data:
                    # 成功
                    step_results[step_num] = StepExecutionResult(
                        step_number=step_num,
                        step_name=result_data.step_name if hasattr(result_data, "step_name") else f"step_{step_num}",
                        success=True,
                        execution_time_ms=step_time,
                        result_data=result_data,
                        retry_count=retry_count
                    )
                    previous_results[step_num] = result_data

                    # 作業ファイル保存
                    if request.save_intermediate_results:
                        # オブジェクトを辞書に変換
                        if hasattr(result_data, "__dict__"):
                            content_dict = result_data.__dict__
                        elif hasattr(result_data, "_asdict"):
                            content_dict = result_data._asdict()
                        else:
                            content_dict = {"result": result_data}

                        self._work_file_manager.save_work_file_with_version(
                            request.episode_number, step_num, content_dict, False
                        )

                    execution_log.append(f"STEP {step_num}: 成功 ({step_time:.1f}ms)")
                else:
                    # 失敗
                    step_results[step_num] = StepExecutionResult(
                        step_number=step_num,
                        step_name=f"step_{step_num}",
                        success=False,
                        execution_time_ms=step_time,
                        error_message=error_msg,
                        retry_count=retry_count
                    )
                    execution_log.append(f"STEP {step_num}: 失敗 - {error_msg}")

            except Exception as e:
                step_time = (time.time() - step_start) * 1000
                step_results[step_num] = StepExecutionResult(
                    step_number=step_num,
                    step_name=f"step_{step_num}",
                    success=False,
                    execution_time_ms=step_time,
                    error_message=str(e)
                )
                execution_log.append(f"STEP {step_num}: 例外エラー - {e}")

        return step_results

    async def _execute_steps_parallel(
        self,
        target_steps: list[int],
        request: StepwiseWritingRequest,
        work_context: dict[str, Any],
        execution_log: list[str]
    ) -> dict[int, StepExecutionResult]:
        """並列ステップ実行（依存関係考慮）"""
        # 現在は順次実行で代替（将来の並列実装への拡張ポイント）
        execution_log.append("並列実行は現在開発中のため、順次実行で代替")

        return await self._execute_steps_sequential(
            target_steps, request, work_context, execution_log
        )

    async def _execute_single_step(
        self,
        step_number: int,
        episode_number: int,
        previous_results: dict[int, Any]
    ) -> Any:
        """単一ステップ実行"""
        if step_number not in self._step_services:
            msg = f"未実装のステップ番号: {step_number}"
            raise ValueError(msg)

        step_service = self._step_services[step_number]

        # ステップ実行
        result = await step_service.execute(episode_number, previous_results)

        if not result or not hasattr(result, "success") or not result.success:
            error_msg = getattr(result, "error_message", "実行失敗") if result else "結果なし"
            msg = f"STEP {step_number} 実行失敗: {error_msg}"
            raise RuntimeError(msg)

        # A38ステップ出力保存機能（StepOutputManagerが利用可能な場合のみ）
        if self._step_output_manager and result:
            try:
                await self._save_step_output(
                    episode_number=episode_number,
                    step_number=step_number,
                    step_result=result
                )
            except Exception as e:
                # ステップ出力保存の失敗は警告に留める（実行を中断しない）
                if self._logger_service:
                    self._logger_service.warning(
                        f"STEP {step_number} 出力保存失敗: {e}",
                        extra={"episode_number": episode_number, "step_number": step_number}
                    )

        return result

    async def _wait_before_retry(self, attempt: int) -> None:
        """リトライ前の待機"""
        wait_time = min(1.0 * (2 ** attempt), 10.0)  # 指数バックオフ（最大10秒）
        await asyncio.sleep(wait_time)

    async def _save_intermediate_results(
        self,
        request: StepwiseWritingRequest,
        step_results: dict[int, StepExecutionResult]
    ) -> None:
        """中間結果保存"""
        for step_num, result in step_results.items():
            if result.success and result.result_data and not result.cached_result:
                try:
                    await self._work_file_manager.save_work_file(
                        request.episode_number, step_num, 1, result.result_data
                    )
                except Exception as e:
                    if self._logger_service:
                        self._logger_service.warning(f"STEP {step_num}の結果保存失敗: {e}")

    async def _evaluate_final_state(
        self,
        request: StepwiseWritingRequest,
        step_results: dict[int, StepExecutionResult]
    ) -> tuple[Path | None, float | None, str]:
        """最終状態評価"""
        final_manuscript_path = None
        quality_score = None
        approval_status = "pending"

        # STEP 11 (原稿生成) の結果から原稿パス取得（STEP繰上げ）
        if 11 in step_results and step_results[11].success:
            step11_result = step_results[11].result_data
            if hasattr(step11_result, "manuscript_path"):
                final_manuscript_path = step11_result.manuscript_path

        # STEP 13 (レビュー統合) から品質・承認状況取得（STEP繰上げ）
        if 13 in step_results and step_results[13].success:
            step13_result = step_results[13].result_data
            if hasattr(step13_result, "review_result"):
                review_result = step13_result.review_result
                if review_result:
                    quality_score = getattr(review_result, "overall_quality_score", None)
                    approval_status = getattr(review_result, "approval_status", "pending")

        # STEP 14 (品質ゲート) からの品質情報（STEP繰上げ）
        if 14 in step_results and step_results[14].success:
            step14_result = step_results[14].result_data
            if hasattr(step14_result, "quality_result"):
                quality_result = step14_result.quality_result
                if quality_result and hasattr(quality_result, "overall_score"):
                    quality_score = quality_result.overall_score

                    # 品質ゲート通過判定
                    if quality_result.gate_passed:
                        approval_status = "approved"
                    elif approval_status == "pending":
                        approval_status = "needs_revision"

        return final_manuscript_path, quality_score, approval_status

    async def _generate_execution_report(
        self,
        request: StepwiseWritingRequest,
        step_results: dict[int, StepExecutionResult],
        execution_log: list[str]
    ) -> Path | None:
        """実行レポート生成"""
        try:
            if self._path_service:
                reports_dir = self._path_service.get_reports_dir()
            else:
                reports_dir = request.project_root / "reports"

            reports_dir.mkdir(parents=True, exist_ok=True)

            # レポートファイル名
            report_filename = f"stepwise_execution_ep{request.episode_number:03d}_{int(time.time())}.md"
            report_path = reports_dir / report_filename

            # レポート内容生成
            report_content = self._create_report_content(
                request, step_results, execution_log
            )

            # レポート保存
            report_path.write_text(report_content, encoding="utf-8")

            return report_path

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"実行レポート生成失敗: {e}")
            return None

    def _create_report_content(
        self,
        request: StepwiseWritingRequest,
        step_results: dict[int, StepExecutionResult],
        execution_log: list[str]
    ) -> str:
        """レポート内容作成"""

        content = f"""# ステップワイズ執筆実行レポート

## 基本情報
- **エピソード番号**: {request.episode_number}
- **実行日時**: {project_now().datetime.strftime('%Y-%m-%d %H:%M:%S')}
- **プロジェクト**: {request.project_root.name}
- **ステップパターン**: {request.step_pattern}

## 実行統計
- **総実行時間**: {sum(result.execution_time_ms for result in step_results.values()):.1f}ms
- **成功ステップ**: {sum(1 for result in step_results.values() if result.success)}
- **失敗ステップ**: {sum(1 for result in step_results.values() if not result.success)}
- **キャッシュ活用**: {sum(1 for result in step_results.values() if result.cached_result)}

## ステップ別結果

"""

        for step_num in sorted(step_results.keys()):
            result = step_results[step_num]
            status_icon = "✅" if result.success else "❌"
            cache_note = " (キャッシュ)" if result.cached_result else ""

            content += f"""### STEP {step_num}: {result.step_name} {status_icon}{cache_note}

- **実行時間**: {result.execution_time_ms:.1f}ms
- **リトライ回数**: {result.retry_count}
"""

            if result.error_message:
                content += f"- **エラー**: {result.error_message}\n"

            content += "\n"

        content += f"""## 実行ログ

```
{chr(10).join(execution_log)}
```

---
*このレポートは StepwiseWritingUseCase により自動生成されました*
"""

        return content

    def _create_error_response(
        self,
        request: StepwiseWritingRequest,
        error_message: str,
        start_time: float
    ) -> StepwiseWritingResponse:
        """エラーレスポンス作成"""
        total_time = (time.time() - start_time) * 1000

        return StepwiseWritingResponse(
            success=False,
            episode_number=request.episode_number,
            project_root=request.project_root,
            total_execution_time_ms=total_time,
            error_summary=[error_message],
            execution_log=[f"エラー: {error_message}"]
        )

    async def _save_step_output(
        self,
        episode_number: int,
        step_number: int,
        step_result: Any,
    ) -> None:
        """A38ステップ出力を保存

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号
            step_result: ステップ実行結果
        """
        if not self._step_output_manager:
            return

        # ステップ名を取得（ステップ番号からサービス名を推定）
        step_service = self._step_services.get(step_number)
        step_name = f"STEP{step_number:02d}"

        if step_service:
            step_name = f"STEP{step_number:02d}_{step_service.__class__.__name__}"

        # LLM応答内容の抽出
        llm_response_content = ""
        structured_data = {}
        quality_metrics = {}
        execution_metadata = {}

        if hasattr(step_result, "response_content"):
            llm_response_content = str(step_result.response_content)

        if hasattr(step_result, "extracted_data"):
            structured_data = step_result.extracted_data or {}

        if hasattr(step_result, "quality_score"):
            quality_metrics["quality_score"] = step_result.quality_score

        if hasattr(step_result, "execution_time_ms"):
            execution_metadata["execution_time_ms"] = step_result.execution_time_ms

        if hasattr(step_result, "metadata"):
            execution_metadata.update(step_result.metadata or {})

        # StructuredStepOutput形式での保存を試みる
        if hasattr(step_result, "to_dict"):
            try:
                # StructuredStepOutput形式の場合
                await self._step_output_manager.save_structured_step_output(
                    episode_number=episode_number,
                    step_number=step_number,
                    structured_output=step_result,
                    llm_response_content=llm_response_content,
                )
                return
            except Exception:
                # フォールバック: 通常の保存方式
                pass

        # 通常の辞書形式での保存
        await self._step_output_manager.save_step_output(
            episode_number=episode_number,
            step_number=step_number,
            step_name=step_name,
            llm_response_content=llm_response_content,
            structured_data=structured_data,
            quality_metrics=quality_metrics,
            execution_metadata=execution_metadata,
        )

    async def execute_with_plot_integration(
        self,
        episode_number: int,
        project_root: Path | None = None
    ) -> StepwiseWritingResponse:
        """プロット統合執筆ワークフロー実行（SPEC-PLOT-MANUSCRIPT-001で追加）

        プロット解析（STEP 1）と原稿生成（STEP 10）の統合ワークフローを実行。

        Args:
            episode_number: エピソード番号
            project_root: プロジェクトルート（省略時は現在のディレクトリ）

        Returns:
            StepwiseWritingResponse: 統合ワークフロー実行結果
        """
        if project_root is None:
            project_root = Path.cwd()

        # プロット→原稿変換に必要なステップのみを実行
        request = StepwiseWritingRequest(
            project_root=project_root,
            episode_number=episode_number,
            step_pattern="1,10",  # STEP 1（プロット解析） + STEP 10（原稿生成）
            resume_from_cache=False,  # 最新結果を確実に取得
            save_intermediate_results=True,
            verbose_logging=True,
            generate_reports=True
        )

        return await self.execute(request)
