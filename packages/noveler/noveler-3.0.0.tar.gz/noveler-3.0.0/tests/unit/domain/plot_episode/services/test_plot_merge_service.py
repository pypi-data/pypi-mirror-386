"""プロットマージサービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- マージ戦略の検証
- ディープマージアルゴリズムのテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.services.plot_merge_service import PlotMergeService
from noveler.domain.value_objects.merge_strategy import MergeStrategy


class TestPlotMergeService:
    """PlotMergeServiceのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.service = PlotMergeService()

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-MERGE_EMPTY_EXISTING")
    def test_merge_empty_existing_data(self) -> None:
        """既存データが空の場合は新規データをそのまま返す"""
        # Given
        existing_data = {}
        new_data = {"title": "転生したら最強の魔法使いだった件", "chapters": [{"number": 1, "title": "ch01"}]}
        strategy = MergeStrategy.MERGE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert result == new_data

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-MERGE_WITH_EXISTING_")
    def test_merge_with_existing_data(self) -> None:
        """既存データと新規データをマージする"""
        # Given
        existing_data = {
            "title": "転生したら最強の魔法使いだった件",
            "chapters": [{"number": 1, "title": "ch01", "custom_notes": "既存のメモ"}],
            "custom_field": "カスタムデータ",
        }
        new_data = {
            "title": "転生したら最強の魔法使いだった件",
            "chapters": [{"number": 1, "title": "ch01 - 覚醒"}, {"number": 2, "title": "ch02"}],
        }
        strategy = MergeStrategy.MERGE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert result["title"] == new_data["title"]
        assert result["custom_field"] == "カスタムデータ"  # 既存フィールドを保持
        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["custom_notes"] == "既存のメモ"  # 既存のカスタムフィールドを保持
        assert result["chapters"][0]["title"] == "ch01 - 覚醒"  # 新規データで更新

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-REPLACE_STRATEGY")
    def test_replace_strategy(self) -> None:
        """REPLACE戦略では既存データを完全に置き換える"""
        # Given
        existing_data = {"title": "古いタイトル", "custom_field": "消えるべきデータ"}
        new_data = {"title": "新しいタイトル"}
        strategy = MergeStrategy.REPLACE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert result == new_data
        assert "custom_field" not in result

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-MERGE_NESTED_STRUCTU")
    def test_merge_nested_structures(self) -> None:
        """ネストした構造のマージ"""
        # Given
        existing_data = {
            "metadata": {"author": "作者名", "custom_tags": ["タグ1", "タグ2"]},
            "plot": {"act1": {"description": "第1幕の説明", "scenes": ["シーン1"]}},
        }
        new_data = {
            "metadata": {"version": "2.0"},
            "plot": {"act1": {"scenes": ["シーン1", "シーン2"]}, "act2": {"description": "第2幕の説明"}},
        }
        strategy = MergeStrategy.MERGE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert result["metadata"]["author"] == "作者名"  # 既存データを保持
        assert result["metadata"]["version"] == "2.0"  # 新規データを追加
        assert result["metadata"]["custom_tags"] == ["タグ1", "タグ2"]  # リストを保持
        assert result["plot"]["act1"]["description"] == "第1幕の説明"  # 既存の説明を保持
        assert result["plot"]["act1"]["scenes"] == ["シーン1", "シーン2"]  # シーンを更新
        assert "act2" in result["plot"]  # 新規セクションを追加

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-MERGE_WITH_LIST_DEDU")
    def test_merge_with_list_deduplication(self) -> None:
        """リストのマージ時に重複を除去"""
        # Given
        existing_data = {
            "tags": ["ファンタジー", "転生"],
            "characters": [{"name": "主人公", "age": 15}, {"name": "ヒロイン", "age": 16}],
        }
        new_data = {
            "tags": ["転生", "魔法", "ファンタジー"],
            "characters": [
                {"name": "主人公", "age": 16},  # 年齢が更新
                {"name": "ライバル", "age": 17},
            ],
        }
        strategy = MergeStrategy.MERGE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert set(result["tags"]) == {"ファンタジー", "転生", "魔法"}  # 重複なし
        assert len(result["characters"]) == 3  # 主人公、ヒロイン、ライバル
        # 主人公の年齢が更新されていることを確認
        protagonist = next(c for c in result["characters"] if c["name"] == "主人公")
        assert protagonist["age"] == 16

    @pytest.mark.spec("SPEC-PLOT_MERGE_SERVICE-PRESERVE_YAML_COMMEN")
    def test_preserve_yaml_comments_metadata(self) -> None:
        """YAMLコメントやメタデータの保持"""
        # Given
        existing_data = {
            "_comments": {"title": "このタイトルは仮です", "chapters": "章構成は変更予定"},
            "title": "仮タイトル",
            "last_modified": "2025-01-20T10:00:00",
        }
        new_data = {"title": "正式タイトル", "chapters": []}
        strategy = MergeStrategy.MERGE

        # When
        result = self.service.merge_plot_data(existing_data, new_data, strategy)

        # Then
        assert result["_comments"] == existing_data["_comments"]  # コメントを保持
        assert result["last_modified"] == existing_data["last_modified"]  # メタデータを保持
        assert result["title"] == "正式タイトル"  # タイトルは更新
