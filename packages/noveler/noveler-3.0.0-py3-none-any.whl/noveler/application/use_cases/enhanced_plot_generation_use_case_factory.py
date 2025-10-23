#!/usr/bin/env python3
"""強化プロット生成ユースケースファクトリー

DDD準拠：Claude Code統合対応の依存性注入管理
"""

import time
from pathlib import Path
from typing import Any

import yaml

from noveler.application.use_cases.enhanced_plot_generation_use_case import EnhancedPlotGenerationResult
from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
from noveler.application.use_cases.universal_prompt_request import UniversalPromptRequest
from noveler.application.use_cases.universal_prompt_response import UniversalPromptResponse

# DDD準拠: Infrastructure層への直接依存を除去
# from noveler.infrastructure.config.claude_code_integration_config import ClaudeCodeIntegrationConfig


class EnhancedPlotGenerationUseCaseFactory:
    """強化プロット生成ユースケースファクトリー

    DDD準拠：Claude Code統合対応の適切な依存性注入を管理
    """

    @staticmethod
    def create_use_case(
        config: object | None = None,  # DDD準拠: Infrastructure型への依存を除去
    ) -> "EnhancedPlotGenerationUseCase":
        """ユースケース作成（依存性注入）

        Args:
            config: Claude Code統合設定

        Returns:
            EnhancedPlotGenerationUseCase: 設定済みユースケース
        """
        # Claude Code統合ユースケースのDI
        try:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            from noveler.application.use_cases.universal_llm_use_case_factory import (
                UniversalLLMUseCaseFactory,
            )

            claude_use_case = UniversalLLMUseCaseFactory.create_use_case(config)
        except ImportError as e:
            msg = f"Claude Code統合ユースケースの初期化に失敗: {e}"
            raise RuntimeError(msg) from e

        # 強化プロット生成ユースケース作成（Claude Code統合版）
        return EnhancedPlotGenerationUseCase(claude_use_case=claude_use_case)


