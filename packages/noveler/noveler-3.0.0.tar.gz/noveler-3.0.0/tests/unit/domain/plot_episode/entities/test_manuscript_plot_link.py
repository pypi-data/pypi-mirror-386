#!/usr/bin/env python3
"""ManuscriptPlotLinkエンティティのユニットテスト

TDD原則に従い、原稿とプロットのリンク管理をテスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import time
from datetime import datetime

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.entities.manuscript_plot_link import ManuscriptPlotLink
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestManuscriptPlotLink:
    """ManuscriptPlotLinkエンティティのテスト"""

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-CREATE_MANUSCRIPT_PL")
    def test_create_manuscript_plot_link(self) -> None:
        """原稿プロットリンクの作成"""
        # Given
        now = project_now().datetime

        # When
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_001",
            plot_id="plot_001",
            plot_version_id="v1.0",
            linked_at=now,
            linked_by="user123",
        )

        # Then
        assert link.manuscript_id == "manuscript_001"
        assert link.plot_id == "plot_001"
        assert link.plot_version_id == "v1.0"
        assert link.linked_at == now
        assert link.linked_by == "user123"
        assert link.link_type == "main"  # デフォルト値
        assert link.notes == ""  # デフォルト値

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-CREATE_LINK_WITH_CUS")
    def test_create_link_with_custom_type_and_notes(self) -> None:
        """カスタムタイプとノート付きのリンク作成"""
        # Given
        now = project_now().datetime

        # When
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_002",
            plot_id="plot_002",
            plot_version_id="v2.0",
            linked_at=now,
            linked_by="user456",
            link_type="reference",
            notes="参考用プロット",
        )

        # Then
        assert link.link_type == "reference"
        assert link.notes == "参考用プロット"

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-UPDATE_VERSION")
    def test_update_version(self) -> None:
        """バージョン更新のテスト"""
        # Given
        original_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=JST)
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_003",
            plot_id="plot_003",
            plot_version_id="v1.0",
            linked_at=original_time,
            linked_by="user789",
        )

        # When
        link.update_version("v2.0")

        # Then
        assert link.plot_version_id == "v2.0"
        assert link.linked_at > original_time  # 時刻が更新されている
        assert link.manuscript_id == "manuscript_003"  # 他のフィールドは変更なし
        assert link.plot_id == "plot_003"

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-ADD_NOTES")
    def test_add_notes(self) -> None:
        """ノート追加のテスト"""
        # Given
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_004",
            plot_id="plot_004",
            plot_version_id="v1.0",
            linked_at=project_now().datetime,
            linked_by="user000",
        )

        # When
        link.add_notes("重要な変更点あり")

        # Then
        assert link.notes == "重要な変更点あり"

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-ADD_NOTES_OVERWRITE")
    def test_add_notes_overwrite(self) -> None:
        """ノートの上書きテスト"""
        # Given
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_005",
            plot_id="plot_005",
            plot_version_id="v1.0",
            linked_at=project_now().datetime,
            linked_by="user111",
            notes="初期ノート",
        )

        # When
        link.add_notes("更新されたノート")

        # Then
        assert link.notes == "更新されたノート"

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-MULTIPLE_VERSION_UPD")
    def test_multiple_version_updates(self) -> None:
        """複数回のバージョン更新"""
        # Given
        link = ManuscriptPlotLink(
            manuscript_id="manuscript_006",
            plot_id="plot_006",
            plot_version_id="v1.0",
            linked_at=project_now().datetime,
            linked_by="user222",
        )

        # When
        link.update_version("v1.1")
        first_update_time = link.linked_at

        time.sleep(0.01)  # 時刻が確実に変わるように少し待つ

        link.update_version("v1.2")
        second_update_time = link.linked_at

        # Then
        assert link.plot_version_id == "v1.2"
        assert second_update_time > first_update_time

    @pytest.mark.spec("SPEC-MANUSCRIPT_PLOT_LINK-LINK_TYPE_VARIATIONS")
    def test_link_type_variations(self) -> None:
        """様々なリンクタイプのテスト"""
        # Given/When
        main_link = ManuscriptPlotLink(
            manuscript_id="m1",
            plot_id="p1",
            plot_version_id="v1",
            linked_at=project_now().datetime,
            linked_by="u1",
            link_type="main",
        )

        reference_link = ManuscriptPlotLink(
            manuscript_id="m2",
            plot_id="p2",
            plot_version_id="v1",
            linked_at=project_now().datetime,
            linked_by="u2",
            link_type="reference",
        )

        alternative_link = ManuscriptPlotLink(
            manuscript_id="m3",
            plot_id="p3",
            plot_version_id="v1",
            linked_at=project_now().datetime,
            linked_by="u3",
            link_type="alternative",
        )

        # Then
        assert main_link.link_type == "main"
        assert reference_link.link_type == "reference"
        assert alternative_link.link_type == "alternative"
