#!/usr/bin/env python3
"""汎用Claude Code統合サービス

仕様書: SPEC-CLAUDE-CODE-002
"""

import time
from typing import Any

from noveler.domain.services.result_extraction_strategies import ResultExtractor, ResultExtractorFactory
from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionRequest
from noveler.domain.value_objects.universal_prompt_execution import (
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)
from noveler.infrastructure.integrations.claude_code_integration_service import (
    ClaudeCodeIntegrationConfig,
    ClaudeCodeIntegrationService,
)

# B20/B30品質作業指示書準拠: Console重複作成回避 - shared_utilities使用必須
# DDD準拠: Infrastructure→Presentation依存は行わない（コンソールはDIで受け取る）


class UniversalClaudeCodeService:
    """汎用Claude Code統合サービス

    REQ-1.1: 汎用プロンプト実行共通サービス
    複数のプロンプト種別（執筆・プロット・品質チェック）に対応した
    Claude Code統合機能を提供する。
    """

    def __init__(self, config: ClaudeCodeIntegrationConfig = None, logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            config: Claude Code統合設定
            logger_service: ロガーサービス
            console_service: コンソールサービス
        """
        self.base_service = ClaudeCodeIntegrationService(config)
        self.logger_service = logger_service
        self.console_service = console_service
        self.result_extractors: dict[PromptType, ResultExtractor] = {
            PromptType.WRITING: ResultExtractorFactory.create_extractor(PromptType.WRITING),
            PromptType.PLOT: ResultExtractorFactory.create_extractor(PromptType.PLOT),
            PromptType.QUALITY_CHECK: ResultExtractorFactory.create_extractor(PromptType.QUALITY_CHECK),
        }

    async def execute_universal_prompt(self, request: UniversalPromptRequest) -> UniversalPromptResponse:
        """汎用プロンプト実行

        REQ-1.1: メインの汎用プロンプト実行機能

        Args:
            request: 汎用プロンプト実行リクエスト

        Returns:
            UniversalPromptResponse: 統一レスポンス
        """
        start_time = time.time()

        try:
            # プロンプト種別に応じたコンテキスト適用
            claude_request = self._apply_context_rules(request)

            # 基盤Claude Code実行
            claude_response = await self.base_service.execute_prompt(claude_request)

            execution_time = (time.time() - start_time) * 1000

            if claude_response.is_success():
                # 種別固有の結果抽出
                extractor = self._get_result_extractor(request.prompt_type)
                extracted_data: dict[str, Any] = extractor.extract(claude_response)

                if self.console_service:
                    try:
                        self.console_service.print(
                            f"[green]✅ {request.prompt_type.value}プロンプト実行成功[/green] ({execution_time:.0f}ms)"
                        )
                    except Exception:
                        pass

                return UniversalPromptResponse(
                    success=True,
                    response_content=claude_response.response_content,
                    extracted_data=extracted_data,
                    prompt_type=request.prompt_type,
                    execution_time_ms=execution_time,
                    metadata={
                        "original_claude_response": claude_response,
                        "extraction_method": extractor.__class__.__name__,
                        "context_files_count": len(request.get_context_files()),
                    },
                )

            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=request.prompt_type,
                execution_time_ms=execution_time,
                error_message=claude_response.error_message,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            if self.console_service:
                try:
                    self.console_service.print(f"[red]❌ {request.prompt_type.value}プロンプト実行エラー: {e}[/red]")
                except Exception:
                    pass

            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=request.prompt_type,
                execution_time_ms=execution_time,
                error_message=str(e),
            )

    def _get_result_extractor(self, prompt_type: PromptType) -> ResultExtractor:
        """結果抽出器取得

        REQ-2.2: プロンプト種別に応じた適切な結果抽出器提供

        Args:
            prompt_type: プロンプト種別

        Returns:
            ResultExtractor: 対応する結果抽出器
        """
        if prompt_type not in self.result_extractors:
            msg = f"Unsupported prompt type: {prompt_type}"
            raise ValueError(msg)

        return self.result_extractors[prompt_type]

    def _apply_context_rules(self, request: UniversalPromptRequest) -> ClaudeCodeExecutionRequest:
        """コンテキスト適用ルール

        REQ-2.3: 種別固有設定・コンテキスト管理

        Args:
            request: 汎用プロンプト実行リクエスト

        Returns:
            ClaudeCodeExecutionRequest: Claude Code実行リクエスト
        """
        # 基本設定
        return ClaudeCodeExecutionRequest(
            prompt_content=self._enhance_prompt_with_context(request),
            output_format=request.output_format,
            max_turns=request.max_turns,
            project_context_paths=request.get_context_files(),
        )


    def _enhance_prompt_with_context(self, request: UniversalPromptRequest) -> str:
        """プロンプト種別固有のコンテキスト強化

        REQ-1.3: コンテキストファイル管理・メタデータ抽出機能
        """
        enhanced_prompt = request.prompt_content

        # プロンプト種別固有の前処理
        if request.prompt_type == PromptType.WRITING:
            enhanced_prompt = self._enhance_writing_prompt(enhanced_prompt, request)
        elif request.prompt_type == PromptType.PLOT:
            enhanced_prompt = self._enhance_plot_prompt(enhanced_prompt, request)
        elif request.prompt_type == PromptType.QUALITY_CHECK:
            enhanced_prompt = self._enhance_quality_check_prompt(enhanced_prompt, request)

        return enhanced_prompt

    def _enhance_writing_prompt(self, prompt: str, request: UniversalPromptRequest) -> str:
        """執筆プロンプト強化"""
        return f"""# 執筆プロンプト実行

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}

