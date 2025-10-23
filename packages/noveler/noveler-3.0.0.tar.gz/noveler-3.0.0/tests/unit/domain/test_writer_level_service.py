#!/usr/bin/env python3
"""WriterLevelServiceのユニットテスト

TDD原則に従い、執筆レベル判定サービスのビジネスロジックをテスト


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.services.writer_level_service import WriterLevelService
from noveler.domain.value_objects.quality_standards import WriterLevel


class TestWriterLevelService:
    """WriterLevelServiceのテスト"""

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_BEGI")
    def test_determine_level_beginner_with_few_episodes(self) -> None:
        """エピソード数が少ない場合は初心者レベルと判定される"""
        # Given
        completed_episodes = 3
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_BEGI")
    def test_determine_level_beginner_boundary(self) -> None:
        """エピソード数5件は初心者レベルの境界値"""
        # Given
        completed_episodes = 5
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_INTE")
    def test_determine_level_intermediate_with_moderate_episodes(self) -> None:
        """エピソード数が6-20の場合は中級者レベルと判定される"""
        # Given
        completed_episodes = 10
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_INTE")
    def test_determine_level_intermediate_boundary(self) -> None:
        """エピソード数20件は中級者レベルの境界値"""
        # Given
        completed_episodes = 20
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_ADVA")
    def test_determine_level_advanced_with_many_episodes(self) -> None:
        """エピソード数が21-50の場合は上級者レベルと判定される"""
        # Given
        completed_episodes = 35
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.ADVANCED

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_ADVA")
    def test_determine_level_advanced_boundary(self) -> None:
        """エピソード数50件は上級者レベルの境界値"""
        # Given
        completed_episodes = 50
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.ADVANCED

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_EXPE")
    def test_determine_level_expert_with_many_episodes(self) -> None:
        """エピソード数が51以上の場合はエキスパートレベルと判定される"""
        # Given
        completed_episodes = 100
        average_quality_score = 70.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.EXPERT

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_UPGR")
    def test_determine_level_upgrade_with_high_score(self) -> None:
        """平均スコアが85以上の場合は1段階レベルアップ"""
        # Given: 本来は初心者レベルのエピソード数
        completed_episodes = 3
        average_quality_score = 90.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then: 中級者にレベルアップ
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_DOWN")
    def test_determine_level_downgrade_with_low_score(self) -> None:
        """平均スコアが60未満の場合は1段階レベルダウン"""
        # Given: 本来は中級者レベルのエピソード数
        completed_episodes = 10
        average_quality_score = 50.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then: 初心者にレベルダウン
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_NO_U")
    def test_determine_level_no_upgrade_for_expert(self) -> None:
        """エキスパートレベルは高スコアでもそれ以上にならない"""
        # Given
        completed_episodes = 100
        average_quality_score = 95.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.EXPERT

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_NO_D")
    def test_determine_level_no_downgrade_for_beginner(self) -> None:
        """初心者レベルは低スコアでもそれ以下にならない"""
        # Given
        completed_episodes = 3
        average_quality_score = 30.0

        # When
        level = WriterLevelService.determine_level(completed_episodes, average_quality_score)

        # Then
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_LEVEL_DESCRIPTIO")
    def test_get_level_description_beginner(self) -> None:
        """初心者レベルの説明文を取得"""
        # When
        description = WriterLevelService.get_level_description(WriterLevel.BEGINNER)

        # Then
        assert description == "初心者 - 基礎を学びながら執筆を楽しみましょう"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_LEVEL_DESCRIPTIO")
    def test_get_level_description_intermediate(self) -> None:
        """中級者レベルの説明文を取得"""
        # When
        description = WriterLevelService.get_level_description(WriterLevel.INTERMEDIATE)

        # Then
        assert description == "中級者 - 安定した品質で執筆できています"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_LEVEL_DESCRIPTIO")
    def test_get_level_description_advanced(self) -> None:
        """上級者レベルの説明文を取得"""
        # When
        description = WriterLevelService.get_level_description(WriterLevel.ADVANCED)

        # Then
        assert description == "上級者 - 高い品質を維持しています"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_LEVEL_DESCRIPTIO")
    def test_get_level_description_expert(self) -> None:
        """エキスパートレベルの説明文を取得"""
        # When
        description = WriterLevelService.get_level_description(WriterLevel.EXPERT)

        # Then
        assert description == "エキスパート - プロ級の執筆技術です"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_beginner_high_score(self) -> None:
        """初心者で高スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.BEGINNER, 65.0)

        # Then
        assert message == "素晴らしい進歩です!この調子で続けましょう。"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_beginner_low_score(self) -> None:
        """初心者で低スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.BEGINNER, 55.0)

        # Then
        assert message == "少しずつ改善していきましょう。基礎をしっかり身につけることが大切です。"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_intermediate_high_score(self) -> None:
        """中級者で高スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.INTERMEDIATE, 80.0)

        # Then
        assert message == "安定した品質です。より高みを目指しましょう!"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_intermediate_low_score(self) -> None:
        """中級者で低スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.INTERMEDIATE, 70.0)

        # Then
        assert message == "もう少しで次のレベルです。細部にこだわってみましょう。"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_advanced_high_score(self) -> None:
        """上級者で高スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.ADVANCED, 90.0)

        # Then
        assert message == "プロ級の品質に近づいています!"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_advanced_low_score(self) -> None:
        """上級者で低スコアの場合の励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.ADVANCED, 80.0)

        # Then
        assert message == "高い水準を維持しています。さらなる洗練を目指しましょう。"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GET_ENCOURAGEMENT_ME")
    def test_get_encouragement_message_expert(self) -> None:
        """エキスパートレベルの励ましメッセージ"""
        # When
        message = WriterLevelService.get_encouragement_message(WriterLevel.EXPERT, 95.0)

        # Then
        assert message == "最高水準の執筆です。あなたの作品は多くの読者を魅了するでしょう。"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-DETERMINE_LEVEL_EDGE")
    def test_determine_level_edge_cases(self) -> None:
        """エッジケースのテスト"""
        # エピソード数0でも正しく動作
        level = WriterLevelService.determine_level(0, 70.0)
        assert level == WriterLevel.BEGINNER

        # スコア0でも正しく動作
        level = WriterLevelService.determine_level(10, 0.0)
        assert level == WriterLevel.BEGINNER

        # スコア100でも正しく動作
        level = WriterLevelService.determine_level(10, 100.0)
        assert level == WriterLevel.ADVANCED

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-LEVEL_ADJUSTMENT_WIT")
    def test_level_adjustment_with_boundary_scores(self) -> None:
        """境界値スコアでのレベル調整テスト"""
        # スコア60ちょうどは調整なし
        level = WriterLevelService.determine_level(10, 60.0)
        assert level == WriterLevel.INTERMEDIATE

        # スコア59.9は1段階ダウン
        level = WriterLevelService.determine_level(10, 59.9)
        assert level == WriterLevel.BEGINNER

        # スコア85ちょうどは1段階アップ
        level = WriterLevelService.determine_level(10, 85.0)
        assert level == WriterLevel.ADVANCED

        # スコア84.9は調整なし
        level = WriterLevelService.determine_level(10, 84.9)
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_T")
    def test_calculate_progress_to_next_level_beginner(self) -> None:
        """初心者レベルの進捗計算"""
        # Given
        completed_episodes = 3
        current_level = WriterLevel.BEGINNER

        # When
        progress = WriterLevelService.calculate_progress_to_next_level(completed_episodes, current_level)

        # Then
        assert progress["current_episodes"] == 3
        assert progress["next_level_threshold"] == 6
        assert progress["progress_percentage"] == 50.0  # 3/6 = 50%

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_T")
    def test_calculate_progress_to_next_level_intermediate(self) -> None:
        """中級者レベルの進捗計算"""
        # Given
        completed_episodes = 15
        current_level = WriterLevel.INTERMEDIATE

        # When
        progress = WriterLevelService.calculate_progress_to_next_level(completed_episodes, current_level)

        # Then
        assert progress["current_episodes"] == 15
        assert progress["next_level_threshold"] == 21
        assert progress["progress_percentage"] == 60.0  # (15-6)/(21-6) = 9/15 = 60%

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_T")
    def test_calculate_progress_to_next_level_advanced(self) -> None:
        """上級者レベルの進捗計算"""
        # Given
        completed_episodes = 35
        current_level = WriterLevel.ADVANCED

        # When
        progress = WriterLevelService.calculate_progress_to_next_level(completed_episodes, current_level)

        # Then
        assert progress["current_episodes"] == 35
        assert progress["next_level_threshold"] == 51
        assert round(progress["progress_percentage"], 2) == 46.67  # (35-21)/(51-21) ≈ 46.67%

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_T")
    def test_calculate_progress_to_next_level_expert(self) -> None:
        """エキスパートレベルの進捗計算(最高レベル)"""
        # Given
        completed_episodes = 100
        current_level = WriterLevel.EXPERT

        # When
        progress = WriterLevelService.calculate_progress_to_next_level(completed_episodes, current_level)

        # Then
        assert progress["current_episodes"] == 100
        assert progress["next_level_threshold"] is None
        assert progress["progress_percentage"] == 100.0

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_A")
    def test_calculate_progress_at_level_start(self) -> None:
        """レベル開始時点での進捗計算"""
        # 中級者レベルの開始時点
        progress = WriterLevelService.calculate_progress_to_next_level(6, WriterLevel.INTERMEDIATE)
        assert progress["progress_percentage"] == 0.0

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_A")
    def test_calculate_progress_at_level_end(self) -> None:
        """レベル終了時点での進捗計算"""
        # 中級者レベルの終了時点
        progress = WriterLevelService.calculate_progress_to_next_level(20, WriterLevel.INTERMEDIATE)
        assert round(progress["progress_percentage"], 2) == 93.33  # (20-6)/(21-6) ≈ 93.33%

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-CALCULATE_PROGRESS_O")
    def test_calculate_progress_over_threshold(self) -> None:
        """しきい値を超えた場合の進捗計算"""
        # 本来は次のレベルになるべきエピソード数
        progress = WriterLevelService.calculate_progress_to_next_level(25, WriterLevel.INTERMEDIATE)
        assert progress["progress_percentage"] == 100.0  # 最大100%

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_empty_data(self) -> None:
        """空データでの統計生成"""
        # When
        stats = WriterLevelService.generate_level_statistics([])

        # Then
        assert stats["total_episodes"] == 0
        assert stats["average_score"] == 0.0
        assert stats["current_level"] == WriterLevel.BEGINNER
        assert stats["score_trend"] == "no_data"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_single_episode(self) -> None:
        """単一エピソードでの統計生成"""
        # Given
        episodes_data = [{"quality_score": 75.0}]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["total_episodes"] == 1
        assert stats["average_score"] == 75.0
        assert stats["current_level"] == WriterLevel.BEGINNER
        assert stats["score_trend"] == "insufficient_data"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_improving_trend(self) -> None:
        """改善傾向の統計生成"""
        # Given
        episodes_data = [
            {"quality_score": 60.0},
            {"quality_score": 65.0},
            {"quality_score": 70.0},
            {"quality_score": 75.0},
            {"quality_score": 80.0},
        ]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["total_episodes"] == 5
        assert stats["average_score"] == 70.0
        assert stats["current_level"] == WriterLevel.BEGINNER
        assert stats["score_trend"] == "improving"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_declining_trend(self) -> None:
        """低下傾向の統計生成"""
        # Given
        episodes_data = [
            {"quality_score": 80.0},
            {"quality_score": 75.0},
            {"quality_score": 70.0},
            {"quality_score": 65.0},
            {"quality_score": 60.0},
        ]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["score_trend"] == "declining"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_stable_trend(self) -> None:
        """安定傾向の統計生成"""
        # Given
        episodes_data = [
            {"quality_score": 75.0},
            {"quality_score": 76.0},
            {"quality_score": 74.0},
            {"quality_score": 75.0},
            {"quality_score": 76.0},
        ]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["score_trend"] == "stable"

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_many_episodes(self) -> None:
        """多数エピソードでの統計生成"""
        # Given
        episodes_data = [{"quality_score": 85.0} for _ in range(25)]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["total_episodes"] == 25
        assert stats["average_score"] == 85.0
        assert stats["current_level"] == WriterLevel.EXPERT  # 25エピソード(ADVANCED) + 高スコア85でレベルアップ
        assert "エキスパート" in stats["level_description"]

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_missing_scores(self) -> None:
        """スコアが欠けているエピソードの処理"""
        # Given
        episodes_data = [
            {"quality_score": 80.0},
            {"other_data": "value"},  # quality_scoreなし
            {"quality_score": 70.0},
        ]

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["total_episodes"] == 3
        assert stats["average_score"] == 75.0  # (80+70)/2

    @pytest.mark.spec("SPEC-WRITER_LEVEL_SERVICE-GENERATE_LEVEL_STATI")
    def test_generate_level_statistics_recent_episodes_only(self) -> None:
        """最近のエピソードのみでトレンド分析"""
        # Given: 10エピソード、最後の5つが改善傾向
        episodes_data = [{"quality_score": 60.0} for _ in range(5)]
        episodes_data.extend(
            [
                {"quality_score": 70.0},
                {"quality_score": 72.0},
                {"quality_score": 74.0},
                {"quality_score": 76.0},
                {"quality_score": 78.0},
            ]
        )

        # When
        stats = WriterLevelService.generate_level_statistics(episodes_data)

        # Then
        assert stats["score_trend"] == "improving"  # 最後の5エピソードで判定
