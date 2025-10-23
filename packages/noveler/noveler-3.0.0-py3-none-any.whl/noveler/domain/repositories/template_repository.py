#!/usr/bin/env python3
"""テンプレートリポジトリインターフェース

テンプレートファイルの操作を抽象化する
リポジトリインターフェース(ドメイン層で定義)
"""

from abc import ABC, abstractmethod
from typing import Any


class TemplateRepository(ABC):
    """テンプレートリポジトリインターフェース"""

    @abstractmethod
    def load_template(self, stage_type: str) -> dict[str, Any]:
        """指定段階のテンプレートを読み込み

        Args:
            stage_type: ワークフロー段階タイプ

        Returns:
            Dict[str, Any]: テンプレート内容

        Raises:
            FileNotFoundError: テンプレートが存在しない場合
        """

    @abstractmethod
    def get_template_path(self, stage_type: str) -> str:
        """指定段階のテンプレートファイルパスを取得

        Args:
            stage_type: ワークフロー段階タイプ

        Returns:
            str: テンプレートファイルパス
        """
