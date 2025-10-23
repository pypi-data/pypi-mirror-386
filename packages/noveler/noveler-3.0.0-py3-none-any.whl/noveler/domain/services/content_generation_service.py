"""TDD-driven Content Generator
テスト駆動開発による内容生成
"""

from typing import Any


class ContentGenerator:
    """コンテンツ生成クラス(TDD実装)"""

    def generate_from_plot(self, plot_info: dict[str, Any]) -> str:
        """プロット情報からコンテンツを生成"""
        title = plot_info.get("title", "")
        episode_num = plot_info.get("episode_number", "001")
        summary = plot_info.get("summary", "")
        plot_points = plot_info.get("plot_points", [])
        characters = plot_info.get("character_focus", [])
        word_target = plot_info.get("word_count_target", 3000)

        plot_section = ""
        if plot_points:
            plot_section = "\n".join([f"- {point}" for point in plot_points])

        character_section = ""
        if characters:
            character_section = f"**登場キャラクター:** {', '.join(characters)}"

        return f"""# 第{episode_num}話 {title}

## あらすじ
{summary}

## 構成プロット
{plot_section}

{character_section}
**目標文字数:** {word_target}文字

---

## 導入部


## 展開部


## 転換部


## 結末部


---

**執筆メモ:**
-
"""

    def calculate_section_targets(self, total_words: int) -> dict[str, int]:
        """セクション別の目標文字数を計算"""
        return {
            "introduction": int(total_words * 0.25),  # 25%
            "development": int(total_words * 0.50),  # 50%
            "climax": int(total_words * 0.20),  # 20%
            "conclusion": int(total_words * 0.05),  # 5%
        }

    def generate_character_hints(self, plot_info: dict[str, Any]) -> str:
        """キャラクター描写ヒントを生成"""
        characters = plot_info.get("character_focus", [])

        if not characters:
            return ""

        hints = [f"- {character}の描写を重視" for character in characters]
        return "\n".join(hints)
