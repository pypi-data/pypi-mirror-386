#!/usr/bin/env python3
"""
プロンプト生成ドメインサービス

A24ガイドベースのプロンプト生成に関するビジネスロジックを実装する。
DDD設計に基づき、プロンプト生成の複雑なビジネスルールを管理する。
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.entities.prompt_generation import (
    A24Stage,
    A24StagePrompt,
    ContextElement,
    ContextElementType,
    OptimizationTarget,
    PromptGenerationSession,
)


class A24GuideRepository(ABC):
    """A24ガイドリポジトリ抽象基底クラス"""

    @abstractmethod
    def get_stage_instructions(self, stage: A24Stage) -> list[str]:
        """指定段階の指示取得"""

    @abstractmethod
    def get_template_structure(self) -> dict[str, Any]:
        """テンプレート構造取得"""

    @abstractmethod
    def get_validation_criteria(self, stage: A24Stage) -> list[str]:
        """指定段階の検証基準取得"""


class ProjectContextRepository(ABC):
    """プロジェクトコンテキストリポジトリ抽象基底クラス"""

    @abstractmethod
    def extract_foreshadowing_elements(self, episode_number: int) -> list[ContextElement]:
        """伏線要素抽出"""

    @abstractmethod
    def extract_important_scenes(self, episode_number: int) -> list[ContextElement]:
        """重要シーン抽出"""

    @abstractmethod
    def extract_chapter_connections(self, episode_number: int) -> list[ContextElement]:
        """章間連携抽出"""


class PromptOptimizer(ABC):
    """プロンプト最適化抽象基底クラス"""

    @abstractmethod
    def optimize_for_target(self, prompt: str, target: OptimizationTarget) -> str:
        """ターゲット向け最適化"""

    @abstractmethod
    def estimate_token_count(self, prompt: str) -> int:
        """トークン数推定"""


class PromptGenerationService:
    """プロンプト生成ドメインサービス

    A24ガイドに基づくプロンプト生成の核となるビジネスロジックを実装。
    段階的プロンプト構築、コンテキスト統合、最適化処理を担当する。
    """

    def __init__(
        self,
        a24_guide_repo: A24GuideRepository,
        context_repo: ProjectContextRepository,
        optimizer: PromptOptimizer,
    ) -> None:
        self._a24_guide_repo = a24_guide_repo
        self._context_repo = context_repo
        self._optimizer = optimizer

    def generate_prompt_for_episode(
        self,
        session: PromptGenerationSession,
    ) -> None:
        """エピソード向けプロンプト生成

        A24ガイドの4段階プロセスに従ってプロンプトを生成し、
        セッションに結果を記録する。

        Args:
            session: プロンプト生成セッション（状態管理）

        Raises:
            ValueError: セッション情報が不正な場合
            RuntimeError: 生成処理でエラーが発生した場合
        """
        if not session.episode_number or not session.project_name:
            msg = "エピソード番号とプロジェクト名は必須です"
            raise ValueError(msg)

        try:
            # Step 1: コンテキスト要素収集
            self._collect_context_elements(session)

            # Step 2: 段階別プロンプト生成
            stage_prompts = self._generate_stage_prompts(session)

            # Step 3: プロンプト統合
            integrated_prompt = self._integrate_prompts(stage_prompts, session)

            # Step 4: ターゲット最適化
            optimized_prompt = self._optimizer.optimize_for_target(integrated_prompt, session.optimization_target)

            # Step 5: 結果セット
            token_estimate = self._optimizer.estimate_token_count(optimized_prompt)
            session.finalize_prompt(optimized_prompt, token_estimate, 0)  # TODO: 実際の生成時間

        except Exception as e:
            session.add_error(f"プロンプト生成エラー: {e!s}")
            msg = f"プロンプト生成に失敗しました: {e!s}"
            raise RuntimeError(msg) from e

    def _collect_context_elements(self, session: PromptGenerationSession) -> None:
        """コンテキスト要素収集

        設定に基づいて各種コンテキスト要素を収集し、セッションに追加する。
        優先度に基づく自動フィルタリングも実行する。
        """
        episode_num = session.episode_number

        # 伏線要素収集
        if session.include_foreshadowing:
            try:
                foreshadowing_elements = self._context_repo.extract_foreshadowing_elements(episode_num)
                for element in foreshadowing_elements:
                    session.add_context_element(element)

                if not foreshadowing_elements:
                    session.add_warning(f"第{episode_num}話の伏線要素が見つかりませんでした")

            except Exception as e:
                session.add_warning(f"伏線要素の取得に失敗: {e!s}")

        # 重要シーン収集
        if session.include_important_scenes:
            try:
                scene_elements = self._context_repo.extract_important_scenes(episode_num)
                for element in scene_elements:
                    session.add_context_element(element)

                if not scene_elements:
                    session.add_warning(f"第{episode_num}話の重要シーンが見つかりませんでした")

            except Exception as e:
                session.add_warning(f"重要シーン取得に失敗: {e!s}")

        # 章間連携要素収集
        try:
            connection_elements = self._context_repo.extract_chapter_connections(episode_num)
            for element in connection_elements:
                session.add_context_element(element)

        except Exception as e:
            session.add_warning(f"章間連携要素取得に失敗: {e!s}")

        # コンテキストレベルに基づくフィルタリング
        self._filter_context_by_level(session)

    def _filter_context_by_level(self, session: PromptGenerationSession) -> None:
        """コンテキストレベルに基づくフィルタリング"""
        if session.context_level == "基本":
            # 高優先度要素のみ（priority >= 0.7）
            high_priority = [e for e in session.integrated_context if e.priority >= 0.7]
            session.integrated_context = high_priority

        elif session.context_level == "拡張":
            # 中優先度以上（priority >= 0.4）
            medium_priority = [e for e in session.integrated_context if e.priority >= 0.4]
            session.integrated_context = medium_priority

        # "完全" の場合はフィルタリングなし

    def _generate_stage_prompts(self, session: PromptGenerationSession) -> list[A24StagePrompt]:
        """段階別プロンプト生成"""
        stage_prompts = []

        for stage in A24Stage:
            session.advance_to_stage(stage)

            try:
                # A24ガイドから基本指示取得
                instructions = self._a24_guide_repo.get_stage_instructions(stage)
                validation_criteria = self._a24_guide_repo.get_validation_criteria(stage)

                # コンテキスト統合ポイント生成
                integration_points = self._generate_context_integration_points(stage, session)

                # 期待出力フォーマット決定
                expected_output = self._determine_output_format(stage)

                stage_prompt = A24StagePrompt(
                    stage=stage,
                    instructions=instructions,
                    validation_criteria=validation_criteria,
                    expected_output_format=expected_output,
                    context_integration_points=integration_points,
                )

                stage_prompts.append(stage_prompt)
                session.complete_current_stage(f"Stage {stage.value} completed")

            except Exception as e:
                session.add_error(f"Stage {stage.value} 生成エラー: {e!s}")
                continue

        return stage_prompts

    def _generate_context_integration_points(self, stage: A24Stage, session: PromptGenerationSession) -> list[str]:
        """指定段階のコンテキスト統合ポイント生成"""
        stage_elements = [e for e in session.integrated_context if e.integration_stage == stage]

        integration_points = []
        for element in stage_elements:
            if element.element_type == ContextElementType.FORESHADOWING:
                integration_points.append(f"【伏線統合】{element.content}")
            elif element.element_type == ContextElementType.IMPORTANT_SCENE:
                integration_points.append(f"【重要シーン】{element.content}")
            elif element.element_type == ContextElementType.CHAPTER_CONNECTION:
                integration_points.append(f"【章間連携】{element.content}")
            elif element.element_type == ContextElementType.TECHNICAL_ELEMENT:
                integration_points.append(f"【技術要素】{element.content}")

        # 優先度順でソート
        stage_elements_sorted = sorted(stage_elements, key=lambda e: e.priority, reverse=True)
        return [
            self._format_integration_point(element)
            for element in stage_elements_sorted[:5]  # 最大5要素まで
        ]

    def _format_integration_point(self, element: ContextElement) -> str:
        """統合ポイント整形"""
        type_prefix = {
            ContextElementType.FORESHADOWING: "【伏線】",
            ContextElementType.IMPORTANT_SCENE: "【重要シーン】",
            ContextElementType.CHAPTER_CONNECTION: "【章間連携】",
            ContextElementType.TECHNICAL_ELEMENT: "【技術】",
        }

        prefix = type_prefix.get(element.element_type, "【要素】")
        priority_indicator = "★" * min(3, int(element.priority * 3) + 1)

        return f"{prefix}{priority_indicator} {element.content}"

    def _determine_output_format(self, stage: A24Stage) -> str:
        """段階別期待出力フォーマット決定"""
        format_templates = {
            A24Stage.SKELETON: "YAML形式の基本情報（episode_info, synopsis等）",
            A24Stage.THREE_ACT: "YAML形式の三幕構成（setup, confrontation, resolution）",
            A24Stage.SCENE_DETAIL: "YAML形式のシーン詳細（characters, key_events等）",
            A24Stage.TECH_INTEGRATION: "YAML形式の統合要素（plot_elements, technical_elements等）",
        }

        return format_templates.get(stage, "YAML形式の構造化データ")

    def _integrate_prompts(self, stage_prompts: list[A24StagePrompt], session: PromptGenerationSession) -> str:
        """段階別プロンプト統合

        4段階のプロンプトを統合し、Claude Codeで実行可能な
        単一のプロンプトを生成する。
        """
        integrated_parts = []

        # ヘッダー生成
        header = self._generate_prompt_header(session)
        integrated_parts.append(header)

        # A24テンプレート構造説明
        template_structure = self._a24_guide_repo.get_template_structure()
        template_explanation = self._generate_template_explanation(template_structure)
        integrated_parts.append(template_explanation)

        # 各段階のプロンプト統合
        for i, stage_prompt in enumerate(stage_prompts, 1):
            stage_section = self._generate_stage_section(stage_prompt, i)
            integrated_parts.append(stage_section)

        # フッター生成
        footer = self._generate_prompt_footer(session)
        integrated_parts.append(footer)

        return "\n\n".join(integrated_parts)

    def _generate_prompt_header(self, session: PromptGenerationSession) -> str:
        """プロンプトヘッダー生成"""
        return f"""# 📘 第{session.episode_number}話プロット作成ガイド

