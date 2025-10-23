"""原稿生成サービス用例外クラス

ゴールデンサンプルパターンに基づいた体系的なエラーハンドリング
"""

from pathlib import Path
from typing import Any


class ManuscriptGenerationError(Exception):
    """原稿生成エラーの基底クラス"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """例外を初期化

        Args:
            message: エラーメッセージ
            details: 詳細情報の辞書
        """
        super().__init__(message)
        self.details = details or {}


class ProjectConfigError(ManuscriptGenerationError):
    """プロジェクト設定関連エラー"""


class ProjectConfigNotFoundError(ProjectConfigError):
    """プロジェクト設定ファイル不在エラー"""

    def __init__(self, config_path: Path) -> None:
        """設定ファイル不在エラーを初期化

        Args:
            config_path: 見つからなかった設定ファイルのパス
        """
        self.config_path = config_path
        message = self._format_message()
        super().__init__(message, {"config_path": str(config_path)})

    def _format_message(self) -> str:
        """エラーメッセージをフォーマット"""
        return (
            f"プロジェクト設定ファイルが見つかりません: {self.config_path}\n"
            f"プロジェクトルートに「プロジェクト設定.yaml」を作成してください。"
        )


class InvalidProjectConfigError(ProjectConfigError):
    """プロジェクト設定不正エラー"""

    def __init__(self, reason: str, config_path: Path | None = None) -> None:
        """設定不正エラーを初期化

        Args:
            reason: エラーの理由
            config_path: 設定ファイルのパス（オプション）
        """
        self.reason = reason
        self.config_path = config_path
        message = f"プロジェクト設定が不正です: {reason}"
        details = {"reason": reason}
        if config_path:
            details["config_path"] = str(config_path)
        super().__init__(message, details)


class TargetLengthNotDefinedError(ProjectConfigError):
    """目標文字数未定義エラー"""

    def __init__(self, config_path: Path | None = None) -> None:
        """目標文字数未定義エラーを初期化

        Args:
            config_path: 設定ファイルのパス（オプション）
        """
        self.config_path = config_path
        message = self._format_message()
        details = {}
        if config_path:
            details["config_path"] = str(config_path)
        super().__init__(message, details)

    def _format_message(self) -> str:
        """エラーメッセージをフォーマット"""
        return (
            "プロジェクト設定.yamlの'settings'セクションに"
            "'target_length_per_episode'が定義されていません。\n"
            "以下の形式で設定を追加してください:\n"
            "settings:\n"
            "  target_length_per_episode: 10000"
        )


class WorkspaceInitializationError(ManuscriptGenerationError):
    """作業領域初期化エラー"""

    def __init__(self, reason: str, episode_number: int) -> None:
        """作業領域初期化エラーを初期化

        Args:
            reason: エラーの理由
            episode_number: エピソード番号
        """
        self.reason = reason
        self.episode_number = episode_number
        message = f"作業領域の初期化に失敗しました（第{episode_number:03d}話）: {reason}"
        super().__init__(message, {
            "reason": reason,
            "episode_number": episode_number
        })


class FileOperationError(ManuscriptGenerationError):
    """ファイル操作エラー"""

    def __init__(self, operation: str, file_path: Path, cause: Exception | None = None) -> None:
        """ファイル操作エラーを初期化

        Args:
            operation: 操作の種類（read, write, delete等）
            file_path: 対象ファイルのパス
            cause: 原因となった例外
        """
        self.operation = operation
        self.file_path = file_path
        self.cause = cause

        message = f"ファイル{operation}操作に失敗: {file_path}"
        if cause:
            message += f" - {cause!s}"

        super().__init__(message, {
            "operation": operation,
            "file_path": str(file_path),
            "cause": str(cause) if cause else None
        })
