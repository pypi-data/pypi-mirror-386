"""
品質チェックプロンプトEntity

SPEC-STAGE5-SEPARATION対応
Claude Code用品質チェックプロンプトの生成・管理を行うドメインエンティティ
"""

import importlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from noveler.domain.entities.enhanced_episode_plot import EnhancedEpisodePlot
from noveler.domain.value_objects.quality_check_level import QualityCheckLevel, QualityCheckRequest, QualityCriterion


@dataclass
class QualityCheckPromptId:
    """品質チェックプロンプトIDを表現するValue Object"""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.value.strip():
            msg = "Quality check prompt ID cannot be empty"
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if not isinstance(other, QualityCheckPromptId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class QualityCheckResult:
    """品質チェック結果を表現するValue Object"""

    overall_score: float
    criterion_scores: dict[str, float]
    passed_criteria: list[str]
    failed_criteria: list[str]
    recommendations: list[str]
    check_timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall_score <= 100.0:
            msg = f"Overall score must be between 0 and 100, got: {self.overall_score}"
            raise ValueError(msg)

    def is_passing_grade(self, threshold: float = 80.0) -> bool:
        """合格判定"""
        return self.overall_score >= threshold

    def get_improvement_priority(self) -> list[str]:
        """改善優先度順の基準ID一覧"""
        failed_with_scores = [
            (criterion_id, score)
            for criterion_id, score in self.criterion_scores.items()
            if criterion_id in self.failed_criteria
        ]
        # スコアが低い順にソート
        failed_with_scores.sort(key=lambda x: x[1])
        return [criterion_id for criterion_id, _ in failed_with_scores]


class QualityCheckPrompt:
    """品質チェックプロンプトを表現するドメインエンティティ"""

    def __init__(
        self,
        prompt_id: QualityCheckPromptId | None = None,
        request: QualityCheckRequest | None = None,
        episode_plot: EnhancedEpisodePlot | None = None,
        check_criteria: list[QualityCriterion] | None = None,
    ) -> None:
        self._prompt_id = prompt_id or QualityCheckPromptId()
        self._request = request
        self._episode_plot = episode_plot
        self._check_criteria = check_criteria or []
        self._generated_prompt: str | None = None
        self._creation_timestamp = datetime.now(timezone.utc)
        self._last_updated = datetime.now(timezone.utc)
        self._check_result: QualityCheckResult | None = None

        # ドメインイベント
        self._domain_events: list[str] = []

    @property
    def prompt_id(self) -> QualityCheckPromptId:
        return self._prompt_id

    @property
    def request(self) -> QualityCheckRequest | None:
        return self._request

    @property
    def episode_plot(self) -> EnhancedEpisodePlot | None:
        return self._episode_plot

    @property
    def check_criteria(self) -> list[QualityCriterion]:
        return self._check_criteria.copy()

    @property
    def generated_prompt(self) -> str | None:
        return self._generated_prompt

    @property
    def creation_timestamp(self) -> datetime:
        return self._creation_timestamp

    @property
    def last_updated(self) -> datetime:
        return self._last_updated

    @property
    def check_result(self) -> QualityCheckResult | None:
        return self._check_result

    def set_request(self, request: QualityCheckRequest) -> None:
        """品質チェック要求を設定"""
        if self._request is not None:
            msg = "Request already set for this prompt"
            raise ValueError(msg)

        self._request = request
        self._last_updated = datetime.now(timezone.utc)
        self._domain_events.append("request_set")

    def set_episode_plot(self, plot: EnhancedEpisodePlot) -> None:
        """エピソードプロットを設定"""
        if self._episode_plot is not None:
            msg = "Episode plot already set for this prompt"
            raise ValueError(msg)

        self._episode_plot = plot
        self._last_updated = datetime.now(timezone.utc)
        self._domain_events.append("plot_set")

    def set_check_criteria(self, criteria: list[QualityCriterion]) -> None:
        """品質チェック基準を設定"""
        if not criteria:
            msg = "Check criteria cannot be empty"
            raise ValueError(msg)

        self._check_criteria = criteria.copy()
        self._last_updated = datetime.now(timezone.utc)
        self._domain_events.append("criteria_set")

    def generate_prompt(self, prompt_template: str) -> str:
        """品質チェックプロンプトを生成"""
        if not self._request:
            msg = "Request must be set before generating prompt"
            raise ValueError(msg)

        if not self._episode_plot:
            msg = "Episode plot must be set before generating prompt"
            raise ValueError(msg)

        if not self._check_criteria:
            msg = "Check criteria must be set before generating prompt"
            raise ValueError(msg)

        # プロンプト生成ロジック
        self._generated_prompt = self._build_quality_check_prompt(prompt_template)
        self._last_updated = datetime.now(timezone.utc)
        self._domain_events.append("prompt_generated")

        return self._generated_prompt

    def _build_quality_check_prompt(self, template: str) -> str:
        """品質チェックプロンプトを構築"""
        # テンプレート変数の置換
        context = {
            "episode_number": self._request.episode_number,
            "project_name": self._request.project_name,
            "check_level": self._request.check_level.value,
            "plot_summary": self._generate_plot_summary(),
            "check_criteria_list": self._format_check_criteria(),
            "quality_focus_areas": ", ".join(self._request.get_quality_focus_areas()),
            "max_prompt_length": self._request.get_max_prompt_length(),
            "estimated_duration": self._request.check_level.get_estimated_duration_minutes(),
        }

        # テンプレート展開
        formatted_prompt = template.format(**context)

        # 長さ制限の確認・調整
        max_length = self._request.get_max_prompt_length()
        if len(formatted_prompt) > max_length:
            formatted_prompt = self._truncate_prompt(formatted_prompt, max_length)

        return formatted_prompt

    def _generate_plot_summary(self) -> str:
        """プロットサマリーを生成"""
        if not self._episode_plot:
            return ""

        summary_parts = []

        # 基本情報
        summary_parts.append(
            f"エピソード{self._episode_plot.episode_info.number}: {self._episode_plot.episode_info.title}"
        )
        summary_parts.append(f"テーマ: {self._episode_plot.episode_info.theme}")
        summary_parts.append(f"目的: {self._episode_plot.episode_info.purpose}")

        # 構造情報
        if self._episode_plot.story_structure:
            summary_parts.append("構造: 三幕構成")
            summary_parts.append(f"シーン数: {self._episode_plot.story_structure.get_total_scene_count()}")

        # キャラクター情報
        if self._episode_plot.characters:
            char_names = [char.name for char in self._episode_plot.characters.values()]
            summary_parts.append(f"主要キャラクター: {', '.join(char_names[:3])}")

        return "\n".join(summary_parts)

    def _format_check_criteria(self) -> str:
        """チェック基準をフォーマット"""
        criteria_lines = []
        for i, criterion in enumerate(self._check_criteria, 1):
            criteria_lines.append(f"{i}. {criterion.name} (重み: {criterion.weight:.2f})\n   {criterion.description}")

        return "\n".join(criteria_lines)

    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """プロンプトを制限長に調整"""
        if len(prompt) <= max_length:
            return prompt

        # 重要な部分を残して調整
        lines = prompt.split("\n")
        truncated_lines = []
        current_length = 0

        for line in lines:
            if current_length + len(line) + 1 <= max_length - 100:  # バッファを残す:
                truncated_lines.append(line)
                current_length += len(line) + 1
            else:
                break

        truncated_lines.append("\n...[内容を制限長に調整しました]...")
        return "\n".join(truncated_lines)

    def set_check_result(self, result: QualityCheckResult) -> None:
        """品質チェック結果を設定"""
        self._check_result = result
        self._last_updated = datetime.now(timezone.utc)
        self._domain_events.append("result_set")

    def is_ready_for_generation(self) -> bool:
        """プロンプト生成準備完了判定"""
        return self._request is not None and self._episode_plot is not None and len(self._check_criteria) > 0

    def get_domain_events(self) -> list[str]:
        """ドメインイベントを取得"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """ドメインイベントをクリア"""
        self._domain_events.clear()

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換"""
        return {
            "prompt_id": str(self._prompt_id),
            "request": {
                "episode_number": self._request.episode_number if self._request else None,
                "project_name": self._request.project_name if self._request else None,
                "check_level": self._request.check_level.value if self._request else None,
            },
            "criteria_count": len(self._check_criteria),
            "generated_prompt_length": len(self._generated_prompt) if self._generated_prompt else 0,
            "creation_timestamp": self._creation_timestamp.isoformat(),
            "last_updated": self._last_updated.isoformat(),
            "has_result": self._check_result is not None,
            "overall_score": self._check_result.overall_score if self._check_result else None,
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, QualityCheckPrompt):
            return False
        return self._prompt_id == other._prompt_id

    def __hash__(self) -> int:
        return hash(self._prompt_id)


class QualityCheckPromptGenerator:
    """品質チェックプロンプト生成ドメインサービス

    SPEC-STAGE5-SEPARATION対応
    Stage4完了済みプロットから品質チェック用プロンプトを生成する
    """

    def __init__(self) -> None:
        """ジェネレーターの初期化"""
        self._default_template = self._create_default_template()

    def generate_prompt(
        self,
        request: QualityCheckRequest,
        episode_plot: EnhancedEpisodePlot,
        criteria: list[QualityCriterion] | None = None,
    ) -> QualityCheckPrompt:
        """品質チェックプロンプトを生成

        Args:
            request: 品質チェック要求
            episode_plot: エピソードプロット
            criteria: チェック基準（Noneの場合はレベルに応じて自動選択）

        Returns:
            生成されたプロンプトEntity

        Raises:
            ValueError: プロット完成度不足、または不正な要求
        """
        # プロット完成度の検証
        validation_result = self.validate_plot_completeness(episode_plot)
        if not validation_result.is_valid:
            msg = f"Plot completeness validation failed: {validation_result.error_message}"
            raise ValueError(msg)

        # チェック基準の決定
        if criteria is None:
            criteria = self._select_criteria_by_level(request.check_level)

        # プロンプト生成
        prompt = QualityCheckPrompt()
        prompt.set_request(request)
        prompt.set_episode_plot(episode_plot)
        prompt.set_check_criteria(criteria)

        # プロンプトテンプレートの取得・適用
        template = self._get_template_by_level(request.check_level)
        prompt.generate_prompt(template)

        return prompt

    def validate_plot_completeness(self, episode_plot: EnhancedEpisodePlot) -> "PlotValidationResult":
        """プロット完成度の検証

        Args:
            episode_plot: 検証対象のエピソードプロット

        Returns:
            検証結果
        """
        validation_errors = []

        # 基本情報の確認
        if not episode_plot.episode_info:
            validation_errors.append("Episode info is missing")
        else:
            if not episode_plot.episode_info.title.strip():
                validation_errors.append("Episode title is empty")
            if not episode_plot.episode_info.theme.strip():
                validation_errors.append("Episode theme is empty")

        # Stage4必須要素の確認
        stage4_requirements = [
            ("foreshadowing_integration", "Foreshadowing integration"),
            ("technical_elements", "Technical elements"),
            ("thematic_elements", "Thematic elements"),
        ]

        for attr_name, display_name in stage4_requirements:
            if not hasattr(episode_plot, attr_name) or not getattr(episode_plot, attr_name):
                validation_errors.append(f"{display_name} is missing (Stage4 requirement)")

        # 構造の確認
        if not episode_plot.story_structure:
            validation_errors.append("Story structure is missing")

        is_valid = len(validation_errors) == 0
        error_message = "; ".join(validation_errors) if validation_errors else None

        return PlotValidationResult(is_valid=is_valid, error_message=error_message)

    def _select_criteria_by_level(self, check_level: QualityCheckLevel) -> list[QualityCriterion]:
        """チェックレベルに応じた基準選択（importlibで遅延ロード）"""
        mod = importlib.import_module("noveler.domain.value_objects.quality_check_level")
        get_claude_optimized_criteria = mod.get_claude_optimized_criteria
        get_standard_quality_criteria = mod.get_standard_quality_criteria

        if check_level == QualityCheckLevel.CLAUDE_OPTIMIZED:
            return get_claude_optimized_criteria()
        if check_level in [QualityCheckLevel.STANDARD, QualityCheckLevel.COMPREHENSIVE]:
            return get_standard_quality_criteria()
        # BASIC
        # 基本的な5基準のみ
        standard = get_standard_quality_criteria()
        return standard[:5]

    def _get_template_by_level(self, check_level: QualityCheckLevel) -> str:
        """チェックレベル別テンプレート取得"""
        templates = {
            QualityCheckLevel.BASIC: self._create_basic_template(),
            QualityCheckLevel.STANDARD: self._create_standard_template(),
            QualityCheckLevel.COMPREHENSIVE: self._create_comprehensive_template(),
            QualityCheckLevel.CLAUDE_OPTIMIZED: self._create_claude_optimized_template(),
        }

        return templates.get(check_level, self._default_template)

    def _create_default_template(self) -> str:
        """デフォルトプロンプトテンプレート"""
        return """# 話別プロット品質チェック

## エピソード情報
- エピソード番号: {episode_number}
- プロジェクト名: {project_name}
- チェックレベル: {check_level}

## プロット概要
{plot_summary}

## 品質チェック基準
{check_criteria_list}

## チェック要求
以下の基準に基づいて、このエピソードプロットの品質を詳細に分析してください：

重点チェック領域: {quality_focus_areas}

推定所要時間: {estimated_duration}分
最大プロンプト長: {max_prompt_length}文字
"""

    def _create_basic_template(self) -> str:
        """基本レベルテンプレート"""
        return """# 話別プロット基本品質チェック

エピソード{episode_number}「{project_name}」の基本品質チェックを実施してください。

{plot_summary}

## チェック項目
{check_criteria_list}

基本的な整合性とストーリー構造を中心に評価し、改善点があれば具体的に指摘してください。
"""

    def _create_standard_template(self) -> str:
        """標準レベルテンプレート"""
        return """# 話別プロット標準品質チェック

## 対象エピソード
エピソード{episode_number}: {project_name}

## プロット概要
{plot_summary}

## 品質評価基準
{check_criteria_list}

## チェック指示
以下の観点から総合的に評価してください：
- ストーリー構造の論理性
- キャラクター行動の一貫性
- 感情変化の自然さ
- 技術要素の統合度
- 読者エンゲージメント

各基準について0-100点で採点し、具体的な改善提案を含めてください。
"""

    def _create_comprehensive_template(self) -> str:
        """包括レベルテンプレート"""
        return """# 話別プロット包括的品質チェック

## エピソード詳細情報
- 番号: {episode_number}
- プロジェクト: {project_name}
- チェックレベル: 包括的分析

## プロット詳細
{plot_summary}

## 評価基準（重み付き）
{check_criteria_list}

## 包括的分析要求

### 1. 構造分析
- 三幕構成の完成度
- シーン遷移の自然さ
- 伏線・回収バランス

### 2. キャラクター分析
- 行動動機の合理性
- 成長アークの完成度
- 対話の自然さ

### 3. 感情・テーマ分析
- 感情変化の深度
- テーマ表現の効果性
- 読者共感度

### 4. 技術・世界観分析
- 世界観整合性
- 技術要素統合度
- 設定活用度

各項目について詳細分析と数値評価を行い、優先度付き改善提案を提供してください。

重点領域: {quality_focus_areas}
推定時間: {estimated_duration}分
"""

    def _create_claude_optimized_template(self) -> str:
        """Claude Code最適化テンプレート"""
        return """# Claude Code最適化品質チェック

## エピソード情報
- エピソード番号: {episode_number}
- プロジェクト名: {project_name}
- 最適化レベル: Claude Code特化

## プロット概要
{plot_summary}

## Claude Code特化評価基準
{check_criteria_list}

## 最適化分析要求

### 構造化分析
プロットの構造を以下の形式で分析してください：

**整合性評価（0-100点）**
- 全体論理性: [点数] - [具体的評価]
- キャラクター一貫性: [点数] - [具体的評価]
- 感情アーク完成度: [点数] - [具体的評価]

**Claude可読性評価**
- 文脈明確性: [評価]
- 構造化表現: [評価]
- 分析しやすさ: [評価]

### 改善提案
優先度順に3-5項目の具体的改善提案を提示してください。

### 総合評価
- 総合スコア: [0-100点]
- Claude Code適性: [高/中/低]
- 推奨次アクション: [具体的推奨]

重点領域: {quality_focus_areas}
制限時間: {estimated_duration}分
"""


@dataclass
class PlotValidationResult:
    """プロット検証結果Value Object"""

    is_valid: bool
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """警告メッセージを追加"""
        self.warnings.append(message)

    def has_warnings(self) -> bool:
        """警告の存在確認"""
        return len(self.warnings) > 0
