#!/usr/bin/env python3
"""エピソードプロンプトリポジトリインターフェース

DDD準拠: Domain層のリポジトリ抽象インターフェース
実装はInfrastructure層に配置
"""

from abc import ABC, abstractmethod
from pathlib import Path

from noveler.domain.entities.episode_prompt import EpisodePrompt
from noveler.domain.value_objects.prompt_save_result import PromptSaveResult


class EpisodePromptRepository(ABC):
    """エピソードプロンプトリポジトリインターフェース

    Domain層の抽象インターフェース。
    Infrastructure層で具体実装を提供。
    """

    @abstractmethod
    def save_prompt(self, prompt: EpisodePrompt, file_path: Path) -> PromptSaveResult:
        """プロンプトを保存

        Args:
            prompt: 保存するエピソードプロンプト
            file_path: 保存先ファイルパス

        Returns:
            PromptSaveResult: 保存結果
        """

    @abstractmethod
    def load_prompt(self, file_path: Path) -> EpisodePrompt | None:
        """プロンプトを読み込み

        Args:
            file_path: プロンプトファイルのパス

        Returns:
            EpisodePrompt | None: 読み込まれたプロンプト、失敗時はNone
        """

    @abstractmethod
    def exists(self, file_path: Path) -> bool:
        """プロンプトファイルの存在確認

        Args:
            file_path: チェックするファイルパス

        Returns:
            bool: ファイルが存在する場合True
        """

    @abstractmethod
    def delete_prompt(self, file_path: Path) -> bool:
        """プロンプトファイルを削除

        Args:
            file_path: 削除するファイルパス

        Returns:
            bool: 削除成功時True
        """

    @abstractmethod
    def list_prompts(self, directory: Path) -> list[Path]:
        """指定ディレクトリ内のプロンプト一覧取得

        Args:
            directory: 検索対象ディレクトリ

        Returns:
            list[Path]: プロンプトファイルのパス一覧
        """
