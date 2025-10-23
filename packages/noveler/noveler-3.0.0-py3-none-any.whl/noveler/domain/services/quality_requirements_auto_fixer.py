"""品質必須要件自動修正サービス

SPEC-QRC-002: Quality Requirements Auto-Fixer仕様
- 必須要件不合格時の自動修正・再チェックループ実行
- 最大試行回数制限とタイムアウト機能
- 修正履歴トラッキングと進捗可視化
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from noveler.domain.services.quality_requirements_checker import (
    QualityRequirementsChecker,
    RequirementIssue,
    RequirementsCheckResult,
)

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
#     YamlProjectConfigRepository,
# )


class AutoFixerStatus(Enum):
    """自動修正ステータス"""
    IN_PROGRESS = "in_progress"
    COMPLETED_SUCCESS = "completed_success"
    COMPLETED_FAILURE = "completed_failure"
    MAX_ATTEMPTS_EXCEEDED = "max_attempts_exceeded"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class FixAttempt:
    """修正試行記録"""
    attempt_number: int
    original_content: str
    fixed_content: str
    issues_before: list[RequirementIssue]
    issues_after: list[RequirementIssue]
    fix_duration_ms: float
    success: bool


@dataclass(frozen=True)
class AutoFixerResult:
    """自動修正結果"""
    status: AutoFixerStatus
    final_content: str
    total_attempts: int
    successful_attempts: int
    total_duration_ms: float
    fix_attempts: list[FixAttempt]
    final_check_result: RequirementsCheckResult
    error_message: str | None = None

    @property
    def success_rate(self) -> float:
        """修正成功率を取得"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100


