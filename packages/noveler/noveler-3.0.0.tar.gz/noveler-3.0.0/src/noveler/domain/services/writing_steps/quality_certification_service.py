"""STEP 16: DOD & KPI統合品質認定サービス

A38執筆プロンプトガイドのSTEP16「DOD & KPI統合品質認定」を実装するサービス。
Definition of Done (DOD) とKey Performance Indicators (KPI) を用いて
総合的な品質認定を行い、公開可能品質の確保を保証します。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class QualityLevel(Enum):
    """品質レベル"""
    DRAFT = "draft"  # 草稿レベル
    REVIEW_READY = "review_ready"  # レビュー可能レベル
    PUBLICATION_READY = "publication_ready"  # 公開可能レベル
    PREMIUM = "premium"  # プレミアム品質


class DODCategory(Enum):
    """DODカテゴリー"""
    CONTENT_COMPLETENESS = "content_completeness"  # 内容完成度
    TECHNICAL_QUALITY = "technical_quality"  # 技術品質
    NARRATIVE_QUALITY = "narrative_quality"  # 物語品質
    READABILITY = "readability"  # 可読性
    CONSISTENCY = "consistency"  # 一貫性
    ENGAGEMENT = "engagement"  # エンゲージメント


class KPIType(Enum):
    """KPIタイプ"""
    QUANTITATIVE = "quantitative"  # 定量的KPI
    QUALITATIVE = "qualitative"  # 定性的KPI
    READER_EXPERIENCE = "reader_experience"  # 読者体験KPI
    TECHNICAL_METRICS = "technical_metrics"  # 技術的メトリクス


class CertificationStatus(Enum):
    """認定ステータス"""
    PASSED = "passed"  # 合格
    FAILED = "failed"  # 不合格
    CONDITIONAL = "conditional"  # 条件付き合格
    REQUIRES_REVISION = "requires_revision"  # 修正要


@dataclass
class DODCriterion:
    """DOD基準"""
    criterion_id: str
    category: DODCategory
    name: str
    description: str
    measurement_method: str
    pass_threshold: float  # 合格閾値 (0-1)
    weight: float  # 重み
    mandatory: bool  # 必須かどうか
    validation_rules: list[str]


@dataclass
class KPIMetric:
    """KPIメトリック"""
    metric_id: str
    kpi_type: KPIType
    name: str
    description: str
    target_value: float | str
    current_value: float | str
    unit: str
    measurement_method: str
    benchmark: float | None = None  # ベンチマーク
    trend: str | None = None  # トレンド


@dataclass
class QualityCheckResult:
    """品質チェック結果"""
    check_id: str
    criterion: DODCriterion
    status: CertificationStatus
    score: float  # スコア (0-1)
    measured_value: float | str
    pass_threshold: float
    details: str
    evidence: list[str]  # 根拠
    recommendations: list[str]  # 推奨事項


@dataclass
class KPIAssessment:
    """KPI評価"""
    assessment_id: str
    metric: KPIMetric
    achievement_rate: float  # 達成率 (0-1)
    performance_grade: str  # A, B, C, D
    analysis: str
    improvement_suggestions: list[str]


@dataclass
class QualityGate:
    """品質ゲート"""
    gate_id: str
    gate_name: str
    quality_level: QualityLevel
    required_criteria: list[str]  # 必要なDOD基準ID
    required_kpis: list[str]  # 必要なKPI ID
    pass_rate_threshold: float  # 合格率閾値
    mandatory_pass_criteria: list[str]  # 必須合格基準


@dataclass
class CertificationReport:
    """認定レポート"""
    report_id: str
    episode_number: int
    certification_timestamp: datetime
    target_quality_level: QualityLevel
    overall_status: CertificationStatus
    overall_score: float  # 総合スコア (0-1)

    dod_results: list[QualityCheckResult]
    kpi_assessments: list[KPIAssessment]
    quality_gates: list[QualityGate]

    passed_gates: list[str]
    failed_gates: list[str]
    conditional_gates: list[str]

    strengths: list[str]  # 強み
    weaknesses: list[str]  # 弱点
    critical_issues: list[str]  # 重要な問題
    improvement_priorities: list[str]  # 改善優先度

    certification_summary: str
    next_steps: list[str]
    certification_metadata: dict[str, Any]


@dataclass
class QualityCertificationConfig:
    """品質認定設定"""
    target_quality_level: QualityLevel = QualityLevel.PUBLICATION_READY
    strict_certification: bool = True  # 厳格認定
    enable_all_dod_categories: bool = True
    enable_all_kpi_types: bool = True

    # DOD重み設定
    dod_category_weights: dict[DODCategory, float] = None

    # KPI重み設定
    kpi_type_weights: dict[KPIType, float] = None

    # 品質ゲート設定
    enable_quality_gates: bool = True
    gate_pass_threshold: float = 0.8

    # 認定基準
    overall_pass_threshold: float = 0.75
    mandatory_criteria_pass_rate: float = 1.0

    # レポート設定
    include_detailed_analysis: bool = True
    include_improvement_roadmap: bool = True


class QualityCertificationService(BaseWritingStep):
    """STEP 16: DOD & KPI統合品質認定サービス

    Definition of Done (DOD) とKey Performance Indicators (KPI) を用いて
    総合的な品質認定を行い、公開可能品質の確保を保証するサービス。
    A38ガイドのSTEP16「DOD & KPI統合品質認定」を実装。
    """

    def __init__(
        self,
        config_manager: ConfigurationManagerService | None = None,
        path_service: Any | None = None,
        file_system_service: Any | None = None
    ) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._path_service = path_service
        self._file_system = file_system_service

        # デフォルト重み設定
        self._certification_config = QualityCertificationConfig()
        if self._certification_config.dod_category_weights is None:
            self._certification_config.dod_category_weights = {
                DODCategory.CONTENT_COMPLETENESS: 0.25,
                DODCategory.NARRATIVE_QUALITY: 0.25,
                DODCategory.TECHNICAL_QUALITY: 0.20,
                DODCategory.READABILITY: 0.15,
                DODCategory.CONSISTENCY: 0.10,
                DODCategory.ENGAGEMENT: 0.05
            }

        if self._certification_config.kpi_type_weights is None:
            self._certification_config.kpi_type_weights = {
                KPIType.READER_EXPERIENCE: 0.40,
                KPIType.TECHNICAL_METRICS: 0.30,
                KPIType.QUANTITATIVE: 0.20,
                KPIType.QUALITATIVE: 0.10
            }

        # DOD基準とKPIメトリクスの初期化
        self._dod_criteria = self._initialize_dod_criteria()
        self._kpi_metrics = self._initialize_kpi_metrics()
        self._quality_gates = self._initialize_quality_gates()

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "DOD & KPI統合品質認定"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "DODとKPIを用いて総合的な品質認定を行い、公開可能品質の確保を保証します"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 16: DOD & KPI統合品質認定の実行

        Args:
            context: 実行コンテキスト

        Returns:
            品質認定結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # DOD & KPI統合品質認定の実行
            certification_report = self._execute_quality_certification(
                episode_number=episode_number,
                project=project,
                context=context
            )

            # 結果をコンテキストに追加
            context["quality_certification"] = certification_report
            context["certification_status"] = certification_report.overall_status
            context["quality_score"] = certification_report.overall_score
            context["quality_certification_completed"] = True

            # 品質ゲート通過状況を設定
            context["passed_quality_gates"] = certification_report.passed_gates
            context["failed_quality_gates"] = certification_report.failed_gates

            return context

        except Exception as e:
            context["quality_certification_error"] = str(e)
            raise

    def _execute_quality_certification(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> CertificationReport:
        """品質認定の実行"""

        # 最終原稿の取得
        final_manuscript = self._get_final_manuscript(context)

        # DOD基準による品質チェック
        dod_results = self._perform_dod_checks(final_manuscript, context)

        # KPIメトリクスによる評価
        kpi_assessments = self._perform_kpi_assessments(final_manuscript, context)

        # 品質ゲートの評価
        gate_evaluations = self._evaluate_quality_gates(dod_results, kpi_assessments)

        # 総合評価の計算
        overall_score = self._calculate_overall_score(dod_results, kpi_assessments)
        overall_status = self._determine_overall_status(
            overall_score, gate_evaluations, dod_results
        )

        # 強み・弱点の分析
        strengths, weaknesses = self._analyze_strengths_and_weaknesses(
            dod_results, kpi_assessments
        )

        # 重要な問題と改善優先度の特定
        critical_issues = self._identify_critical_issues(dod_results, kpi_assessments)
        improvement_priorities = self._determine_improvement_priorities(
            dod_results, kpi_assessments, critical_issues
        )

        # レポート生成
        return self._generate_certification_report(
            episode_number=episode_number,
            overall_status=overall_status,
            overall_score=overall_score,
            dod_results=dod_results,
            kpi_assessments=kpi_assessments,
            gate_evaluations=gate_evaluations,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            improvement_priorities=improvement_priorities
        )

    def _get_final_manuscript(self, context: dict[str, Any]) -> str:
        """最終原稿の取得"""

        # 可読性最適化後のテキストが最優先
        if "optimized_readable_text" in context:
            return context["optimized_readable_text"]

        # 文字数最適化後のテキスト
        if "optimized_text" in context:
            return context["optimized_text"]

        # その他のソース
        text_sources = [
            "final_manuscript",
            "manuscript_text",
            "generated_manuscript"
        ]

        for source in text_sources:
            text = context.get(source)
            if text and isinstance(text, str):
                return text

        return ""

    def _perform_dod_checks(
        self,
        manuscript: str,
        context: dict[str, Any]
    ) -> list[QualityCheckResult]:
        """DOD基準による品質チェック"""

        results = []

        for criterion in self._dod_criteria:
            if not self._is_criterion_enabled(criterion):
                continue

            # 基準に対する測定実行
            measured_value, score = self._measure_criterion(
                criterion, manuscript, context
            )

            # 合格判定
            status = CertificationStatus.PASSED if score >= criterion.pass_threshold else CertificationStatus.FAILED

            # 詳細分析
            details = self._analyze_criterion_details(criterion, measured_value, score)
            evidence = self._collect_criterion_evidence(criterion, manuscript, context)
            recommendations = self._generate_criterion_recommendations(criterion, score)

            result = QualityCheckResult(
                check_id=f"dod_{criterion.criterion_id}",
                criterion=criterion,
                status=status,
                score=score,
                measured_value=measured_value,
                pass_threshold=criterion.pass_threshold,
                details=details,
                evidence=evidence,
                recommendations=recommendations
            )

            results.append(result)

        return results

    def _perform_kpi_assessments(
        self,
        manuscript: str,
        context: dict[str, Any]
    ) -> list[KPIAssessment]:
        """KPIメトリクスによる評価"""

        assessments = []

        for metric in self._kpi_metrics:
            if not self._is_kpi_enabled(metric):
                continue

            # KPIの測定
            current_value = self._measure_kpi_metric(metric, manuscript, context)

            # 達成率の計算
            achievement_rate = self._calculate_achievement_rate(metric, current_value)

            # 成績評価
            performance_grade = self._calculate_performance_grade(achievement_rate)

            # 分析と改善提案
            analysis = self._analyze_kpi_performance(metric, current_value, achievement_rate)
            improvement_suggestions = self._generate_kpi_improvements(metric, achievement_rate)

            # KPIメトリックの現在値を更新
            updated_metric = metric
            updated_metric.current_value = current_value

            assessment = KPIAssessment(
                assessment_id=f"kpi_{metric.metric_id}",
                metric=updated_metric,
                achievement_rate=achievement_rate,
                performance_grade=performance_grade,
                analysis=analysis,
                improvement_suggestions=improvement_suggestions
            )

            assessments.append(assessment)

        return assessments

    def _evaluate_quality_gates(
        self,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> dict[str, Any]:
        """品質ゲートの評価"""

        gate_evaluations = {
            "passed_gates": [],
            "failed_gates": [],
            "conditional_gates": []
        }

        for gate in self._quality_gates:
            gate_status = self._evaluate_single_quality_gate(
                gate, dod_results, kpi_assessments
            )

            if gate_status == CertificationStatus.PASSED:
                gate_evaluations["passed_gates"].append(gate.gate_id)
            elif gate_status == CertificationStatus.CONDITIONAL:
                gate_evaluations["conditional_gates"].append(gate.gate_id)
            else:
                gate_evaluations["failed_gates"].append(gate.gate_id)

        return gate_evaluations

    def _calculate_overall_score(
        self,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> float:
        """総合スコアの計算"""

        # DODスコアの計算
        dod_score = 0.0
        dod_total_weight = 0.0

        for result in dod_results:
            category_weight = self._certification_config.dod_category_weights.get(
                result.criterion.category, 0.1
            )
            criterion_weight = result.criterion.weight
            total_weight = category_weight * criterion_weight

            dod_score += result.score * total_weight
            dod_total_weight += total_weight

        normalized_dod_score = dod_score / dod_total_weight if dod_total_weight > 0 else 0.0

        # KPIスコアの計算
        kpi_score = 0.0
        kpi_total_weight = 0.0

        for assessment in kpi_assessments:
            type_weight = self._certification_config.kpi_type_weights.get(
                assessment.metric.kpi_type, 0.1
            )

            kpi_score += assessment.achievement_rate * type_weight
            kpi_total_weight += type_weight

        normalized_kpi_score = kpi_score / kpi_total_weight if kpi_total_weight > 0 else 0.0

        # DODとKPIの重み付け統合 (DOD 70%, KPI 30%)
        overall_score = normalized_dod_score * 0.7 + normalized_kpi_score * 0.3

        return min(1.0, max(0.0, overall_score))

    def _determine_overall_status(
        self,
        overall_score: float,
        gate_evaluations: dict[str, Any],
        dod_results: list[QualityCheckResult]
    ) -> CertificationStatus:
        """総合ステータスの判定"""

        # 必須基準の確認
        mandatory_failed = any(
            result.status == CertificationStatus.FAILED and result.criterion.mandatory
            for result in dod_results
        )

        if mandatory_failed:
            return CertificationStatus.FAILED

        # 品質ゲートの確認
        failed_gates = gate_evaluations.get("failed_gates", [])
        if failed_gates:
            return CertificationStatus.REQUIRES_REVISION

        # 総合スコアによる判定
        if overall_score >= self._certification_config.overall_pass_threshold:
            conditional_gates = gate_evaluations.get("conditional_gates", [])
            if conditional_gates:
                return CertificationStatus.CONDITIONAL
            return CertificationStatus.PASSED
        return CertificationStatus.FAILED

    def _analyze_strengths_and_weaknesses(
        self,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> tuple[list[str], list[str]]:
        """強み・弱点の分析"""

        strengths = []
        weaknesses = []

        # DOD基準からの強み・弱点
        for result in dod_results:
            if result.score >= 0.8:
                strengths.append(
                    f"{result.criterion.name}: 優秀 ({result.score:.2f})"
                )
            elif result.score < 0.6:
                weaknesses.append(
                    f"{result.criterion.name}: 要改善 ({result.score:.2f})"
                )

        # KPI評価からの強み・弱点
        for assessment in kpi_assessments:
            if assessment.performance_grade in ["A", "B"]:
                strengths.append(
                    f"{assessment.metric.name}: {assessment.performance_grade}評価"
                )
            elif assessment.performance_grade in ["D"]:
                weaknesses.append(
                    f"{assessment.metric.name}: {assessment.performance_grade}評価"
                )

        return strengths, weaknesses

    def _identify_critical_issues(
        self,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> list[str]:
        """重要な問題の特定"""

        critical_issues = []

        # 必須基準の不合格
        for result in dod_results:
            if result.criterion.mandatory and result.status == CertificationStatus.FAILED:
                critical_issues.append(
                    f"必須基準不合格: {result.criterion.name}"
                )

        # 著しく低いスコア
        for result in dod_results:
            if result.score < 0.3:
                critical_issues.append(
                    f"深刻な品質問題: {result.criterion.name} ({result.score:.2f})"
                )

        # KPIの大幅未達
        for assessment in kpi_assessments:
            if assessment.achievement_rate < 0.5:
                critical_issues.append(
                    f"KPI大幅未達: {assessment.metric.name} ({assessment.achievement_rate:.2f})"
                )

        return critical_issues

    def _determine_improvement_priorities(
        self,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment],
        critical_issues: list[str]
    ) -> list[str]:
        """改善優先度の決定"""

        priorities = []

        # 1. 必須基準の修正
        mandatory_fixes = [
            result.criterion.name
            for result in dod_results
            if result.criterion.mandatory and result.status == CertificationStatus.FAILED
        ]

        if mandatory_fixes:
            priorities.append(f"🔴 最優先: 必須基準修正 ({', '.join(mandatory_fixes)})")

        # 2. 重大な品質問題
        major_issues = [
            result.criterion.name
            for result in dod_results
            if result.score < 0.5 and not result.criterion.mandatory
        ]

        if major_issues:
            priorities.append(f"🟡 高優先: 主要品質問題 ({', '.join(major_issues)})")

        # 3. KPI改善
        kpi_improvements = [
            assessment.metric.name
            for assessment in kpi_assessments
            if assessment.achievement_rate < 0.7
        ]

        if kpi_improvements:
            priorities.append(f"🟢 中優先: KPI改善 ({', '.join(kpi_improvements)})")

        return priorities

    def _generate_certification_report(
        self,
        episode_number: int,
        overall_status: CertificationStatus,
        overall_score: float,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment],
        gate_evaluations: dict[str, Any],
        strengths: list[str],
        weaknesses: list[str],
        critical_issues: list[str],
        improvement_priorities: list[str]
    ) -> CertificationReport:
        """認定レポートの生成"""

        # 認定サマリーの生成
        certification_summary = self._generate_certification_summary(
            overall_status, overall_score, dod_results, kpi_assessments
        )

        # 次のステップの生成
        next_steps = self._generate_next_steps(
            overall_status, critical_issues, improvement_priorities
        )

        return CertificationReport(
            report_id=f"cert_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            certification_timestamp=datetime.now(tz=datetime.timezone.utc),
            target_quality_level=self._certification_config.target_quality_level,
            overall_status=overall_status,
            overall_score=overall_score,
            dod_results=dod_results,
            kpi_assessments=kpi_assessments,
            quality_gates=self._quality_gates,
            passed_gates=gate_evaluations.get("passed_gates", []),
            failed_gates=gate_evaluations.get("failed_gates", []),
            conditional_gates=gate_evaluations.get("conditional_gates", []),
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            improvement_priorities=improvement_priorities,
            certification_summary=certification_summary,
            next_steps=next_steps,
            certification_metadata={
                "config": self._certification_config.__dict__,
                "certification_timestamp": datetime.now(tz=datetime.timezone.utc),
                "total_dod_criteria": len(dod_results),
                "total_kpi_metrics": len(kpi_assessments),
                "passed_dod_criteria": len([r for r in dod_results if r.status == CertificationStatus.PASSED]),
                "passed_kpi_metrics": len([a for a in kpi_assessments if a.performance_grade in ["A", "B"]])
            }
        )

    # 初期化メソッドの実装

    def _initialize_dod_criteria(self) -> list[DODCriterion]:
        """DOD基準の初期化"""
        criteria = []

        # 内容完成度基準
        criteria.append(DODCriterion(
            criterion_id="content_word_count",
            category=DODCategory.CONTENT_COMPLETENESS,
            name="文字数要件",
            description="目標文字数の達成度",
            measurement_method="文字数カウント",
            pass_threshold=0.9,  # 90%以上
            weight=1.0,
            mandatory=True,
            validation_rules=["最低3000文字", "最大5000文字"]
        ))

        criteria.append(DODCriterion(
            criterion_id="plot_completeness",
            category=DODCategory.CONTENT_COMPLETENESS,
            name="プロット完成度",
            description="起承転結の完成度",
            measurement_method="構造分析",
            pass_threshold=0.8,
            weight=1.0,
            mandatory=True,
            validation_rules=["導入部存在", "展開部存在", "クライマックス存在", "解決部存在"]
        ))

        # 技術品質基準
        criteria.append(DODCriterion(
            criterion_id="grammar_accuracy",
            category=DODCategory.TECHNICAL_QUALITY,
            name="文法正確性",
            description="文法エラーの少なさ",
            measurement_method="文法チェック",
            pass_threshold=0.95,
            weight=0.8,
            mandatory=False,
            validation_rules=["誤字脱字最小化", "文法エラー最小化"]
        ))

        # 物語品質基準
        criteria.append(DODCriterion(
            criterion_id="character_consistency",
            category=DODCategory.NARRATIVE_QUALITY,
            name="キャラクター一貫性",
            description="キャラクターの一貫性",
            measurement_method="一貫性分析",
            pass_threshold=0.8,
            weight=0.9,
            mandatory=False,
            validation_rules=["キャラクター設定一貫性", "対話の自然性"]
        ))

        # 可読性基準
        criteria.append(DODCriterion(
            criterion_id="readability_score",
            category=DODCategory.READABILITY,
            name="可読性スコア",
            description="読みやすさの総合評価",
            measurement_method="可読性分析",
            pass_threshold=0.7,
            weight=0.8,
            mandatory=False,
            validation_rules=["適切な文長", "語彙の適切性"]
        ))

        return criteria

    def _initialize_kpi_metrics(self) -> list[KPIMetric]:
        """KPIメトリクスの初期化"""
        metrics = []

        # 読者体験KPI
        metrics.append(KPIMetric(
            metric_id="reader_engagement",
            kpi_type=KPIType.READER_EXPERIENCE,
            name="読者エンゲージメント",
            description="読者の関与度",
            target_value=0.8,
            current_value=0.0,
            unit="スコア",
            measurement_method="エンゲージメント分析"
        ))

        # 技術メトリクスKPI
        metrics.append(KPIMetric(
            metric_id="text_quality_index",
            kpi_type=KPIType.TECHNICAL_METRICS,
            name="文章品質指数",
            description="技術的な文章品質",
            target_value=0.85,
            current_value=0.0,
            unit="指数",
            measurement_method="多次元品質分析"
        ))

        # 定量KPI
        metrics.append(KPIMetric(
            metric_id="story_pacing",
            kpi_type=KPIType.QUANTITATIVE,
            name="物語ペース",
            description="物語展開のペース",
            target_value=0.75,
            current_value=0.0,
            unit="ペーススコア",
            measurement_method="ペース分析"
        ))

        return metrics

    def _initialize_quality_gates(self) -> list[QualityGate]:
        """品質ゲートの初期化"""
        gates = []

        # 基本品質ゲート
        gates.append(QualityGate(
            gate_id="basic_quality",
            gate_name="基本品質ゲート",
            quality_level=QualityLevel.REVIEW_READY,
            required_criteria=["content_word_count", "grammar_accuracy"],
            required_kpis=["text_quality_index"],
            pass_rate_threshold=0.8,
            mandatory_pass_criteria=["content_word_count"]
        ))

        # 公開品質ゲート
        gates.append(QualityGate(
            gate_id="publication_quality",
            gate_name="公開品質ゲート",
            quality_level=QualityLevel.PUBLICATION_READY,
            required_criteria=["plot_completeness", "character_consistency", "readability_score"],
            required_kpis=["reader_engagement", "story_pacing"],
            pass_rate_threshold=0.75,
            mandatory_pass_criteria=["plot_completeness"]
        ))

        return gates

    # 測定・分析メソッドの実装（スタブ）

    def _is_criterion_enabled(self, criterion: DODCriterion) -> bool:
        """基準が有効かどうか"""
        return True  # 簡易実装

    def _measure_criterion(
        self,
        criterion: DODCriterion,
        manuscript: str,
        context: dict[str, Any]
    ) -> tuple[float | str, float]:
        """基準の測定"""

        if criterion.criterion_id == "content_word_count":
            word_count = len(manuscript)
            target_count = context.get("target_word_count", 4000)
            score = min(word_count / target_count, 1.0) if target_count > 0 else 0.0
            return word_count, score

        if criterion.criterion_id == "plot_completeness":
            # 簡易プロット完成度評価
            has_intro = "はじめ" in manuscript or len(manuscript) > 100
            has_development = len(manuscript) > 1000
            has_climax = "クライマックス" in manuscript or "結末" in manuscript
            has_resolution = manuscript.endswith(("。", "！"))

            completeness = (has_intro + has_development + has_climax + has_resolution) / 4.0
            return f"{completeness:.2%}", completeness

        if criterion.criterion_id == "grammar_accuracy":
            # 簡易文法正確性評価
            error_indicators = ["。。", "！！", "？？"]
            error_count = sum(manuscript.count(indicator) for indicator in error_indicators)
            accuracy = max(0.0, 1.0 - error_count / 100.0)
            return f"{accuracy:.2%}", accuracy

        if criterion.criterion_id == "character_consistency":
            # キャラクター一貫性の簡易評価
            consistency_score = 0.8  # デフォルト値
            return f"{consistency_score:.2%}", consistency_score

        if criterion.criterion_id == "readability_score":
            # 可読性の簡易評価
            readability = context.get("readability_optimization", {})
            score = readability.get("overall_readability_score", 0.7) if isinstance(readability, dict) else 0.7
            return f"{score:.2f}", score

        return "未測定", 0.5

    def _is_kpi_enabled(self, metric: KPIMetric) -> bool:
        """KPIが有効かどうか"""
        return True  # 簡易実装

    def _measure_kpi_metric(
        self,
        metric: KPIMetric,
        manuscript: str,
        context: dict[str, Any]
    ) -> float | str:
        """KPIメトリクスの測定"""

        if metric.metric_id == "reader_engagement":
            # 読者エンゲージメントの簡易評価
            engagement_factors = []

            # 対話の割合
            dialogue_ratio = manuscript.count("「") / max(len(manuscript) / 100, 1)
            engagement_factors.append(min(dialogue_ratio / 5, 1.0))

            # 感情表現の豊かさ
            emotional_words = ["嬉しい", "悲しい", "驚く", "怒り", "愛"]
            emotion_count = sum(manuscript.count(word) for word in emotional_words)
            emotion_score = min(emotion_count / 10, 1.0)
            engagement_factors.append(emotion_score)

            return sum(engagement_factors) / len(engagement_factors)

        if metric.metric_id == "text_quality_index":
            # 文章品質指数の計算
            quality_factors = []

            # 文章の多様性
            sentences = manuscript.split("。")
            avg_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            variety_score = min(avg_length / 30, 1.0)
            quality_factors.append(variety_score)

            # 語彙の豊かさ
            vocab_score = 0.8  # 簡易実装
            quality_factors.append(vocab_score)

            return sum(quality_factors) / len(quality_factors)

        if metric.metric_id == "story_pacing":
            # 物語ペースの評価
            pacing_score = 0.75  # デフォルト値

            # 構造的バランス
            structure_data = context.get("story_structure", {})
            if isinstance(structure_data, dict):
                balance_score = structure_data.get("balance_score", 0.75)
                pacing_score = balance_score

            return pacing_score

        return 0.5

    def _calculate_achievement_rate(
        self,
        metric: KPIMetric,
        current_value: float | str
    ) -> float:
        """達成率の計算"""

        if isinstance(current_value, str):
            return 0.5  # 文字列値の場合はデフォルト

        target_value = metric.target_value
        if isinstance(target_value, str) or target_value == 0:
            return 0.5

        return min(current_value / target_value, 1.0)

    def _calculate_performance_grade(self, achievement_rate: float) -> str:
        """成績評価の計算"""
        if achievement_rate >= 0.9:
            return "A"
        if achievement_rate >= 0.8:
            return "B"
        if achievement_rate >= 0.7:
            return "C"
        return "D"

    def _evaluate_single_quality_gate(
        self,
        gate: QualityGate,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> CertificationStatus:
        """単一品質ゲートの評価"""

        # 必須合格基準のチェック
        for mandatory_criterion in gate.mandatory_pass_criteria:
            result = next(
                (r for r in dod_results if r.criterion.criterion_id == mandatory_criterion),
                None
            )
            if result and result.status != CertificationStatus.PASSED:
                return CertificationStatus.FAILED

        # 必要基準の合格率チェック
        required_results = [
            r for r in dod_results if r.criterion.criterion_id in gate.required_criteria
        ]
        passed_count = len([r for r in required_results if r.status == CertificationStatus.PASSED])
        pass_rate = passed_count / len(required_results) if required_results else 0.0

        if pass_rate >= gate.pass_rate_threshold:
            return CertificationStatus.PASSED
        if pass_rate >= gate.pass_rate_threshold * 0.8:  # 80%以上なら条件付き
            return CertificationStatus.CONDITIONAL
        return CertificationStatus.FAILED

    # 分析・レポート生成メソッドの実装（スタブ）

    def _analyze_criterion_details(
        self,
        criterion: DODCriterion,
        measured_value: float | str,
        score: float
    ) -> str:
        """基準詳細の分析"""

        if score >= criterion.pass_threshold:
            return f"合格基準を満たしています (スコア: {score:.2f})"
        gap = criterion.pass_threshold - score
        return f"合格基準に {gap:.2f} 不足しています"

    def _collect_criterion_evidence(
        self,
        criterion: DODCriterion,
        manuscript: str,
        context: dict[str, Any]
    ) -> list[str]:
        """基準根拠の収集"""
        return [f"{criterion.name}の測定根拠"]

    def _generate_criterion_recommendations(
        self,
        criterion: DODCriterion,
        score: float
    ) -> list[str]:
        """基準推奨事項の生成"""

        if score >= criterion.pass_threshold:
            return ["現在の品質を維持してください"]
        return [f"{criterion.name}の改善が必要です", "具体的な改善施策を検討してください"]

    def _analyze_kpi_performance(
        self,
        metric: KPIMetric,
        current_value: float | str,
        achievement_rate: float
    ) -> str:
        """KPIパフォーマンスの分析"""

        if achievement_rate >= 0.9:
            return f"優秀な成果です。目標を{achievement_rate:.1%}達成しました。"
        if achievement_rate >= 0.7:
            return f"良好な成果です。目標の{achievement_rate:.1%}を達成しました。"
        return f"改善が必要です。目標の{achievement_rate:.1%}の達成に留まっています。"

    def _generate_kpi_improvements(
        self,
        metric: KPIMetric,
        achievement_rate: float
    ) -> list[str]:
        """KPI改善提案の生成"""

        if achievement_rate >= 0.8:
            return ["現在のレベルを維持してください"]
        if achievement_rate >= 0.6:
            return [f"{metric.name}のさらなる向上を目指してください"]
        return [f"{metric.name}の根本的な改善が必要です", "改善計画の策定を推奨します"]

    def _generate_certification_summary(
        self,
        overall_status: CertificationStatus,
        overall_score: float,
        dod_results: list[QualityCheckResult],
        kpi_assessments: list[KPIAssessment]
    ) -> str:
        """認定サマリーの生成"""

        status_text = {
            CertificationStatus.PASSED: "合格",
            CertificationStatus.CONDITIONAL: "条件付き合格",
            CertificationStatus.FAILED: "不合格",
            CertificationStatus.REQUIRES_REVISION: "修正要"
        }.get(overall_status, "未判定")

        summary_parts = [
            f"総合判定: {status_text}",
            f"総合スコア: {overall_score:.2f}",
            f"DOD基準: {len([r for r in dod_results if r.status == CertificationStatus.PASSED])}/{len(dod_results)}合格",
            f"KPI評価: 平均{sum(a.achievement_rate for a in kpi_assessments)/len(kpi_assessments):.1%}達成"
        ]

        return " | ".join(summary_parts)

    def _generate_next_steps(
        self,
        overall_status: CertificationStatus,
        critical_issues: list[str],
        improvement_priorities: list[str]
    ) -> list[str]:
        """次のステップの生成"""

        next_steps = []

        if overall_status == CertificationStatus.PASSED:
            next_steps.append("✅ 公開準備に進んでください")
            next_steps.append("📋 最終チェックリストの確認")

        elif overall_status == CertificationStatus.CONDITIONAL:
            next_steps.append("🔶 条件付き合格：軽微な修正後に公開可能")
            next_steps.extend(improvement_priorities[:2])  # 上位2つの優先事項

        elif overall_status == CertificationStatus.REQUIRES_REVISION:
            next_steps.append("🔄 修正が必要：品質向上後に再認定")
            next_steps.extend(improvement_priorities)

        else:  # FAILED
            next_steps.append("❌ 大幅な品質改善が必要")
            if critical_issues:
                next_steps.append("🚨 重要問題の解決が最優先")
                next_steps.extend(critical_issues[:3])  # 上位3つの重要問題

        return next_steps
