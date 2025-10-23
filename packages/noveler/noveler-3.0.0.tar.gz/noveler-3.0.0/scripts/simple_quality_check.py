#!/usr/bin/env python3
"""シンプルな品質チェックスクリプト"""

import re
from pathlib import Path
from typing import Any


def analyze_manuscript(file_path: Path) -> dict[str, Any]:
    """原稿ファイルの品質分析"""

    text = file_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 基本統計
    word_count = len(re.findall(r"\S+", text))
    char_count = len(re.sub(r"\s", "", text))
    line_count = len([line for line in lines if line.strip()])

    # 文章構造分析
    dialogue_lines = [line for line in lines if "「" in line and "」" in line]
    dialogue_ratio = len(dialogue_lines) / max(line_count, 1)

    # セクション分析
    sections = [line for line in lines if line.startswith("#")]

    # 品質指標計算
    avg_words_per_line = word_count / max(line_count, 1)
    readability_score = min(100, max(0, 100 - abs(avg_words_per_line - 20) * 2))

    return {
        "basic_stats": {
            "word_count": word_count,
            "char_count": char_count,
            "line_count": line_count,
            "dialogue_lines": len(dialogue_lines),
            "sections": len(sections)
        },
        "quality_metrics": {
            "dialogue_ratio": round(dialogue_ratio * 100, 1),
            "avg_words_per_line": round(avg_words_per_line, 1),
            "readability_score": round(readability_score, 1)
        },
        "recommendations": generate_recommendations(word_count, dialogue_ratio, readability_score)
    }


def generate_recommendations(word_count: int, dialogue_ratio: float, readability_score: float) -> list[str]:
    """改善提案の生成"""
    recommendations = []

    if word_count < 500:
        recommendations.append("📝 文章量が少なめです。より詳細な描写を追加することを検討してください。")
    elif word_count > 5000:
        recommendations.append("📚 文章量が多めです。章を分割することを検討してください。")

    if dialogue_ratio < 0.2:
        recommendations.append("💬 会話が少なめです。キャラクター間の対話を増やすことを検討してください。")
    elif dialogue_ratio > 0.6:
        recommendations.append("💭 地の文が少なめです。情景描写や心理描写を追加することを検討してください。")

    if readability_score < 60:
        recommendations.append("📖 読みやすさを改善できます。文の長さを調整してください。")

    if not recommendations:
        recommendations.append("✨ 全体的に良好なバランスです！")

    return recommendations


def main():
    """メイン処理"""
    manuscript_file = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/40_原稿/第001話_MCPサーバーテスト.md")

    if not manuscript_file.exists():
        print(f"❌ ファイルが見つかりません: {manuscript_file}")
        return

    print(f"📝 品質チェック実行中: {manuscript_file.name}")
    print("=" * 60)

    results = analyze_manuscript(manuscript_file)

    # 基本統計表示
    print("\n📊 基本統計:")
    stats = results["basic_stats"]
    print(f"  - 単語数: {stats['word_count']:,}")
    print(f"  - 文字数: {stats['char_count']:,}")
    print(f"  - 行数: {stats['line_count']}")
    print(f"  - 会話行数: {stats['dialogue_lines']}")
    print(f"  - セクション数: {stats['sections']}")

    # 品質指標表示
    print("\n⭐ 品質指標:")
    metrics = results["quality_metrics"]
    print(f"  - 会話比率: {metrics['dialogue_ratio']}%")
    print(f"  - 平均単語数/行: {metrics['avg_words_per_line']}")
    print(f"  - 読みやすさスコア: {metrics['readability_score']}/100")

    # 改善提案表示
    print("\n💡 改善提案:")
    for recommendation in results["recommendations"]:
        print(f"  {recommendation}")

    print("\n" + "=" * 60)
    print("✅ 品質チェック完了")


if __name__ == "__main__":
    main()
