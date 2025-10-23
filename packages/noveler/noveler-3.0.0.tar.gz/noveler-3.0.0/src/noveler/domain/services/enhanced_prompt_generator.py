#!/usr/bin/env python3
"""強化プロンプト生成サービス

A31カテゴリ別に最適化されたプロンプトを生成し、
手動Claude Code分析を上回る精度を実現するドメインサービス。
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


@dataclass
class PromptContext:
    """プロンプト生成コンテキスト"""

    project_name: str
    episode_number: int
    episode_content: str
    target_category: A31EvaluationCategory
    previous_episode_content: str | None = None
    character_profiles: dict[str, Any] | None = None
    quality_threshold: float = 80.0


@dataclass
class GeneratedPrompt:
    """生成されたプロンプト"""

    category: A31EvaluationCategory
    system_prompt: str
    user_prompt: str
    evaluation_criteria: list[str]
    expected_output_format: str
    confidence_boost_factors: list[str]


class EnhancedPromptGenerator:
    """強化プロンプト生成サービス

    各A31カテゴリに特化した高精度プロンプトを生成。
    手動Claude Code分析レベルの詳細度と正確性を実現。
    """

    def __init__(self) -> None:
        """強化プロンプト生成サービス初期化"""
        self._category_templates = self._initialize_category_templates()
        self._evaluation_criteria = self._initialize_evaluation_criteria()
        self._output_formats = self._initialize_output_formats()

    def generate_category_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """カテゴリ別プロンプトを生成

        Args:
            context: プロンプト生成コンテキスト

        Returns:
            GeneratedPrompt: 生成されたプロンプト
        """
        category = context.target_category

        if category == A31EvaluationCategory.FORMAT_CHECK:
            return self._generate_format_check_prompt(context)
        if category == A31EvaluationCategory.CONTENT_BALANCE:
            return self._generate_content_balance_prompt(context)
        if category == A31EvaluationCategory.STYLE_CONSISTENCY:
            return self._generate_style_consistency_prompt(context)
        if category == A31EvaluationCategory.READABILITY_CHECK:
            return self._generate_readability_prompt(context)
        if category == A31EvaluationCategory.CHARACTER_CONSISTENCY:
            return self._generate_character_consistency_prompt(context)
        return self._generate_generic_prompt(context)

    def _generate_format_check_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """フォーマット・構造チェック用プロンプト生成"""
        system_prompt = f"""あなたは日本語小説の構造・フォーマット分析専門家です。

以下の観点で{context.project_name}のエピソード{context.episode_number}を徹底分析してください：

【重要な分析観点】
1. 冒頭3行の読者引き込み効果（具体的な改善案必須）
2. 段落構成の適切性（理想的な分割位置を提示）
3. 章節構造の明確性（見出し・場面転換の効果測定）
4. 文章のリズムと緩急（具体的な修正箇所を指摘）

【評価基準】
- 90-100点: 商業出版レベルの完璧な構造
- 80-89点: 読者を惹きつける良好な構造
- 70-79点: 基本構造は保たれているが改善余地あり
- 60-69点: 構造的問題が複数存在
- 60点未満: 大幅な構造修正が必要

必ず行番号を指定した具体的修正案を提示してください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}

## 要求分析
上記エピソードについて、フォーマット・構造の観点から詳細分析を実行してください。

特に以下を重点的に：
1. 冒頭の引き込み効果（1-3行目の具体的改善案）
2. 段落分割の最適化（推奨分割位置）
3. 場面転換の明確性（改善が必要な箇所）
4. 全体的な読みやすさ向上策"""

        return GeneratedPrompt(
            category=A31EvaluationCategory.FORMAT_CHECK,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=[
                "冒頭3行の引き込み効果測定",
                "段落構成の論理性評価",
                "章節構造の明確性チェック",
                "読みやすさの定量評価",
            ],
            expected_output_format="行番号付き具体的修正案と100点満点スコア",
            confidence_boost_factors=["商業出版作品との比較分析", "読者視点での構造評価", "編集者基準での品質判定"],
        )

    def _generate_content_balance_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """内容バランス分析用プロンプト生成"""
        system_prompt = f"""あなたは小説の内容バランス分析専門家です。

{context.project_name}のエピソード{context.episode_number}について、以下の観点で詳細分析：

【重要分析観点】
1. 会話と地の文の黄金比率（理想: 40-60%）
2. 五感描写の充実度（視覚・聴覚・触覚・嗅覚・味覚の具体的欠損指摘）
3. 情報密度の適切性（薄い箇所の具体的改善案）
4. 展開のテンポ感（遅い・早い箇所の特定）

【評価基準】
- 90+点: 完璧なバランスで読者を飽きさせない
- 80-89点: 良好なバランス、軽微な調整で向上
- 70-79点: バランス問題あり、具体的改善必要
- 60-69点: 大きなバランス崩れ、大幅修正必要
- 60点未満: 根本的な構成見直し必要

