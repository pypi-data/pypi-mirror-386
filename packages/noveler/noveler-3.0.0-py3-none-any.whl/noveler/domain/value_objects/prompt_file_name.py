"""
プロンプトファイル名バリューオブジェクト

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptFileName:
    """プロンプトファイル名を表すバリューオブジェクト

    第000話_タイトル.yaml 形式でのファイル名生成・検証を担当
    """

    episode_number: int
    title: str

    def __post_init__(self) -> None:
        """バリデーション実行"""
        self._validate_episode_number()
        self._validate_title()

    def _validate_episode_number(self) -> None:
        """エピソード番号の検証"""
        if not isinstance(self.episode_number, int):
            msg = "Episode number must be integer"
            raise ValueError(msg)
        if self.episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)
        if self.episode_number > 999:
            msg = "Episode number must be <= 999"
            raise ValueError(msg)

    def _validate_title(self) -> None:
        """タイトルの検証"""
        if not isinstance(self.title, str):
            msg = "Title must be string"
            raise ValueError(msg)
        if not self.title.strip():
            msg = "Title cannot be empty"
            raise ValueError(msg)
        if len(self.title) > 50:
            msg = "Title must be <= 50 characters"
            raise ValueError(msg)

        # ファイル名に使用不可能な文字チェック
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, self.title):
            msg = f"Title contains invalid filename characters: {invalid_chars}"
            raise ValueError(msg)

    def to_filename(self) -> str:
        """ファイル名文字列生成

        Returns:
            str: 第000話_タイトル.yaml 形式の文字列
        """
        sanitized_title = self._sanitize_title()
        return f"第{self.episode_number:03d}話_{sanitized_title}.yaml"

    def _sanitize_title(self) -> str:
        """タイトルのファイル名安全化"""
        # 日本語文字のみ保持、その他は_に置換
        sanitized = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", "_", self.title)
        # 連続する_を単一にまとめる
        sanitized = re.sub(r"_+", "_", sanitized)
        # 前後の_を除去
        return sanitized.strip("_")

    @classmethod
    def from_filename(cls, filename: str) -> "PromptFileName":
        """ファイル名からバリューオブジェクト復元

        Args:
            filename: 第000話_タイトル.yaml 形式の文字列

        Returns:
            PromptFileName: 復元されたバリューオブジェクト

        Raises:
            ValueError: ファイル名形式が不正な場合
        """
        pattern = r"^第(\d{3})話_(.+)\.yaml$"
        match = re.match(pattern, filename)

        if not match:
            msg = f"Invalid filename format: {filename}"
            raise ValueError(msg)

        episode_number = int(match.group(1))
        title = match.group(2).replace("_", " ").strip()

        return cls(episode_number=episode_number, title=title)

    def __str__(self) -> str:
        """文字列表現"""
        return self.to_filename()
