#!/usr/bin/env python3
"""
Claude Codeプロンプト最適化サービス

Claude Codeの特性に合わせたプロンプト最適化を実装する
インフラストラクチャ層のサービス。
"""

import re
from typing import Any

from noveler.domain.entities.prompt_generation import OptimizationTarget
from noveler.domain.services.prompt_generation_service import PromptOptimizer


class ClaudeCodePromptOptimizer(PromptOptimizer):
    """Claude Code最適化プロンプトオプティマイザー

    Claude Codeの特性（トークン制限、構造化指示の好み等）に
    特化したプロンプト最適化を実装する。
    """

    # トークン数推定の基準値（日本語文字の場合）
    CHARS_PER_TOKEN_JP = 2.5
    CHARS_PER_TOKEN_EN = 4.0

    # 各ターゲットの推奨最大トークン数
    MAX_TOKENS = {
        OptimizationTarget.CLAUDE_CODE: 18000,
        OptimizationTarget.CLAUDE_WEB: 20000,
        OptimizationTarget.CHATGPT: 15000,
        OptimizationTarget.GENERIC: 12000,
    }

    def optimize_for_target(self, prompt: str, target: OptimizationTarget) -> str:
        """ターゲット向け最適化"""
        if target == OptimizationTarget.CLAUDE_CODE:
            return self._optimize_for_claude_code(prompt)
        if target == OptimizationTarget.CLAUDE_WEB:
            return self._optimize_for_claude_web(prompt)
        if target == OptimizationTarget.CHATGPT:
            return self._optimize_for_chatgpt(prompt)
        return self._optimize_generic(prompt)

    def estimate_token_count(self, prompt: str) -> int:
        """トークン数推定"""
        # 日本語文字と英語文字を分別してトークン数推定
        jp_chars = len(re.findall(r"[ひらがなカタカナ漢字]", prompt))
        en_chars = len(re.findall(r"[a-zA-Z]", prompt))
        other_chars = len(prompt) - jp_chars - en_chars

        # トークン数推定
        jp_tokens = jp_chars / self.CHARS_PER_TOKEN_JP
        en_tokens = en_chars / self.CHARS_PER_TOKEN_EN
        other_tokens = other_chars / 3.0  # その他文字の平均的な変換率

        return int(jp_tokens + en_tokens + other_tokens)

    def _optimize_for_claude_code(self, prompt: str) -> str:
        """Claude Code向け最適化"""
        optimized = prompt

        # 1. 構造化マークダウンの強化
        optimized = self._enhance_markdown_structure(optimized)

        # 2. ステップバイステップ指示の明確化
        optimized = self._clarify_step_by_step_instructions(optimized)

        # 3. YAML出力強制の強化
        optimized = self._strengthen_yaml_output_requirement(optimized)

        # 4. Claude Code特有の注意事項追加
        optimized = self._add_claude_code_specific_notes(optimized)

        # 5. トークン数制限チェック
        return self._trim_to_token_limit(optimized, OptimizationTarget.CLAUDE_CODE)


    def _optimize_for_claude_web(self, prompt: str) -> str:
        """Claude Web向け最適化"""
        optimized = prompt

        # Claude Webは対話的な要素を強化
        optimized = self._add_interactive_elements(optimized)
        return self._trim_to_token_limit(optimized, OptimizationTarget.CLAUDE_WEB)


    def _optimize_for_chatgpt(self, prompt: str) -> str:
        """ChatGPT向け最適化"""
        optimized = prompt

        # ChatGPTは簡潔で直接的な指示を好む
        optimized = self._make_instructions_more_direct(optimized)
        return self._trim_to_token_limit(optimized, OptimizationTarget.CHATGPT)


    def _optimize_generic(self, prompt: str) -> str:
        """汎用最適化"""
        optimized = prompt

        # 最も保守的な最適化
        return self._trim_to_token_limit(optimized, OptimizationTarget.GENERIC)


    def _enhance_markdown_structure(self, prompt: str) -> str:
        """マークダウン構造強化"""
        # セクションヘッダーの階層化を強化
        lines = prompt.split("\n")
        enhanced_lines = []

        for line in lines:
            # Stage セクションの視認性向上
            if line.strip().startswith("## Stage"):
                enhanced_lines.append("")
                enhanced_lines.append("---")
                enhanced_lines.append("")
                enhanced_lines.append(line)
                enhanced_lines.append("")
            else:
                enhanced_lines.append(line)

        return "\n".join(enhanced_lines)

    def _clarify_step_by_step_instructions(self, prompt: str) -> str:
        """ステップ指示明確化"""
        # 作業手順セクションに番号と優先度を追加
        clarified = prompt

        # "🛠 作業手順" セクションの後の項目を強化
        step_pattern = r"(### 🛠 作業手順\n\n)(.*?)(?=\n### |$)"

        def enhance_steps(match) -> Any:
            header = match.group(1)
            content = match.group(2)

            # 既存の番号付きリストを強化
            enhanced_content = re.sub(
                r"^(\d+)\. (.+)$",
                r"**\1.** \2\n   > **重要**: この手順を完了してから次に進んでください。",
                content,
                flags=re.MULTILINE,
            )

            return header + enhanced_content

        return re.sub(step_pattern, enhance_steps, clarified, flags=re.DOTALL)


    def _strengthen_yaml_output_requirement(self, prompt: str) -> str:
        """YAML出力要求強化"""
        # プロンプト末尾に強力なYAML出力指示を追加
        yaml_enforcement = """

## ⚠️ 絶対遵守事項

**YAML出力形式の厳守**:
    - 出力は必ずYAML形式でなければなりません
- コードブロック（```yaml）で囲んで出力してください
- YAMLの構文エラーがないことを確認してください
- テンプレート構造に完全に準拠してください

**出力例**:
    ```yaml
episode_info:
  episode_number: 12
  title: "エピソードタイトル"
  # ... 他の項目
```

**重要**: マークダウン形式の説明文は出力せず、YAML形式のプロット情報のみを出力してください。"""

        return prompt + yaml_enforcement

    def _add_claude_code_specific_notes(self, prompt: str) -> str:
        """Claude Code特有注意事項追加"""
        claude_code_notes = """

## 💻 Claude Code実行環境での注意点

- このプロンプトはClaude Codeで実行されています
- ファイル作成や編集は想定していません
- プロット情報のYAML出力のみを行ってください
- 長時間の処理は避けて、効率的に作業してください"""

        return prompt + claude_code_notes

    def _add_interactive_elements(self, prompt: str) -> str:
        """対話的要素追加（Claude Web向け）"""
        interactive_note = """

## 💬 対話的改善

プロット作成後、以下について質問してください：
- 改善したい部分はありますか？
- 追加したい要素はありますか？
- 不明な点はありますか？"""

        return prompt + interactive_note

    def _make_instructions_more_direct(self, prompt: str) -> str:
        """指示の直接化（ChatGPT向け）"""
        # 冗長な説明を簡潔に
        direct = prompt

        # "してください" → "せよ" など、より直接的な表現に変換
        replacements = [
            (r"してください", "せよ"),
            (r"お願いします", ""),
            (r"以下の.*?に従って", ""),
        ]

        for pattern, replacement in replacements:
            direct = re.sub(pattern, replacement, direct)

        return direct

    def _trim_to_token_limit(self, prompt: str, target: OptimizationTarget) -> str:
        """トークン数制限への調整"""
        max_tokens = self.MAX_TOKENS.get(target, 12000)
        current_tokens = self.estimate_token_count(prompt)

        if current_tokens <= max_tokens:
            return prompt

        # トークン数オーバーの場合、段階的に内容を削減
        lines = prompt.split("\n")

        # 1. 空行の削減
        lines = [
            line for i, line in enumerate(lines) if not (line.strip() == "" and i > 0 and lines[i - 1].strip() == "")
        ]

        # 2. 例文の削減
        lines = [line for line in lines if not line.strip().startswith("例：")]

        # 3. 説明文の簡略化
        simplified_lines = []
        for line in lines:
            if len(line) > 100 and not line.strip().startswith("#"):
                # 長い説明文を短縮
                simplified = line[:80] + "..." if len(line) > 80 else line
                simplified_lines.append(simplified)
            else:
                simplified_lines.append(line)

        trimmed = "\n".join(simplified_lines)

        # 再チェック
        if self.estimate_token_count(trimmed) > max_tokens:
            # さらに削減が必要な場合は、セクション単位で削減
            sections = trimmed.split("## ")
            essential_sections = []

            for section in sections:
                if any(keyword in section for keyword in ["Stage", "絶対遵守", "実行指示"]):
                    essential_sections.append(section)

            trimmed = "## ".join(essential_sections)
        return trimmed