このガイドを使用して「{session.project_name}」第{session.episode_number}話の詳細プロットを作成してください。

## 🎯 作業概要

A24ガイドの4段階プロセスに従って、なろう小説に適したエピソードプロットを構築します：

1. **骨格構築** - 基本情報・テーマ・概要の定義
2. **三幕構成設計** - 物語構造の設計と感情曲線
3. **シーン肉付け** - 具体的シーンの詳細化
4. **技術伏線統合** - 技術要素と伏線の統合

## 📋 重要な指示

- 各段階を順次完了してください
- YAML形式での出力を厳守してください
- 提供されたテンプレート構造に従ってください
- コンテキスト統合ポイントを必ず反映してください"""

    def _generate_template_explanation(self, template_structure: dict[str, Any]) -> str:
        """テンプレート構造説明生成"""
        return """## 📐 使用テンプレート構造

以下のYAML構造に従ってプロットを作成してください：

```yaml
# 基本エピソード情報
episode_info:
  episode_number: int
  title: str
  chapter_number: int
  theme: str
  purpose: str
  emotional_core: str

# 視点情報
viewpoint_info:
  viewpoint: str
  character: str

# 概要
synopsis: |
  400字程度のあらすじ

# 三幕構成
story_structure:
  setup: {...}
  confrontation: {...}
  resolution: {...}

# キャラクター詳細
characters: {...}

# 技術的要素
technical_elements: {...}

# 感情的要素
emotional_elements: {...}

# 伏線・テーマ要素
plot_elements: {...}
```"""

    def _generate_stage_section(self, stage_prompt: A24StagePrompt, stage_number: int) -> str:
        """段階セクション生成"""
        section = f"""## Stage {stage_number}: {stage_prompt.stage.value}