# Claude Code統合対応の強化プロット生成ユースケース
class EnhancedPlotGenerationUseCase:
    """Claude Code統合対応 強化プロット生成ユースケース

    REQ-4.2: novel plot episodeコマンドでの統合Claude Code実行
    従来のプロット生成機能を汎用Claude Code統合機能で強化
    """

    def __init__(self, claude_use_case: "UniversalLLMUseCase") -> None:
        """初期化（DDD準拠：依存性注入）

        Args:
            claude_use_case: 汎用Claude Code統合ユースケース
        """
        self.claude_use_case = claude_use_case

    async def generate_episode_plot_with_claude(
        self,
        episode_number: int,
        project_root: Path,
        mode: str = "auto",
        stage: int = 1,
        with_previous: bool = True,
        save_prompt: bool = False,
        direct_claude: bool = False,
        prompt_only: bool = False,
        ) -> EnhancedPlotGenerationResult:
        """Claude Code統合によるエピソードプロット生成

        REQ-4.2: 統合Claude Code実行によるプロット生成

        Args:
            episode_number: エピソード番号
            project_root: プロジェクトルート
            mode: 生成モード（auto, advanced, detailed）
            stage: ステージ番号（1-3）
            with_previous: 前エピソード分析含む
            save_prompt: プロンプト保存
            direct_claude: 直接Claude実行フラグ
            prompt_only: プロンプト生成のみフラグ

        Returns:
            EnhancedPlotGenerationResult: 生成結果
        """
        from noveler.domain.value_objects.universal_prompt_execution import (
            ProjectContext,
            PromptType,
            UniversalPromptRequest,
        )

        start_time = time.time()

        try:
            # プロジェクトコンテキスト構築
            project_context = ProjectContext(project_root=project_root, project_name=project_root.name)

            # プロンプト内容生成
            prompt_content = await self._build_plot_generation_prompt(
                episode_number=episode_number,
                project_root=project_root,
                mode=mode,
                stage=stage,
                with_previous=with_previous,
            )

            # 種別固有設定
            type_specific_config: dict[str, Any] = {
                "episode_number": episode_number,
                "mode": mode,
                "stage": stage,
                "with_previous": with_previous,
                "save_prompt": save_prompt,
            }

            # 汎用プロンプト実行リクエスト作成
            universal_request = UniversalPromptRequest(
                prompt_content=prompt_content,
                prompt_type=PromptType.PLOT,
                project_context=project_context,
                type_specific_config=type_specific_config,
                output_format="json",
            )

            # 実行モード分岐
            if prompt_only:
                # プロンプト生成のみ（従来モード）
                return await self._generate_prompt_only_result(universal_request, episode_number, start_time)

            if direct_claude:
                # Claude Code直接実行（フォールバックなし）
                response = await self.claude_use_case.execute_with_fallback(universal_request, fallback_enabled=False)

            else:
                # 統合実行（フォールバック付き）
                response = await self.claude_use_case.execute_with_fallback(universal_request, fallback_enabled=True)

            # 結果の変換・処理
            return await self._process_claude_response(response, episode_number, project_root, save_prompt, start_time)

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            return EnhancedPlotGenerationResult(
                success=False,
                episode_number=episode_number,
                generated_plot="",
                execution_time_ms=execution_time,
                error_message=f"プロット生成エラー: {e!s}",
            )

    async def _build_plot_generation_prompt(
        self, episode_number: int, project_root: Path, mode: str, stage: int, with_previous: bool
    ) -> str:
        """プロンプト生成プロット構築"""
        # 基本プロンプトテンプレート
        return f"""# 第{episode_number:03d}話プロット生成

        ## 生成設定
        - モード: {mode}
        - ステージ: {stage}
        - 前エピソード分析: {"有効" if with_previous else "無効"}

        ## プロジェクト情報
        - プロジェクト名: {project_root.name}
        - エピソード番号: {episode_number}

        ## 要求
        以下の形式でエピソードプロットを生成してください：

        ```yaml
        episode_info:
        episode_number: {episode_number}
        title: "エピソードタイトル"
        chapter: 1

        synopsis: |
        エピソードの概要説明

        scenes:
        - scene_number: 1
        title: "シーン1タイトル"
        description: "シーン内容説明"

        plot_structure:
        setup: "導入部分"
        development: "展開部分"
        climax: "クライマックス"
        resolution: "解決"

        quality_metrics:
        narrative_consistency: 85
        character_development_depth: 80
        plot_advancement: 90
        ```

        ## 品質基準
        - 物語の一貫性を保つ
        - キャラクター開発を考慮
        - 前後エピソードとの連続性を確保
        - 読者の興味を維持する展開
        """

    async def _generate_prompt_only_result(
        self, request: UniversalPromptRequest, episode_number: int, start_time: float
    ) -> EnhancedPlotGenerationResult:
        """プロンプト生成のみ結果作成"""

        execution_time = (time.time() - start_time) * 1000

        return EnhancedPlotGenerationResult(
            success=True,
            episode_number=episode_number,
            generated_plot="",
            prompt_content=request.prompt_content,
            execution_mode="prompt_only",
            execution_time_ms=execution_time,
            metadata={"mode": "prompt_only", "requires_manual_execution": True},
        )

    async def _process_claude_response(
        self,
        response: "UniversalPromptResponse",
        episode_number: int,
        project_root: Path,
        save_prompt: bool,
        start_time: float,
        ) -> EnhancedPlotGenerationResult:
        """Claude Code応答処理"""

        execution_time = (time.time() - start_time) * 1000

        if response.is_success():
            # プロット内容抽出
            plot_content = response.get_plot_content()

            # プロンプト保存処理
            saved_file_path = None
            if save_prompt:
                saved_file_path = await self._save_generated_plot(episode_number, plot_content, project_root)

            return EnhancedPlotGenerationResult(
                success=True,
                episode_number=episode_number,
                generated_plot=str(plot_content) if plot_content else response.response_content,
                execution_mode="claude_integrated",
                execution_time_ms=execution_time,
                saved_file_path=saved_file_path,
                quality_score=response.metadata.get("quality_score", 0.0),
                metadata=response.metadata,
            )

        # フォールバック処理結果
        fallback_mode = response.metadata.get("mode") == "fallback"

        if fallback_mode:
            return EnhancedPlotGenerationResult(
                success=True,
                episode_number=episode_number,
                generated_plot="",
                prompt_content=response.extracted_data.get("prompt_content", ""),
                execution_mode="fallback",
                execution_time_ms=execution_time,
                metadata={
                    "mode": "fallback",
                    "requires_manual_execution": True,
                    "fallback_reason": response.error_message,
                },
            )

        return EnhancedPlotGenerationResult(
            success=False,
            episode_number=episode_number,
            generated_plot="",
            execution_mode="failed",
            execution_time_ms=execution_time,
            error_message=response.error_message,
        )

    async def _save_generated_plot(self, episode_number: int, plot_content: str, project_root: Path) -> None:
        """生成プロット保存"""
        try:
            # DDD準拠: Application→Presentation違反を依存性注入で回避
            # TODO: IPathService経由でパス取得に変更
            episode_plots_dir = project_root / "data" / "plots" / "episodes"  # ハードコード回避のため仮実装

            # ディレクトリ確保
            episode_plots_dir.mkdir(parents=True, exist_ok=True)

            # ファイル保存
            plot_file = episode_plots_dir / f"第{episode_number:03d}話_生成プロット.yaml"

            # YAML形式での保存

            if isinstance(plot_content, dict):
                content = yaml.dump(plot_content, default_flow_style=False, allow_unicode=True)
            else:
                content = str(plot_content)

            Path(plot_file).write_text(content, encoding="utf-8")

            return plot_file

        except Exception:
            return None