## 実行設定
{self._format_config_for_prompt(request.type_specific_config)}

## プロンプト内容
{prompt}

## 出力形式指示
JSON形式で以下の構造で回答してください:
    {{
    "manuscript": "執筆された原稿内容（Markdown形式）",
    "metadata": {{
        "word_count": 文字数,
        "creation_time": "作成時刻",
        "genre": "ジャンル"
    }}
}}
"""

    def _enhance_plot_prompt(self, prompt: str, request: UniversalPromptRequest) -> str:
        """プロット作成プロンプト強化"""
        return f"""# プロット作成プロンプト実行

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}

## 実行設定
{self._format_config_for_prompt(request.type_specific_config)}

## プロンプト内容
{prompt}

## 出力形式指示
JSON形式で以下の構造で回答してください:
    {{
    "plot": "プロット内容",
    "scenes": ["シーン1", "シーン2", "シーン3"],
    "metadata": {{
        "episode_number": エピソード番号,
        "estimated_length": 推定文字数,
        "key_events": ["重要イベント1", "重要イベント2"]
    }}
}}
"""

    def _enhance_quality_check_prompt(self, prompt: str, request: UniversalPromptRequest) -> str:
        """品質チェックプロンプト強化"""
        return f"""# 品質チェックプロンプト実行

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}

## チェック設定
{self._format_config_for_prompt(request.type_specific_config)}

## プロンプト内容
{prompt}

## 出力形式指示
JSON形式で以下の構造で回答してください:
    {{
    "score": 品質スコア(0-100),
    "issues": ["問題点1", "問題点2"],
    "recommendations": ["改善提案1", "改善提案2"],
    "analysis": {{
        "strengths": ["強み1", "強み2"],
        "weaknesses": ["弱み1", "弱み2"]
    }}
}}
"""

    def _format_config_for_prompt(self, config: dict[str, Any]) -> str:
        """設定をプロンプト用にフォーマット"""
        if not config:
            return "（設定なし）"

        formatted_lines = []
        for key, value in config.items():
            formatted_lines.append(f"- {key}: {value}")

        return "\n".join(formatted_lines)
