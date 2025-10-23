#!/usr/bin/env python3
"""
Stage Name Mapper - 10段階執筆ステージ名マッピング

Purpose: ステージ名とステージ番号の双方向変換
Architecture: Presentation Layer Helper
"""

from typing import ClassVar


class StageNameMapper:
    """10段階執筆ステージ名とステージ番号のマッピング"""

    # ステージ名 → ステージ番号マッピング
    STAGE_NAME_TO_NUMBER: ClassVar[dict[str, int]] = {
        "context_extraction": 1,
        "plot_analysis": 2,
        "character_consistency": 3,
        "scene_design": 4,
        "dialogue_design": 5,
        "narrative_structure": 6,
        "emotion_curve_design": 7,
        "sensory_design": 8,
        "manuscript_generation": 9,
        "quality_certification": 10,
    }

    # ステージ番号 → ステージ名マッピング
    STAGE_NUMBER_TO_NAME: ClassVar[dict[int, str]] = {v: k for k, v in STAGE_NAME_TO_NUMBER.items()}

    # 表示名マッピング
    STAGE_DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "context_extraction": "文脈抽出",
        "plot_analysis": "プロット分析",
        "character_consistency": "キャラクター一貫性",
        "scene_design": "シーン設計",
        "dialogue_design": "対話設計",
        "narrative_structure": "物語構造",
        "emotion_curve_design": "感情曲線設計",
        "sensory_design": "感覚描写設計",
        "manuscript_generation": "原稿生成",
        "quality_certification": "品質認証",
    }

    @classmethod
    def get_stage_number(cls, stage_name: str) -> int:
        """ステージ名からステージ番号を取得

        Args:
            stage_name: ステージ名

        Returns:
            int: ステージ番号（1-10）、見つからない場合は0
        """
        return cls.STAGE_NAME_TO_NUMBER.get(stage_name.lower(), 0)

    @classmethod
    def get_stage_name(cls, stage_number: int) -> str | None:
        """ステージ番号からステージ名を取得

        Args:
            stage_number: ステージ番号（1-10）

        Returns:
            Optional[str]: ステージ名、見つからない場合はNone
        """
        return cls.STAGE_NUMBER_TO_NAME.get(stage_number)

    @classmethod
    def get_display_name(cls, stage_name: str) -> str:
        """ステージ名から表示名を取得

        Args:
            stage_name: ステージ名

        Returns:
            str: 日本語表示名
        """
        return cls.STAGE_DISPLAY_NAMES.get(stage_name.lower(), stage_name)

    @classmethod
    def is_valid_stage_name(cls, stage_name: str) -> bool:
        """ステージ名の有効性チェック

        Args:
            stage_name: チェックするステージ名

        Returns:
            bool: 有効な場合True
        """
        return stage_name.lower() in cls.STAGE_NAME_TO_NUMBER

    @classmethod
    def is_valid_stage_number(cls, stage_number: int) -> bool:
        """ステージ番号の有効性チェック

        Args:
            stage_number: チェックするステージ番号

        Returns:
            bool: 有効な場合True（1-10の範囲）
        """
        return 1 <= stage_number <= 10
