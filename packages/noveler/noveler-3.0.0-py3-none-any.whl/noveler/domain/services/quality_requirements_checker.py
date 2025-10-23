"""品質必須要件チェッカー

必須要件（Must Pass）と加点要素（Nice to Have）を明確に分離し、
必須要件未達の場合は即不合格として具体的な修正指示を提供する。

SPEC-QRC-001: Quality Requirements Checker仕様
- 目標文字数範囲チェック（8,000-10,000文字）
- 文章リズム基準チェック（連続パターン検出）
- 修正指示の具体的生成
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from noveler.domain.services.text_rhythm_analysis_service import TextRhythmAnalysisService
from noveler.domain.value_objects.text_rhythm_analysis import RhythmIssueType, RhythmSeverity
from noveler.domain.writing.value_objects.word_count import WordCount

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
#     YamlProjectConfigRepository,
# )


class RequirementType(Enum):
    """必須要件タイプ"""
    WORD_COUNT = "word_count"
    TEXT_RHYTHM = "text_rhythm"


@dataclass(frozen=True)
class RequirementIssue:
    """必須要件違反項目"""

    requirement_type: RequirementType
    title: str
    description: str
    current_value: str
    expected_value: str
    fix_instruction: str
    severity: str = "critical"


@dataclass(frozen=True)
class RequirementsCheckResult:
    """必須要件チェック結果"""

    all_passed: bool
    issues: list[RequirementIssue]
    word_count_passed: bool
    rhythm_passed: bool
    total_word_count: int

    @property
    def has_word_count_issue(self) -> bool:
        """文字数要件に問題があるか"""
        return not self.word_count_passed

    @property
    def has_rhythm_issue(self) -> bool:
        """リズム要件に問題があるか"""
        return not self.rhythm_passed


class QualityRequirementsChecker:
    """品質必須要件チェッカー

    必須要件を満たさない場合は即不合格とし、
    具体的な修正指示を提供する。
    """

    def __init__(self, project_name: str = "default") -> None:
        """初期化

        Args:
            project_name: プロジェクト名（設定読み込み用）
        """
        self.rhythm_analyzer = TextRhythmAnalysisService()
        self.project_name = project_name

        # デフォルト文字数要件（プロジェクト設定が取得できない場合）
        self.DEFAULT_MIN_WORD_COUNT = 8000
        self.DEFAULT_MAX_WORD_COUNT = 10000

    def _get_word_count_requirements(self) -> tuple[int, int]:
        """プロジェクト設定から文字数要件を取得

        Returns:
            tuple[int, int]: (最小文字数, 最大文字数)
        """
        try:
            # プロジェクト設定からtarget_word_countを取得
            project_path = Path(f"projects/{self.project_name}")  # TODO: IPathServiceを使用するように修正
            if project_path.exists():
                # TODO: F821修正 - YamlProjectConfigRepository未定義のため一時的にコメントアウト
                # config_repo = YamlProjectConfigRepository(project_path)
                # config = config_repo.load_config(project_path)
                config = {}

                # target_word_countが設定されている場合はそれを使用
                if "target_word_count" in config:
                    target_count = int(config["target_word_count"])
                    # target_word_countを中心とした範囲を設定（±20%）
                    min_count = max(1000, int(target_count * 0.8))
                    max_count = int(target_count * 1.2)
                    return min_count, max_count

                # min_word_count/max_word_countが個別に設定されている場合
                min_count = config.get("min_word_count", self.DEFAULT_MIN_WORD_COUNT)
                max_count = config.get("max_word_count", self.DEFAULT_MAX_WORD_COUNT)
                return int(min_count), int(max_count)

        except Exception:
            # 設定読み込みに失敗した場合はデフォルト値を使用
            pass

        return self.DEFAULT_MIN_WORD_COUNT, self.DEFAULT_MAX_WORD_COUNT

    def check_must_pass_requirements(self, content: str) -> RequirementsCheckResult:
        """必須要件の総合チェック

        Args:
            content: チェック対象テキスト

        Returns:
            RequirementsCheckResult: チェック結果
        """
        issues = []

        # 1. 文字数要件チェック
        word_count_result = self._check_word_count_requirement(content)
        word_count_passed = word_count_result.all_passed
        if not word_count_passed:
            issues.extend(word_count_result.issues)

        # 2. 文章リズム要件チェック
        rhythm_result = self._check_rhythm_requirement(content)
        rhythm_passed = rhythm_result.all_passed
        if not rhythm_passed:
            issues.extend(rhythm_result.issues)

        # 3. 総合判定
        all_passed = word_count_passed and rhythm_passed

        # 実際の文字数を取得
        actual_word_count = WordCount.from_japanese_text(content)

        return RequirementsCheckResult(
            all_passed=all_passed,
            issues=issues,
            word_count_passed=word_count_passed,
            rhythm_passed=rhythm_passed,
            total_word_count=actual_word_count.value,
        )

    def _check_word_count_requirement(self, content: str) -> RequirementsCheckResult:
        """文字数要件チェック"""
        issues = []
        word_count = WordCount.from_japanese_text(content)

        # プロジェクト設定から文字数要件を取得
        min_count, max_count = self._get_word_count_requirements()

        if word_count.value < min_count:
            shortage = min_count - word_count.value
            percentage_short = (shortage / min_count) * 100

            issue = RequirementIssue(
                requirement_type=RequirementType.WORD_COUNT,
                title="文字数要件未達",
                description=f"現在{word_count.format()}、目標{min_count:,}-{max_count:,}文字",
                current_value=str(word_count.value),
                expected_value=f"{min_count}-{max_count}",
                fix_instruction=self._generate_word_count_fix_instruction(
                    current=word_count.value,
                    shortage=shortage,
                    percentage=percentage_short,
                    content=content
                )
            )
            issues.append(issue)

        elif word_count.value > max_count:
            excess = word_count.value - max_count
            percentage_over = (excess / max_count) * 100

            issue = RequirementIssue(
                requirement_type=RequirementType.WORD_COUNT,
                title="文字数上限超過",
                description=f"現在{word_count.format()}、上限{max_count:,}文字",
                current_value=str(word_count.value),
                expected_value=f"{min_count}-{max_count}",
                fix_instruction=self._generate_word_count_reduction_instruction(
                    current=word_count.value,
                    excess=excess,
                    percentage=percentage_over
                )
            )
            issues.append(issue)

        return RequirementsCheckResult(
            all_passed=len(issues) == 0,
            issues=issues,
            word_count_passed=len(issues) == 0,
            rhythm_passed=True,  # この関数では文字数のみチェック
            total_word_count=word_count.value,
        )

    def _check_rhythm_requirement(self, content: str) -> RequirementsCheckResult:
        """文章リズム要件チェック"""
        issues = []

        # リズム分析実行
        rhythm_report = self.rhythm_analyzer.analyze_text_rhythm(content)

        # 重大なリズム問題をチェック
        for rhythm_issue in rhythm_report.issues:
            if rhythm_issue.severity in [RhythmSeverity.HIGH, RhythmSeverity.CRITICAL]:
                issue = RequirementIssue(
                    requirement_type=RequirementType.TEXT_RHYTHM,
                    title=self._get_rhythm_issue_title(rhythm_issue.issue_type),
                    description=rhythm_issue.description,
                    current_value=f"行{rhythm_issue.start_index+1}-{rhythm_issue.end_index+1}",
                    expected_value="適切なリズム",
                    fix_instruction=rhythm_issue.suggestion
                )
                issues.append(issue)

        # 全体的なリズムスコアが低すぎる場合
        if rhythm_report.overall_score < 40:  # 40点未満は必須要件違反
            issue = RequirementIssue(
                requirement_type=RequirementType.TEXT_RHYTHM,
                title="文章リズム全体的問題",
                description=f"リズムスコア{rhythm_report.overall_score:.1f}点（最低基準: 40点）",
                current_value=f"{rhythm_report.overall_score:.1f}点",
                expected_value="40点以上",
                fix_instruction=self._generate_overall_rhythm_fix_instruction(rhythm_report)
            )
            issues.append(issue)

        return RequirementsCheckResult(
            all_passed=len(issues) == 0,
            issues=issues,
            word_count_passed=True,  # この関数ではリズムのみチェック
            rhythm_passed=len(issues) == 0,
            total_word_count=0,  # リズムチェックでは文字数は計算しない
        )

    def _generate_word_count_fix_instruction(self, current: int, shortage: int, percentage: float, content: str) -> str:
        """文字数不足の修正指示生成"""
        lines = content.split("\n")
        len([line for line in lines if line.strip()])

        instruction_parts = [
            f"📝 {shortage:,}文字の追加が必要です（約{percentage:.0f}%不足）",
            "",
            "推奨する追加方法:",
        ]

        if shortage <= 1000:
            instruction_parts.extend([
                "• 既存の描写をより詳細に（各シーン100-200文字追加）",
                "• キャラクターの内面描写を充実",
                "• 環境や雰囲気の描写を追加"
            ])
        elif shortage <= 2000:
            instruction_parts.extend([
                "• 新しいサブシーンを1-2個追加",
                "• 会話シーンの前後に心理描写を追加",
                "• 五感を使った詳細な情景描写",
                "• キャラクター間の関係性を深める描写"
            ])
        else:
            instruction_parts.extend([
                "• メインプロットに新しいエピソードを追加",
                "• サブキャラクターとの交流シーンを挿入",
                "• 世界観の説明を充実させる",
                "• 主人公の成長過程をより詳細に描写"
            ])

        instruction_parts.extend([
            "",
            f"目標: {current:,}文字 → {current + shortage:,}文字以上"
        ])

        return "\n".join(instruction_parts)

    def _generate_word_count_reduction_instruction(self, current: int, excess: int, percentage: float) -> str:
        """文字数超過の修正指示生成"""
        return f"""📝 {excess:,}文字の削減が必要です（約{percentage:.0f}%超過）

