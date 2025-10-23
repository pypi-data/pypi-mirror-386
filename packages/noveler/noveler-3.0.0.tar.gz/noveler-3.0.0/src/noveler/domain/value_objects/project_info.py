"""プロジェクト情報値オブジェクト"""

from dataclasses import dataclass
from pathlib import Path

from noveler.domain.value_objects.path_configuration import get_default_manuscript_dir


@dataclass(frozen=True)
class ProjectInfo:
    """プロジェクト情報を表す値オブジェクト"""

    name: str | None = None
    root_path: Path | None = None
    config_path: Path | None = None
    title: str | None = None
    author: str | None = None
    genre: str | None = None
    description: str | None = None
    target_word_count: int | None = None

    @property
    def manuscript_path(self) -> Path:
        """原稿フォルダのパス

        DDD準拠: Domain層はPresentation層に依存できません
        基本的なパス構成で代替実装を提供
        """
        if self.root_path is None:
            msg = "root_pathが設定されていません"
            raise ValueError(msg)
        return get_default_manuscript_dir(self.root_path)

    @property
    def management_path(self) -> Path:
        """管理資料フォルダのパス

        DDD準拠: Domain層はPresentation層に依存できません
        基本的なパス構成で代替実装を提供
        """
        if self.config_path is None:
            msg = "config_pathが設定されていません"
            raise ValueError(msg)
        return self.config_path.parent / "50_管理資料"

    def __post_init__(self) -> None:
        """バリデーション"""
        effective_name = self.name.strip() if isinstance(self.name, str) else ""
        if not effective_name and self.title and self.title.strip():
            object.__setattr__(self, "name", self.title)
            effective_name = self.title.strip()

        if not effective_name:
            msg = "プロジェクト名は必須です"
            raise ValueError(msg)
        if self.root_path is not None and not isinstance(self.root_path, Path):
            msg = "root_pathはPathオブジェクトである必要があります"
            raise TypeError(msg)
        if self.config_path is not None and not isinstance(self.config_path, Path):
            msg = "config_pathはPathオブジェクトである必要があります"
            raise TypeError(msg)
        if self.title is not None and not self.title.strip():
            msg = "タイトルは空にできません"
            raise ValueError(msg)
        if self.author is not None and not self.author.strip():
            msg = "作者名は空にできません"
            raise ValueError(msg)
        if self.target_word_count is not None and self.target_word_count <= 0:
            msg = "target_word_countは正の整数である必要があります"
            raise ValueError(msg)
