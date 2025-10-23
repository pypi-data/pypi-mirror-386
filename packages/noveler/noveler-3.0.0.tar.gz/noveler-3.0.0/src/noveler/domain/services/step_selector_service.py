#!/usr/bin/env python3

"""Domain.services.step_selector_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""ステップ選択サービス

SPEC-STEPWISE-WRITING-001に基づく正規表現によるステップ選択機能
B20準拠: Functional Core実装（純粋関数）
"""


import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_interface import ILogger



class InvalidStepPatternError(ValueError):
    """無効なステップパターンエラー"""

    def __init__(self,pattern: str, reason: str, logger: ILogger) -> None:
        self._logger = logger
        self.pattern = pattern
        self.reason = reason
        super().__init__(f"無効なステップパターン '{pattern}': {reason}")


class StepSelectorService:
    """ステップ選択サービス

    正規表現による柔軟なステップ選択機能を提供
    B20準拠: Functional Core（副作用なし）
    """

    # ステップエイリアス定義
    STEP_ALIASES: dict[str, str] = {
        # グループエイリアス
        "structure": "0-9",  # 構造設計フェーズ
        "writing": "10-17",  # 執筆実装フェーズ
        "quality": "5-9,13-14",  # 品質関連
        "optimization": "3,11,12",  # 最適化関連
        # 個別エイリアス（わかりやすい名前）
        "scope": "0",  # スコープ定義
        "story": "1",  # 物語構造
        "phase": "2",  # 段階構造
        "section": "3",  # セクション最適化
        "scene": "4",  # シーン設計
        "logic": "5",  # 論理検証
        "character": "6",  # キャラクター一貫性
        "dialogue": "7",  # 会話設計
        "emotion": "8",  # 感情曲線
        "world": "9",  # 世界観構築
        "sensory": "10",  # 五感描写設計
        "props": "11",  # 小道具・世界観設計
        "manuscript": "12",  # 初稿生成
        "length": "13",  # 文字数最適化
        "readability": "14",  # 文体・可読性パス
        "gate": "15",  # 必須品質ゲート
        "certification": "16",  # DOD & KPI統合品質認定
        "publish": "17",  # 公開準備
    }

    # ステップ番号からサービス名へのマッピング（A38ガイド準拠：0-17の18ステップ）
    STEP_SERVICE_MAPPING: dict[int, str] = {
        0: "ScopeDefinerService",                    # STEP 0: スコープ定義
        1: "StoryStructureDesignerService",         # STEP 1: 大骨（章の目的線）
        2: "PhaseStructureDesignerService",         # STEP 2: 中骨（段階目標・行動フェーズ）
        3: "SectionBalanceOptimizerService",        # STEP 3: セクションバランス設計
        4: "SceneBeatDesignerService",              # STEP 4: 小骨（シーン／ビート）
        5: "LogicValidatorService",                 # STEP 5: 論理検証
        6: "CharacterConsistencyService",          # STEP 6: キャラクター一貫性検証
        7: "DialogueDesignerService",              # STEP 7: 会話設計
        8: "EmotionCurveDesignerService",          # STEP 8: 感情曲線
        9: "SceneSettingService",                  # STEP 9: 情景設計
        10: "SensoryDesignService",                # STEP 10: 五感描写設計
        11: "PropsWorldBuildingService",           # STEP 11: 小道具・世界観設計
        12: "ManuscriptGeneratorService",          # STEP 12: 初稿生成
        13: "TextLengthOptimizerService",          # STEP 13: 文字数最適化
        14: "ReadabilityOptimizerService",         # STEP 14: 文体・可読性パス
        15: "QualityGateService",                  # STEP 15: 必須品質ゲート
        16: "QualityCertificationService",         # STEP 16: DOD & KPI統合品質認定
        17: "PublishingPreparationService",        # STEP 17: 公開準備
    }

    # 正規表現マッチング用サービス名パターン（A38ガイド準拠：18ステップ）
    SERVICE_NAME_PATTERNS: dict[str, list[int]] = {
        r".*optimizer": [3, 13, 14],  # SectionBalanceOptimizer, TextLengthOptimizer, ReadabilityOptimizer
        r".*designer": [
            1,  # StoryStructureDesigner
            2,  # PhaseStructureDesigner
            4,  # SceneBeatDesigner
            7,  # DialogueDesigner
            8,  # EmotionCurveDesigner
            10, # SensoryDesigner
        ],
        r".*service": [
            9,  # SceneSettingService
            11, # PropsWorldBuildingService
            15, # QualityGateService
            16, # QualityCertificationService
            17, # PublishingPreparationService
        ],
        r".*validator": [5],  # LogicValidator
        r".*consistency": [6],  # CharacterConsistency
        r".*generator": [12],  # ManuscriptGenerator
        r".*definer": [0],  # ScopeDefiner
        r".*building": [11],  # PropsWorldBuilding
        r".*curve": [8],  # EmotionCurve
        r".*setting": [9],  # SceneSetting
        r".*sensory": [10],  # SensoryDesign
        r".*gate": [15],  # QualityGate
        r".*certification": [16],  # QualityCertification
        r".*preparation": [17],  # PublishingPreparation
    }

    def __init__(self, logger: ILogger) -> None:
        """初期化"""
        self._logger = logger
        self._logger.debug("StepSelectorService initialized")

    def parse_step_pattern(self, pattern: str) -> list[int]:
        """ステップパターンを解析して実行対象ステップリストを生成

        B20準拠: Functional Core（純粋関数）

        Args:
            pattern: ステップパターン文字列

        Returns:
            List[int]: 実行対象ステップリスト（0-17）

        Raises:
            InvalidStepPatternError: 無効なパターンの場合

        Examples:
            >>> service = StepSelectorService()
            >>> service.parse_step_pattern("0-3")
            [0, 1, 2, 3]
            >>> service.parse_step_pattern("structure")
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> service.parse_step_pattern("scope|story")
            [0, 1]
            >>> service.parse_step_pattern(".*optimizer")
            [3, 13, 14]
        """
        if not pattern or not isinstance(pattern, str):
            raise InvalidStepPatternError(pattern, "パターンが空または無効な型です")

        try:
            self._logger.debug(f"Parsing step pattern: {pattern}")

            # 除外パターンの処理
            include_steps, exclude_steps = self._split_exclusion_pattern(pattern)

            # 包含ステップの解析
            selected_steps = self._parse_include_pattern(include_steps)

            # 除外ステップの解析と適用
            if exclude_steps:
                excluded_steps = self._parse_exclude_pattern(exclude_steps)
                selected_steps = [step for step in selected_steps if step not in excluded_steps]

            # 重複除去とソート
            result = sorted(set(selected_steps))

            # 結果の妥当性確認
            self._validate_step_list(result)

            self._logger.debug(f"Pattern '{pattern}' resolved to steps: {result}")
            return result

        except InvalidStepPatternError:
            raise
        except Exception as e:
            raise InvalidStepPatternError(pattern, f"パターン解析エラー: {e!s}")

    def get_service_name(self, step_number: int) -> str:
        """ステップ番号からサービス名を取得

        Args:
            step_number: ステップ番号（0-17）

        Returns:
            str: サービス名

        Raises:
            ValueError: 無効なステップ番号の場合
        """
        if not isinstance(step_number, int) or step_number < 0 or step_number > 17:
            msg = f"無効なステップ番号: {step_number}"
            raise ValueError(msg)

        return self.STEP_SERVICE_MAPPING[step_number]

    def _split_exclusion_pattern(self, pattern: str) -> tuple[str, list[str]]:
        """除外パターンを分離

        Args:
            pattern: 元のパターン文字列

        Returns:
            tuple[包含パターン, 除外パターンリスト]
        """
        parts = pattern.split(",")
        include_parts = []
        exclude_parts = []

        for part in parts:
            part = part.strip()
            if part.startswith("!"):
                exclude_parts.append(part[1:])  # !を除去
            else:
                include_parts.append(part)

        include_pattern = ",".join(include_parts) if include_parts else "0-17"
        return include_pattern, exclude_parts

    def _parse_include_pattern(self, pattern: str, _depth: int = 0) -> list[int]:
        """包含パターンを解析

        Args:
            pattern: 包含パターン文字列
            _depth: 再帰の深度（無限ループ防止）

        Returns:
            List[int]: 選択されたステップリスト
        """
        if _depth > 5:  # 無限ループ防止
            raise InvalidStepPatternError(pattern, "パターンの解析が深すぎます（無限ループの可能性）")

        steps: set[int] = set()

        # カンマ区切りで分割
        parts = [part.strip() for part in pattern.split(",") if part.strip()]

        for part in parts:
            part_steps = self._parse_single_pattern(part, _depth + 1)
            steps.update(part_steps)

        return list(steps)

    def _parse_exclude_pattern(self, exclude_patterns: list[str]) -> set[int]:
        """除外パターンを解析

        Args:
            exclude_patterns: 除外パターンリスト

        Returns:
            Set[int]: 除外対象ステップセット
        """
        excluded_steps: set[int] = set()

        for pattern in exclude_patterns:
            pattern_steps = self._parse_single_pattern(pattern, 0)  # 除外パターンは深度0から開始
            excluded_steps.update(pattern_steps)

        return excluded_steps

    def _parse_single_pattern(self, pattern: str, _depth: int = 0) -> list[int]:
        """単一パターンを解析

        Args:
            pattern: 単一パターン文字列
            _depth: 再帰の深度（無限ループ防止）

        Returns:
            List[int]: 解析されたステップリスト
        """
        # OR演算子の処理
        if "|" in pattern:
            return self._parse_or_pattern(pattern, _depth)

        # 範囲指定の処理（例: 0-3）
        if "-" in pattern and re.match(r"^\d+-\d+$", pattern):
            return self._parse_range_pattern(pattern)

        # 数値の処理
        if pattern.isdigit():
            step_num = int(pattern)
            if 0 <= step_num <= 17:
                return [step_num]
            raise InvalidStepPatternError(pattern, f"ステップ番号は0-17の範囲で指定してください: {step_num}")

        # 「all」パターンの処理
        if pattern.lower() == "all":
            return list(range(18))  # 0-17の全ステップ

        # エイリアスの処理
        if pattern in self.STEP_ALIASES:
            alias_pattern = self.STEP_ALIASES[pattern]
            return self._parse_include_pattern(
                alias_pattern, _depth
            )  # カンマ区切り対応のため_parse_include_patternを使用

        # 正規表現パターンの処理
        return self._parse_regex_pattern(pattern)

    def _parse_or_pattern(self, pattern: str, _depth: int = 0) -> list[int]:
        """OR演算子パターンを解析

        Args:
            pattern: OR演算子を含むパターン（例: "scope|story"）
            _depth: 再帰の深度（無限ループ防止）

        Returns:
            List[int]: 解析されたステップリスト
        """
        steps: set[int] = set()

        parts = pattern.split("|")
        for part in parts:
            part = part.strip()
            if part:
                part_steps = self._parse_single_pattern(part, _depth)
                steps.update(part_steps)

        return list(steps)

    def _parse_range_pattern(self, pattern: str) -> list[int]:
        """範囲パターンを解析

        Args:
            pattern: 範囲パターン（例: "0-3"）

        Returns:
            List[int]: 範囲内のステップリスト
        """
        try:
            start_str, end_str = pattern.split("-")
            start = int(start_str)
            end = int(end_str)

            if start < 0 or end < 0:
                raise InvalidStepPatternError(pattern, "負の数は指定できません")

            if start > end:
                raise InvalidStepPatternError(pattern, f"開始値({start})が終了値({end})より大きいです")

            if end > 17:
                raise InvalidStepPatternError(pattern, f"ステップ番号は17以下で指定してください: {end}")

            return list(range(start, end + 1))

        except ValueError as e:
            raise InvalidStepPatternError(pattern, f"範囲パターンの解析に失敗: {e!s}")

    def _parse_regex_pattern(self, pattern: str) -> list[int]:
        """正規表現パターンを解析

        Args:
            pattern: 正規表現パターン（例: ".*optimizer"）

        Returns:
            List[int]: マッチするステップリスト
        """
        try:
            compiled_regex = re.compile(pattern, re.IGNORECASE)
            matched_steps: set[int] = set()

            # サービス名パターンとのマッチング
            for service_pattern, steps in self.SERVICE_NAME_PATTERNS.items():
                if compiled_regex.match(service_pattern):
                    matched_steps.update(steps)

            # 個別エイリアスとのマッチング
            for alias, alias_pattern in self.STEP_ALIASES.items():
                if compiled_regex.match(alias):
                    alias_steps = self._parse_include_pattern(alias_pattern, 0)  # カンマ区切り対応、深度0から開始
                    matched_steps.update(alias_steps)

            if not matched_steps:
                # 直接的なサービス名マッチングを試行
                for step_num, service_name in self.STEP_SERVICE_MAPPING.items():
                    if compiled_regex.search(service_name.lower()):
                        matched_steps.add(step_num)

            if not matched_steps:
                raise InvalidStepPatternError(pattern, "正規表現にマッチするステップが見つかりません")

            return list(matched_steps)

        except re.error as e:
            raise InvalidStepPatternError(pattern, f"無効な正規表現: {e!s}")

    def _validate_step_list(self, steps: list[int]) -> None:
        """ステップリストの妥当性確認

        Args:
            steps: ステップリスト

        Raises:
            InvalidStepPatternError: 無効なステップが含まれる場合
        """
        if not steps:
            msg = ""
            raise InvalidStepPatternError(msg, "実行対象ステップが選択されていません")

        for step in steps:
            if not isinstance(step, int) or step < 0 or step > 17:
                raise InvalidStepPatternError(str(step), f"無効なステップ番号: {step}")

    def get_pattern_examples(self) -> dict[str, list[int]]:
        """パターン例とその結果を取得

        Returns:
            Dict[str, List[int]]: パターン例辞書
        """
        return {
            # 基本パターン
            "0": [0],
            "17": [17],
            "0-3": [0, 1, 2, 3],
            "10-12": [10, 11, 12],
            "all": list(range(18)),  # 全ステップ（0-17）
            # エイリアス
            "scope": [0],
            "structure": list(range(10)),
            "writing": list(range(10, 18)),
            "quality": [5, 6, 7, 8, 9, 15, 16],
            # OR演算子
            "scope|story": [0, 1],
            "manuscript|gate": [12, 15],
            # カンマ区切り
            "0,5,10": [0, 5, 10],
            "0-2,12-14": [0, 1, 2, 12, 13, 14],
            # 正規表現
            ".*optimizer": [3, 13, 14],
            ".*designer": [1, 2, 4, 7, 8, 10],
            ".*service": [9, 11, 15, 16, 17],
            # 除外パターン
            "0-5,!3": [0, 1, 2, 4, 5],
            "structure,!quality": [0, 1, 2, 3, 4],
        }

    def validate_pattern(self, pattern: str) -> bool:
        """パターンの妥当性を検証

        Args:
            pattern: 検証対象パターン

        Returns:
            bool: パターンが有効かどうか
        """
        try:
            self.parse_step_pattern(pattern)
            return True
        except InvalidStepPatternError:
            return False


def create_step_selector() -> StepSelectorService:
    """StepSelectorServiceのファクトリ関数

    Returns:
        StepSelectorService: 初期化済みのインスタンス
    """
    return StepSelectorService()
