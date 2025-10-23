"""プロジェクト設定を表す値オブジェクト"""

import re
from dataclasses import dataclass

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class ProjectSettings:
    """プロジェクト設定を表す値オブジェクト"""

    title: str
    ncode: str
    author_name: str
    target_audience: str = "general"
    quality_threshold: int = 70
    project_path: str | None = None

    def __post_init__(self) -> None:
        """入力値の検証"""
        if not self.title:
            msg = "プロジェクトタイトルは必須です"
            raise DomainException(msg)

        if not self.author_name:
            msg = "著者名は必須です"
            raise DomainException(msg)

        if self.quality_threshold < 0 or self.quality_threshold > 100:
            msg = "品質閾値は0-100の範囲である必要があります"
            raise ValueError(msg)

        # ncodeの形式チェック
        if self.ncode and not self._is_valid_ncode(self.ncode):
            msg = f"無効なncode形式: {self.ncode}"
            raise DomainException(msg)

    def _is_valid_ncode(self, ncode: str) -> bool:
        """ncodeの形式を検証"""

        # n + 7桁の数字 + アルファベット1文字
        return bool(re.match(r"^n\d{7}[a-z]$", str(ncode).lower()))

    def is_high_quality_mode(self) -> bool:
        """高品質モードかどうか"""
        return self.quality_threshold >= 80

    def get_manuscript_path(self) -> str | None:
        """原稿ディレクトリのパスを取得"""
        if self.project_path:
            return f"{self.project_path}/40_原稿"
        return None

    def get_management_path(self) -> str | None:
        """管理資料ディレクトリのパスを取得"""
        if self.project_path:
            return f"{self.project_path}/50_管理資料"
        return None

    def get_settings_path(self) -> str | None:
        """設定集ディレクトリのパスを取得"""
        if self.project_path:
            return f"{self.project_path}/30_設定集"
        return None
