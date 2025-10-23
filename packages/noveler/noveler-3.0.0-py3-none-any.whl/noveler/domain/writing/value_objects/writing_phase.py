"""執筆フェーズと公開ステータスの列挙型"""

from enum import Enum


class WritingPhase(Enum):
    """執筆フェーズ"""

    DRAFT = "draft"  # 下書き
    REVISION = "revision"  # 推敲
    FINAL_CHECK = "final_check"  # 最終チェック
    PUBLISHED = "published"  # 公開済み


class PublicationStatus(Enum):
    """公開ステータス"""

    UNPUBLISHED = "unpublished"  # 未公開
    SCHEDULED = "scheduled"  # 公開予定
    PUBLISHED = "published"  # 公開済み
    WITHDRAWN = "withdrawn"  # 公開停止
