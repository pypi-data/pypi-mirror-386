#!/usr/bin/env python3
"""文章リズム視覚化サービス（Domain-safe）

Domain 層では外部UI依存を持たず、テキストレポート生成に限定する。
リッチ表示は上位層で担当する。
"""


# DDD違反修正: Domain層から外部UI依存を除去し、テキスト表現のみ提供する。

from noveler.domain.utils.domain_console import get_console
from noveler.domain.value_objects.text_rhythm_analysis import TextRhythmReport


class TextRhythmVisualizer:
    """文章リズム視覚化サービス

    責務:
        - 文章リズム分析結果の視覚的表現
        - 問題箇所のハイライトと改善提案の提示
        - 統計情報と分布のグラフィカル表示

    設計原則:
        - Richライブラリによる美しいターミナル出力
        - 色分けとアイコンによる直感的な情報伝達
        - 深刻度別の問題グルーピング


    """

    def __init__(self, console: object | None = None) -> None:
        """初期化

        Args:
            console: コンソール相当（省略時はDomain NullConsole）
        """
        self.console = console or get_console()

        # 色やリッチ表現は上位層に委譲

    def display_rhythm_report(self, report: TextRhythmReport) -> None:
        """リズム分析レポートの表示

        処理フロー:
            1. 総合スコアとランクの表示
            2. 統計情報のテーブル表示
            3. 文字数分布のプログレスバー表示
            4. 問題一覧の深刻度別表示
            5. 各文の詳細情報表示（オプション）

        Args:
            report: TextRhythmReportインスタンス
        """
        # Domain層ではリッチ描画は行わず、テキストレポートを出力
        self.console.print(self.generate_text_report(report))

    def _get_grade_text(self, grade: str) -> str:
        """ランクテキストの取得"""
        grade_texts = {"excellent": "優秀", "good": "良好", "fair": "普通", "poor": "要改善", "critical": "要修正"}
        return grade_texts.get(grade, grade)

    def _get_average_length_evaluation(self, avg_length: float) -> str:
        """平均文字数の評価をテキストで返す"""
        if 25 <= avg_length <= 45:
            return "理想的"
        if 20 <= avg_length < 25 or 45 < avg_length <= 50:
            return "やや長め/短め"
        return "要調整"

    def _get_std_dev_evaluation(self, std_dev: float) -> str:
        """標準偏差の評価をテキストで返す"""
        if 8 <= std_dev <= 20:
            return "良好"
        if std_dev < 8:
            return "単調"
        return "ばらつき大"

    def _get_rhythm_score_evaluation(self, score: float) -> str:
        """リズムスコアの評価をテキストで返す"""
        if score >= 80:
            return "優秀"
        if score >= 60:
            return "良好"
        return "要改善"

    def generate_text_report(self, report: TextRhythmReport) -> str:
        """テキスト形式のレポート生成

        プレーンテキスト形式のレポートを生成。
        ログファイルや他システムへの出力用。

        Args:
            report: TextRhythmReportインスタンス

        Returns:
            整形されたテキストレポート
        """
        lines = []
        lines.append("📊 文章リズム・読みやすさ分析レポート")
        lines.append("=" * 50)
        lines.append("")

        # 総合スコア
        lines.append(
            f"🎯 総合スコア: {report.overall_score:.1f}/100 ({self._get_grade_text(report.readability_grade)})"
        )
        lines.append("")

        # 統計情報
        stats = report.statistics
        lines.append("📈 統計情報:")
        lines.append(f"  総文数: {stats.total_sentences}文")
        lines.append(
            f"  平均文字数: {stats.average_length:.1f}文字 ({self._get_average_length_evaluation(stats.average_length)})"
        )
        lines.append(f"  文字数範囲: {stats.min_length}〜{stats.max_length}文字")
        lines.append(f"  標準偏差: {stats.std_deviation:.1f} ({self._get_std_dev_evaluation(stats.std_deviation)})")
        lines.append(
            f"  リズムスコア: {stats.rhythm_score:.1f}/100 ({self._get_rhythm_score_evaluation(stats.rhythm_score)})"
        )
        lines.append("")

        # 分布情報
        percentages = stats.get_distribution_percentages()
        lines.append("📊 文字数分布:")
        lines.append(f"  極短文 (≤15字): {percentages['very_short']:.1f}% ({stats.very_short_count}文)")
        lines.append(f"  短文 (16-25字): {percentages['short']:.1f}% ({stats.short_count}文)")
        lines.append(f"  中文 (26-40字): {percentages['medium']:.1f}% ({stats.medium_count}文)")
        lines.append(f"  長文 (41-60字): {percentages['long']:.1f}% ({stats.long_count}文)")
        lines.append(f"  極長文 (≥61字): {percentages['very_long']:.1f}% ({stats.very_long_count}文)")
        lines.append("")

        # 問題一覧
        if report.issues:
            lines.append(f"🚨 発見された問題: {len(report.issues)}件")
            for i, issue in enumerate(report.issues, 1):
                lines.append(f"  {i}. {issue.description}")
                lines.append(f"     提案: {issue.suggestion}")
        else:
            lines.append("✅ 問題は見つかりませんでした")

        return "\n".join(lines)
