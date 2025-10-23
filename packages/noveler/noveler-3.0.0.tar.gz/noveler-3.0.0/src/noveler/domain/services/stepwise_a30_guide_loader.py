#!/usr/bin/env python3

"""Domain.services.stepwise_a30_guide_loader
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""段階的A30ガイド読み込みサービス

SPEC-A30-STEPWISE-001に基づく段階的A30ガイド読み込み機能の実装。
"""



from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from noveler.domain.entities.a30_guide_content import A30GuideContent
from noveler.domain.value_objects.writing_phase import WritingPhase

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_interface import ILogger

# B20準拠: LoggerはDI注入されたものを使用
# logger = self._logger  # TODO: DI Container実装で修正


class StepwiseA30GuideLoader:
    """段階的A30ガイド読み込みサービス

    執筆フェーズに応じて必要なA30ガイドコンテンツのみを読み込む
    """

    def __init__(self, logger: ILogger, guide_root_path: Path | None = None, config_service: object | None = None) -> None:
        """初期化

        Args:
            guide_root_path: ガイドファイル格納ディレクトリのパス
            config_service: 設定サービス（B20準拠）
        """
        self._logger = logger
        # A30ガイドファイルはarchiveに移動されているため、パスを更新
        self._guide_root_path = (
            guide_root_path or Path(__file__)  # TODO: IPathServiceを使用するように修正.parent.parent.parent.parent / "docs" / "archive" / "A30_legacy"
        )
        self._config_service = config_service
        self._fallback_content = self._create_fallback_content()

    def load_for_phase(self, phase: WritingPhase | str) -> A30GuideContent:
        """指定フェーズに応じたA30ガイドコンテンツを読み込み

        Args:
            phase: 執筆フェーズまたはフェーズ文字列

        Returns:
            A30GuideContent: 読み込まれたガイドコンテンツ

        Raises:
            ValueError: 不正なフェーズが指定された場合
        """
        # 文字列の場合はWritingPhaseに変換
        if isinstance(phase, str):
            try:
                phase = WritingPhase.from_string(phase)
            except ValueError:
                error_msg = f"Unsupported writing phase: {phase}"
                raise ValueError(error_msg) from None

        try:
            match phase:
                case WritingPhase.DRAFT:
                    return self._load_draft_content()
                case WritingPhase.REFINEMENT:
                    return self._load_refinement_content()
                case WritingPhase.TROUBLESHOOTING:
                    return self._load_troubleshooting_content()
                case _:
                    error_msg = f"Unsupported writing phase: {phase}"
                    raise ValueError(error_msg)

        except Exception as e:
            self._logger.warning("ガイド読み込み失敗、フォールバックを使用: %s", e)
            return self._get_fallback_content_for_phase(phase)

    def _load_draft_content(self) -> A30GuideContent:
        """初稿フェーズ用コンテンツ読み込み"""
        master_guide = self._load_yaml_file("A30_執筆ガイド.yaml")

        return A30GuideContent(master_guide=master_guide, phase=WritingPhase.DRAFT)

    def _load_refinement_content(self) -> A30GuideContent:
        """仕上げフェーズ用コンテンツ読み込み"""
        master_guide = self._load_yaml_file("A30_執筆ガイド.yaml")
        detailed_rules = self._load_yaml_file("A30_執筆ガイド（詳細ルール集）.yaml")
        quality_checklist = self._load_yaml_file("A30_執筆ガイド（ステージ別詳細チェック項目）.yaml")

        return A30GuideContent(
            master_guide=master_guide,
            detailed_rules=detailed_rules,
            quality_checklist=quality_checklist,
            phase=WritingPhase.REFINEMENT,
        )

    def _load_troubleshooting_content(self) -> A30GuideContent:
        """トラブルシューティングフェーズ用コンテンツ読み込み"""
        master_guide = self._load_yaml_file("A30_執筆ガイド.yaml")
        troubleshooting_guide = self._load_yaml_file("A30_執筆ガイド（シューティング事例集）.yaml")

        return A30GuideContent(
            master_guide=master_guide, troubleshooting_guide=troubleshooting_guide, phase=WritingPhase.TROUBLESHOOTING
        )

    def _load_yaml_file(self, filename: str) -> dict[str, Any]:
        """YAMLファイルを読み込み

        Args:
            filename: ファイル名

        Returns:
            dict[str, Any]: 読み込まれたYAMLデータ

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            yaml.YAMLError: YAML解析に失敗した場合
        """
        file_path = self._guide_root_path / filename

        if not file_path.exists():
            error_msg = f"ガイドファイルが見つかりません: {file_path}"
            raise FileNotFoundError(error_msg)

        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                error_msg = f"空のYAMLファイル: {file_path}"
                raise ValueError(error_msg)

            return data

        except yaml.YAMLError as e:
            error_msg = f"YAML解析エラー {file_path}: {e}"
            raise yaml.YAMLError(error_msg) from e

    def _get_fallback_content_for_phase(self, phase: WritingPhase) -> A30GuideContent:
        """フォールバック用コンテンツ取得

        Args:
            phase: 対象フェーズ

        Returns:
            A30GuideContent: フォールバック用コンテンツ
        """
        fallback_master = {**self._fallback_content, "metadata": {"source": "fallback", "phase": phase.value}}

        # フェーズ別の追加コンテンツ
        additional_content = {}
        if phase == WritingPhase.TROUBLESHOOTING:
            additional_content["troubleshooting_guide"] = {
                "common_issues": ["文章の冗長性", "キャラクターの一貫性", "プロットの進行"],
                "solutions": ["簡潔な表現を心がける", "キャラクター設定を再確認", "話の流れを見直す"],
                "fallback": True,
            }
        elif phase == WritingPhase.REFINEMENT:
            additional_content["detailed_rules"] = {
                "style_guide": ["読みやすさ重視", "適切な改行"],
                "quality_standards": ["誤字脱字チェック", "論理的構成"],
                "fallback": True,
            }
            additional_content["quality_checklist"] = {
                "structure_check": ["論理的構成", "段落分割"],
                "style_check": ["表現の一貫性", "適切な語彙選択"],
                "fallback": True,
            }

        return A30GuideContent(
            master_guide=fallback_master,
            troubleshooting_guide=additional_content.get("troubleshooting_guide"),
            detailed_rules=additional_content.get("detailed_rules"),
            quality_checklist=additional_content.get("quality_checklist"),
            phase=phase,
        )

    def _create_fallback_content(self) -> dict[str, Any]:
        """フォールバック用の最小コンテンツ作成

        Returns:
            dict[str, Any]: 最小のA30ガイドコンテンツ
        """
        return {
            "metadata": {"version": "fallback", "purpose": "最小フォールバック用A30ガイド"},
            "rules": [
                "視点統一（1シーン1視点）",
                "話別プロットの改変禁止",
                "世界観・キャラクター設定の矛盾禁止",
                "各話の終わりに必ず引きを設定",
            ],
            "stepwise_writing_system": {
                "methodology": "骨格→肉付け→描写強化→調整→仕上げ",
                "stages": {
                    "stage1": {"name": "骨格構築"},
                    "stage2": {"name": "基本幹構築"},
                    "stage3": {"name": "描写強化"},
                    "stage4": {"name": "調整"},
                    "stage5": {"name": "仕上げ"},
                },
            },
        }
