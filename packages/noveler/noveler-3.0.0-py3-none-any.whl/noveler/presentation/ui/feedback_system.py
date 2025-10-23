"""
フィードバックシステム

執筆プロセスのユーザーフィードバック収集・表示機能。
品質評価、改善提案、インタラクティブな確認機能を提供。
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
from noveler.presentation.shared.shared_utilities import _get_console


def get_console():
    return _get_console()


class FeedbackType(Enum):
    """フィードバックの種類"""
    CONFIRMATION = "confirmation"
    QUALITY_CHECK = "quality_check"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"
    USER_INPUT = "user_input"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class FeedbackMessage:
    """フィードバックメッセージ"""
    feedback_type: FeedbackType
    title: str
    message: str
    step_id: int | None = None
    options: list[str] | None = None
    default_option: str | None = None
    timestamp: datetime | None = None
    requires_response: bool = False
    severity: str = "info"  # info, warning, error, success

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class InteractiveFeedbackSystem:
    """インタラクティブフィードバックシステム

    執筆プロセス中のユーザーとのインタラクションを管理し、
    品質チェック、確認、改善提案などのフィードバックを提供する。
    """

    def __init__(self, episode_number: int) -> None:
        self.episode_number = episode_number
        self.console = get_console()
        self.feedback_history: list[FeedbackMessage] = []
        self.user_preferences = {
            "auto_confirm_low_risk": False,
            "detailed_explanations": True,
            "show_improvement_tips": True,
            "interactive_mode": True
        }

    @performance_monitor
    def request_confirmation(
        self,
        title: str,
        message: str,
        step_id: int | None = None,
        default: bool = True
    ) -> bool:
        """確認を要求"""
        feedback = FeedbackMessage(
            feedback_type=FeedbackType.CONFIRMATION,
            title=title,
            message=message,
            step_id=step_id,
            options=["はい", "いいえ"],
            default_option="はい" if default else "いいえ",
            requires_response=True
        )

        self._log_feedback(feedback)

        if not self.user_preferences["interactive_mode"]:
            return default

        self._display_feedback(feedback)

        # ユーザー入力の待機（実際のCLI環境では input() を使用）
        response = self._get_user_response(feedback.options, feedback.default_option)

        return response.lower() in ["はい", "yes", "y", "1"]

    @performance_monitor
    def show_quality_check_result(
        self,
        step_id: int,
        quality_score: float,
        issues: list[str],
        suggestions: list[str]
    ) -> dict[str, Any]:
        """品質チェック結果の表示"""

        # 品質レベルの判定
        quality_level = self._determine_quality_level(quality_score)

        feedback = FeedbackMessage(
            feedback_type=FeedbackType.QUALITY_CHECK,
            title=f"ステップ{step_id} 品質チェック結果",
            message=f"品質スコア: {quality_score:.1f}/100 ({quality_level})",
            step_id=step_id,
            severity=self._get_severity_from_score(quality_score)
        )

        self._log_feedback(feedback)
        self._display_quality_result(feedback, quality_score, issues, suggestions)

        # 改善が必要な場合のインタラクション
        requires_improvement = quality_score < 70
        user_choice = None

        if requires_improvement:
            user_choice = self._handle_quality_improvement_dialog(step_id, issues, suggestions)

        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "issues": issues,
            "suggestions": suggestions,
            "requires_improvement": requires_improvement,
            "user_choice": user_choice
        }

    @performance_monitor
    def show_improvement_suggestions(
        self,
        step_id: int,
        suggestions: list[dict[str, str]]
    ) -> str | None:
        """改善提案の表示"""
        if not self.user_preferences["show_improvement_tips"] or not suggestions:
            return None

        feedback = FeedbackMessage(
            feedback_type=FeedbackType.IMPROVEMENT_SUGGESTION,
            title=f"ステップ{step_id} 改善提案",
            message=f"{len(suggestions)}個の改善提案があります",
            step_id=step_id
        )

        self._log_feedback(feedback)
        self._display_improvement_suggestions(feedback, suggestions)

        # ユーザーが改善提案を選択
        if self.user_preferences["interactive_mode"]:
            return self._select_improvement_suggestion(suggestions)

        return None

    @performance_monitor
    def show_warning(
        self,
        title: str,
        message: str,
        step_id: int | None = None,
        require_acknowledgment: bool = False
    ) -> bool:
        """警告の表示"""
        feedback = FeedbackMessage(
            feedback_type=FeedbackType.WARNING,
            title=title,
            message=message,
            step_id=step_id,
            severity="warning",
            requires_response=require_acknowledgment
        )

        self._log_feedback(feedback)
        self._display_feedback(feedback)

        if require_acknowledgment:
            return self.request_confirmation("警告を確認しましたか？", "続行しますか？")

        return True

    @performance_monitor
    def show_error(
        self,
        title: str,
        message: str,
        step_id: int | None = None,
        recovery_options: list[str] | None = None
    ) -> str | None:
        """エラーの表示と復旧オプション"""
        feedback = FeedbackMessage(
            feedback_type=FeedbackType.ERROR,
            title=title,
            message=message,
            step_id=step_id,
            options=recovery_options,
            severity="error",
            requires_response=bool(recovery_options)
        )

        self._log_feedback(feedback)
        self._display_feedback(feedback)

        if recovery_options:
            return self._get_user_response(recovery_options, recovery_options[0])

        return None

    @performance_monitor
    def show_success(
        self,
        title: str,
        message: str,
        step_id: int | None = None,
        details: dict[str, Any] | None = None
    ) -> None:
        """成功メッセージの表示"""
        feedback = FeedbackMessage(
            feedback_type=FeedbackType.SUCCESS,
            title=title,
            message=message,
            step_id=step_id,
            severity="success"
        )

        self._log_feedback(feedback)
        self._display_feedback(feedback)

        if details and self.user_preferences["detailed_explanations"]:
            self._display_success_details(details)

    @performance_monitor
    def collect_user_input(
        self,
        prompt: str,
        input_type: str = "text",
        validation_func: Callable | None = None
    ) -> Any:
        """ユーザー入力の収集"""
        feedback = FeedbackMessage(
            feedback_type=FeedbackType.USER_INPUT,
            title="ユーザー入力要求",
            message=prompt,
            requires_response=True
        )

        self._log_feedback(feedback)
        self._display_feedback(feedback)

        # 実際の実装ではここでユーザー入力を受け取る
        # 今回はモックとして処理
        return self._mock_user_input(input_type)

    def _display_feedback(self, feedback: FeedbackMessage) -> None:
        """フィードバックの表示"""
        # 色とアイコンの設定
        color_map = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }

        icon_map = {
            FeedbackType.CONFIRMATION: "❓",
            FeedbackType.QUALITY_CHECK: "📊",
            FeedbackType.IMPROVEMENT_SUGGESTION: "💡",
            FeedbackType.USER_INPUT: "✏️ ",
            FeedbackType.WARNING: "⚠️ ",
            FeedbackType.ERROR: "❌",
            FeedbackType.SUCCESS: "✅"
        }

        color = color_map.get(feedback.severity, "white")
        icon = icon_map.get(feedback.feedback_type, "ℹ️ ")

        step_info = f" [ステップ{feedback.step_id}]" if feedback.step_id else ""

        self.console.print(f"\n[bold {color}]{icon} {feedback.title}{step_info}[/bold {color}]")
        self.console.print(f"[{color}]{feedback.message}[/{color}]")

        if feedback.options:
            self.console.print(f"[dim]選択肢: {', '.join(feedback.options)}[/dim]")

    def _display_quality_result(
        self,
        feedback: FeedbackMessage,
        quality_score: float,
        issues: list[str],
        suggestions: list[str]
    ) -> None:
        """品質チェック結果の詳細表示"""
        self._display_feedback(feedback)

        # 品質バー
        quality_bar = self._create_quality_bar(quality_score)
        self.console.print(f"品質: {quality_bar} {quality_score:.1f}/100")

        # 問題点
        if issues:
            self.console.print(f"\n[red]検出された問題 ({len(issues)}件):[/red]")
            for i, issue in enumerate(issues[:5], 1):  # 最大5件表示
                self.console.print(f"  {i}. {issue}")
            if len(issues) > 5:
                self.console.print(f"  ... 他 {len(issues)-5} 件")

        # 改善提案
        if suggestions:
            self.console.print(f"\n[blue]改善提案 ({len(suggestions)}件):[/blue]")
            for i, suggestion in enumerate(suggestions[:3], 1):  # 最大3件表示
                self.console.print(f"  💡 {suggestion}")
            if len(suggestions) > 3:
                self.console.print(f"  ... 他 {len(suggestions)-3} 件")

    def _display_improvement_suggestions(
        self,
        feedback: FeedbackMessage,
        suggestions: list[dict[str, str]]
    ) -> None:
        """改善提案の表示"""
        self._display_feedback(feedback)

        for i, suggestion in enumerate(suggestions, 1):
            title = suggestion.get("title", f"提案 {i}")
            description = suggestion.get("description", "")
            impact = suggestion.get("impact", "medium")

            impact_icon = {"high": "🔥", "medium": "⭐", "low": "💫"}.get(impact, "⭐")

            self.console.print(f"\n{impact_icon} [bold]{title}[/bold]")
            self.console.print(f"   {description}")

    def _display_success_details(self, details: dict[str, Any]) -> None:
        """成功の詳細情報表示"""
        self.console.print("\n[dim]詳細情報:[/dim]")
        for key, value in details.items():
            self.console.print(f"  • {key}: {value}")

    def _handle_quality_improvement_dialog(
        self,
        step_id: int,
        issues: list[str],
        suggestions: list[str]
    ) -> str:
        """品質改善ダイアログの処理"""
        options = [
            "自動修正を適用",
            "手動で修正",
            "このまま続行",
            "ステップをスキップ"
        ]

        self.console.print(f"\n[yellow]ステップ{step_id}の品質に問題があります。どうしますか？[/yellow]")

        return self._get_user_response(options, options[0])

    def _select_improvement_suggestion(self, suggestions: list[dict[str, str]]) -> str:
        """改善提案の選択"""
        if len(suggestions) == 1:
            return suggestions[0].get("title", "")

        options = [s.get("title", f"提案{i+1}") for i, s in enumerate(suggestions)]
        options.append("提案を適用しない")

        self.console.print("\n[blue]適用する改善提案を選択してください:[/blue]")

        return self._get_user_response(options, options[0])

    def _get_user_response(self, options: list[str], default: str) -> str:
        """ユーザーレスポンスの取得（モック実装）"""
        # 実際の実装では input() を使用してユーザー入力を受け取る
        # 今回は自動的にデフォルト選択を返す
        return default

    def _mock_user_input(self, input_type: str) -> Any:
        """ユーザー入力のモック"""
        mock_inputs = {
            "text": "ユーザー入力テキスト",
            "number": 42,
            "boolean": True
        }
        return mock_inputs.get(input_type, "デフォルト値")

    def _create_quality_bar(self, score: float, width: int = 30) -> str:
        """品質バーの作成"""
        filled = int((score / 100) * width)

        # 色分け
        if score >= 80:
            bar_char = "█"
            color = "green"
        elif score >= 60:
            bar_char = "█"
            color = "yellow"
        else:
            bar_char = "█"
            color = "red"

        bar = bar_char * filled + "░" * (width - filled)
        return f"[{color}][{bar}][/{color}]"

    def _determine_quality_level(self, score: float) -> str:
        """品質レベルの判定"""
        if score >= 90:
            return "優秀"
        if score >= 80:
            return "良好"
        if score >= 70:
            return "合格"
        if score >= 60:
            return "要改善"
        return "不合格"

    def _get_severity_from_score(self, score: float) -> str:
        """スコアから深刻度を取得"""
        if score >= 80:
            return "success"
        if score >= 60:
            return "warning"
        return "error"

    def _log_feedback(self, feedback: FeedbackMessage) -> None:
        """フィードバックのログ記録"""
        self.feedback_history.append(feedback)

    @performance_monitor
    def export_feedback_report(self) -> dict[str, Any]:
        """フィードバックレポートのエクスポート"""
        return {
            "episode_number": self.episode_number,
            "timestamp": datetime.now().isoformat(),
            "total_feedback_count": len(self.feedback_history),
            "feedback_by_type": {
                feedback_type.value: len([f for f in self.feedback_history if f.feedback_type == feedback_type])
                for feedback_type in FeedbackType
            },
            "feedback_history": [
                {
                    "type": f.feedback_type.value,
                    "title": f.title,
                    "message": f.message,
                    "step_id": f.step_id,
                    "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                    "severity": f.severity
                }
                for f in self.feedback_history
            ],
            "user_preferences": self.user_preferences
        }

    def set_user_preferences(self, preferences: dict[str, Any]) -> None:
        """ユーザー設定の更新"""
        self.user_preferences.update(preferences)

    def get_feedback_summary(self) -> dict[str, Any]:
        """フィードバック サマリーの取得"""
        return {
            "total_feedback": len(self.feedback_history),
            "confirmations": len([f for f in self.feedback_history if f.feedback_type == FeedbackType.CONFIRMATION]),
            "quality_checks": len([f for f in self.feedback_history if f.feedback_type == FeedbackType.QUALITY_CHECK]),
            "warnings": len([f for f in self.feedback_history if f.feedback_type == FeedbackType.WARNING]),
            "errors": len([f for f in self.feedback_history if f.feedback_type == FeedbackType.ERROR]),
            "last_feedback": self.feedback_history[-1] if self.feedback_history else None
        }
