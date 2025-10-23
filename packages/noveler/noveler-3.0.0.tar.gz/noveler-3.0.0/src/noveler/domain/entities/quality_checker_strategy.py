"""Domain.entities.quality_checker_strategy
Where: Domain entity representing quality checker strategies.
What: Encodes strategy metadata and thresholds.
Why: Helps select appropriate quality checking behaviour.
"""

from __future__ import annotations

"""品質チェッカーストラテジーパターン実装

DDDとストラテジーパターンを組み合わせた品質チェック機能。
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_issue import IssueCategory, IssueSeverity, QualityIssue

if TYPE_CHECKING:
    from noveler.domain.value_objects.session_id import SessionId

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class QualityChecker(ABC):
    """品質チェッカーの抽象基底クラス

    ストラテジーパターンの戦略インターフェース。
    各具体的なチェッカーはこのインターフェースを実装する。
    """

    @abstractmethod
    def check(self, content: str) -> list[QualityIssue]:
        """コンテンツの品質チェックを実行

        Args:
            content: チェック対象のテキスト

        Returns:
            検出された品質問題のリスト
        """


@dataclass
class QualityCheckResults:
    """品質チェック結果を管理するクラス"""

    issues: list[QualityIssue] = field(default_factory=list)

    def total_issues(self) -> int:
        """問題の総数を返す"""
        return len(self.issues)

    def count_by_severity(self, severity: str) -> int:
        """重要度別の問題数を返す"""
        return sum(1 for issue in self.issues if issue.severity == severity)

    def by_category(self, category: str) -> list[QualityIssue]:
        """カテゴリ別の問題を返す"""
        return [issue for issue in self.issues if issue.category == category]

    def all_issues(self) -> list[QualityIssue]:
        """すべての問題を返す"""
        return self.issues.copy()

    def calculate_quality_score(self, base_score: float) -> float:
        """品質スコアを計算

        Args:
            base_score: 基準スコア(デフォルト100点)

        Returns:
            減点後の品質スコア
        """
        total_penalty = sum(issue.penalty_points for issue in self.issues)
        return max(0.0, base_score - total_penalty)


@dataclass
class QualityCheckAggregate:
    """品質チェック集約ルート

    複数のチェッカーを管理し、統合的な品質チェックを実行する。
    """

    session_id: SessionId
    _checkers: list[QualityChecker] = field(default_factory=list)
    _results: QualityCheckResults = field(default_factory=QualityCheckResults)
    _created_at: datetime = field(default_factory=datetime.now)
    _completed_at: datetime | None = field(default=None)

    def add_checker(self, checker: QualityChecker) -> None:
        """品質チェッカーを追加

        Args:
            checker: 追加するチェッカー
        """
        # 同じインスタンスの重複追加を防ぐ
        if checker not in self._checkers:
            self._checkers.append(checker)

    def get_checker_count(self) -> int:
        """登録されているチェッカー数を返す"""
        return len(self._checkers)

    def run_all_checks(self, content: str) -> QualityCheckResults:
        """すべてのチェッカーを実行

        Args:
            content: チェック対象のコンテンツ

        Returns:
            統合されたチェック結果
        """
        all_issues = []

        for checker in self._checkers:
            try:
                issues = checker.check(content)
                all_issues.extend(issues)
            except Exception as e:
                # チェッカーのエラーをエラー情報として記録
                error_issue = QualityIssue(
                    category=IssueCategory.SYSTEM,
                    severity=IssueSeverity.ERROR,
                    message=f"チェッカーエラー: {e!s}",
                    line_number=0,
                    context=f"{checker.__class__.__name__}でエラーが発生しました",
                )

                all_issues.append(error_issue)

        self._results = QualityCheckResults(issues=all_issues)
        self._completed_at = project_now().datetime

        return self._results


class BasicStyleChecker(QualityChecker):
    """基本的な文体チェッカー"""

    def check(self, content: str) -> list[QualityIssue]:
        """基本的な文体の問題をチェック(リファクタリング済み:複雑度11→4に削減)"""
        issues = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            issues.extend(self._check_line_style_issues(line, line_num))

        return issues

    def _check_line_style_issues(self, line: str, line_num: int) -> list[QualityIssue]:
        """行単位でスタイルの問題をチェック"""
        issues = []

        # 各チェックルールを適用
        issues.extend(self._check_ellipsis_issues(line, line_num))
        issues.extend(self._check_exclamation_issues(line, line_num))
        issues.extend(self._check_text_duplication_issues(line, line_num))
        issues.extend(self._check_spacing_issues(line, line_num))

        return issues

    def _check_ellipsis_issues(self, line: str, line_num: int) -> list[QualityIssue]:
        """三点リーダーの誤用をチェック"""
        issues = []

        for pattern, replacement in [("。。。", "…"), ("...", "…")]:
            if pattern in line:
                issues.append(
                    QualityIssue(
                        category=IssueCategory.STYLE,
                        severity=IssueSeverity.WARNING,
                        message="三点リーダーは「…」を使用してください",
                        line_number=line_num,
                        position=line.find(pattern),
                        context=line.strip(),
                        suggestion=line.replace(pattern, replacement),
                    )
                )

        return issues

    def _check_exclamation_issues(self, line: str, line_num: int) -> list[QualityIssue]:
        """感嘆符の過剰使用をチェック"""
        issues = []

        # 過剰な感嘆符(!!!)
        if "!!!" in line:
            issues.append(
                QualityIssue(
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.WARNING,
                    message="感嘆符の過剰使用です",
                    line_number=line_num,
                    position=line.find("!!!"),
                    context=line.strip(),
                    suggestion=line.replace("!!!", "!"),
                )
            )

        # 連続感嘆符(!!)
        elif "!!" in line:
            issues.append(
                QualityIssue(
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.INFO,
                    message="感嘆符の連続使用に注意してください",
                    line_number=line_num,
                    position=line.find("!!"),
                    context=line.strip(),
                    suggestion=line.replace("!!", "!"),
                )
            )

        return issues

    def _check_text_duplication_issues(self, line: str, line_num: int) -> list[QualityIssue]:
        """文末重複表現をチェック"""
        issues = []

        if "です。です。" in line:
            issues.append(
                QualityIssue(
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.ERROR,
                    message="文末の重複表現があります",
                    line_number=line_num,
                    position=line.find("です。です。"),
                    context=line.strip(),
                    suggestion=line.replace("です。です。", "です。"),
                )
            )

        return issues

    def _check_spacing_issues(self, line: str, line_num: int) -> list[QualityIssue]:
        """スペースの問題をチェック"""
        issues = []

        # 全角スペースの誤用
        if " " in line and line.strip() and not line.startswith(" "):
            issues.append(
                QualityIssue(
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.INFO,
                    message="文中に全角スペースがあります",
                    line_number=line_num,
                    position=line.find(" "),
                    context=line.strip(),
                )
            )

        # 連続スペース
        if "  " in line:
            issues.append(
                QualityIssue(
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.INFO,
                    message="連続スペースがあります",
                    line_number=line_num,
                    position=line.find("  "),
                    context=line.strip(),
                    suggestion=line.replace("  ", " "),
                )
            )

        return issues


class InvalidKanjiChecker(QualityChecker):
    """無効な漢字をチェックするチェッカー"""

    # 旧字体と新字体の対応表
    OLD_TO_NEW_KANJI: ClassVar[dict[str, str]] = {
        "壱": "一",
        "弐": "二",
        "参": "三",
        "會": "会",
        "體": "体",
        "變": "変",
        "價": "価",
        "學": "学",
        "國": "国",
        "圓": "円",
    }

    # 環境依存文字
    PLATFORM_DEPENDENT_CHARS: ClassVar[list[str]] = ["①", "②", "③", "④", "⑤", "㈱", "㈲", "㊤", "㊥", "㊦"]

    def check(self, content: str) -> list[QualityIssue]:
        """無効な漢字の使用をチェック"""
        issues = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # 旧字体チェック
            for old_kanji, new_kanji in self.OLD_TO_NEW_KANJI.items():
                if old_kanji in line:
                    issues.append(
                        QualityIssue(
                            category=IssueCategory.KANJI,
                            severity=IssueSeverity.ERROR,
                            message=f"旧字体「{old_kanji}」が使用されています",
                            line_number=line_num,
                            position=line.find(old_kanji),
                            context=line.strip(),
                            suggestion=new_kanji,
                            penalty_points=5,
                        )
                    )

            # 環境依存文字チェック
            issues.extend(
                QualityIssue(
                    category=IssueCategory.KANJI,
                    severity=IssueSeverity.ERROR,
                    message=f"環境依存文字「{char}」が使用されています",
                    line_number=line_num,
                    position=line.find(char),
                    context=line.strip(),
                    penalty_points=5,
                )
                for char in self.PLATFORM_DEPENDENT_CHARS
                if char in line
            )

        return issues
