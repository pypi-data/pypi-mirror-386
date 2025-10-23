#!/usr/bin/env python3
"""PreWritingCheckエンティティのユニットテスト

TDD原則に従い、事前執筆チェックのビジネスロジックをテスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import pytest

from noveler.domain.entities.pre_writing_check import (
    CheckItemStatus,
    CheckItemType,
    PreWritingCheck,
    PreWritingCheckItem,
)
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber


class TestPreWritingCheckItem:
    """PreWritingCheckItemのテスト"""

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-CREATE_CHECK_ITEM")
    def test_create_check_item(self) -> None:
        """チェック項目の作成"""
        # When
        item = PreWritingCheckItem(
            type=CheckItemType.EPISODE_INFO,
            title="基本情報確認",
            description="エピソード情報の確認",
        )

        # Then
        assert item.type == CheckItemType.EPISODE_INFO
        assert item.title == "基本情報確認"
        assert item.description == "エピソード情報の確認"
        assert item.status == CheckItemStatus.PENDING
        assert item.checked_at is None
        assert item.notes == ""

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-COMPLETE_ITEM")
    def test_complete_item(self) -> None:
        """項目の完了"""
        # Given
        item = PreWritingCheckItem(
            type=CheckItemType.EPISODE_INFO,
            title="基本情報確認",
            description="エピソード情報の確認",
        )

        # When
        item.complete("確認完了")

        # Then
        assert item.status == CheckItemStatus.COMPLETED
        assert item.checked_at is not None
        assert item.notes == "確認完了"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-SKIP_ITEM")
    def test_skip_item(self) -> None:
        """項目のスキップ"""
        # Given
        item = PreWritingCheckItem(
            type=CheckItemType.PREVIOUS_FLOW,
            title="前話確認",
            description="前話からの流れ確認",
        )

        # When
        item.skip("第1話のため不要")

        # Then
        assert item.status == CheckItemStatus.SKIPPED
        assert item.checked_at is not None
        assert item.notes == "第1話のため不要"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-IS_DONE")
    def test_is_done(self) -> None:
        """完了状態の判定"""
        # Given
        item = PreWritingCheckItem(
            type=CheckItemType.EPISODE_INFO,
            title="基本情報確認",
            description="エピソード情報の確認",
        )

        # When/Then
        assert not item.is_done()  # 初期状態

        item.complete()
        assert item.is_done()  # 完了状態

        item.status = CheckItemStatus.SKIPPED
        assert item.is_done()  # スキップも完了扱い


class TestPreWritingCheck:
    """PreWritingCheckエンティティのテスト"""

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-CREATE_PRE_WRITING_C")
    def test_create_pre_writing_check(self) -> None:
        """事前チェックの作成"""
        # When
        check = PreWritingCheck(
            episode_number=EpisodeNumber(1),
            project_name="テストプロジェクト",
        )

        # Then
        assert check.episode_number.value == 1
        assert check.project_name == "テストプロジェクト"
        assert len(check.check_items) == 5  # 標準項目数
        assert check.completed_at is None

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-INITIALIZE_STANDARD_")
    def test_initialize_standard_items(self) -> None:
        """標準チェック項目の初期化"""
        # When
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # Then
        assert len(check.check_items) == 5
        # 各項目タイプが存在することを確認
        types = {item.type for item in check.check_items}
        assert CheckItemType.EPISODE_INFO in types
        assert CheckItemType.PREVIOUS_FLOW in types
        assert CheckItemType.EPISODE_PURPOSE in types
        assert CheckItemType.DROPOUT_RISK in types
        assert CheckItemType.IMPORTANT_SCENE in types

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-FIRST_EPISODE_AUTO_S")
    def test_first_episode_auto_skip(self) -> None:
        """第1話の前話チェック自動スキップ"""
        # When
        check = PreWritingCheck(
            episode_number=EpisodeNumber(1),
            project_name="テストプロジェクト",
        )

        # Then
        prev_flow_item = check.get_check_item(CheckItemType.PREVIOUS_FLOW)
        assert prev_flow_item is not None
        assert prev_flow_item.status == CheckItemStatus.SKIPPED
        assert "第1話" in prev_flow_item.notes

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_CHECK_ITEM")
    def test_get_check_item(self) -> None:
        """チェック項目の取得"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When
        item = check.get_check_item(CheckItemType.EPISODE_INFO)

        # Then
        assert item is not None
        assert item.type == CheckItemType.EPISODE_INFO

        # 存在しないタイプ
        custom_item = check.get_check_item(CheckItemType.CUSTOM)
        assert custom_item is None

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-COMPLETE_ITEM")
    def test_complete_item(self) -> None:
        """チェック項目の完了"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When
        check.complete_item(CheckItemType.EPISODE_INFO, "基本情報を確認しました")

        # Then
        item = check.get_check_item(CheckItemType.EPISODE_INFO)
        assert item.status == CheckItemStatus.COMPLETED
        assert item.notes == "基本情報を確認しました"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-COMPLETE_NONEXISTENT")
    def test_complete_nonexistent_item(self) -> None:
        """存在しない項目の完了はエラー"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When/Then
        with pytest.raises(DomainException, match="チェック項目が見つかりません"):
            check.complete_item(CheckItemType.CUSTOM)

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-SKIP_ITEM")
    def test_skip_item(self) -> None:
        """チェック項目のスキップ"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When
        check.skip_item(CheckItemType.DROPOUT_RISK, "今回は不要")

        # Then
        item = check.get_check_item(CheckItemType.DROPOUT_RISK)
        assert item.status == CheckItemStatus.SKIPPED
        assert item.notes == "今回は不要"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-ADD_CUSTOM_ITEM")
    def test_add_custom_item(self) -> None:
        """カスタム項目の追加"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        custom_item = PreWritingCheckItem(
            type=CheckItemType.CUSTOM,
            title="特別な確認",
            description="プロジェクト固有の確認事項",
        )

        # When
        check.add_custom_item(custom_item)

        # Then
        assert len(check.check_items) == 6
        assert custom_item in check.check_items

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-ADD_NON_CUSTOM_ITEM")
    def test_add_non_custom_item(self) -> None:
        """非カスタム項目の追加はエラー"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        item = PreWritingCheckItem(
            type=CheckItemType.EPISODE_INFO,
            title="重複項目",
            description="追加できない",
        )

        # When/Then
        with pytest.raises(DomainException, match="カスタム項目のタイプはCUSTOMである必要があります"):
            check.add_custom_item(item)

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-IS_COMPLETED_ALL_DON")
    def test_is_completed_all_done(self) -> None:
        """全項目完了の判定"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When
        check.skip_item(CheckItemType.PREVIOUS_FLOW, "スキップ")
        check.complete_item(CheckItemType.EPISODE_INFO)
        check.complete_item(CheckItemType.EPISODE_PURPOSE)
        check.complete_item(CheckItemType.DROPOUT_RISK)
        check.complete_item(CheckItemType.IMPORTANT_SCENE)

        # Then
        assert check.is_completed()
        assert check.completed_at is not None

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-IS_COMPLETED_PARTIAL")
    def test_is_completed_partial(self) -> None:
        """部分完了の判定"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When
        check.complete_item(CheckItemType.EPISODE_INFO)

        # Then
        assert not check.is_completed()
        assert check.completed_at is None

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_COMPLETION_RATE")
    def test_get_completion_rate(self) -> None:
        """完了率の計算"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When/Then
        assert check.get_completion_rate() == 0.0

        check.complete_item(CheckItemType.EPISODE_INFO)
        assert check.get_completion_rate() == 20.0  # 1/5

        check.complete_item(CheckItemType.EPISODE_PURPOSE)
        assert check.get_completion_rate() == 40.0  # 2/5

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_SUMMARY")
    def test_get_summary(self) -> None:
        """サマリー情報の取得"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        check.complete_item(CheckItemType.EPISODE_INFO)
        check.skip_item(CheckItemType.PREVIOUS_FLOW)

        # When
        summary = check.get_summary()

        # Then
        assert summary["episode_number"] == 2
        assert summary["project_name"] == "テストプロジェクト"
        assert summary["total_items"] == 5
        assert summary["completed_items"] == 1
        assert summary["skipped_items"] == 1
        assert summary["pending_items"] == 3
        assert summary["completion_rate"] == 40.0
        assert not summary["is_completed"]

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_CHECK_DETAILS")
    def test_get_check_details(self) -> None:
        """チェック詳細情報の取得"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        check.complete_item(CheckItemType.EPISODE_INFO, "確認済み")

        # When
        details = check.get_check_details()

        # Then
        assert len(details) == 5
        episode_info_detail = next(d for d in details if d["type"] == "episode_info")
        assert episode_info_detail["status"] == "completed"
        assert episode_info_detail["notes"] == "確認済み"
        assert episode_info_detail["checked_at"] is not None

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_DROPOUT_RISKS")
    def test_get_dropout_risks(self) -> None:
        """離脱リスク情報の取得"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        check.complete_item(CheckItemType.DROPOUT_RISK, "- 序盤の説明が長い\n- 中盤に緊張感が薄い")

        # When
        risks = check.get_dropout_risks()

        # Then
        assert len(risks) == 2
        assert "序盤の説明が長い" in risks
        assert "中盤に緊張感が薄い" in risks

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-GET_DROPOUT_RISKS_WI")
    def test_get_dropout_risks_with_bullet_points(self) -> None:
        """離脱リスク情報の取得(中黒記号)"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        check.complete_item(CheckItemType.DROPOUT_RISK, "・序盤の説明が長い\n・中盤に緊張感が薄い")

        # When
        risks = check.get_dropout_risks()

        # Then
        assert len(risks) == 2
        assert "序盤の説明が長い" in risks
        assert "中盤に緊張感が薄い" in risks

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-VALIDATE_FOR_WRITING")
    def test_validate_for_writing(self) -> None:
        """執筆開始可能性の検証"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # When/Then - 初期状態では未確認項目が多い
        issues = check.validate_for_writing()
        assert len(issues) == 5  # 全項目が未確認

        # 重要項目を完了
        check.complete_item(CheckItemType.EPISODE_INFO)
        check.complete_item(CheckItemType.EPISODE_PURPOSE)
        check.complete_item(CheckItemType.IMPORTANT_SCENE)
        check.skip_item(CheckItemType.PREVIOUS_FLOW)
        check.complete_item(CheckItemType.DROPOUT_RISK, "- リスクポイント1")

        issues = check.validate_for_writing()
        assert len(issues) == 0  # 全項目が確認済み

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK-VALIDATE_FOR_WRITING")
    def test_validate_for_writing_with_empty_dropout_risks(self) -> None:
        """離脱リスクが空の場合の検証"""
        # Given
        check = PreWritingCheck(
            episode_number=EpisodeNumber(2),
            project_name="テストプロジェクト",
        )

        # 全項目を完了(ただし離脱リスクのノートは空)
        for item in check.check_items:
            if item.type == CheckItemType.DROPOUT_RISK:
                check.complete_item(CheckItemType.DROPOUT_RISK, "")
            else:
                item.complete()

        # When
        issues = check.validate_for_writing()

        # Then
        assert len(issues) == 1
        assert "離脱リスクポイントが記録されていません" in issues[0]
