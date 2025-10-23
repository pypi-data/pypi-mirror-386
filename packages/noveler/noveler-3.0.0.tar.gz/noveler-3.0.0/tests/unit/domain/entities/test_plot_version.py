#!/usr/bin/env python3
"""PlotVersionエンティティのユニットテスト

TDD原則に従い、プロットバージョン管理のビジネスロジックをテスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import time
from datetime import datetime

import pytest

from noveler.domain.entities.plot_version import PlotVersion
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestPlotVersion:
    """PlotVersionエンティティのテスト"""

    @pytest.mark.spec("SPEC-PLOT_VERSION-CREATE_PLOT_VERSION")
    def test_create_plot_version(self) -> None:
        """プロットバージョンの作成"""
        # Given
        now = project_now().datetime

        # When
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "ch01", "scenes": []},
            created_at=now,
            updated_at=now,
            author="author123",
        )

        # Then
        assert version.version_id == "v1.0"
        assert version.plot_id == "plot_001"
        assert version.version_number == 1
        assert version.content == {"title": "ch01", "scenes": []}
        assert version.created_at == now
        assert version.updated_at == now
        assert version.author == "author123"
        assert version.description == ""  # デフォルト値
        assert version.is_active is True  # デフォルト値
        assert version.metadata == {}  # デフォルト値

    @pytest.mark.spec("SPEC-PLOT_VERSION-CREATE_PLOT_VERSION_")
    def test_create_plot_version_with_all_fields(self) -> None:
        """全フィールドを指定してプロットバージョンを作成"""
        # Given
        now = project_now().datetime
        metadata = {"tags": ["重要", "改訂版"]}

        # When
        version = PlotVersion(
            version_id="v2.0",
            plot_id="plot_002",
            version_number=2,
            content={"title": "ch02", "scenes": ["scene1", "scene2"]},
            created_at=now,
            updated_at=now,
            author="author456",
            description="ch02の大幅改訂版",
            is_active=False,
            metadata=metadata,
        )

        # Then
        assert version.description == "ch02の大幅改訂版"
        assert version.is_active is False
        assert version.metadata == metadata

    @pytest.mark.spec("SPEC-PLOT_VERSION-UPDATE_CONTENT")
    def test_update_content(self) -> None:
        """コンテンツの更新"""
        # Given
        original_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=JST)
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "初版"},
            created_at=original_time,
            updated_at=original_time,
            author="author123",
        )

        # When
        new_content = {"title": "改訂版", "scenes": ["新シーン"]}
        version.update_content(new_content)

        # Then
        assert version.content == new_content
        assert version.updated_at > original_time
        # 他のフィールドは変更されない
        assert version.version_id == "v1.0"
        assert version.created_at == original_time

    @pytest.mark.spec("SPEC-PLOT_VERSION-DEACTIVATE")
    def test_deactivate(self) -> None:
        """非アクティブ化"""
        # Given
        original_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=JST)
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "ch01"},
            created_at=original_time,
            updated_at=original_time,
            author="author123",
            is_active=True,
        )

        # When
        version.deactivate()

        # Then
        assert version.is_active is False
        assert version.updated_at > original_time

    @pytest.mark.spec("SPEC-PLOT_VERSION-ADD_METADATA")
    def test_add_metadata(self) -> None:
        """メタデータの追加"""
        # Given
        original_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=JST)
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "ch01"},
            created_at=original_time,
            updated_at=original_time,
            author="author123",
        )

        # When
        version.add_metadata("review_status", "approved")

        # Then
        assert version.metadata["review_status"] == "approved"
        assert version.updated_at > original_time

    @pytest.mark.spec("SPEC-PLOT_VERSION-ADD_METADATA_MULTIPL")
    def test_add_metadata_multiple(self) -> None:
        """複数のメタデータを追加"""
        # Given
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "ch01"},
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
            author="author123",
            metadata={"initial": "value"},
        )

        # When
        version.add_metadata("key1", "value1")
        first_update = version.updated_at

        time.sleep(0.01)  # 時刻が確実に変わるように

        version.add_metadata("key2", "value2")
        second_update = version.updated_at

        # Then
        assert version.metadata == {"initial": "value", "key1": "value1", "key2": "value2"}
        assert second_update > first_update

    @pytest.mark.spec("SPEC-PLOT_VERSION-ADD_METADATA_OVERWRI")
    def test_add_metadata_overwrite(self) -> None:
        """既存のメタデータを上書き"""
        # Given
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "ch01"},
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
            author="author123",
            metadata={"status": "draft"},
        )

        # When
        version.add_metadata("status", "published")

        # Then
        assert version.metadata["status"] == "published"

    @pytest.mark.spec("SPEC-PLOT_VERSION-COMPLEX_CONTENT_STRU")
    def test_complex_content_structure(self) -> None:
        """複雑なコンテンツ構造のテスト"""
        # Given
        complex_content = {
            "title": "ch03:クライマックス",
            "scenes": [
                {"id": "scene_001", "title": "対決", "characters": ["主人公", "敵"], "location": "古城"},
                {"id": "scene_002", "title": "決着", "characters": ["主人公"], "location": "古城・崩壊"},
            ],
            "themes": ["勇気", "友情", "成長"],
            "notes": "感動的な結末を意識",
        }

        # When
        version = PlotVersion(
            version_id="v3.0",
            plot_id="plot_003",
            version_number=3,
            content=complex_content,
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
            author="author789",
        )

        # Then
        assert version.content["title"] == "ch03:クライマックス"
        assert len(version.content["scenes"]) == 2
        assert version.content["scenes"][0]["id"] == "scene_001"
        assert "themes" in version.content
        assert len(version.content["themes"]) == 3

    @pytest.mark.spec("SPEC-PLOT_VERSION-VERSION_LIFECYCLE")
    def test_version_lifecycle(self) -> None:
        """バージョンのライフサイクル全体のテスト"""
        # Given
        version = PlotVersion(
            version_id="v1.0",
            plot_id="plot_001",
            version_number=1,
            content={"title": "初版", "status": "draft"},
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
            author="author123",
        )

        # 初期状態の確認
        assert version.is_active is True
        assert version.metadata == {}

        # When: レビュー状態を追加
        version.add_metadata("review_status", "in_review")
        version.add_metadata("reviewer", "editor001")

        # Then
        assert len(version.metadata) == 2

        # When: コンテンツを更新
        version.update_content({"title": "初版(修正版)", "status": "reviewed", "changes": ["誤字修正", "シーン追加"]})

        # Then
        assert version.content["status"] == "reviewed"
        assert "changes" in version.content

        # When: 古いバージョンとして非アクティブ化
        version.deactivate()

        # Then
        assert version.is_active is False
        # メタデータとコンテンツは保持される
        assert version.metadata["review_status"] == "in_review"
        assert version.content["title"] == "初版(修正版)"
