"""小説情報値オブジェクト

離脱率分析などで使用する小説の基本情報。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NovelInfo:
    """小説情報を表す値オブジェクト

    「小説家になろう」の作品を識別する情報。
    """

    name: str
    ncode: str

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.name:
            msg = "小説名が空です"
            raise ValueError(msg)
        if not self.ncode:
            msg = "ncodeが空です"
            raise ValueError(msg)

        # ncodeの形式チェック(例: n1234kr)
        if not self.ncode.startswith("n"):
            msg = "ncodeは'n'で始まる必要があります"
            raise ValueError(msg)
        if len(self.ncode) < 3:
            msg = "ncodeが短すぎます"
            raise ValueError(msg)