推奨する削減方法:
• 冗長な描写を簡潔に整理
• 重複する表現を統合
• 本筋に関係の薄い描写を削除
• 会話の無駄な部分を削除

目標: {current:,}文字 → {current - excess:,}文字以下"""

    def _get_rhythm_issue_title(self, issue_type: RhythmIssueType) -> str:
        """リズム問題タイトルの取得"""
        title_map = {
            RhythmIssueType.CONSECUTIVE_SHORT: "連続短文問題",
            RhythmIssueType.CONSECUTIVE_LONG: "連続長文問題",
            RhythmIssueType.MONOTONOUS_LENGTH: "単調長さ問題",
            RhythmIssueType.IRREGULAR_PATTERN: "不規則パターン問題"
        }
        return title_map.get(issue_type, "リズム問題")

    def _generate_overall_rhythm_fix_instruction(self, rhythm_report) -> str:
        """全体的なリズム問題の修正指示"""
        stats = rhythm_report.statistics

        instruction_parts = ["📝 文章リズム全体の改善が必要です", ""]

        # 統計情報に基づく具体的指示
        if stats.average_length < 20:
            instruction_parts.append("• 短文が多すぎます。文を結合して25-40文字程度にしてください")
        elif stats.average_length > 50:
            instruction_parts.append("• 長文が多すぎます。句点で分割して40文字以下にしてください")

        if stats.std_deviation < 5:
            instruction_parts.append("• 文長のバリエーションが少なすぎます。長短を組み合わせてください")
        elif stats.std_deviation > 20:
            instruction_parts.append("• 文長のばらつきが大きすぎます。適度に統一してください")

        instruction_parts.extend([
            "",
            "理想的な文章リズム:",
            "• 短文（15-25文字）30%",
            "• 中文（26-40文字）50%",
            "• 長文（41-60文字）20%"
        ])

        return "\n".join(instruction_parts)
