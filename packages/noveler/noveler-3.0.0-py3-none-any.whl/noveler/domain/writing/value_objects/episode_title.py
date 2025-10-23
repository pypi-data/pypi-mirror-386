"""エピソードタイトルを表す値オブジェクト"""

from dataclasses import dataclass

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class EpisodeTitle:
    """エピソードタイトルを表す値オブジェクト

    不変条件:
    - タイトルは空でない
    - タイトルは100文字以内
    - 前後の空白は自動的に除去される
    """

    value: str

    def __post_init__(self) -> None:
        """不変条件の検証"""
        # 前後の空白を除去(正規化)
        normalized_value = self.value.strip() if self.value else ""

        # dataclassのfrozenを回避して正規化された値を設定
        object.__setattr__(self, "value", normalized_value)

        # 空チェック
        if not self.value:
            msg = "タイトルは空にできません"
            raise DomainException(msg)

        # 長さチェック
        if len(self.value) > 100:
            msg = "タイトルは100文字以内である必要があります"
            raise DomainException(msg)

    def contains_episode_number(self) -> bool:
        """話数が含まれているかチェック"""
        return "第" in self.value and "話" in self.value

    def format(self) -> str:
        """タイトルをフォーマット"""
        return self.value

    def __str__(self) -> str:
        return self.value