行番号を指定した具体的改善提案を必ず含めてください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}

## 分析要求
内容バランスの観点から徹底分析を実行してください。

重点分析項目：
1. 会話文比率の測定と最適化提案
2. 五感描写の具体的不足箇所と追加案
3. 情報密度が低い段落の特定と改善案
4. テンポ感の問題箇所と調整方法

必ず行番号付きで具体的修正案を提示してください。"""

        return GeneratedPrompt(
            category=A31EvaluationCategory.CONTENT_BALANCE,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=[
                "会話・地の文比率の定量評価",
                "五感描写の網羅性チェック",
                "情報密度の均一性測定",
                "展開テンポの適切性評価",
            ],
            expected_output_format="比率データと行番号付き改善案",
            confidence_boost_factors=[
                "ベストセラー小説との比較データ",
                "読者エンゲージメント最適化",
                "エンターテイメント性の定量評価",
            ],
        )

    def _generate_style_consistency_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """文体一貫性分析用プロンプト生成"""
        system_prompt = f"""あなたは日本語文体分析の専門家です。

{context.project_name}のエピソード{context.episode_number}の文体について、以下を詳細分析：

【核心分析観点】
1. 文末表現の多様性（「だった」連続使用等の単調性検出）
2. 敬語・丁寧語・普通語の統一性
3. 同一語句の過度な反復パターン
4. 文章の自然性と読みやすさ

【評価基準】
- 95+点: プロ作家レベルの完璧な文体統一
- 85-94点: 高品質、軽微な調整で完璧
- 75-84点: 良好だが明確な改善点あり
- 65-74点: 文体の不統一が目立つ
- 65点未満: 大幅な文体修正が必要

必ず問題箇所の行番号と具体的修正例を提示してください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}

## 分析要求
文体一貫性の観点から詳細分析を実行してください。

特に重点チェック：
1. 文末表現の単調性（「だった」「である」等の連続使用）
2. 文体レベルの統一性（敬語混在等）
3. 語句反復の適切性（過度な反復の特定）
4. 自然な日本語表現の確認

各問題に対して行番号付きの具体的修正案を提示してください。"""

        return GeneratedPrompt(
            category=A31EvaluationCategory.STYLE_CONSISTENCY,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=[
                "文末表現多様性の定量評価",
                "文体レベル統一性チェック",
                "語句反復頻度の適切性評価",
                "日本語として自然性判定",
            ],
            expected_output_format="問題パターンと行番号付き修正例",
            confidence_boost_factors=["プロ作家の文体パターン分析", "日本語文法の厳密な適用", "読み手の負担軽減観点"],
        )

    def _generate_readability_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """読みやすさ分析用プロンプト生成"""
        system_prompt = f"""あなたは読みやすさ分析の専門家です。

{context.project_name}のエピソード{context.episode_number}について読みやすさを徹底分析：

【重要分析観点】
1. 文章長のバランス（短・中・長文の配分）
2. 漢字・ひらがなの理想的配分（7:3比率）
3. 複雑な文構造の特定と簡略化提案
4. 読み手の負担となる表現の検出

【評価基準】
- 90+点: 年齢層を問わず読みやすい完璧な文章
- 80-89点: 高い読みやすさ、軽微な調整で完璧
- 70-79点: 読みやすいが改善余地あり
- 60-69点: 読みにくい箇所が複数存在
- 60点未満: 大幅な読みやすさ改善が必要

必ず行番号付きの具体的改善案を提示してください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}

## 分析要求
読みやすさの観点から詳細分析を実行してください。

重点分析項目：
1. 文章長バランスの最適化提案
2. 漢字・ひらがな比率の調整案
3. 複雑な文構造の簡略化提案
4. 読み手の負担軽減策

各改善案に行番号と具体的修正例を含めてください。"""

        return GeneratedPrompt(
            category=A31EvaluationCategory.READABILITY_CHECK,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=[
                "文章長バランスの定量評価",
                "文字種比率の適切性測定",
                "文構造複雑度の評価",
                "認知負荷の軽減度評価",
            ],
            expected_output_format="読みやすさ指標と行番号付き改善案",
            confidence_boost_factors=["読書体験の最適化", "認知科学に基づく分析", "多様な読者層への配慮"],
        )

    def _generate_character_consistency_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """キャラクター一貫性分析用プロンプト生成"""
        character_info = ""
        if context.character_profiles:
            character_info = f"\n## キャラクター設定\n{context.character_profiles}"

        system_prompt = f"""あなたはキャラクター一貫性分析の専門家です。

{context.project_name}の第{context.episode_number}話について、キャラクターの一貫性を詳細分析：

