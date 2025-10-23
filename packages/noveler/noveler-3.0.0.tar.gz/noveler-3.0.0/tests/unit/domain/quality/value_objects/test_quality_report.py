"""品質レポート値オブジェクトのテスト

TDD準拠テスト:
    - QualityReport


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.value_objects.quality_report import QualityReport


class TestQualityReport:
    """QualityReport値オブジェクトのテストクラス"""

    @pytest.fixture
    def valid_quality_report(self) -> QualityReport:
        """有効な品質レポート"""
        return QualityReport(
            project_name="テストプロジェクト",
            total_episodes=10,
            average_score=85.5,
            problematic_episodes=[2, 5, 8],
            suggestions=["文章の流れを改善してください", "キャラクターの一貫性を確認してください"],
        )

    def test_quality_report_creation_valid(self, valid_quality_report: QualityReport) -> None:
        """有効な品質レポート作成テスト"""
        assert valid_quality_report.project_name == "テストプロジェクト"
        assert valid_quality_report.total_episodes == 10
        assert valid_quality_report.average_score == 85.5
        assert valid_quality_report.problematic_episodes == [2, 5, 8]
        assert valid_quality_report.suggestions == [
            "文章の流れを改善してください",
            "キャラクターの一貫性を確認してください",
        ]

    def test_quality_report_creation_minimal(self) -> None:
        """最小パラメータでの品質レポート作成テスト"""
        report = QualityReport(
            project_name="最小プロジェクト",
            total_episodes=1,
            average_score=70.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report.project_name == "最小プロジェクト"
        assert report.total_episodes == 1
        assert report.average_score == 70.0
        assert report.problematic_episodes == []
        assert report.suggestions == []

    def test_quality_report_creation_empty_project_name(self) -> None:
        """空のプロジェクト名での品質レポート作成テスト"""
        report = QualityReport(
            project_name="", total_episodes=5, average_score=80.0, problematic_episodes=[1], suggestions=["改善案"]
        )

        assert report.project_name == ""

    def test_quality_report_creation_zero_episodes(self) -> None:
        """エピソード数0での品質レポート作成テスト"""
        report = QualityReport(
            project_name="ゼロエピソードプロジェクト",
            total_episodes=0,
            average_score=0.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report.total_episodes == 0
        assert report.average_score == 0.0

    def test_quality_report_creation_negative_episodes(self) -> None:
        """負のエピソード数での品質レポート作成テスト"""
        report = QualityReport(
            project_name="負のエピソードプロジェクト",
            total_episodes=-1,
            average_score=50.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report.total_episodes == -1

    def test_quality_report_creation_boundary_scores(self) -> None:
        """境界値スコアでの品質レポート作成テスト"""
        # 最低スコア
        report_min = QualityReport(
            project_name="最低スコアプロジェクト",
            total_episodes=1,
            average_score=0.0,
            problematic_episodes=[1],
            suggestions=["大幅な改善が必要"],
        )

        assert report_min.average_score == 0.0

        # 最高スコア
        report_max = QualityReport(
            project_name="最高スコアプロジェクト",
            total_episodes=1,
            average_score=100.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report_max.average_score == 100.0

        # 負のスコア(技術的には可能)
        report_negative = QualityReport(
            project_name="負のスコアプロジェクト",
            total_episodes=1,
            average_score=-10.0,
            problematic_episodes=[1],
            suggestions=["スコア計算を確認してください"],
        )

        assert report_negative.average_score == -10.0

        # 100を超えるスコア(技術的には可能)
        report_over = QualityReport(
            project_name="超高スコアプロジェクト",
            total_episodes=1,
            average_score=120.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report_over.average_score == 120.0

    def test_quality_report_creation_large_problematic_episodes(self) -> None:
        """多数の問題エピソードでの品質レポート作成テスト"""
        large_list = list(range(1, 101))  # 1-100
        report = QualityReport(
            project_name="多問題プロジェクト",
            total_episodes=100,
            average_score=60.0,
            problematic_episodes=large_list,
            suggestions=["全体的な見直しが必要"],
        )

        assert len(report.problematic_episodes) == 100
        assert report.problematic_episodes[0] == 1
        assert report.problematic_episodes[-1] == 100

    def test_quality_report_creation_duplicate_problematic_episodes(self) -> None:
        """重複する問題エピソードでの品質レポート作成テスト"""
        report = QualityReport(
            project_name="重複問題プロジェクト",
            total_episodes=5,
            average_score=70.0,
            problematic_episodes=[1, 2, 2, 3, 3, 3],
            suggestions=["重複チェックが必要"],
        )

        assert report.problematic_episodes == [1, 2, 2, 3, 3, 3]

    def test_quality_report_creation_long_suggestions(self) -> None:
        """長い改善提案での品質レポート作成テスト"""
        long_suggestions = [
            "この小説の構成について、まず第一章から第三章にかけての展開が急激すぎる印象があります。読者が物語の世界観に慣れ親しむ前に重要な出来事が立て続けに起こってしまうため、感情移入が困難になっている可能性があります。",
            "キャラクターの心理描写をもう少し丁寧に描写することで、読者との距離感を縮めることができるでしょう。特に主人公の内面の葛藤や成長過程をより詳細に表現することをお勧めします。",
            "文章のリズムに関して、短文と長文のバランスを見直すことで、より読みやすい文体にすることができます。現在は長文が多用されている傾向にあるため、適度に短文を挟むことで緩急をつけることができるでしょう。",
        ]

        report = QualityReport(
            project_name="詳細フィードバックプロジェクト",
            total_episodes=15,
            average_score=75.0,
            problematic_episodes=[3, 7, 12],
            suggestions=long_suggestions,
        )

        assert len(report.suggestions) == 3
        assert all(len(suggestion) > 100 for suggestion in report.suggestions)

    def test_quality_report_creation_empty_suggestions(self) -> None:
        """空の改善提案での品質レポート作成テスト"""
        report = QualityReport(
            project_name="提案なしプロジェクト",
            total_episodes=5,
            average_score=95.0,
            problematic_episodes=[],
            suggestions=[],
        )

        assert report.suggestions == []

    def test_quality_report_creation_mixed_language_suggestions(self) -> None:
        """多言語混在改善提案での品質レポート作成テスト"""
        mixed_suggestions = [
            "日本語での改善提案です。",
            "English suggestion for improvement.",
            "Suggestion avec du français mélangé.",
            "文章の流れをimproveしてください。",
        ]

        report = QualityReport(
            project_name="多言語プロジェクト",
            total_episodes=8,
            average_score=82.5,
            problematic_episodes=[2, 6],
            suggestions=mixed_suggestions,
        )

        assert len(report.suggestions) == 4
        assert "日本語での改善提案です。" in report.suggestions
        assert "English suggestion for improvement." in report.suggestions

    def test_quality_report_equality(self) -> None:
        """品質レポート等価性テスト"""
        report1 = QualityReport(
            project_name="テストプロジェクト",
            total_episodes=5,
            average_score=80.0,
            problematic_episodes=[1, 3],
            suggestions=["改善案1", "改善案2"],
        )

        report2 = QualityReport(
            project_name="テストプロジェクト",
            total_episodes=5,
            average_score=80.0,
            problematic_episodes=[1, 3],
            suggestions=["改善案1", "改善案2"],
        )

        report3 = QualityReport(
            project_name="別のプロジェクト",
            total_episodes=5,
            average_score=80.0,
            problematic_episodes=[1, 3],
            suggestions=["改善案1", "改善案2"],
        )

        assert report1 == report2
        assert report1 != report3

    def test_quality_report_string_representation(self, valid_quality_report: QualityReport) -> None:
        """品質レポート文字列表現テスト"""
        str_repr = str(valid_quality_report)

        # 基本的な情報が含まれていることを確認
        assert "テストプロジェクト" in str_repr
        assert "10" in str_repr
        assert "85.5" in str_repr

    def test_quality_report_repr(self, valid_quality_report: QualityReport) -> None:
        """品質レポートrepr表現テスト"""
        repr_str = repr(valid_quality_report)

        # QualityReportクラス名が含まれていることを確認
        assert "QualityReport" in repr_str

    def test_quality_report_hash(self) -> None:
        """品質レポートハッシュテスト"""
        report1 = QualityReport(
            project_name="テストプロジェクト",
            total_episodes=5,
            average_score=80.0,
            problematic_episodes=[1, 3],
            suggestions=["改善案1"],
        )

        report2 = QualityReport(
            project_name="テストプロジェクト",
            total_episodes=5,
            average_score=80.0,
            problematic_episodes=[1, 3],
            suggestions=["改善案1"],
        )

        # 同じ内容のオブジェクトは同じハッシュ値を持つ
        assert hash(report1) == hash(report2)

    def test_quality_report_mutability(self, valid_quality_report: QualityReport) -> None:
        """品質レポート可変性テスト"""
        # データクラスはデフォルトで可変
        original_score = valid_quality_report.average_score
        valid_quality_report.average_score = 90.0

        assert valid_quality_report.average_score == 90.0
        assert valid_quality_report.average_score != original_score

    def test_quality_report_list_modification(self, valid_quality_report: QualityReport) -> None:
        """品質レポートリスト変更テスト"""
        # リストは参照なので変更可能
        original_length = len(valid_quality_report.problematic_episodes)
        valid_quality_report.problematic_episodes.append(10)

        assert len(valid_quality_report.problematic_episodes) == original_length + 1
        assert 10 in valid_quality_report.problematic_episodes

        # 改善提案リストも変更可能
        original_suggestions_length = len(valid_quality_report.suggestions)
        valid_quality_report.suggestions.append("新しい改善提案")

        assert len(valid_quality_report.suggestions) == original_suggestions_length + 1
        assert "新しい改善提案" in valid_quality_report.suggestions

    def test_quality_report_extreme_values(self) -> None:
        """品質レポート極端な値テスト"""
        # 非常に大きな値でのテスト
        large_report = QualityReport(
            project_name="A" * 1000,  # 長いプロジェクト名
            total_episodes=999999,
            average_score=999.999,
            problematic_episodes=list(range(10000)),  # 1万個の問題エピソード
            suggestions=["改善案"] * 1000,  # 1000個の改善提案
        )

        assert len(large_report.project_name) == 1000
        assert large_report.total_episodes == 999999
        assert large_report.average_score == 999.999
        assert len(large_report.problematic_episodes) == 10000
        assert len(large_report.suggestions) == 1000

    def test_quality_report_none_handling(self) -> None:
        """品質レポートNone値処理テスト"""
        # リストフィールドにNoneを直接代入(技術的には可能だが推奨されない)
        report = QualityReport(
            project_name="Noneテストプロジェクト",
            total_episodes=5,
            average_score=75.0,
            problematic_episodes=None,  # type: ignore
            suggestions=None,  # type: ignore
        )

        assert report.problematic_episodes is None
        assert report.suggestions is None
