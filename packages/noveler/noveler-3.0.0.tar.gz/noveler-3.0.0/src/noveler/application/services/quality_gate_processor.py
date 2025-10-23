"""Quality gate processing service.

Implements the multi-phase quality evaluation workflow defined by the A31 quality baseline and
provides actionable feedback for interactive writing sessions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.application.interfaces.quality_service_interface import IQualityService
from noveler.domain.entities.interactive_writing_session import InteractiveWritingSession
from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_check_result import QualityCheckResult, QualityIssue, QualitySuggestion
from noveler.presentation.shared.shared_utilities import console


class QualityGateStatus(Enum):
    """Enumerates the possible outcomes of a quality gate evaluation."""
    PASSED = "passed"      # 品質基準を満たしている
    WARNING = "warning"    # 改善推奨だが進行可能
    BLOCKED = "blocked"    # 品質基準未達で進行不可


@dataclass
class QualityGateResult:
    """Structured result returned from a quality gate evaluation.

    Attributes:
        step: Sequential step identifier.
        status: Outcome produced by the gate evaluation.
        overall_score: Weighted score aggregated across criteria.
        detailed_scores: Mapping of criterion identifiers to their respective scores.
        critical_issues: Blocking issues that require resolution before proceeding.
        warning_issues: Non-blocking issues that still require attention.
        suggestions: Improvement suggestions proposed for the author.
        can_proceed: Indicates whether the workflow is allowed to continue.
        evaluation_time_ms: Execution time of the gate evaluation in milliseconds.
        metadata: Additional diagnostic or trace information.
    """
    step: int
    status: QualityGateStatus
    overall_score: float
    detailed_scores: dict[str, float]
    critical_issues: list[QualityIssue]
    warning_issues: list[QualityIssue]
    suggestions: list[QualitySuggestion]
    can_proceed: bool
    evaluation_time_ms: int
    metadata: dict[str, Any]


@dataclass
class QualityCriterion:
    """Definition of a single quality evaluation criterion.

    Attributes:
        name: Human readable name of the criterion.
        description: Explanation of what the criterion evaluates.
        weight: Relative weight used when calculating the overall score.
        threshold_pass: Score required to mark the criterion as passed.
        threshold_warning: Score required to emit a warning without blocking.
        step_specific: True when the criterion applies only to a specific step.
    """
    name: str
    description: str
    weight: float
    threshold_pass: float
    threshold_warning: float
    step_specific: bool = False


class QualityGateProcessor:
    """Coordinate quality gate evaluations for interactive writing sessions.

    The processor delegates scoring to the quality service, applies step-specific criteria,
    and builds improvement suggestions that can be surfaced to authors.
    """

    def __init__(self, quality_service: IQualityService) -> None:
        """Initialize the quality gate processor.

        Args:
            quality_service: Service responsible for running the quality evaluation.
        """
        self.quality_service = quality_service
        self.console = console

        # 段階別品質基準を初期化
        self._initialize_step_criteria()

    def _initialize_step_criteria(self) -> None:
        """Populate base and step-specific quality criteria collections."""

        # 基本品質基準（全段階共通）
        self.base_criteria = [
            QualityCriterion(
                name="構造整合性",
                description="ストーリー構造の論理的一貫性",
                weight=0.25,
                threshold_pass=75.0,
                threshold_warning=65.0
            ),
            QualityCriterion(
                name="キャラ一貫性",
                description="キャラクター設定・行動の一貫性",
                weight=0.20,
                threshold_pass=80.0,
                threshold_warning=70.0
            ),
            QualityCriterion(
                name="文章表現力",
                description="文章の読みやすさ・表現力",
                weight=0.15,
                threshold_pass=70.0,
                threshold_warning=60.0
            ),
            QualityCriterion(
                name="論理一貫性",
                description="設定・展開の論理的妥当性",
                weight=0.25,
                threshold_pass=75.0,
                threshold_warning=65.0
            ),
            QualityCriterion(
                name="読者エンゲージメント",
                description="読者の関心・共感を引く要素",
                weight=0.15,
                threshold_pass=70.0,
                threshold_warning=60.0
            )
        ]

        # 段階別特化基準
        self.step_specific_criteria = {
            1: [  # プロットデータ準備
                QualityCriterion(
                    name="プロット完整性",
                    description="プロット要素の完全性・矛盾のなさ",
                    weight=0.4,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="設定明確性",
                    description="世界観・キャラ設定の明確さ",
                    weight=0.3,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                )
            ],
            2: [  # 構造分析
                QualityCriterion(
                    name="起承転結明確性",
                    description="起承転結構造の明確性",
                    weight=0.35,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="ペース配分",
                    description="展開ペースの適切性",
                    weight=0.25,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                )
            ],
            3: [  # 感情設計
                QualityCriterion(
                    name="感情表現妥当性",
                    description="感情描写の自然さ・説得力",
                    weight=0.4,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="感情変化論理性",
                    description="感情変化の論理的妥当性",
                    weight=0.3,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                )
            ],
            4: [  # ユーモア要素設計
                QualityCriterion(
                    name="エンターテイメント性",
                    description="面白さ・引きつけ力",
                    weight=0.4,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="ユーモア適切性",
                    description="ユーモアの文脈適合性",
                    weight=0.3,
                    threshold_pass=70.0,
                    threshold_warning=60.0,
                    step_specific=True
                )
            ],
            5: [  # キャラクター対話設計
                QualityCriterion(
                    name="対話自然性",
                    description="対話の自然さ・リアリティ",
                    weight=0.35,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="キャラ個性表現",
                    description="キャラ個性の対話での表現",
                    weight=0.3,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                )
            ],
            6: [  # 場面演出設計
                QualityCriterion(
                    name="場面描写力",
                    description="情景・雰囲気描写の鮮明さ",
                    weight=0.35,
                    threshold_pass=75.0,
                    threshold_warning=65.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="演出効果性",
                    description="演出の効果的な配置",
                    weight=0.3,
                    threshold_pass=70.0,
                    threshold_warning=60.0,
                    step_specific=True
                )
            ],
            7: [  # 論理整合調整
                QualityCriterion(
                    name="設定整合性",
                    description="設定間の矛盾のなさ",
                    weight=0.4,
                    threshold_pass=85.0,
                    threshold_warning=75.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="因果関係明確性",
                    description="原因と結果の明確性",
                    weight=0.3,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                )
            ],
            8: [  # 原稿執筆（最重要段階）
                QualityCriterion(
                    name="総合完成度",
                    description="原稿としての総合完成度",
                    weight=0.3,
                    threshold_pass=85.0,
                    threshold_warning=75.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="文章品質",
                    description="文章の品質・読みやすさ",
                    weight=0.25,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="A31準拠度",
                    description="A31品質基準68項目への準拠度",
                    weight=0.2,
                    threshold_pass=85.0,
                    threshold_warning=75.0,
                    step_specific=True
                )
            ],
            9: [  # 品質改善
                QualityCriterion(
                    name="改善効果性",
                    description="品質改善の効果",
                    weight=0.4,
                    threshold_pass=80.0,
                    threshold_warning=70.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="問題解決度",
                    description="指摘問題の解決度",
                    weight=0.35,
                    threshold_pass=85.0,
                    threshold_warning=75.0,
                    step_specific=True
                )
            ],
            10: [  # 最終調整（最高基準）
                QualityCriterion(
                    name="出版品質",
                    description="出版・投稿可能な品質レベル",
                    weight=0.3,
                    threshold_pass=90.0,
                    threshold_warning=80.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="読者満足度",
                    description="読者満足度予測",
                    weight=0.25,
                    threshold_pass=85.0,
                    threshold_warning=75.0,
                    step_specific=True
                ),
                QualityCriterion(
                    name="最終完成度",
                    description="作品としての最終完成度",
                    weight=0.3,
                    threshold_pass=90.0,
                    threshold_warning=80.0,
                    step_specific=True
                )
            ]
        }

    async def execute_quality_gate(
        self,
        session: InteractiveWritingSession,
        step: int,
        step_data: dict[str, Any]
    ) -> QualityGateResult:
        """品質ゲート実行"""

        start_time = project_now().datetime
        self.console.info(f"ステップ {step} の品質ゲートを実行中...")

        try:
            # 段階別品質基準取得
            criteria = self._get_step_criteria(step)

            # 品質チェック実行
            quality_result = await self.quality_service.check_step_quality(
                episode_number=session.episode_number,
                step=step,
                step_data=step_data,
                session_context=session.data,
                criteria=criteria
            )

            # 品質ゲート評価
            gate_status = self._evaluate_quality_gate(quality_result, step, session)

            # 問題分類
            critical_issues = [i for i in quality_result.issues if i.severity == "critical"]
            warning_issues = [i for i in quality_result.issues if i.severity == "warning"]

            # 改善提案生成
            suggestions = await self._generate_step_improvement_suggestions(
                quality_result, step, session
            )

            # 実行時間計算
            execution_time = (project_now().datetime - start_time).total_seconds() * 1000

            # detailed_scores は無い実装もあるため安全に取得
            detailed_scores = getattr(quality_result, "detailed_scores", {}) or {}

            result = QualityGateResult(
                step=step,
                status=gate_status,
                overall_score=quality_result.overall_score,
                detailed_scores=detailed_scores,
                critical_issues=critical_issues,
                warning_issues=warning_issues,
                suggestions=suggestions,
                can_proceed=gate_status != QualityGateStatus.BLOCKED,
                evaluation_time_ms=int(execution_time),
                metadata={
                    "criteria_count": len(criteria),
                    "total_issues": len(quality_result.issues),
                    "step_name": self._get_step_name(step)
                }
            )

            self.console.success(
                f"ステップ {step} 品質ゲート完了: {gate_status.value} "
                f"(スコア: {quality_result.overall_score:.1f})"
            )

            return result

        except Exception as e:
            # エラー時はデフォルト結果を返す
            self.console.error(f"品質ゲート実行エラー: {e!s}")
            return self._create_default_gate_result(step, str(e))

    def _get_step_criteria(self, step: int) -> list[QualityCriterion]:
        """Return the combined quality criteria for a given step.

        Args:
            step: Step identifier.

        Returns:
            list[QualityCriterion]: Criteria that should be evaluated for the step.
        """

        # 基本基準をコピー
        criteria = self.base_criteria.copy()

        # 段階特化基準を追加
        step_criteria = self.step_specific_criteria.get(step, [])
        criteria.extend(step_criteria)

        return criteria

    def _evaluate_quality_gate(
        self,
        quality_result: QualityCheckResult,
        step: int,
        session: InteractiveWritingSession
    ) -> QualityGateStatus:
        """Derive the quality gate status for the given evaluation result.

        Args:
            quality_result: Result returned by the quality service.
            step: Step identifier for which the evaluation was produced.
            session: Interactive writing session providing thresholds.

        Returns:
            QualityGateStatus: Status that reflects whether the step can proceed.
        """

        score = quality_result.overall_score

        # セッション設定からしきい値取得
        threshold = session.get_step_quality_threshold(step)

        # クリティカル問題がある場合は即座にBLOCKED
        critical_count = len([i for i in quality_result.issues if i.severity == "critical"])
        if critical_count > 0:
            return QualityGateStatus.BLOCKED

        # スコアベース評価
        if score >= threshold["pass"]:
            return QualityGateStatus.PASSED
        if score >= threshold["warning"]:
            return QualityGateStatus.WARNING
        return QualityGateStatus.BLOCKED

    async def _generate_step_improvement_suggestions(
        self,
        quality_result: QualityCheckResult,
        step: int,
        session: InteractiveWritingSession  # noqa: ARG002
    ) -> list[QualitySuggestion]:
        """Build step-specific improvement suggestions for the author.

        Args:
            quality_result: Result returned by the quality service.
            step: Step identifier currently under review.
            session: Interactive writing session context; used for future extensions.

        Returns:
            list[QualitySuggestion]: Suggestions tailored to the current step.
        """

        suggestions = []

        # 段階別提案テンプレート
        step_suggestion_templates = {
            1: {  # プロットデータ準備
                "plot_inconsistency": "プロット設定の矛盾を解決してください。キャラクター動機と行動の整合性を確認してください。",
                "setting_unclear": "世界観設定をより具体的に描写してください。読者が想像しやすい詳細を追加してください。"
            },
            2: {  # 構造分析
                "structure_weak": "起承転結の構造を明確にしてください。特に転の部分で読者を引きつける展開を検討してください。",
                "pacing_issues": "展開ペースを調整してください。重要な場面により多くの描写を割り当ててください。"
            },
            3: {  # 感情設計
                "emotion_unnatural": "キャラクターの感情変化をより自然に描写してください。心理的な背景を明確にしてください。",
                "emotion_logic": "感情の変化に論理的な理由を追加してください。読者が共感できる動機を示してください。"
            },
            8: {  # 原稿執筆
                "manuscript_incomplete": "原稿の完成度を高めてください。不完全な描写や説明不足の箇所を補完してください。",
                "quality_low": "A31品質基準を参考に、文章表現・構成・キャラ描写を改善してください。"
            },
            10: {  # 最終調整
                "final_polish": "最終的な文章の磨き上げを行ってください。誤字脱字、表現の精密化を確認してください。",
                "reader_experience": "読者体験を最適化してください。第一印象と読後感を重視した調整を行ってください。"
            }
        }

        # 段階別提案生成
        templates = step_suggestion_templates.get(step, {})

        for issue in quality_result.issues[:5]:  # 上位5件
            # 問題タイプから提案テンプレート検索（属性が無い場合に備えて安全に参照）
            issue_type = getattr(issue, "type", getattr(issue, "category", "general"))
            issue_desc = getattr(issue, "description", getattr(issue, "message", "改善を検討してください。"))
            issue_severity = getattr(issue, "severity", "warning")

            suggestion_text = templates.get(issue_type, f"{issue_desc}の改善を検討してください。")

            # QualitySuggestion は (type, description, priority) のみを受け付ける実装に合わせる
            suggestion = QualitySuggestion(
                type="step_improvement",
                description=suggestion_text,
                priority="high" if str(issue_severity).lower() == "critical" else "medium",
            )

            suggestions.append(suggestion)

        return suggestions

    def _is_auto_fixable(self, issue: QualityIssue) -> bool:
        """Return whether the issue can be auto-fixed by the system.

        Args:
            issue: Quality issue reported by the evaluator.

        Returns:
            bool: True if the issue can be addressed automatically.
        """

        auto_fixable_types = [
            "typo",
            "grammar_error",
            "formatting_issue",
            "punctuation_error"
        ]

        return issue.type in auto_fixable_types

    def _create_default_gate_result(self, step: int, error: str) -> QualityGateResult:
        """Create a default gate result when evaluation fails unexpectedly.

        Args:
            step: Step identifier associated with the failed evaluation.
            error: Error message encountered during evaluation.

        Returns:
            QualityGateResult: Fallback result with warning status.
        """

        return QualityGateResult(
            step=step,
            status=QualityGateStatus.WARNING,
            overall_score=70.0,  # デフォルトスコア
            detailed_scores={"default": 70.0},
            critical_issues=[],
            warning_issues=[],
            suggestions=[
                # QualitySuggestion は簡易スキーマに準拠
                QualitySuggestion(
                    type="system_error",
                    description=f"品質チェック中にエラーが発生しました: {error}",
                    priority="medium",
                )
            ],
            can_proceed=True,  # エラー時は進行を許可
            evaluation_time_ms=0,
            metadata={"error": error}
        )

    def _get_step_name(self, step: int) -> str:
        """Return the human-readable name for a step.

        Args:
            step: Step identifier.

        Returns:
            str: Step name used for reporting.
        """
        step_names = {
            1: "プロットデータ準備",
            2: "構造分析",
            3: "感情設計",
            4: "ユーモア要素設計",
            5: "キャラクター対話設計",
            6: "場面演出設計",
            7: "論理整合性調整",
            8: "原稿執筆",
            9: "品質改善",
            10: "最終調整"
        }
        return step_names.get(step, f"ステップ {step}")

    def get_quality_gate_summary(
        self,
        results: list[QualityGateResult]
    ) -> dict[str, Any]:
        """Aggregate multiple quality gate results into a summary.

        Args:
            results: Collection of per-step quality gate results.

        Returns:
            dict[str, Any]: Summary statistics including distribution and readiness flags.
        """

        if not results:
            return {"error": "品質ゲート結果がありません"}

        total_score = sum(r.overall_score for r in results)
        avg_score = total_score / len(results)

        passed_count = sum(1 for r in results if r.status == QualityGateStatus.PASSED)
        warning_count = sum(1 for r in results if r.status == QualityGateStatus.WARNING)
        blocked_count = sum(1 for r in results if r.status == QualityGateStatus.BLOCKED)

        total_critical = sum(len(r.critical_issues) for r in results)
        total_warnings = sum(len(r.warning_issues) for r in results)

        return {
            "total_steps": len(results),
            "average_score": round(avg_score, 1),
            "status_distribution": {
                "passed": passed_count,
                "warning": warning_count,
                "blocked": blocked_count
            },
            "issue_summary": {
                "critical_issues": total_critical,
                "warning_issues": total_warnings,
                "total_issues": total_critical + total_warnings
            },
            "overall_status": "excellent" if avg_score >= 85 else
                            "good" if avg_score >= 75 else
                            "needs_improvement" if avg_score >= 65 else
                            "poor",
            "completion_ready": blocked_count == 0 and avg_score >= 75
        }