### 🛠 作業手順

"""
        # 指示リスト追加
        for i, instruction in enumerate(stage_prompt.instructions, 1):
            section += f"{i}. {instruction}\n"

        # コンテキスト統合ポイント追加
        if stage_prompt.context_integration_points:
            section += "\n### 🔗 コンテキスト統合ポイント\n\n"
            for point in stage_prompt.context_integration_points:
                section += f"- {point}\n"

        # 検証基準追加
        if stage_prompt.validation_criteria:
            section += "\n### ✅ チェックリスト\n\n"
            for criterion in stage_prompt.validation_criteria:
                section += f"- {criterion}\n"

        # 期待出力追加
        section += f"\n### 📤 期待される出力\n\n{stage_prompt.expected_output_format}"

        return section

    def _generate_prompt_footer(self, session: PromptGenerationSession) -> str:
        """プロンプトフッター生成"""
        context_summary = session.get_context_summary()
        context_info = ", ".join([f"{k}: {v}個" for k, v in context_summary.items() if v > 0])

        return f"""## 📊 生成情報

- **プロジェクト**: {session.project_name}
- **エピソード**: 第{session.episode_number}話
- **コンテキスト**: {context_info}
- **最適化ターゲット**: {session.optimization_target.value}
- **コンテキストレベル**: {session.context_level}

## 🚀 実行指示

上記のガイドラインに従って、第{session.episode_number}話の詳細プロットをYAML形式で作成してください。
各段階を順次完了し、コンテキスト統合ポイントを必ず反映してください。

**重要**: 最終出力は必ずYAML形式で、テンプレート構造に完全準拠してください。"""
