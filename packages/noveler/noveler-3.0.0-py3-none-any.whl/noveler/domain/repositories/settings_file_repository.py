#!/usr/bin/env python3
"""設定ファイルリポジトリインターフェース

設定ファイルからの固有名詞抽出を抽象化する
リポジトリインターフェース(ドメイン層で定義)
"""

from abc import ABC, abstractmethod

# pathlib import removed - using str for paths in domain layer


class SettingsFileRepository(ABC):
    """設定ファイルリポジトリインターフェース"""

    @abstractmethod
    def extract_proper_nouns_from_file(self, file_path: str) -> set[str]:
        """指定されたファイルから固有名詞を抽出

        Args:
            file_path: 抽出対象ファイルのパス

        Returns:
            Set[str]: 抽出された固有名詞のセット

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: ファイル形式が不正な場合
        """

    @abstractmethod
    def extract_all_proper_nouns(self) -> set[str]:
        """全設定ファイルから固有名詞を抽出

        Returns:
            Set[str]: 抽出された固有名詞のセット
        """

    @abstractmethod
    def get_supported_files(self) -> set[str]:
        """サポートされているファイルの一覧を取得

        Returns:
            Set[Path]: サポートファイルのパスセット
        """

    @abstractmethod
    def is_file_supported(self, file_path: str) -> bool:
        """ファイルがサポートされているかどうかの判定

        Args:
            file_path: 判定対象ファイルのパス

        Returns:
            bool: サポートされている場合True
        """
