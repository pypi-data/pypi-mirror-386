"""品質閾値値オブジェクト"""

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityThreshold:
    """品質チェックの閾値を表す値オブジェクト"""

    name: str
    value: float
    min_value: float
    max_value: float

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.name:
            msg = "名前は空にできません"
            raise ValueError(msg)

        if self.min_value > self.max_value:
            msg = "最小値は最大値以下である必要があります"
            raise ValueError(msg)

        if self.value < self.min_value or self.value > self.max_value:
            msg = f"{self.name}の値は範囲外です: {self.value} (範囲: {self.min_value}-{self.max_value})"
            raise ValueError(msg)

    def update_value(self, new_value: float) -> "QualityThreshold":
        """値を更新した新しいインスタンスを返す"""
        return QualityThreshold(
            name=self.name,
            value=new_value,
            min_value=self.min_value,
            max_value=self.max_value,
        )

    def __str__(self) -> str:
        """人間が読みやすい文字列表現"""
        return f"{self.name}: {self.value} (範囲: {self.min_value}-{self.max_value})"
