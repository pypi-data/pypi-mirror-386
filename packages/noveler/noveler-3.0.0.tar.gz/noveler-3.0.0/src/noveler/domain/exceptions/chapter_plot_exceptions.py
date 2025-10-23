"""章別プロット関連のドメイン例外"""

from noveler.domain.repositories.chapter_plot_repository import (
    ChapterPlotNotFoundError as _ChapterPlotNotFoundError,
)


class ChapterPlotNotFoundError(_ChapterPlotNotFoundError):
    """章別プロットが見つからない場合の例外

    既存の `ChapterPlotNotFoundError` をドメイン例外モジュール経由でも
    利用できるようにするエイリアスです。
    """

    pass

__all__ = ["ChapterPlotNotFoundError"]

import builtins
builtins.ChapterPlotNotFoundError = ChapterPlotNotFoundError