【重要分析観点】
1. 各キャラクターの話し方の一貫性（口調・語尾・敬語使用）
2. 行動パターンの設定との一致性
3. 性格表現の首尾一貫性
4. キャラクター間の関係性の自然さ

【評価基準】
- 95+点: 完璧なキャラクター造形と一貫性
- 85-94点: 高い一貫性、軽微な調整で完璧
- 75-84点: 良好だが一部不一致あり
- 65-74点: キャラクター設定との齟齬が目立つ
- 65点未満: 大幅なキャラクター修正が必要

キャラクター名と行番号を明記した具体的修正案を提示してください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}{character_info}

## 分析要求
キャラクター一貫性の観点から詳細分析を実行してください。

重点分析項目：
1. 各キャラクターの話し方の一貫性チェック
2. 行動パターンの設定適合性
3. 性格表現の首尾一貫性確認
4. キャラクター間関係の自然性評価

キャラクター名・行番号・具体的修正案をセットで提示してください。"""

        return GeneratedPrompt(
            category=A31EvaluationCategory.CHARACTER_CONSISTENCY,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=[
                "話し方パターンの一貫性評価",
                "行動の設定適合性チェック",
                "性格表現の首尾一貫性測定",
                "キャラクター関係の自然性評価",
            ],
            expected_output_format="キャラクター別一貫性評価と修正案",
            confidence_boost_factors=[
                "キャラクター設定との厳密な照合",
                "人物造形の心理学的妥当性",
                "読者の感情移入促進観点",
            ],
        )

    def _generate_generic_prompt(self, context: PromptContext) -> GeneratedPrompt:
        """汎用プロンプト生成"""
        system_prompt = f"""あなたは小説品質分析の専門家です。

{context.project_name}のエピソード{context.episode_number}について、{context.target_category.value}の観点から詳細分析を実行してください。

【基本評価基準】
- 90+点: 商業出版レベルの高品質
- 80-89点: 良好な品質、軽微な改善で完璧
- 70-79点: 標準的品質、改善余地あり
- 60-69点: 品質問題あり、改善必要
- 60点未満: 大幅な改善が必要

具体的な改善提案を含めてください。"""

        user_prompt = f"""# 分析対象エピソード
プロジェクト名: {context.project_name}
エピソード番号: {context.episode_number}

## エピソード内容
{context.episode_content}

## 分析要求
{context.target_category.value}の観点から詳細分析を実行し、具体的改善提案を提示してください。"""

        return GeneratedPrompt(
            category=context.target_category,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_criteria=["基本品質評価", "改善点の特定"],
            expected_output_format="スコアと改善提案",
            confidence_boost_factors=["専門的観点での分析"],
        )

    def _initialize_category_templates(self) -> dict[A31EvaluationCategory, str]:
        """カテゴリテンプレート初期化"""
        return {
            A31EvaluationCategory.FORMAT_CHECK: "構造・フォーマット分析専門家",
            A31EvaluationCategory.CONTENT_BALANCE: "内容バランス分析専門家",
            A31EvaluationCategory.STYLE_CONSISTENCY: "文体一貫性分析専門家",
            A31EvaluationCategory.READABILITY_CHECK: "読みやすさ分析専門家",
            A31EvaluationCategory.CHARACTER_CONSISTENCY: "キャラクター一貫性分析専門家",
        }

    def _initialize_evaluation_criteria(self) -> dict[A31EvaluationCategory, list[str]]:
        """評価基準初期化"""
        return {
            A31EvaluationCategory.FORMAT_CHECK: ["冒頭引き込み効果", "段落構成", "構造明確性", "読みやすさ"],
            A31EvaluationCategory.CONTENT_BALANCE: ["会話・地の文比率", "五感描写", "情報密度", "展開テンポ"],
            A31EvaluationCategory.STYLE_CONSISTENCY: ["文末表現多様性", "文体統一性", "語句反復", "自然性"],
            A31EvaluationCategory.READABILITY_CHECK: ["文章長バランス", "文字種比率", "文構造", "認知負荷"],
            A31EvaluationCategory.CHARACTER_CONSISTENCY: ["話し方一貫性", "行動パターン", "性格表現", "関係性"],
        }

    def _initialize_output_formats(self) -> dict[A31EvaluationCategory, str]:
        """出力フォーマット初期化"""
        return {
            A31EvaluationCategory.FORMAT_CHECK: "行番号付き構造改善案とスコア",
            A31EvaluationCategory.CONTENT_BALANCE: "比率データと改善提案",
            A31EvaluationCategory.STYLE_CONSISTENCY: "文体問題パターンと修正例",
            A31EvaluationCategory.READABILITY_CHECK: "読みやすさ指標と改善案",
            A31EvaluationCategory.CHARACTER_CONSISTENCY: "キャラクター別評価と修正案",
        }
