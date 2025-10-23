"""STEP 5: 論理検証サービス

A38執筆プロンプトガイドのSTEP5「論理検証」を実装するサービス。
プロット・設定・構造の論理的一貫性を総合的に検証し、
矛盾点の発見と修正案の提案を行います。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class LogicValidationSeverity(Enum):
    """論理検証問題の重要度分類"""
    CRITICAL = "critical"  # 致命的な矛盾：読者の理解を阻害する
    HIGH = "high"  # 重要な不整合：世界観・キャラ設定の矛盾
    MEDIUM = "medium"  # 一般的な論理問題：細かい設定の不一致
    LOW = "low"  # 軽微な問題：推奨される改善点


class LogicValidationType(Enum):
    """論理検証のタイプ分類"""
    PLOT_CONSISTENCY = "plot_consistency"  # プロット内論理一貫性
    CHARACTER_CONSISTENCY = "character_consistency"  # キャラクター論理一貫性
    WORLD_CONSISTENCY = "world_consistency"  # 世界観論理一貫性
    TIMELINE_CONSISTENCY = "timeline_consistency"  # 時系列論理一貫性
    CAUSAL_RELATIONSHIP = "causal_relationship"  # 因果関係論理一貫性
    SETTING_CONSISTENCY = "setting_consistency"  # 設定論理一貫性


@dataclass
class LogicValidationIssue:
    """論理検証で発見された問題"""
    issue_id: str
    validation_type: LogicValidationType
    severity: LogicValidationSeverity
    title: str
    description: str
    location: str  # どこで発見されたか
    conflicting_elements: list[str]  # 矛盾する要素
    evidence: list[str]  # 矛盾の根拠
    suggested_fixes: list[str]  # 修正案
    impact_assessment: str  # 影響範囲の評価
    related_issues: list[str]  # 関連する他の問題
    detection_timestamp: datetime


@dataclass
class CausalChain:
    """因果関係のチェーン"""
    chain_id: str
    cause: str  # 原因
    effect: str  # 結果
    intermediates: list[str]  # 中間要素
    strength: float  # 因果関係の強さ (0-1)
    evidence: list[str]  # 根拠
    alternatives: list[str]  # 代替可能な因果関係


@dataclass
class TimelineEvent:
    """時系列イベント"""
    event_id: str
    event_name: str
    timestamp: str  # 作品内時刻
    duration: str | None  # 継続時間
    location: str  # 場所
    participants: list[str]  # 参加者
    prerequisites: list[str]  # 前提条件
    consequences: list[str]  # 結果
    dependencies: list[str]  # 依存関係


@dataclass
class ConsistencyMatrix:
    """一貫性マトリクス"""
    element_pairs: list[tuple[str, str]]  # 検証対象要素ペア
    consistency_scores: dict[tuple[str, str], float]  # 一貫性スコア (0-1)
    inconsistency_reasons: dict[tuple[str, str], list[str]]  # 不整合の理由
    validation_details: dict[tuple[str, str], dict[str, Any]]  # 検証詳細


@dataclass
class LogicValidationReport:
    """論理検証レポート"""
    validation_id: str
    episode_number: int
    validation_timestamp: datetime
    total_issues: int
    issues_by_severity: dict[LogicValidationSeverity, int]
    issues_by_type: dict[LogicValidationType, int]
    detected_issues: list[LogicValidationIssue]
    consistency_matrix: ConsistencyMatrix
    causal_chains: list[CausalChain]
    timeline_events: list[TimelineEvent]
    overall_logic_score: float  # 全体論理スコア (0-1)
    validation_summary: str
    recommended_actions: list[str]
    validation_metadata: dict[str, Any]


@dataclass
class LogicValidationConfig:
    """論理検証設定"""
    enable_plot_validation: bool = True
    enable_character_validation: bool = True
    enable_world_validation: bool = True
    enable_timeline_validation: bool = True
    enable_causal_validation: bool = True
    enable_setting_validation: bool = True
    severity_threshold: LogicValidationSeverity = LogicValidationSeverity.LOW
    consistency_threshold: float = 0.7  # 一貫性の閾値
    causal_strength_threshold: float = 0.5  # 因果関係強度の閾値
    max_validation_depth: int = 5  # 検証の最大深度
    enable_cross_episode_validation: bool = False
    validation_timeout: int = 300  # タイムアウト（秒）


class LogicValidatorService(BaseWritingStep):
    """STEP 5: 論理検証サービス

    プロット・設定・構造の論理的一貫性を検証し、
    矛盾や不整合を発見・修正するためのサービス。
    A38ガイドのSTEP5「論理検証」を実装。
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
        self._validation_config = LogicValidationConfig()

        # 検証結果キャッシュ
        self._validation_cache: dict[str, LogicValidationReport] = {}
        self._consistency_cache: dict[str, ConsistencyMatrix] = {}

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "論理検証"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "プロット・設定・構造の論理的一貫性を検証し、矛盾点を発見・修正します"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 5: 論理検証の実行

        Args:
            context: 実行コンテキスト

        Returns:
            論理検証結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # 論理検証の実行
            validation_report = self._execute_logic_validation(
                episode_number=episode_number,
                project=project,
                context=context
            )

            # 結果をコンテキストに追加
            context["logic_validation_report"] = validation_report
            context["logic_validation_completed"] = True

            return context

        except Exception as e:
            context["logic_validation_error"] = str(e)
            raise

    def _execute_logic_validation(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> LogicValidationReport:
        """論理検証の実行"""

        # キャッシュチェック
        cache_key = f"{project.project_name}_{episode_number}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]

        # データ収集
        validation_data = self._collect_validation_data(episode_number, project, context)

        # 各タイプの検証実行
        all_issues = []

        if self._validation_config.enable_plot_validation:
            plot_issues = self._validate_plot_consistency(validation_data)
            all_issues.extend(plot_issues)

        if self._validation_config.enable_character_validation:
            character_issues = self._validate_character_consistency(validation_data)
            all_issues.extend(character_issues)

        if self._validation_config.enable_world_validation:
            world_issues = self._validate_world_consistency(validation_data)
            all_issues.extend(world_issues)

        if self._validation_config.enable_timeline_validation:
            timeline_issues = self._validate_timeline_consistency(validation_data)
            all_issues.extend(timeline_issues)

        if self._validation_config.enable_causal_validation:
            causal_issues = self._validate_causal_relationships(validation_data)
            all_issues.extend(causal_issues)

        if self._validation_config.enable_setting_validation:
            setting_issues = self._validate_setting_consistency(validation_data)
            all_issues.extend(setting_issues)

        # 一貫性マトリクスの生成
        consistency_matrix = self._generate_consistency_matrix(validation_data)

        # 因果関係チェーンの分析
        causal_chains = self._analyze_causal_chains(validation_data)

        # 時系列イベントの整理
        timeline_events = self._organize_timeline_events(validation_data)

        # レポート生成
        validation_report = self._generate_validation_report(
            episode_number=episode_number,
            issues=all_issues,
            consistency_matrix=consistency_matrix,
            causal_chains=causal_chains,
            timeline_events=timeline_events,
            validation_data=validation_data
        )

        # キャッシュに保存
        self._validation_cache[cache_key] = validation_report

        return validation_report

    def _collect_validation_data(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """検証用データの収集"""

        validation_data = {
            "episode_number": episode_number,
            "project": project,
            "plot_data": context.get("plot_data", {}),
            "character_data": context.get("character_data", {}),
            "world_data": context.get("world_data", {}),
            "setting_data": context.get("setting_data", {}),
            "story_structure": context.get("story_structure", {}),
            "phase_structure": context.get("phase_structure", {}),
            "section_balance": context.get("section_balance", {}),
            "previous_episodes": [],
            "related_episodes": []
        }

        # 前話データの取得（設定で有効な場合）
        if self._validation_config.enable_cross_episode_validation:
            validation_data["previous_episodes"] = self._get_previous_episodes_data(
                episode_number, project
            )
            validation_data["related_episodes"] = self._get_related_episodes_data(
                episode_number, project
            )

        return validation_data

    def _validate_plot_consistency(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """プロット論理一貫性の検証"""
        issues = []
        plot_data = validation_data.get("plot_data", {})

        # プロット内部の一貫性チェック
        plot_elements = plot_data.get("elements", [])
        for i, element in enumerate(plot_elements):
            for j, other_element in enumerate(plot_elements[i+1:], i+1):
                consistency_score = self._calculate_plot_consistency(element, other_element)
                if consistency_score < self._validation_config.consistency_threshold:
                    issue = LogicValidationIssue(
                        issue_id=f"plot_consistency_{i}_{j}",
                        validation_type=LogicValidationType.PLOT_CONSISTENCY,
                        severity=self._determine_severity(consistency_score),
                        title="プロット要素間の論理不整合",
                        description=f"要素「{element.get('name', f'Element{i}')}」と「{other_element.get('name', f'Element{j}')}」に論理的矛盾があります",
                        location=f"プロット要素 {i}↔{j}",
                        conflicting_elements=[
                            element.get("name", f"Element{i}"),
                            other_element.get("name", f"Element{j}")
                        ],
                        evidence=self._extract_inconsistency_evidence(element, other_element),
                        suggested_fixes=self._generate_plot_fixes(element, other_element, consistency_score),
                        impact_assessment=self._assess_plot_impact(element, other_element),
                        related_issues=[],
                        detection_timestamp=datetime.now(tz=datetime.timezone.utc)
                    )
                    issues.append(issue)

        # プロット進行の論理チェック
        plot_progression = plot_data.get("progression", [])
        progression_issues = self._validate_plot_progression(plot_progression)
        issues.extend(progression_issues)

        return issues

    def _validate_character_consistency(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """キャラクター論理一貫性の検証"""
        issues = []
        character_data = validation_data.get("character_data", {})

        # キャラクター設定の内部一貫性
        for char_id, character in character_data.items():
            char_issues = self._validate_single_character_logic(char_id, character)
            issues.extend(char_issues)

        # キャラクター間の関係性一貫性
        characters = list(character_data.items())
        for i, (char_id1, char1) in enumerate(characters):
            for char_id2, char2 in characters[i+1:]:
                relationship_issues = self._validate_character_relationship_logic(
                    char_id1, char1, char_id2, char2
                )
                issues.extend(relationship_issues)

        return issues

    def _validate_world_consistency(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """世界観論理一貫性の検証"""
        issues = []
        world_data = validation_data.get("world_data", {})

        # 世界設定の内部一貫性
        world_rules = world_data.get("rules", [])
        for i, rule in enumerate(world_rules):
            for j, other_rule in enumerate(world_rules[i+1:], i+1):
                if self._rules_conflict(rule, other_rule):
                    issue = LogicValidationIssue(
                        issue_id=f"world_rule_conflict_{i}_{j}",
                        validation_type=LogicValidationType.WORLD_CONSISTENCY,
                        severity=LogicValidationSeverity.HIGH,
                        title="世界設定ルール間の矛盾",
                        description=f"世界ルール「{rule.get('name', f'Rule{i}')}」と「{other_rule.get('name', f'Rule{j}')}」が矛盾しています",
                        location=f"世界設定ルール {i}↔{j}",
                        conflicting_elements=[
                            rule.get("name", f"Rule{i}"),
                            other_rule.get("name", f"Rule{j}")
                        ],
                        evidence=self._extract_rule_conflict_evidence(rule, other_rule),
                        suggested_fixes=self._generate_world_rule_fixes(rule, other_rule),
                        impact_assessment="世界観の一貫性に影響し、読者の理解を阻害する可能性があります",
                        related_issues=[],
                        detection_timestamp=datetime.now(tz=datetime.timezone.utc)
                    )
                    issues.append(issue)

        # 物理法則・魔法システムの一貫性
        physics_issues = self._validate_physics_consistency(world_data)
        issues.extend(physics_issues)

        # 地理・歴史の一貫性
        geography_issues = self._validate_geography_consistency(world_data)
        issues.extend(geography_issues)

        return issues

    def _validate_timeline_consistency(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """時系列論理一貫性の検証"""
        issues = []

        # 時系列イベントの抽出
        timeline_events = self._extract_timeline_events(validation_data)

        # 時系列順序の検証
        for i, event in enumerate(timeline_events):
            for j, other_event in enumerate(timeline_events[i+1:], i+1):
                if self._timeline_conflict(event, other_event):
                    issue = LogicValidationIssue(
                        issue_id=f"timeline_conflict_{i}_{j}",
                        validation_type=LogicValidationType.TIMELINE_CONSISTENCY,
                        severity=LogicValidationSeverity.HIGH,
                        title="時系列の論理矛盾",
                        description=f"イベント「{event.event_name}」と「{other_event.event_name}」の時系列に矛盾があります",
                        location=f"時系列 {event.timestamp} vs {other_event.timestamp}",
                        conflicting_elements=[event.event_name, other_event.event_name],
                        evidence=self._extract_timeline_evidence(event, other_event),
                        suggested_fixes=self._generate_timeline_fixes(event, other_event),
                        impact_assessment="物語の時系列理解に混乱を生じさせる可能性があります",
                        related_issues=[],
                        detection_timestamp=datetime.now(tz=datetime.timezone.utc)
                    )
                    issues.append(issue)

        return issues

    def _validate_causal_relationships(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """因果関係論理一貫性の検証"""
        issues = []

        # 因果関係の抽出
        causal_chains = self._extract_causal_relationships(validation_data)

        # 因果関係の妥当性検証
        for chain in causal_chains:
            if chain.strength < self._validation_config.causal_strength_threshold:
                issue = LogicValidationIssue(
                    issue_id=f"weak_causal_{chain.chain_id}",
                    validation_type=LogicValidationType.CAUSAL_RELATIONSHIP,
                    severity=LogicValidationSeverity.MEDIUM,
                    title="因果関係の薄弱性",
                    description=f"「{chain.cause}」→「{chain.effect}」の因果関係が薄弱です",
                    location=f"因果関係チェーン {chain.chain_id}",
                    conflicting_elements=[chain.cause, chain.effect],
                    evidence=chain.evidence,
                    suggested_fixes=self._generate_causal_fixes(chain),
                    impact_assessment="読者の納得感を損なう可能性があります",
                    related_issues=[],
                    detection_timestamp=datetime.now(tz=datetime.timezone.utc)
                )
                issues.append(issue)

        # 循環論理の検出
        circular_logic_issues = self._detect_circular_logic(causal_chains)
        issues.extend(circular_logic_issues)

        return issues

    def _validate_setting_consistency(self, validation_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """設定論理一貫性の検証"""
        issues = []
        setting_data = validation_data.get("setting_data", {})

        # 設定項目間の一貫性チェック
        settings = setting_data.get("items", {})
        for setting_key, setting_value in settings.items():
            # 設定の内部一貫性
            internal_issues = self._validate_setting_internal_logic(setting_key, setting_value)
            issues.extend(internal_issues)

            # 他の設定との一貫性
            for other_key, other_value in settings.items():
                if setting_key != other_key:
                    cross_issues = self._validate_cross_setting_logic(
                        setting_key, setting_value, other_key, other_value
                    )
                    issues.extend(cross_issues)

        return issues

    def _generate_consistency_matrix(self, validation_data: dict[str, Any]) -> ConsistencyMatrix:
        """一貫性マトリクスの生成"""

        # 検証対象要素の特定
        elements = []
        elements.extend(validation_data.get("plot_data", {}).get("elements", []))
        elements.extend(validation_data.get("character_data", {}).keys())
        elements.extend(validation_data.get("world_data", {}).get("rules", []))

        # 要素ペアの生成
        element_pairs = []
        for i, element1 in enumerate(elements):
            for element2 in elements[i+1:]:
                element_pairs.append((str(element1), str(element2)))

        # 一貫性スコアの計算
        consistency_scores = {}
        inconsistency_reasons = {}
        validation_details = {}

        for pair in element_pairs:
            score, reasons, details = self._calculate_pair_consistency(
                pair[0], pair[1], validation_data
            )
            consistency_scores[pair] = score
            inconsistency_reasons[pair] = reasons
            validation_details[pair] = details

        return ConsistencyMatrix(
            element_pairs=element_pairs,
            consistency_scores=consistency_scores,
            inconsistency_reasons=inconsistency_reasons,
            validation_details=validation_details
        )

    def _analyze_causal_chains(self, validation_data: dict[str, Any]) -> list[CausalChain]:
        """因果関係チェーンの分析"""
        causal_chains = []

        # プロットからの因果関係抽出
        plot_chains = self._extract_plot_causal_chains(validation_data.get("plot_data", {}))
        causal_chains.extend(plot_chains)

        # キャラクター行動からの因果関係抽出
        character_chains = self._extract_character_causal_chains(validation_data.get("character_data", {}))
        causal_chains.extend(character_chains)

        # 世界設定からの因果関係抽出
        world_chains = self._extract_world_causal_chains(validation_data.get("world_data", {}))
        causal_chains.extend(world_chains)

        return causal_chains

    def _organize_timeline_events(self, validation_data: dict[str, Any]) -> list[TimelineEvent]:
        """時系列イベントの整理"""
        events = []

        # プロットからのイベント抽出
        plot_events = self._extract_plot_timeline_events(validation_data.get("plot_data", {}))
        events.extend(plot_events)

        # キャラクター行動からのイベント抽出
        character_events = self._extract_character_timeline_events(validation_data.get("character_data", {}))
        events.extend(character_events)

        # 時系列順にソート
        events.sort(key=lambda e: e.timestamp)

        return events

    def _generate_validation_report(
        self,
        episode_number: int,
        issues: list[LogicValidationIssue],
        consistency_matrix: ConsistencyMatrix,
        causal_chains: list[CausalChain],
        timeline_events: list[TimelineEvent],
        validation_data: dict[str, Any]
    ) -> LogicValidationReport:
        """論理検証レポートの生成"""

        # 問題の統計
        issues_by_severity = dict.fromkeys(LogicValidationSeverity, 0)
        issues_by_type = dict.fromkeys(LogicValidationType, 0)

        for issue in issues:
            issues_by_severity[issue.severity] += 1
            issues_by_type[issue.validation_type] += 1

        # 全体論理スコアの計算
        overall_logic_score = self._calculate_overall_logic_score(
            issues, consistency_matrix, causal_chains
        )

        # 推奨アクションの生成
        recommended_actions = self._generate_recommended_actions(issues, overall_logic_score)

        # 検証サマリーの生成
        validation_summary = self._generate_validation_summary(
            issues, overall_logic_score, issues_by_severity
        )

        return LogicValidationReport(
            validation_id=f"logic_validation_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            validation_timestamp=datetime.now(tz=datetime.timezone.utc),
            total_issues=len(issues),
            issues_by_severity=issues_by_severity,
            issues_by_type=issues_by_type,
            detected_issues=issues,
            consistency_matrix=consistency_matrix,
            causal_chains=causal_chains,
            timeline_events=timeline_events,
            overall_logic_score=overall_logic_score,
            validation_summary=validation_summary,
            recommended_actions=recommended_actions,
            validation_metadata={
                "validation_config": self._validation_config.__dict__,
                "validation_data_summary": self._summarize_validation_data(validation_data)
            }
        )

    def _calculate_plot_consistency(self, element1: dict[str, Any], element2: dict[str, Any]) -> float:
        """プロット要素間の一貫性スコア計算"""
        # 実装：要素間の論理的一貫性を0-1で評価
        consistency_factors = []

        # 目的の一貫性
        if "purpose" in element1 and "purpose" in element2:
            purpose_consistency = self._calculate_purpose_alignment(
                element1["purpose"], element2["purpose"]
            )
            consistency_factors.append(purpose_consistency)

        # 結果の一貫性
        if "outcome" in element1 and "outcome" in element2:
            outcome_consistency = self._calculate_outcome_consistency(
                element1["outcome"], element2["outcome"]
            )
            consistency_factors.append(outcome_consistency)

        # 前提条件の一貫性
        prerequisites1 = element1.get("prerequisites", [])
        prerequisites2 = element2.get("prerequisites", [])
        prerequisite_consistency = self._calculate_prerequisite_consistency(
            prerequisites1, prerequisites2
        )
        consistency_factors.append(prerequisite_consistency)

        # 全体の一貫性スコア
        return sum(consistency_factors) / len(consistency_factors) if consistency_factors else 0.5

    def _determine_severity(self, consistency_score: float) -> LogicValidationSeverity:
        """一貫性スコアから重要度を判定"""
        if consistency_score < 0.3:
            return LogicValidationSeverity.CRITICAL
        if consistency_score < 0.5:
            return LogicValidationSeverity.HIGH
        if consistency_score < 0.7:
            return LogicValidationSeverity.MEDIUM
        return LogicValidationSeverity.LOW

    def _extract_inconsistency_evidence(
        self,
        element1: dict[str, Any],
        element2: dict[str, Any]
    ) -> list[str]:
        """不整合の根拠を抽出"""
        evidence = []

        # 目的の矛盾
        if element1.get("purpose") and element2.get("purpose"):
            if self._purposes_conflict(element1["purpose"], element2["purpose"]):
                evidence.append(f"目的の矛盾: {element1['purpose']} vs {element2['purpose']}")

        # 結果の矛盾
        if element1.get("outcome") and element2.get("outcome"):
            if self._outcomes_conflict(element1["outcome"], element2["outcome"]):
                evidence.append(f"結果の矛盾: {element1['outcome']} vs {element2['outcome']}")

        # 前提条件の矛盾
        prerequisites1 = set(element1.get("prerequisites", []))
        prerequisites2 = set(element2.get("prerequisites", []))
        conflicting_prerequisites = prerequisites1.intersection(prerequisites2)
        if conflicting_prerequisites:
            evidence.append(f"前提条件の競合: {', '.join(conflicting_prerequisites)}")

        return evidence

    def _generate_plot_fixes(
        self,
        element1: dict[str, Any],
        element2: dict[str, Any],
        consistency_score: float
    ) -> list[str]:
        """プロット要素の修正案を生成"""
        fixes = []

        if consistency_score < 0.3:
            fixes.append("要素の根本的な見直しが必要です")
            fixes.append("どちらか一方の要素を削除または大幅変更を検討してください")
        elif consistency_score < 0.5:
            fixes.append("要素間の関係性を明確化してください")
            fixes.append("矛盾する部分の調整が必要です")
        else:
            fixes.append("細かい表現の調整で改善可能です")
            fixes.append("要素間の連携を強化してください")

        return fixes

    def _assess_plot_impact(
        self,
        element1: dict[str, Any],
        element2: dict[str, Any]
    ) -> str:
        """プロット要素の影響範囲評価"""
        # 実装：要素の重要度と影響範囲を評価
        importance1 = element1.get("importance", 5)  # 1-10スケール
        importance2 = element2.get("importance", 5)

        average_importance = (importance1 + importance2) / 2

        if average_importance >= 8:
            return "高影響：物語の核心部分に関わる重要な矛盾です"
        if average_importance >= 6:
            return "中影響：読者の理解に影響を与える可能性があります"
        return "低影響：軽微な不整合ですが改善が推奨されます"

    def _calculate_overall_logic_score(
        self,
        issues: list[LogicValidationIssue],
        consistency_matrix: ConsistencyMatrix,
        causal_chains: list[CausalChain]
    ) -> float:
        """全体論理スコアの計算"""

        # 問題数による減点
        issue_penalty = len(issues) * 0.1
        severity_penalty = sum([
            2.0 if issue.severity == LogicValidationSeverity.CRITICAL else
            1.5 if issue.severity == LogicValidationSeverity.HIGH else
            1.0 if issue.severity == LogicValidationSeverity.MEDIUM else 0.5
            for issue in issues
        ]) * 0.05

        # 一貫性マトリクスからのスコア
        if consistency_matrix.consistency_scores:
            avg_consistency = sum(consistency_matrix.consistency_scores.values()) / len(consistency_matrix.consistency_scores)
        else:
            avg_consistency = 1.0

        # 因果関係の強度
        if causal_chains:
            avg_causal_strength = sum(chain.strength for chain in causal_chains) / len(causal_chains)
        else:
            avg_causal_strength = 1.0

        # 総合スコア計算 (0-1スケール)
        base_score = (avg_consistency + avg_causal_strength) / 2
        final_score = max(0.0, base_score - issue_penalty - severity_penalty)

        return min(1.0, final_score)

    def _generate_recommended_actions(
        self,
        issues: list[LogicValidationIssue],
        overall_score: float
    ) -> list[str]:
        """推奨アクションの生成"""
        actions = []

        if overall_score < 0.4:
            actions.append("🚨 緊急：根本的な構造見直しが必要です")
            actions.append("主要プロット要素の再検討を行ってください")
        elif overall_score < 0.6:
            actions.append("⚠️ 重要：複数の論理問題の修正が必要です")
            actions.append("重要度の高い問題から順次対応してください")
        elif overall_score < 0.8:
            actions.append("📝 推奨：軽微な調整で品質向上が期待できます")
            actions.append("検出された問題の確認と修正を検討してください")
        else:
            actions.append("✅ 良好：論理的一貫性は十分に確保されています")
            actions.append("現在の品質を維持してください")

        # 問題タイプ別の具体的アクション
        critical_issues = [i for i in issues if i.severity == LogicValidationSeverity.CRITICAL]
        if critical_issues:
            actions.append(f"⭐ 最優先：{len(critical_issues)}件の致命的問題の即座な修正")

        return actions

    def _generate_validation_summary(
        self,
        issues: list[LogicValidationIssue],
        overall_score: float,
        issues_by_severity: dict[LogicValidationSeverity, int]
    ) -> str:
        """検証サマリーの生成"""

        summary_parts = []

        # 全体評価
        if overall_score >= 0.8:
            summary_parts.append("論理的一貫性は優秀です。")
        elif overall_score >= 0.6:
            summary_parts.append("論理的一貫性は良好ですが、いくつかの改善点があります。")
        elif overall_score >= 0.4:
            summary_parts.append("論理的一貫性に課題があります。修正が必要です。")
        else:
            summary_parts.append("論理的一貫性に深刻な問題があります。緊急の対応が必要です。")

        # 問題の内訳
        if issues:
            severity_text = []
            for severity, count in issues_by_severity.items():
                if count > 0:
                    severity_name = {
                        LogicValidationSeverity.CRITICAL: "致命的",
                        LogicValidationSeverity.HIGH: "重要",
                        LogicValidationSeverity.MEDIUM: "一般的",
                        LogicValidationSeverity.LOW: "軽微"
                    }[severity]
                    severity_text.append(f"{severity_name}:{count}件")

            if severity_text:
                summary_parts.append(f"検出された問題: {', '.join(severity_text)}")
        else:
            summary_parts.append("論理的な問題は検出されませんでした。")

        return " ".join(summary_parts)

    # ヘルパーメソッドのスタブ実装（実際にはより詳細な実装が必要）
    def _validate_plot_progression(self, progression: list[dict[str, Any]]) -> list[LogicValidationIssue]:
        """プロット進行の論理検証"""
        # スタブ実装
        return []

    def _validate_single_character_logic(self, char_id: str, character: dict[str, Any]) -> list[LogicValidationIssue]:
        """単一キャラクターの論理検証"""
        # スタブ実装
        return []

    def _validate_character_relationship_logic(self, char_id1: str, char1: dict[str, Any], char_id2: str, char2: dict[str, Any]) -> list[LogicValidationIssue]:
        """キャラクター関係性の論理検証"""
        # スタブ実装
        return []

    def _rules_conflict(self, rule1: dict[str, Any], rule2: dict[str, Any]) -> bool:
        """ルール間の矛盾判定"""
        # スタブ実装
        return False

    def _extract_rule_conflict_evidence(self, rule1: dict[str, Any], rule2: dict[str, Any]) -> list[str]:
        """ルール矛盾の根拠抽出"""
        # スタブ実装
        return []

    def _generate_world_rule_fixes(self, rule1: dict[str, Any], rule2: dict[str, Any]) -> list[str]:
        """世界ルール修正案生成"""
        # スタブ実装
        return ["ルールの調整が必要です"]

    def _validate_physics_consistency(self, world_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """物理法則の一貫性検証"""
        # スタブ実装
        return []

    def _validate_geography_consistency(self, world_data: dict[str, Any]) -> list[LogicValidationIssue]:
        """地理の一貫性検証"""
        # スタブ実装
        return []

    def _extract_timeline_events(self, validation_data: dict[str, Any]) -> list[TimelineEvent]:
        """時系列イベントの抽出"""
        # スタブ実装
        return []

    def _timeline_conflict(self, event1: TimelineEvent, event2: TimelineEvent) -> bool:
        """時系列矛盾の判定"""
        # スタブ実装
        return False

    def _extract_timeline_evidence(self, event1: TimelineEvent, event2: TimelineEvent) -> list[str]:
        """時系列矛盾の根拠抽出"""
        # スタブ実装
        return []

    def _generate_timeline_fixes(self, event1: TimelineEvent, event2: TimelineEvent) -> list[str]:
        """時系列修正案生成"""
        # スタブ実装
        return ["時系列の調整が必要です"]

    def _extract_causal_relationships(self, validation_data: dict[str, Any]) -> list[CausalChain]:
        """因果関係の抽出"""
        # スタブ実装
        return []

    def _generate_causal_fixes(self, chain: CausalChain) -> list[str]:
        """因果関係修正案生成"""
        # スタブ実装
        return ["因果関係の強化が必要です"]

    def _detect_circular_logic(self, causal_chains: list[CausalChain]) -> list[LogicValidationIssue]:
        """循環論理の検出"""
        # スタブ実装
        return []

    def _validate_setting_internal_logic(self, setting_key: str, setting_value: Any) -> list[LogicValidationIssue]:
        """設定内部論理の検証"""
        # スタブ実装
        return []

    def _validate_cross_setting_logic(self, key1: str, value1: Any, key2: str, value2: Any) -> list[LogicValidationIssue]:
        """設定間論理の検証"""
        # スタブ実装
        return []

    def _calculate_pair_consistency(self, element1: str, element2: str, validation_data: dict[str, Any]) -> tuple[float, list[str], dict[str, Any]]:
        """要素ペアの一貫性計算"""
        # スタブ実装
        return 0.8, [], {}

    def _extract_plot_causal_chains(self, plot_data: dict[str, Any]) -> list[CausalChain]:
        """プロットからの因果関係抽出"""
        # スタブ実装
        return []

    def _extract_character_causal_chains(self, character_data: dict[str, Any]) -> list[CausalChain]:
        """キャラクターからの因果関係抽出"""
        # スタブ実装
        return []

    def _extract_world_causal_chains(self, world_data: dict[str, Any]) -> list[CausalChain]:
        """世界設定からの因果関係抽出"""
        # スタブ実装
        return []

    def _extract_plot_timeline_events(self, plot_data: dict[str, Any]) -> list[TimelineEvent]:
        """プロットからの時系列イベント抽出"""
        # スタブ実装
        return []

    def _extract_character_timeline_events(self, character_data: dict[str, Any]) -> list[TimelineEvent]:
        """キャラクターからの時系列イベント抽出"""
        # スタブ実装
        return []

    def _get_previous_episodes_data(self, episode_number: int, project: ProjectModel) -> list[dict[str, Any]]:
        """前話データの取得"""
        # スタブ実装
        return []

    def _get_related_episodes_data(self, episode_number: int, project: ProjectModel) -> list[dict[str, Any]]:
        """関連話データの取得"""
        # スタブ実装
        return []

    def _summarize_validation_data(self, validation_data: dict[str, Any]) -> dict[str, Any]:
        """検証データのサマリー生成"""
        # スタブ実装
        return {"summary": "validation data summary"}

    def _calculate_purpose_alignment(self, purpose1: str, purpose2: str) -> float:
        """目的の整合性計算"""
        # スタブ実装
        return 0.8

    def _calculate_outcome_consistency(self, outcome1: str, outcome2: str) -> float:
        """結果の一貫性計算"""
        # スタブ実装
        return 0.8

    def _calculate_prerequisite_consistency(self, prereq1: list[str], prereq2: list[str]) -> float:
        """前提条件の一貫性計算"""
        # スタブ実装
        return 0.8

    def _purposes_conflict(self, purpose1: str, purpose2: str) -> bool:
        """目的の競合判定"""
        # スタブ実装
        return False

    def _outcomes_conflict(self, outcome1: str, outcome2: str) -> bool:
        """結果の競合判定"""
        # スタブ実装
        return False
