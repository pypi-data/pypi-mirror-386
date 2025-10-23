"""Domain.value_objects.file_path
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""ファイルパスを表す値オブジェクト"""


from pathlib import Path


class FilePath:
    """ファイルパスを表す値オブジェクト

    ファイルシステム上のパスを安全に扱うための値オブジェクト。
    プラットフォームに依存しないパス操作を提供する。
    """

    def __init__(self, path: str | Path) -> None:
        """FilePathを初期化する

        Args:
            path: ファイルパス(文字列またはPathオブジェクト)

        Raises:
            ValueError: 無効なパスの場合
            TypeError: pathが文字列でもPathでもない場合
        """
        if isinstance(path, Path):
            path_str = str(path)
        elif isinstance(path, str):
            path_str = path.strip()
        else:
            msg = f"File path must be a string or Path, got {type(path).__name__}"
            raise TypeError(msg)

        if not path_str:
            msg = "File path cannot be empty"
            raise ValueError(msg)

        self._path = Path(path_str)

    def exists(self) -> bool:
        """ファイルまたはディレクトリが存在するかを確認する

        Returns:
            存在する場合True
        """
        return self._path.exists()

    def is_absolute(self) -> bool:
        """絶対パスかどうかを判定する

        Returns:
            絶対パスの場合True
        """
        return self._path.is_absolute()

    def parent(self) -> FilePath:
        """親ディレクトリのFilePathを返す

        Returns:
            親ディレクトリのFilePath
        """
        return FilePath(self._path.parent)

    def with_suffix(self, suffix: str) -> FilePath:
        """拡張子を変更した新しいFilePathを返す

        Args:
            suffix: 新しい拡張子(ドット付き)

        Returns:
            拡張子を変更したFilePath
        """
        return FilePath(self._path.with_suffix(suffix))

    def join(self, *parts: str) -> FilePath:
        """パスを結合した新しいFilePathを返す

        Args:
            *parts: 結合するパス要素

        Returns:
            結合されたFilePath
        """
        new_path = self._path
        for part in parts:
            new_path = new_path / part
        return FilePath(new_path)

    def __str__(self) -> str:
        """文字列表現を返す"""
        return str(self._path)

    def __eq__(self, other: object) -> bool:
        """等価性を判定する"""
        if not isinstance(other, FilePath):
            return False
        return self._path == other._path

    def __hash__(self) -> int:
        """ハッシュ値を返す"""
        return hash(self._path)

    def __repr__(self) -> str:
        """デバッグ用の文字列表現を返す"""
        return f"FilePath('{self._path}')"

    def __setattr__(self, name: str, value: object) -> None:
        """属性の設定を制限して不変性を保証する"""
        if hasattr(self, "_path"):
            msg = f"FilePath is immutable, cannot set attribute '{name}'"
            raise AttributeError(msg)
        super().__setattr__(name, value)