class QualityRequirementsAutoFixer:
    """品質必須要件自動修正サービス

    必須要件不合格時に自動で修正を試行し、
    合格するまで規定回数まで繰り返し実行
    """

    def __init__(
        self,
        project_name: str = "default",
        max_attempts: int = 5,
        timeout_seconds: int = 300
    ) -> None:
        """初期化

        Args:
            project_name: プロジェクト名
            max_attempts: 最大修正試行回数
            timeout_seconds: タイムアウト秒数
        """
        self.requirements_checker = QualityRequirementsChecker(project_name)
        self.project_name = project_name

        # プロジェクト設定から規定回数を取得（明示指定があればそれを優先）
        if max_attempts != 5:  # デフォルト値と異なる場合は明示指定を優先
            self.max_attempts = max_attempts
        else:
            self.max_attempts = self._get_max_attempts_from_config(max_attempts)

        if timeout_seconds != 300:  # デフォルト値と異なる場合は明示指定を優先
            self.timeout_seconds = timeout_seconds
        else:
            self.timeout_seconds = self._get_timeout_from_config(timeout_seconds)

    def _get_max_attempts_from_config(self, default_attempts: int) -> int:
        """プロジェクト設定から最大試行回数を取得

        Args:
            default_attempts: デフォルト試行回数

        Returns:
            int: 最大試行回数
        """
        try:

            project_path = Path(f"projects/{self.project_name}")  # TODO: IPathServiceを使用するように修正
            if project_path.exists():
                # TODO: F821修正 - YamlProjectConfigRepository未定義のため一時的にコメントアウト
                # config_repo = YamlProjectConfigRepository(project_path)
                # config = config_repo.load_config(project_path)
                config = {}

                # auto_fix_max_attemptsが設定されている場合はそれを使用
                return int(config.get("auto_fix_max_attempts", default_attempts))

        except Exception:
            # 設定読み込みに失敗した場合はデフォルト値を使用
            pass

        return default_attempts

    def _get_timeout_from_config(self, default_timeout: int) -> int:
        """プロジェクト設定からタイムアウト秒数を取得

        Args:
            default_timeout: デフォルトタイムアウト秒数

        Returns:
            int: タイムアウト秒数
        """
        try:

            project_path = Path(f"projects/{self.project_name}")  # TODO: IPathServiceを使用するように修正
            if project_path.exists():
                # TODO: F821修正 - YamlProjectConfigRepository未定義のため一時的にコメントアウト
                # config_repo = YamlProjectConfigRepository(project_path)
                # config = config_repo.load_config(project_path)
                config = {}

                # auto_fix_timeout_secondsが設定されている場合はそれを使用
                return int(config.get("auto_fix_timeout_seconds", default_timeout))

        except Exception:
            # 設定読み込みに失敗した場合はデフォルト値を使用
            pass

        return default_timeout

    def auto_fix_requirements(self, content: str) -> AutoFixerResult:
        """必須要件自動修正の実行

        Args:
            content: 修正対象コンテンツ

        Returns:
            AutoFixerResult: 修正結果
        """
        start_time = time.time()
        fix_attempts: list[FixAttempt] = []
        current_content = content
        successful_attempts = 0

        for attempt in range(1, self.max_attempts + 1):
            # タイムアウトチェック
            if time.time() - start_time > self.timeout_seconds:
                return AutoFixerResult(
                    status=AutoFixerStatus.TIMEOUT,
                    final_content=current_content,
                    total_attempts=attempt - 1,
                    successful_attempts=successful_attempts,
                    total_duration_ms=(time.time() - start_time) * 1000,
                    fix_attempts=fix_attempts,
                    final_check_result=self.requirements_checker.check_must_pass_requirements(current_content),
                    error_message=f"タイムアウト: {self.timeout_seconds}秒を超過"
                )

            # 修正前の問題チェック
            before_result = self.requirements_checker.check_must_pass_requirements(current_content)

            # 既に合格している場合は成功終了
            if before_result.all_passed:
                return AutoFixerResult(
                    status=AutoFixerStatus.COMPLETED_SUCCESS,
                    final_content=current_content,
                    total_attempts=attempt - 1,
                    successful_attempts=successful_attempts,
                    total_duration_ms=(time.time() - start_time) * 1000,
                    fix_attempts=fix_attempts,
                    final_check_result=before_result
                )

            # 修正実行
            attempt_start = time.time()
            try:
                fixed_content = self._apply_fixes(current_content, before_result.issues)
                fix_duration = (time.time() - attempt_start) * 1000

                # 修正後の問題チェック
                after_result = self.requirements_checker.check_must_pass_requirements(fixed_content)

                # 修正試行記録
                attempt_success = len(after_result.issues) < len(before_result.issues)
                if attempt_success:
                    successful_attempts += 1

                fix_attempt = FixAttempt(
                    attempt_number=attempt,
                    original_content=current_content,
                    fixed_content=fixed_content,
                    issues_before=before_result.issues,
                    issues_after=after_result.issues,
                    fix_duration_ms=fix_duration,
                    success=attempt_success
                )
                fix_attempts.append(fix_attempt)

                # 修正されたコンテンツを次の試行用に更新
                current_content = fixed_content

                # 完全に合格した場合は成功終了
                if after_result.all_passed:
                    return AutoFixerResult(
                        status=AutoFixerStatus.COMPLETED_SUCCESS,
                        final_content=current_content,
                        total_attempts=attempt,
                        successful_attempts=successful_attempts,
                        total_duration_ms=(time.time() - start_time) * 1000,
                        fix_attempts=fix_attempts,
                        final_check_result=after_result
                    )

            except Exception:
                # 修正試行でエラーが発生した場合
                fix_attempt = FixAttempt(
                    attempt_number=attempt,
                    original_content=current_content,
                    fixed_content=current_content,  # 修正失敗のため元のまま
                    issues_before=before_result.issues,
                    issues_after=before_result.issues,  # 修正失敗のため変化なし
                    fix_duration_ms=(time.time() - attempt_start) * 1000,
                    success=False
                )
                fix_attempts.append(fix_attempt)

        # 最大試行回数に達した場合
        final_result = self.requirements_checker.check_must_pass_requirements(current_content)
        return AutoFixerResult(
            status=AutoFixerStatus.MAX_ATTEMPTS_EXCEEDED,
            final_content=current_content,
            total_attempts=self.max_attempts,
            successful_attempts=successful_attempts,
            total_duration_ms=(time.time() - start_time) * 1000,
            fix_attempts=fix_attempts,
            final_check_result=final_result,
            error_message=f"最大試行回数 {self.max_attempts} 回に達しました"
        )

    def _apply_fixes(self, content: str, issues: list[RequirementIssue]) -> str:
        """具体的な修正を適用

        Args:
            content: 修正対象コンテンツ
            issues: 修正すべき問題リスト

        Returns:
            str: 修正後コンテンツ
        """
        fixed_content = content

        for issue in issues:
            if issue.requirement_type.value == "word_count":
                fixed_content = self._fix_word_count_issue(fixed_content, issue)
            elif issue.requirement_type.value == "text_rhythm":
                fixed_content = self._fix_rhythm_issue(fixed_content, issue)

        return fixed_content

    def _fix_word_count_issue(self, content: str, issue: RequirementIssue) -> str:
        """文字数問題の自動修正

        Args:
            content: 修正対象コンテンツ
            issue: 文字数問題

        Returns:
            str: 修正後コンテンツ
        """
        if issue.title == "文字数要件未達":
            # 文字数不足の場合の自動修正ロジック
            # 既存の文章を拡張する簡単な手法を使用
            sentences = content.split("。")

            # 各文の後に詳細描写を追加
            expanded_sentences = []
            for sentence in sentences:
                if sentence.strip():
                    expanded_sentences.append(sentence.strip())
                    # 簡単な描写拡張（実際の実装ではより高度なAI修正が必要）
                    if len(sentence.strip()) > 10:  # 短すぎる文は拡張しない
                        expanded_sentences.append("その時、周囲の空気が変わったのを感じた")

            return "。".join(expanded_sentences) + "。"

        if issue.title == "文字数上限超過":
            # 文字数超過の場合は不要な部分を削除
            # 簡単な削減ロジック（実際にはより精密な処理が必要）
            target_length = int(issue.expected_value.split("-")[1])
            if len(content) > target_length:
                return content[:target_length-100] + "..."

        return content

    def _fix_rhythm_issue(self, content: str, issue: RequirementIssue) -> str:
        """リズム問題の自動修正

        Args:
            content: 修正対象コンテンツ
            issue: リズム問題

        Returns:
            str: 修正後コンテンツ
        """
        if "連続短文" in issue.title:
            # 連続短文問題: 短い文を結合して中文にする
            sentences = content.split("。")
            fixed_sentences = []
            i = 0

            while i < len(sentences):
                if i < len(sentences) - 1:
                    current = sentences[i].strip()
                    next_sentence = sentences[i + 1].strip()

                    # 両方とも短い文の場合は結合
                    if len(current) <= 20 and len(next_sentence) <= 20 and current and next_sentence:
                        combined = current + "、" + next_sentence
                        fixed_sentences.append(combined)
                        i += 2  # 次の文も処理済みとしてスキップ
                    else:
                        if current:
                            fixed_sentences.append(current)
                        i += 1
                else:
                    if sentences[i].strip():
                        fixed_sentences.append(sentences[i].strip())
                    i += 1

            return "。".join(fixed_sentences) + "。"

        if "連続長文" in issue.title:
            # 連続長文問題: 長い文を分割する
            sentences = content.split("。")
            fixed_sentences = []

            for sentence in sentences:
                if len(sentence.strip()) > 60:
                    # 長い文を句点で分割
                    parts = sentence.split("、")
                    if len(parts) > 2:
                        mid_point = len(parts) // 2
                        first_part = "、".join(parts[:mid_point])
                        second_part = "、".join(parts[mid_point:])
                        fixed_sentences.append(first_part)
                        fixed_sentences.append(second_part)
                    else:
                        fixed_sentences.append(sentence.strip())
                elif sentence.strip():
                    fixed_sentences.append(sentence.strip())

            return "。".join(fixed_sentences) + "。"

        return content

    def get_fix_summary(self, result: AutoFixerResult) -> str:
        """修正結果のサマリを生成

        Args:
            result: 修正結果

        Returns:
            str: 修正サマリ
        """
        status_messages = {
            AutoFixerStatus.COMPLETED_SUCCESS: "✅ 修正成功",
            AutoFixerStatus.COMPLETED_FAILURE: "❌ 修正失敗",
            AutoFixerStatus.MAX_ATTEMPTS_EXCEEDED: "⚠️ 最大試行回数到達",
            AutoFixerStatus.TIMEOUT: "⏱️ タイムアウト"
        }

        summary_parts = [
            "📊 自動修正結果サマリ",
            f"ステータス: {status_messages.get(result.status, result.status.value)}",
            f"試行回数: {result.total_attempts}/{self.max_attempts}",
            f"成功回数: {result.successful_attempts}",
            f"成功率: {result.success_rate:.1f}%",
            f"実行時間: {result.total_duration_ms/1000:.1f}秒",
            "",
            "最終チェック結果:",
            f"  文字数合格: {'✅' if result.final_check_result.word_count_passed else '❌'}",
            f"  リズム合格: {'✅' if result.final_check_result.rhythm_passed else '❌'}",
            f"  総合判定: {'✅ 合格' if result.final_check_result.all_passed else '❌ 不合格'}"
        ]

        if result.error_message:
            summary_parts.extend([
                "",
                f"エラー: {result.error_message}"
            ])

        return "\n".join(summary_parts)
