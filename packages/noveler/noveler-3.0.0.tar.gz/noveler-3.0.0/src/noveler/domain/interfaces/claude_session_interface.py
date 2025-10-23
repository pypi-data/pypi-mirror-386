"""Claude セッション統合インターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class ClaudeSessionExecutorInterface(ABC):
    """Claude Code セッション実行抽象インターフェース

    ドメインサービスがClaude Codeセッションを実行する際の
    抽象インターフェース。インフラストラクチャ依存を排除。
    """

    @abstractmethod
    def execute_prompt(
        self,
        prompt: str,
        response_format: str = "json",
        timeout: int | None = None,  # ConfigManagerから取得
    ) -> dict[str, Any]:
        """プロンプト実行

        Args:
            prompt: 実行対象プロンプト
            response_format: レスポンス形式 (json/yaml)
            timeout: タイムアウト秒数

        Returns:
            Dict[str, Any]: 実行結果
        """

    @abstractmethod
    def is_available(self) -> bool:
        """セッション利用可能性確認

        Returns:
            bool: 利用可能かどうか
        """


class EnvironmentDetectorInterface(ABC):
    """環境検出抽象インターフェース

    実行環境の検出・判定を行う抽象インターフェース。
    """

    @abstractmethod
    def is_claude_code_environment(self) -> bool:
        """Claude Code環境判定

        Returns:
            bool: Claude Code環境かどうか
        """

    @abstractmethod
    def get_current_project_name(self) -> str:
        """現在のプロジェクト名取得

        Returns:
            str: プロジェクト名（取得できない場合は'不明'）
        """


class PromptRecordRepositoryInterface(ABC):
    """プロンプト記録リポジトリ抽象インターフェース"""

    @abstractmethod
    def save_prompt_record(self, record_data: dict[str, Any]) -> None:
        """プロンプト記録保存

        Args:
            record_data: 記録データ
        """
