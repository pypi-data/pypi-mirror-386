"""執筆レベル判定サービス - ドメインサービス

執筆者の経験値に基づいてレベルを判定する
"""

from typing import Any

from noveler.domain.value_objects.quality_standards import WriterLevel


class WriterLevelService:
    """執筆レベル判定サービス"""

    @staticmethod
    def determine_level(completed_episodes: int, average_quality_score: float) -> WriterLevel:
        """完了エピソード数と平均品質スコアから執筆レベルを判定

        Args:
            completed_episodes: 完了したエピソード数
            average_quality_score: 平均品質スコア(0-100)

        Returns:
            WriterLevel: 判定された執筆レベル
        """
        # エピソード数による基本レベル判定
        if completed_episodes <= 5:
            base_level = WriterLevel.BEGINNER
        elif completed_episodes <= 20:
            base_level = WriterLevel.INTERMEDIATE
        elif completed_episodes <= 50:
            base_level = WriterLevel.ADVANCED
        else:
            base_level = WriterLevel.EXPERT

        # 品質スコアによる調整
        # 平均スコアが高い場合は1段階上のレベルとして扱う
        if average_quality_score >= 85 and base_level != WriterLevel.EXPERT:
            levels = list(WriterLevel)
            current_index = levels.index(base_level)
            return levels[min(current_index + 1, len(levels) - 1)]

        # 平均スコアが低い場合は1段階下のレベルとして扱う
        if average_quality_score < 60 and base_level != WriterLevel.BEGINNER:
            levels = list(WriterLevel)
            current_index = levels.index(base_level)
            return levels[max(current_index - 1, 0)]

        return base_level

    @staticmethod
    def get_level_description(level: WriterLevel) -> str:
        """レベルの説明を取得"""
        descriptions = {
            WriterLevel.BEGINNER: "初心者 - 基礎を学びながら執筆を楽しみましょう",
            WriterLevel.INTERMEDIATE: "中級者 - 安定した品質で執筆できています",
            WriterLevel.ADVANCED: "上級者 - 高い品質を維持しています",
            WriterLevel.EXPERT: "エキスパート - プロ級の執筆技術です",
        }
        return descriptions.get(level, "不明なレベル")

    @staticmethod
    def get_encouragement_message(level: WriterLevel, score: float) -> str:
        """励ましのメッセージを生成"""
        messages: dict[str, Any] = {
            WriterLevel.BEGINNER: {
                True: "素晴らしい進歩です!この調子で続けましょう。",
                False: "少しずつ改善していきましょう。基礎をしっかり身につけることが大切です。",
            },
            WriterLevel.INTERMEDIATE: {
                True: "安定した品質です。より高みを目指しましょう!",
                False: "もう少しで次のレベルです。細部にこだわってみましょう。",
            },
            WriterLevel.ADVANCED: {
                True: "プロ級の品質に近づいています!",
                False: "高い水準を維持しています。さらなる洗練を目指しましょう。",
            },
            WriterLevel.EXPERT: {
                True: "最高水準の執筆です。あなたの作品は多くの読者を魅了するでしょう。",
                False: "最高水準の執筆です。あなたの作品は多くの読者を魅了するでしょう。",
            },
        }

        # レベル別の閾値
        thresholds = {
            WriterLevel.BEGINNER: 60,
            WriterLevel.INTERMEDIATE: 75,
            WriterLevel.ADVANCED: 85,
            WriterLevel.EXPERT: 0,  # EXPERTは常に同じメッセージ
        }

        high_score = score >= thresholds.get(level, 0)
        return messages[level][high_score]

    @staticmethod
    def calculate_progress_to_next_level(completed_episodes: int, current_level: WriterLevel) -> dict[str, Any]:
        """次のレベルまでの進捗を計算

        Args:
            completed_episodes: 完了したエピソード数
            current_level: 現在のレベル

        Returns:
            dict: 進捗情報(current_episodes, next_level_threshold, progress_percentage)
        """
        thresholds = {
            WriterLevel.BEGINNER: 6,  # 次は中級者(6エピソード以上)
            WriterLevel.INTERMEDIATE: 21,  # 次は上級者(21エピソード以上)
            WriterLevel.ADVANCED: 51,  # 次はエキスパート(51エピソード以上)
            WriterLevel.EXPERT: None,  # 最高レベル
        }

        next_threshold = thresholds.get(current_level)
        if next_threshold is None:
            return {"current_episodes": completed_episodes, "next_level_threshold": None, "progress_percentage": 100.0}

        # 現在のレベルの開始エピソード数を計算
        level_starts = {
            WriterLevel.BEGINNER: 0,
            WriterLevel.INTERMEDIATE: 6,
            WriterLevel.ADVANCED: 21,
            WriterLevel.EXPERT: 51,
        }

        current_start = level_starts.get(current_level, 0)
        level_range = next_threshold - current_start
        progress_in_level = completed_episodes - current_start
        progress_percentage = min(100.0, (progress_in_level / level_range) * 100)

        return {
            "current_episodes": completed_episodes,
            "next_level_threshold": next_threshold,
            "progress_percentage": max(0.0, progress_percentage),
        }

    @staticmethod
    def generate_level_statistics(episodes_data: list[dict[str, Any]]) -> dict[str, Any]:
        """エピソードデータからレベル統計を生成

        Args:
            episodes_data: エピソードデータのリスト(各要素は{'quality_score': float}を含む)

        Returns:
            dict: レベル統計情報
        """
        if not episodes_data:
            return {
                "total_episodes": 0,
                "average_score": 0.0,
                "current_level": WriterLevel.BEGINNER,
                "level_description": "初心者 - 基礎を学びながら執筆を楽しみましょう",
                "score_trend": "no_data",
            }

        total_episodes = len(episodes_data)
        scores = [ep.get("quality_score", 0.0) for ep in episodes_data if "quality_score" in ep]
        average_score = sum(scores) / len(scores) if scores else 0.0

        current_level = WriterLevelService.determine_level(total_episodes, average_score)

        # スコアのトレンドを分析(最後の5エピソード)
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        if len(recent_scores) >= 2:
            score_diff = recent_scores[-1] - recent_scores[0]
            if score_diff > 5:
                score_trend = "improving"
            elif score_diff < -5:
                score_trend = "declining"
            else:
                score_trend = "stable"
        else:
            score_trend = "insufficient_data"

        return {
            "total_episodes": total_episodes,
            "average_score": round(average_score, 2),
            "current_level": current_level,
            "level_description": WriterLevelService.get_level_description(current_level),
            "score_trend": score_trend,
        }
