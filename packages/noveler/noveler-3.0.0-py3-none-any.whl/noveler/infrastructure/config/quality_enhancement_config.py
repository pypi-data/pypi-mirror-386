#!/usr/bin/env python3
"""品質記録活用システム設定
B50_DDD設計ガイド準拠
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class QualityEnhancementConfig:
    """品質記録活用システムの設定"""

    # 機能の有効化
    enabled: bool = True
    auto_save: bool = True

    # 学習データの設定
    min_entries_for_analysis: int = 3
    max_suggestions: int = 5

    # ファイル保存設定
    quality_record_filename: str = "品質記録_AI学習用.yaml"
    learning_sessions_filename: str = "学習セッション記録.yaml"

    # 改善提案の設定
    suggestion_confidence_threshold: float = 0.7
    suggestion_priority_levels: list[str] = None

    # トレンド分析の設定
    trend_window_size: int = 10  # 直近何話分を分析対象とするか
    improvement_threshold: float = 5.0  # 改善とみなす%

    def __post_init__(self) -> None:
        if self.suggestion_priority_levels is None:
            self.suggestion_priority_levels = ["high", "medium", "low"]

    @classmethod
    def load_from_project(cls, project_path: Path) -> "QualityEnhancementConfig":
        """プロジェクト設定から読み込む"""
        config_file = project_path / ".novel" / "quality_enhancement.yaml"

        if config_file.exists():
            with Path(config_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls(**data)

        # デフォルト設定を返す
        return cls()

    def should_show_suggestions(self, quality_score: float) -> bool:
        """改善提案を表示すべきかどうか"""
        # スコアが80点未満の場合は提案を表示
        return self.enabled and quality_score < 80.0

    def should_save_learning_data(self) -> bool:
        """学習データを保存すべきかどうか"""
        return self.enabled and self.auto_save
