"""品質問題値オブジェクト

品質チェックで検出された問題を表現する値オブジェクト。
"""

from dataclasses import dataclass
from enum import Enum


class IssueSeverity(Enum):
    """問題の重要度"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def weight(self) -> float:
        """重要度の重み"""
        weights = {"error": 2.0, "warning": 1.5, "info": 0.5}
        return weights.get(self.value, 1.0)

    def __str__(self) -> str:
        """日本語表示"""
        display_names = {"error": "エラー", "warning": "警告", "info": "情報"}
        return display_names.get(self.value, self.value)


class IssueCategory(Enum):
    """問題のカテゴリ"""

    STYLE = "style"
    GRAMMAR = "grammar"
    KANJI = "kanji"
    COMPOSITION = "composition"
    CHARACTER = "character"
    READABILITY = "readability"
    SYSTEM = "system"  # システムエラー用

    @property
    def display_name(self) -> str:
        """カテゴリの日本語表示名"""
        names = {
            "style": "文体・スタイル",
            "grammar": "文法",
            "kanji": "漢字・表記",
            "composition": "構成",
            "character": "キャラクター",
            "readability": "読みやすさ",
            "system": "システム",
        }
        return names.get(self.value, self.value)

    @property
    def description(self) -> str:
        """カテゴリの説明"""
        descriptions = {
            "style": "三点リーダー、感嘆符、句読点などの文体に関する問題",
            "grammar": "文法的な誤りや不自然な表現",
            "kanji": "旧字体、環境依存文字、誤字などの漢字表記の問題",
            "composition": "章構成、段落構成、起承転結などの構成上の問題",
            "character": "キャラクター設定の一貫性、描写の問題",
            "readability": "文章の読みやすさ、理解しやすさの問題",
            "system": "システム内部のエラーや警告",
        }
        return descriptions.get(self.value, "")


@dataclass(frozen=True)
class QualityIssue:
    """品質問題を表す値オブジェクト

    不変オブジェクトとして実装し、品質チェックで検出された
    個々の問題を表現する。
    """

    category: IssueCategory
    severity: IssueSeverity
    message: str
    line_number: int
    position: int = 0
    context: str = ""
    suggestion: str | None = None
    penalty_points: int | None = None

    def __post_init__(self) -> None:
        """初期化後の処理"""
        # penalty_pointsが指定されていない場合、重要度に基づいて設定
        if self.penalty_points is None:
            default_penalties = {IssueSeverity.ERROR: 5, IssueSeverity.WARNING: 3, IssueSeverity.INFO: 1}
            object.__setattr__(self, "penalty_points", default_penalties.get(self.severity, 1))

    def has_suggestion(self) -> bool:
        """修正提案があるかどうか"""
        return self.suggestion is not None

    def __str__(self) -> str:
        """文字列表現"""
        location = f"{self.line_number}行目"
        if self.position > 0:
            location += f" {self.position}文字目"

        return f"[{self.severity.value.upper()}] {location}: {self.message}"
