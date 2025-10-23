"""自動連鎖実行プロット生成ユースケース"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.interfaces.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.application.use_cases.previous_episode_analysis_use_case import (
    PreviousEpisodeAnalysisRequest,
    PreviousEpisodeAnalysisUseCase,
)
from noveler.domain.entities.auto_chaining_stage import AutoChainingStage, ChainStage
from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass
class AutoChainingPlotGenerationRequest:
    """自動連鎖実行プロット生成リクエスト"""

    episode_number: int
    project_root: Path | None = None
    save_prompt: bool = True
    save_analysis: bool = True
    force: bool = False


@dataclass
class AutoChainingPlotGenerationResponse:
    """自動連鎖実行プロット生成レスポンス"""

    success: bool
    execution_id: str
    episode_number: int
    completed_stages: list[str]
    failed_stages: list[str]
    final_output_path: Path | None = None
    error_message: str | None = None
    execution_summary: dict[str, Any] | None = None
    progress_percentage: float = 0.0
    total_duration_seconds: float | None = None


class AutoChainingPlotGenerationUseCase(
    AbstractUseCase[AutoChainingPlotGenerationRequest, AutoChainingPlotGenerationResponse]
):
    """自動連鎖実行プロット生成ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        previous_episode_analysis_use_case: PreviousEpisodeAnalysisUseCase | None = None,
        **kwargs) -> None:
        """初期化

        DDD準拠: 依存性注入パターン対応
        Args:
            previous_episode_analysis_use_case: 前話分析ユースケース（依存性注入）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        self.previous_episode_analysis_use_case = previous_episode_analysis_use_case or PreviousEpisodeAnalysisUseCase()

    async def execute(self, request: AutoChainingPlotGenerationRequest) -> AutoChainingPlotGenerationResponse:
        """自動連鎖実行を実行"""
        episode_number_vo = EpisodeNumber(request.episode_number)
        auto_chaining_stage = AutoChainingStage(episode_number_vo)

        start_time = datetime.now(timezone.utc)

        try:
            # Stage 1 から 4 まで順次実行
            for stage in [ChainStage.STAGE_1, ChainStage.STAGE_2, ChainStage.STAGE_3, ChainStage.STAGE_4]:
                success = await self._execute_single_stage(auto_chaining_stage, stage, request)

                if not success:
                    # 失敗した場合は実行を停止
                    break

                # 次のステージがある場合、自動的に次のステージ実行指示をプロンプトに組み込む
                if auto_chaining_stage.has_next_stage():
                    next_stage = auto_chaining_stage.get_next_stage()
                    next_command = self._generate_next_stage_command(request.episode_number, next_stage)
                    auto_chaining_stage.complete_stage(
                        stage, output_data={"generated": True}, next_command=next_command
                    )

            end_time = datetime.now(timezone.utc)

            return AutoChainingPlotGenerationResponse(
                success=not auto_chaining_stage.has_failed_stage(),
                execution_id=auto_chaining_stage.execution_id,
                episode_number=request.episode_number,
                completed_stages=[s.value for s in auto_chaining_stage.get_completed_stages()],
                failed_stages=[s.value for s in auto_chaining_stage.get_failed_stages()],
                final_output_path=self._get_final_output_path(request.episode_number, request.project_root),
                execution_summary=auto_chaining_stage.generate_summary(),
                progress_percentage=auto_chaining_stage.get_progress_percentage(),
                total_duration_seconds=(end_time - start_time).total_seconds(),
            )

        except Exception as e:
            return AutoChainingPlotGenerationResponse(
                success=False,
                execution_id=auto_chaining_stage.execution_id,
                episode_number=request.episode_number,
                completed_stages=[s.value for s in auto_chaining_stage.get_completed_stages()],
                failed_stages=[s.value for s in auto_chaining_stage.get_failed_stages()],
                error_message=str(e),
                execution_summary=auto_chaining_stage.generate_summary(),
                progress_percentage=auto_chaining_stage.get_progress_percentage(),
                total_duration_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
            )

    async def _execute_single_stage(
        self, auto_chaining_stage: AutoChainingStage, stage: ChainStage, request: AutoChainingPlotGenerationRequest
    ) -> bool:
        """単一ステージの実行"""
        try:
            auto_chaining_stage.start_stage(stage)

            # 既存のPreviousEpisodeAnalysisUseCaseを利用してステージ実行
            analysis_request = PreviousEpisodeAnalysisRequest(
                episode_number=request.episode_number,
                stage=self._convert_stage_to_int(stage),
                project_root=request.project_root,
                enhanced=True,
                save_prompt=request.save_prompt,
                save_analysis=request.save_analysis,
            )

            response = await self.previous_episode_analysis_use_case.execute(analysis_request)

            if response.success:
                # 次のステージ実行コマンドを生成
                next_stage = auto_chaining_stage.get_next_stage()
                next_command = None
                if next_stage:
                    next_command = self._generate_next_stage_command(request.episode_number, next_stage)

                auto_chaining_stage.complete_stage(
                    stage,
                    output_data={
                        "prompt_path": str(response.prompt_path) if response.prompt_path else None,
                        "analysis_path": str(response.analysis_path) if response.analysis_path else None,
                        "final_score": response.final_score,
                    },
                    next_command=next_command,
                )

                return True
            auto_chaining_stage.fail_stage(stage, response.error_message or "Unknown error")
            return False

        except Exception as e:
            auto_chaining_stage.fail_stage(stage, str(e))
            return False

    def _convert_stage_to_int(self, stage: ChainStage) -> int:
        """ChainStageを整数に変換"""
        stage_mapping = {ChainStage.STAGE_1: 1, ChainStage.STAGE_2: 2, ChainStage.STAGE_3: 3, ChainStage.STAGE_4: 4}
        return stage_mapping[stage]

    def _generate_next_stage_command(self, episode_number: int, next_stage: ChainStage) -> str:
        """次のステージ実行コマンドを生成"""
        stage_number = self._convert_stage_to_int(next_stage)
        return f"novel plot episode {episode_number} --stage {stage_number}"

    def _get_final_output_path(self, episode_number: int, project_root: Path | None) -> Path | None:
        """最終出力パスを取得"""
        if not project_root:
            return None

        # パスサービス使用（DI注入による依存性解決）
        path_service = self.get_path_service(project_root)
        plot_dir = path_service.get_plot_dir()

        return plot_dir / f"第{episode_number:03d}話_自動連鎖実行完成版.yaml"

    def generate_stage_embedded_prompt(self, stage: ChainStage, episode_number: int, base_prompt: str) -> str:
        """ステージに次の実行指示を埋め込んだプロンプトを生成"""
        next_stage_instruction = ""

        if stage != ChainStage.STAGE_4:  # 最後のステージでない場合:
            next_stage = self._get_next_stage_from_current(stage)
            if next_stage:
                stage_num = self._convert_stage_to_int(next_stage)
                next_stage_instruction = f"""

## 🔄 次ステージ自動実行指示

この作業完了後、自動的に次のコマンドを実行してください：

```bash
novel plot episode {episode_number} --stage {stage_num}
```

**重要**: この指示は自動連鎖実行システムの一部です。作業完了と同時に上記コマンドを実行し、Stage {stage_num} の処理に進んでください。
"""

        return base_prompt + next_stage_instruction

    def _get_next_stage_from_current(self, current_stage: ChainStage) -> ChainStage | None:
        """現在のステージから次のステージを取得"""
        stage_order = [ChainStage.STAGE_1, ChainStage.STAGE_2, ChainStage.STAGE_3, ChainStage.STAGE_4]

        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass

        return None
