"""品質基準ファクトリー - アプリケーション層

ジャンルと執筆レベルに応じた品質基準を生成する
"""

from noveler.domain.value_objects.quality_standards import Genre, QualityStandard, QualityThreshold, WriterLevel


class QualityStandardFactory:
    """品質基準を生成するファクトリー"""

    @staticmethod
    def create_standard(writer_level: WriterLevel, genre: Genre) -> QualityStandard:
        """執筆レベルとジャンルに応じた品質基準を生成

        Args:
            writer_level: 執筆者レベル
            genre: 小説ジャンル

        Returns:
            QualityStandard: 生成された品質基準
        """
        # 基本閾値の定義
        base_thresholds = QualityStandardFactory._get_base_thresholds(writer_level)

        # ジャンル別の調整
        adjusted_thresholds = QualityStandardFactory._adjust_for_genre(
            base_thresholds,
            genre,
        )

        # 重み係数の設定
        weight_adjustments = QualityStandardFactory._get_weight_adjustments(
            writer_level,
            genre,
        )

        return QualityStandard(
            writer_level=writer_level,
            genre=genre,
            thresholds=adjusted_thresholds,
            weight_adjustments=weight_adjustments,
        )

    @staticmethod
    def _get_base_thresholds(writer_level: WriterLevel) -> dict[str, QualityThreshold]:
        """執筆レベルに応じた基本閾値を取得"""
        # レベル別の基準値(最小、目標、優秀)
        level_values = {
            WriterLevel.BEGINNER: {
                "overall": (50, 60, 70),
                "readability": (45, 55, 65),
                "composition": (45, 55, 65),
                "style": (50, 60, 70),
                "dialogue": (40, 50, 60),
                "narrative_depth": (40, 50, 60),
            },
            WriterLevel.INTERMEDIATE: {
                "overall": (60, 70, 80),
                "readability": (55, 65, 75),
                "composition": (55, 65, 75),
                "style": (60, 70, 80),
                "dialogue": (50, 60, 70),
                "narrative_depth": (50, 60, 70),
            },
            WriterLevel.ADVANCED: {
                "overall": (70, 80, 90),
                "readability": (65, 75, 85),
                "composition": (65, 75, 85),
                "style": (70, 80, 90),
                "dialogue": (60, 70, 80),
                "narrative_depth": (60, 70, 80),
            },
            WriterLevel.EXPERT: {
                "overall": (75, 85, 95),
                "readability": (70, 80, 90),
                "composition": (70, 80, 90),
                "style": (75, 85, 95),
                "dialogue": (65, 75, 85),
                "narrative_depth": (65, 75, 85),
            },
        }

        thresholds = {}
        for check_type, (min_val, target, excellent) in level_values[writer_level].items():
            thresholds[check_type] = QualityThreshold(min_val, target, excellent)

        return thresholds

    @staticmethod
    def _adjust_for_genre(base_thresholds: dict[str, QualityThreshold], genre: Genre) -> dict[str, QualityThreshold]:
        """ジャンルに応じて閾値を調整"""
        adjustments = {
            Genre.LIGHT_NOVEL: {
                # ライトノベルは会話と読みやすさを重視
                "readability": -5,  # 基準を緩和
                "dialogue": -10,  # 会話多めでもOK
                "style": -5,  # カジュアルな文体OK
            },
            Genre.LITERARY: {
                # 純文学は文体と深度を重視
                "style": +5,  # 高い文体基準
                "narrative_depth": +10,  # 深い内面描写必須
                "dialogue": +5,  # 会話の質も重要
            },
            Genre.MYSTERY: {
                # ミステリーは構成と論理性を重視
                "composition": +5,  # 緻密な構成必須
                "readability": +5,  # 明確な文章必須
            },
            Genre.FANTASY: {
                # ファンタジーは世界観と描写を重視
                "narrative_depth": +5,  # 世界観描写重要
                "style": +3,  # 雰囲気作り重要
            },
            Genre.SF: {
                # SFは論理性と世界観を重視
                "composition": +5,  # 論理的構成
                "narrative_depth": +5,  # 設定説明重要
            },
            Genre.ROMANCE: {
                # 恋愛は感情描写と会話を重視
                "dialogue": -5,  # 会話多めOK
                "narrative_depth": +5,  # 感情描写重要
            },
        }

        # 調整を適用
        adjusted = base_thresholds.copy()
        if genre in adjustments:
            for check_type, adjustment in adjustments[genre].items():
                if check_type in adjusted:
                    threshold = adjusted[check_type]
                    adjusted[check_type] = QualityThreshold(
                        max(0, threshold.minimum_score + adjustment),
                        max(0, threshold.target_score + adjustment),
                        min(100, threshold.excellent_score + adjustment),
                    )

        return adjusted

    @staticmethod
    def _get_weight_adjustments(writer_level: WriterLevel, genre: Genre) -> dict[str, float]:
        """重み係数を設定"""
        # デフォルトの重み
        weights = {
            "readability": 1.0,
            "composition": 1.0,
            "style": 1.0,
            "dialogue": 1.0,
            "narrative_depth": 1.0,
        }

        # ジャンル別の重み調整
        genre_weights = {
            Genre.LIGHT_NOVEL: {
                "readability": 1.2,  # 読みやすさ重視
                "dialogue": 1.3,  # 会話重視
                "style": 0.8,  # 文体は緩め
            },
            Genre.LITERARY: {
                "style": 1.5,  # 文体最重視
                "narrative_depth": 1.5,  # 深度最重視
                "readability": 0.8,  # 難解でもOK
            },
            Genre.MYSTERY: {
                "composition": 1.5,  # 構成最重視
                "readability": 1.2,  # 明確さ重視
            },
            Genre.FANTASY: {
                "narrative_depth": 1.3,  # 世界観描写重視
                "style": 1.2,  # 雰囲気重視
            },
        }

        # 初心者は基礎項目の重みを増やす
        if writer_level == WriterLevel.BEGINNER:
            weights["readability"] *= 1.2
            weights["style"] *= 1.2

        # ジャンル別重みを適用
        if genre in genre_weights:
            for check_type, multiplier in genre_weights[genre].items():
                weights[check_type] *= multiplier

        return weights
