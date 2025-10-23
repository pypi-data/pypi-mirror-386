"""Domain.services.configuration_loader_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""Domain-level configuration loading without UI side effects."""

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectSettingsBundle:
    """プロジェクト設定バンドル"""

    character_voice_patterns: dict[str, Any]
    quality_rules_summary: dict[str, Any]
    emotion_expression_rules: str
    dialogue_ratio_targets: str
    character_interaction_requirements: str
    explanation_limits: str
    quantitative_check_criteria: dict[str, Any]
    quality_scoring_rubric: dict[str, Any]
    quality_rules_application: dict[str, Any]


class ConfigurationLoaderService:
    """設定ファイル読み込みサービス

    キャラクター口調辞書、執筆品質ルール等を読み込み、
    プロンプトテンプレートで使用可能な形式に変換する。
    """

    def __init__(self, project_root: str | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートディレクトリ。Noneの場合は自動検出
        """
        self._project_root = Path(project_root)  # TODO: IPathServiceを使用するように修正 if project_root else self._detect_project_root()
        self._log_messages: list[str] = []

    @property
    def log_messages(self) -> list[str]:
        """Return accumulated diagnostic messages."""

        return list(self._log_messages)

    def _detect_project_root(self) -> Path:
        """プロジェクトルートディレクトリを自動検出"""
        current = Path.cwd()
        for path in [current, *list(current.parents)]:
            if (path / "プロジェクト設定.yaml").exists() or (path / "30_設定集").exists():
                return path
        return current

    def load_project_settings(self) -> ProjectSettingsBundle:
        """プロジェクト設定一式を読み込み

        Returns:
            ProjectSettingsBundle: 全設定データのバンドル

        Raises:
            FileNotFoundError: 必須設定ファイルが存在しない
            yaml.YAMLError: YAML解析エラー
        """
        try:
            settings_dir = self._project_root / "30_設定集"
            if not settings_dir.exists():
                settings_dir = self._project_root / "settings"
            if not settings_dir.exists():
                settings_dir = self._project_root
            character_voice = self._load_character_voice_patterns(settings_dir)
            quality_rules = self._load_quality_rules(settings_dir)
            emotion_rules_str = self._format_emotion_expression_rules(quality_rules)
            dialogue_targets_str = self._format_dialogue_ratio_targets(quality_rules)
            interaction_reqs_str = self._format_character_interaction_requirements(quality_rules)
            explanation_limits_str = self._format_explanation_limits(quality_rules)
            return ProjectSettingsBundle(
                character_voice_patterns=character_voice,
                quality_rules_summary=quality_rules,
                emotion_expression_rules=emotion_rules_str,
                dialogue_ratio_targets=dialogue_targets_str,
                character_interaction_requirements=interaction_reqs_str,
                explanation_limits=explanation_limits_str,
                quantitative_check_criteria=quality_rules.get("quantitative_checks", {}),
                quality_scoring_rubric=quality_rules.get("quality_scoring", {}),
                quality_rules_application=quality_rules.get("genre_crossing_rules", {}),
            )
        except Exception as e:
            self._log_error(f"設定ファイル読み込みエラー: {e}")
            return self._create_fallback_settings()

    def _load_character_voice_patterns(self, settings_dir: Path) -> dict[str, Any]:
        """キャラクター口調辞書を読み込み"""
        candidates = [
            settings_dir / "キャラクター口調辞書.yaml",
            settings_dir / "character_voices.yaml",
            self._project_root / "templates" / "キャラクター口調辞書テンプレート.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                self._log_info(f"キャラクター口調辞書読み込み: {candidate}")
                with candidate.open(encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
        self._log_info("キャラクター口調辞書が見つかりません。テンプレートを使用します。")
        return {}

    def _load_quality_rules(self, settings_dir: Path) -> dict[str, Any]:
        """執筆品質ルールを読み込み"""
        # Honour template override for quality rules filename if available
        try:
            _cm_mod = importlib.import_module('noveler.infrastructure.factories.configuration_service_factory')
            get_configuration_manager = getattr(_cm_mod, 'get_configuration_manager')
            _cm = get_configuration_manager()
            _qr_name = _cm.get_file_template("quality_rules")
        except Exception:
            _qr_name = "執筆品質ルール.yaml"

        candidates = [
            settings_dir / _qr_name,
            settings_dir / "quality_rules.yaml",
            self._project_root / "templates" / "執筆品質ルールテンプレート.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                self._log_info(f"執筆品質ルール読み込み: {candidate}")
                with candidate.open(encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
        self._log_info("執筆品質ルールが見つかりません。テンプレートを使用します。")
        return {}

    def _format_emotion_expression_rules(self, quality_rules: dict[str, Any]) -> str:
        """感情表現ルールをプロンプト用文字列に整形"""
        emotion_rule = quality_rules.get("genre_crossing_rules", {}).get("emotional_expression", {})
        if not emotion_rule:
            return "感情三層表現（身体反応+比喩+内面独白）を最低3回実装してください。"
        min_count = emotion_rule.get("minimum_count_per_episode", 3)
        components = emotion_rule.get("components", [])
        rule_text = "【感情三層表現ルール】\n"
        rule_text += f"- 必須回数: {min_count}回/話\n"
        rule_text += f"- 構成要素: {', '.join(components)}\n"
        examples = emotion_rule.get("examples", {})
        if examples:
            rule_text += "- 実装例:\n"
            for key, example in examples.items():
                if isinstance(example, dict):
                    rule_text += f"  {key}: {example.get('body', '')}, {example.get('metaphor', '')}, {example.get('inner', '')}\n"
        return rule_text

    def _format_dialogue_ratio_targets(self, quality_rules: dict[str, Any]) -> str:
        """会話比率ルールをプロンプト用文字列に整形"""
        dialogue_rule = quality_rules.get("genre_crossing_rules", {}).get("dialogue_ratio", {})
        if not dialogue_rule:
            return "会話比率: 対話60%、独白40%を目標としてください。"
        ratios = dialogue_rule.get("target_ratios", {})
        dialogue_pct = ratios.get("dialogue", 60)
        monologue_pct = ratios.get("monologue", 40)
        return f"【会話比率管理】\n- 対話: {dialogue_pct}%\n- 独白・地の文: {monologue_pct}%\n- 測定方法: 文字数ベース"

    def _format_character_interaction_requirements(self, quality_rules: dict[str, Any]) -> str:
        """キャラクター相互作用要求をプロンプト用文字列に整形"""
        rules = quality_rules.get("character_focused_rules", {})
        sub_char_rule = rules.get("sub_character_appearance", {})
        relationship_rule = rules.get("relationship_dialogue", {})
        text = "【キャラクター相互作用要求】\n"
        if sub_char_rule:
            min_scenes = sub_char_rule.get("minimum_scenes_per_episode", 2)
            text += f"- サブキャラ能動登場: {min_scenes}シーン/話\n"
        if relationship_rule:
            min_count = relationship_rule.get("minimum_count_per_episode", 3)
            text += f"- 関係性雑談: {min_count}回/話\n"
        if not sub_char_rule and (not relationship_rule):
            text += "- サブキャラクターの能動的関与: 2シーン/話\n- 関係性を示す雑談: 3回/話"
        return text

    def _format_explanation_limits(self, quality_rules: dict[str, Any]) -> str:
        """説明制限ルールをプロンプト用文字列に整形"""
        explanation_rule = quality_rules.get("genre_crossing_rules", {}).get("explanation_balance", {})
        if not explanation_rule:
            return "情報解説は2文以内とし、その後は必ずキャラクターの反応または会話に変換してください。"
        rules = explanation_rule.get("rules", {})
        max_sentences = rules.get("max_consecutive_sentences", 2)
        follow_up = rules.get("required_follow_up", "キャラクターの反応または会話")
        return f"【説明制限ルール】\n- 連続説明文: {max_sentences}文以内\n- 必須後続: {follow_up}\n- 違反時: 即座に会話・行動に転換"

    def _create_fallback_settings(self) -> ProjectSettingsBundle:
        """フォールバック用の最小設定を作成"""
        return ProjectSettingsBundle(
            character_voice_patterns={},
            quality_rules_summary={},
            emotion_expression_rules="感情三層表現（身体反応+比喩+内面独白）を最低3回実装してください。",
            dialogue_ratio_targets="会話比率: 対話60%、独白40%を目標としてください。",
            character_interaction_requirements="サブキャラクターの能動的関与: 2シーン/話、関係性を示す雑談: 3回/話",
            explanation_limits="情報解説は2文以内とし、その後は必ずキャラクターの反応または会話に変換してください。",
            quantitative_check_criteria={},
            quality_scoring_rubric={},
            quality_rules_application={},
        )

    def _log_info(self, message: str) -> None:
        self._log_messages.append(message)

    def _log_error(self, message: str) -> None:
        self._log_messages.append(message)
