#!/usr/bin/env python3

# B30準拠TODO: Console service DI統合 - get_console_service()使用

"""汎用Claude Code統合ユースケース

仕様書: SPEC-CLAUDE-CODE-002
"""

import time
from typing import Protocol

from noveler.domain.value_objects.universal_prompt_execution import (
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)


# DDD準拠：インフラ層依存解消のためのプロトコル定義
class UniversalLLMServiceProtocol(Protocol):
    """汎用Claude Code統合サービスプロトコル（DDD準拠）"""

    async def execute_universal_prompt(self, request: UniversalPromptRequest) -> UniversalPromptResponse:
        """汎用プロンプト実行"""
        ...

    def is_claude_code_available(self) -> bool:
        """Claude Code利用可能性チェック"""
        ...


class ConsoleProtocol(Protocol):
    """コンソール出力プロトコル（プレゼンテーション層依存解消）"""

    def print(self, message: str) -> None:
        """メッセージ出力"""
        ...


class UniversalLLMUseCase:
    """汎用Claude Code統合ユースケース

    REQ-4.1: 統一されたClaude Code統合機能のユースケース層
    複数のプロンプト種別（執筆・プロット・品質チェック）に対応した
    Claude Code統合機能を提供する。（DDD準拠：依存性注入対応）
    """

    def __init__(self, universal_service: UniversalLLMServiceProtocol, console: ConsoleProtocol | None = None) -> None:
        """初期化（DDD準拠：依存性注入）

        Args:
            universal_service: 汎用Claude Code統合サービス
            console: コンソール出力サービス
        """
        self.universal_service = universal_service
        self._console = console or self._create_default_console()

    def _create_default_console(self) -> ConsoleProtocol:
        """デフォルトコンソール作成（B30統一コンソール使用）"""
        from noveler.presentation.shared.shared_utilities import console

        return console

    async def execute_with_fallback(
        self, request: UniversalPromptRequest, fallback_enabled: bool = True
    ) -> UniversalPromptResponse:
        """フォールバック機能付きプロンプト実行

        REQ-4.3: Claude Code統合失敗時の従来モード自動フォールバック

        Args:
            request: 汎用プロンプト実行リクエスト
            fallback_enabled: フォールバック機能有効フラグ

        Returns:
            UniversalPromptResponse: 統一レスポンス
        """
        start_time = time.time()

        try:
            # Claude Code統合実行を試行
            response = await self.universal_service.execute_universal_prompt(request)

            if response.is_success():
                self._console.print(f"[green]✅ {request.prompt_type.value}プロンプトClaude Code統合実行成功[/green]")
                # LLM I/O保存（B20準拠: Imperative Shellで副作用集約）
                try:
                    from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger

                    io_logger = LLMIOLogger(request.project_context.project_root)
                    io_logger.save_request_response(request, response)
                except Exception:
                    # ログ保存失敗は無視（処理継続）
                    pass
                return response
            # Claude Code実行が失敗した場合
            self._console.print(f"[yellow]⚠️ Claude Code実行失敗: {response.error_message}[/yellow]")

            if fallback_enabled:
                # フォールバックモードに切り替え
                return await self._execute_fallback_mode(request, start_time)
            return response

        except Exception as e:
            self._console.print(f"[red]❌ Claude Code統合実行中にエラー: {e}[/red]")

            if fallback_enabled:
                # フォールバックモードに切り替え
                return await self._execute_fallback_mode(request, start_time)
            execution_time = (time.time() - start_time) * 1000
            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=request.prompt_type,
                execution_time_ms=execution_time,
                error_message=f"Claude Code統合実行エラー: {e!s}",
            )

    async def _execute_fallback_mode(
        self, request: UniversalPromptRequest, start_time: float
    ) -> UniversalPromptResponse:
        """フォールバックモード実行

        REQ-5.1: 従来のプロンプトファイル生成モードへのフォールバック

        Args:
            request: プロンプト実行リクエスト
            start_time: 実行開始時刻

        Returns:
            UniversalPromptResponse: フォールバック実行結果
        """
        self._console.print("[blue]📝 従来のプロンプトファイル生成モードにフォールバック[/blue]")

        try:
            # プロンプト種別に応じたフォールバック処理
            if request.prompt_type == PromptType.WRITING:
                return await self._fallback_writing_mode(request, start_time)
            if request.prompt_type == PromptType.PLOT:
                return await self._fallback_plot_mode(request, start_time)
            if request.prompt_type == PromptType.QUALITY_CHECK:
                return await self._fallback_quality_check_mode(request, start_time)
            msg = f"Unsupported prompt type for fallback: {request.prompt_type}"
            raise ValueError(msg)

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._console.print(f"[red]❌ フォールバックモード実行エラー: {e}[/red]")

            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=request.prompt_type,
                execution_time_ms=execution_time,
                error_message=f"フォールバックモード実行エラー: {e!s}",
            )

    async def _fallback_writing_mode(
        self, request: UniversalPromptRequest, start_time: float
    ) -> UniversalPromptResponse:
        """執筆プロンプトフォールバックモード

        従来の執筆プロンプトファイル生成を実行
        """
        execution_time = (time.time() - start_time) * 1000

        # プロンプトファイルの生成情報を提供
        fallback_content = f"""# 従来モード: プロンプトファイル生成

## 生成されるプロンプト内容
{request.prompt_content}

## 手動実行手順
1. 上記プロンプト内容をClaude Codeに貼り付け
2. プロジェクトディレクトリで実行
3. 生成された内容を適切な場所に保存

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}
"""

        self._console.print("[blue]📝 執筆プロンプトファイル生成完了（手動実行が必要）[/blue]")

        response = UniversalPromptResponse(
            success=True,  # フォールバック成功として扱う
            response_content=fallback_content,
            extracted_data={
                "fallback_mode": True,
                "prompt_content": request.prompt_content,
                "execution_type": "manual",
            },
            prompt_type=request.prompt_type,
            execution_time_ms=execution_time,
            metadata={"mode": "fallback", "requires_manual_execution": True, "fallback_type": "writing"},
        )
        # I/O保存
        try:
            from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger

            io_logger = LLMIOLogger(request.project_context.project_root)
            io_logger.save_request_response(request, response)
        except Exception:
            pass
        return response

    async def _fallback_plot_mode(self, request: UniversalPromptRequest, start_time: float) -> UniversalPromptResponse:
        """プロット作成フォールバックモード

        従来のプロット作成プロンプトファイル生成を実行
        """
        execution_time = (time.time() - start_time) * 1000

        # プロンプトファイルの生成情報を提供
        fallback_content = f"""# 従来モード: プロット作成プロンプトファイル生成

## 生成されるプロンプト内容
{request.prompt_content}

## 手動実行手順
1. 上記プロンプト内容をClaude Codeに貼り付け
2. プロジェクトディレクトリで実行
3. 生成されたプロット内容を適切な場所に保存

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}

## 出力先ディレクトリ
- プロット: 20_プロット/
"""

        self._console.print("[blue]📝 プロット作成プロンプトファイル生成完了（手動実行が必要）[/blue]")

        response = UniversalPromptResponse(
            success=True,  # フォールバック成功として扱う
            response_content=fallback_content,
            extracted_data={
                "fallback_mode": True,
                "prompt_content": request.prompt_content,
                "execution_type": "manual",
            },
            prompt_type=request.prompt_type,
            execution_time_ms=execution_time,
            metadata={"mode": "fallback", "requires_manual_execution": True, "fallback_type": "plot"},
        )
        try:
            from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger

            io_logger = LLMIOLogger(request.project_context.project_root)
            io_logger.save_request_response(request, response)
        except Exception:
            pass
        return response

    async def _fallback_quality_check_mode(
        self, request: UniversalPromptRequest, start_time: float
    ) -> UniversalPromptResponse:
        """品質チェックフォールバックモード

        従来の品質チェックプロンプトファイル生成を実行
        """
        execution_time = (time.time() - start_time) * 1000

        # プロンプトファイルの生成情報を提供
        fallback_content = f"""# 従来モード: 品質チェックプロンプトファイル生成

## 生成されるプロンプト内容
{request.prompt_content}

## 手動実行手順
1. 上記プロンプト内容をClaude Codeに貼り付け
2. プロジェクトディレクトリで実行
3. 品質チェック結果を確認・記録

## プロジェクト情報
- プロジェクト名: {request.project_context.project_name}
- プロジェクトルート: {request.project_context.project_root}
"""

        self._console.print("[blue]📝 品質チェックプロンプトファイル生成完了（手動実行が必要）[/blue]")

        response = UniversalPromptResponse(
            success=True,  # フォールバック成功として扱う
            response_content=fallback_content,
            extracted_data={
                "fallback_mode": True,
                "prompt_content": request.prompt_content,
                "execution_type": "manual",
            },
            prompt_type=request.prompt_type,
            execution_time_ms=execution_time,
            metadata={"mode": "fallback", "requires_manual_execution": True, "fallback_type": "quality_check"},
        )
        try:
            from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger

            io_logger = LLMIOLogger(request.project_context.project_root)
            io_logger.save_request_response(request, response)
        except Exception:
            pass
        return response

    def is_claude_code_available(self) -> bool:
        """Claude Code利用可能性チェック

        REQ-4.3: Claude Code統合機能の利用可能性事前チェック

        Returns:
            bool: Claude Codeが利用可能かどうか
        """
        try:
            # 基盤サービスの利用可能性をチェック
            return self.universal_service.base_service.is_available()
        except Exception:
            return False

    def get_supported_prompt_types(self) -> list[PromptType]:
        """対応プロンプト種別一覧取得

        REQ-2.1: サポートされているプロンプト種別の一覧提供

        Returns:
            list[PromptType]: 対応プロンプト種別一覧
        """
        return [PromptType.WRITING, PromptType.PLOT, PromptType.QUALITY_CHECK]
