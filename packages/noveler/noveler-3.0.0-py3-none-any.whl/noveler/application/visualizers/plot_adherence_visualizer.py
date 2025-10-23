#!/usr/bin/env python3

"""Application.visualizers.plot_adherence_visualizer
Where: Application visualiser for plot adherence results.
What: Generates visual summaries highlighting plot adherence findings.
Why: Helps stakeholders quickly understand plot alignment status.
"""

from __future__ import annotations

"""プロット準拠可視化機能

プロット準拠検証結果の視覚的レポート生成
SPEC-PLOT-ADHERENCE-001準拠実装
"""


from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from noveler.application.validators.plot_adherence_validator import (
    AdherenceElementType,
    AdherenceScore,
    PlotAdherenceResult,
    PlotElement,
)

if TYPE_CHECKING:
    from pathlib import Path

# B20準拠: 共有コンポーネント必須使用
from noveler.presentation.shared.shared_utilities import console, get_logger

logger = get_logger(__name__)


class PlotAdherenceVisualizer:
    """プロット準拠可視化機能

    検証結果を視覚的に分かりやすく表示するビューコンポーネント
    SPEC-PLOT-ADHERENCE-001の可視化要件を実装
    """

    def __init__(self) -> None:
        """初期化"""
        self.logger = logger
        self._element_type_icons = {
            AdherenceElementType.KEY_EVENT: "🎯",
            AdherenceElementType.CHARACTER_DEVELOPMENT: "👤",
            AdherenceElementType.WORLD_BUILDING: "🌍",
            AdherenceElementType.FORESHADOWING: "🔮",
        }
        self._element_type_names = {
            AdherenceElementType.KEY_EVENT: "キーイベント",
            AdherenceElementType.CHARACTER_DEVELOPMENT: "キャラクター描写",
            AdherenceElementType.WORLD_BUILDING: "世界観描写",
            AdherenceElementType.FORESHADOWING: "伏線設置",
        }

    def display_adherence_report(self, result: PlotAdherenceResult) -> None:
        """プロット準拠レポートを表示

        Args:
            result: プロット準拠検証結果
        """
        console.print("\n" + "=" * 50)
        console.print(f"📊 第{result.episode_number:03d}話 プロット準拠レポート")
        console.print("━" * 50)

        # 総合準拠率表示
        self._display_overall_score(result.adherence_score)

        # 要素別準拠状況表示
        console.print("\n🎯 要素別準拠状況:")
        self._display_element_scores(result.adherence_score.element_scores)

        # 不足要素表示
        if result.missing_elements:
            console.print("\n⚠️ 不足要素:")
            self._display_missing_elements(result.missing_elements)

        # 改善提案表示
        if result.improvement_suggestions:
            console.print("\n💡 改善提案:")
            self._display_improvement_suggestions(result.improvement_suggestions)

        # 評価コメント表示
        self._display_evaluation_comment(result.adherence_score)

        console.print("=" * 50 + "\n")

    def _display_overall_score(self, score: AdherenceScore) -> None:
        """総合準拠率を表示

        Args:
            score: 準拠率データ
        """
        score_color = self._get_score_color(score.total_score)
        status_icon = self._get_score_icon(score.total_score)

        console.print(
            f"\n{status_icon} 総合準拠率: [{score_color}]{score.total_score:.1f}%[/{score_color}] (推奨: 95%以上)"
        )

        # 実装状況
        console.print(f"   実装済み: {score.implemented_count}/{score.total_count} 要素")

    def _display_element_scores(self, element_scores: dict[AdherenceElementType, float]) -> None:
        """要素別準拠率を表示

        Args:
            element_scores: 要素別準拠率辞書
        """
        for element_type, score in element_scores.items():
            icon = self._element_type_icons.get(element_type, "📋")
            name = self._element_type_names.get(element_type, str(element_type.value))
            score_color = self._get_score_color(score)
            status_icon = self._get_score_icon(score)

            console.print(f"  {status_icon} {icon} {name}: [{score_color}]{score:.0f}%[/{score_color}]")

    def _display_missing_elements(self, missing_elements: list[PlotElement]) -> None:
        """不足要素を表示

        Args:
            missing_elements: 不足要素リスト
        """
        for element in missing_elements:
            icon = self._element_type_icons.get(element.element_type, "📋")
            type_name = self._element_type_names.get(element.element_type, str(element.element_type.value))

            console.print(f"  ❌ {icon} [{type_name}] {element.description}")

    def _display_improvement_suggestions(self, suggestions: list[str]) -> None:
        """改善提案を表示

        Args:
            suggestions: 改善提案リスト
        """
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"  {i}. {suggestion}")

    def _display_evaluation_comment(self, score: AdherenceScore) -> None:
        """評価コメントを表示

        Args:
            score: 準拠率データ
        """
        if score.is_excellent:
            console.print("\n🌟 [green]優秀![/green] プロット準拠率が非常に高く、公開品質に達しています。")
        elif score.is_acceptable:
            console.print("\n✅ [yellow]良好[/yellow] 基本的な要件は満たしていますが、さらなる改善の余地があります。")
        else:
            console.print("\n⚠️ [red]要改善[/red] プロット要件を十分に満たしていません。大幅な修正をお勧めします。")

    def _get_score_color(self, score: float) -> str:
        """スコアに応じた色を取得

        Args:
            score: スコア (0-100)

        Returns:
            str: Rich用カラーコード
        """
        if score >= 95.0:
            return "green"
        if score >= 80.0:
            return "yellow"
        return "red"

    def _get_score_icon(self, score: float) -> str:
        """スコアに応じたアイコンを取得

        Args:
            score: スコア (0-100)

        Returns:
            str: アイコン文字
        """
        if score >= 95.0:
            return "✅"
        if score >= 80.0:
            return "⚠️"
        return "❌"

    def display_pre_writing_checklist(self, episode_number: int, plot_data: dict[str, Any]) -> None:
        """執筆前チェックリストを表示

        Args:
            episode_number: エピソード番号
            plot_data: プロットデータ
        """
        console.print("\n" + "=" * 50)
        console.print(f"📋 第{episode_number:03d}話 執筆チェックリスト")
        console.print("━" * 50)

        # エピソード概要
        summary = plot_data.get("episode_summary", "概要未設定")
        console.print("\n📝 エピソード概要:")
        console.print(f"   {summary}")

        # キーイベント
        key_events = plot_data.get("key_events", [])
        if key_events:
            console.print("\n🎯 必須キーイベント:")
            for _i, event in enumerate(key_events, 1):
                console.print(f"   □ {event}")

        # 必須要素
        required_elements = plot_data.get("required_elements", {})
        if required_elements:
            console.print("\n✅ 必須描写要素:")
            for category, description in required_elements.items():
                icon = self._element_type_icons.get(self._get_element_type_from_category(category), "📋")
                console.print(f"   □ {icon} {description}")

        console.print("\n💡 執筆時のポイント:")
        console.print("   • 各チェック項目を意識して執筆してください")
        console.print("   • 完了後に自動的にプロット準拠率が算出されます")
        console.print("   • 95%以上の準拠率を目指しましょう")

        console.print("=" * 50 + "\n")

    def _get_element_type_from_category(self, category: str) -> AdherenceElementType:
        """カテゴリ文字列から要素タイプを取得

        Args:
            category: カテゴリ文字列

        Returns:
            AdherenceElementType: 対応する要素タイプ
        """
        category_lower = category.lower()

        if "character" in category_lower:
            return AdherenceElementType.CHARACTER_DEVELOPMENT
        if "world" in category_lower:
            return AdherenceElementType.WORLD_BUILDING
        if "foreshadow" in category_lower:
            return AdherenceElementType.FORESHADOWING
        return AdherenceElementType.KEY_EVENT

    def generate_html_report(self, result: PlotAdherenceResult, output_path: Path) -> None:
        """HTML形式の詳細レポートを生成

        Args:
            result: プロット準拠検証結果
            output_path: 出力ファイルパス
        """
        try:
            html_content = self._generate_html_content(result)
            output_path.write_text(html_content, encoding="utf-8")

            self.logger.info("HTML レポート生成: %s", output_path)
            console.print(f"📄 詳細レポートを生成しました: {output_path}")

        except Exception as e:
            self.logger.exception("HTML レポート生成エラー")
            console.print(f"[red]❌ HTML レポート生成に失敗しました: {e}[/red]")

    def _generate_html_content(self, result: PlotAdherenceResult) -> str:
        """HTML コンテンツを生成

        Args:
            result: プロット準拠検証結果

        Returns:
            str: HTML コンテンツ
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>第{result.episode_number:03d}話 プロット準拠レポート</title>
    <style>
        body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; margin: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .score-excellent {{ color: #28a745; font-weight: bold; }}
        .score-acceptable {{ color: #ffc107; font-weight: bold; }}
        .score-poor {{ color: #dc3545; font-weight: bold; }}
        .element-section {{ margin: 20px 0; }}
        .missing-item {{ background-color: #f8d7da; padding: 8px; margin: 4px 0; border-radius: 4px; }}
        .suggestion-item {{ background-color: #d1ecf1; padding: 8px; margin: 4px 0; border-radius: 4px; }}
        .timestamp {{ text-align: right; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>第{result.episode_number:03d}話 プロット準拠レポート</h1>
        <div class="timestamp">生成日時: {timestamp}</div>
    </div>

    <div class="score-section">
        <h2>📊 総合準拠率</h2>
        <p class="score-{self._get_score_class(result.adherence_score.total_score)}">
            {result.adherence_score.total_score:.1f}%
            ({result.adherence_score.implemented_count}/{result.adherence_score.total_count} 要素実装済み)
        </p>
    </div>

    <div class="element-section">
        <h2>🎯 要素別準拠状況</h2>
        <ul>
"""

        for element_type, score in result.adherence_score.element_scores.items():
            name = self._element_type_names.get(element_type, str(element_type.value))
            class_name = self._get_score_class(score)
            html += f'            <li><span class="score-{class_name}">{name}: {score:.0f}%</span></li>\n'

        html += """        </ul>
    </div>
"""

        if result.missing_elements:
            html += """    <div class="element-section">
        <h2>⚠️ 不足要素</h2>
"""
            for element in result.missing_elements:
                html += f'        <div class="missing-item">{element.description}</div>\n'
            html += "    </div>\n"

        if result.improvement_suggestions:
            html += """    <div class="element-section">
        <h2>💡 改善提案</h2>
"""
            for suggestion in result.improvement_suggestions:
                html += f'        <div class="suggestion-item">{suggestion}</div>\n'
            html += "    </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _get_score_class(self, score: float) -> str:
        """スコアに応じたCSSクラス名を取得

        Args:
            score: スコア (0-100)

        Returns:
            str: CSSクラス名
        """
        if score >= 95.0:
            return "excellent"
        if score >= 80.0:
            return "acceptable"
        return "poor"
