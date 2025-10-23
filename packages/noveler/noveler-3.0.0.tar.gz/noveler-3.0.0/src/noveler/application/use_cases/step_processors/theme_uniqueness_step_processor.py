#!/usr/bin/env python3
"""テーマ性・独自性検証ステッププロセッサー

A38 STEP 2.5の実装として、構造分析後にテーマ性・独自性検証を実行
Golden Sampleとの比較分析による差別化戦略の提案と品質保証
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from noveler.application.use_cases.theme_uniqueness_verification_use_case import (
    ThemeUniquenessVerificationRequest,
    create_theme_uniqueness_verification_use_case,
)
from noveler.domain.entities.interactive_writing_session import InteractiveWritingSession, StepExecutionResult
from noveler.presentation.shared.shared_utilities import console

from .base_step_processor import BaseStepProcessor

if TYPE_CHECKING:
    from noveler.application.use_cases.theme_uniqueness_verification_use_case import ThemeUniquenessVerificationResponse


class ThemeUniquenessStepProcessor(BaseStepProcessor):
    """テーマ性・独自性検証ステップ・プロセッサー

    A38 STEP 2.5の実装として以下を実行：
    1. Golden Sampleとの比較分析
    2. テーマ一貫性評価
    3. 独自性スコア算出
    4. 差別化戦略提案
    """

    def __init__(self) -> None:
        super().__init__(step_number=3)
        self.verification_use_case = create_theme_uniqueness_verification_use_case()

    async def execute(
        self,
        session: InteractiveWritingSession,
        context: dict[str, Any] | None = None
        ) -> StepExecutionResult:
        """テーマ性・独自性検証を実行"""

        console.print("\n🎯 [bold blue]STEP 3: テーマ性・独自性検証を開始...[/bold blue]")

        try:
            # セッションからプロット情報を抽出
            plot_content = self._extract_plot_content(session)
            theme_elements = self._extract_theme_elements(session, context)
            story_elements = self._extract_story_elements(session, _context=None)
            character_descriptions = self._extract_character_descriptions(session, _context=None)

            console.print(f"📊 プロット内容: {len(plot_content)} 文字")
            console.print(f"🎨 テーマ要素: {len(theme_elements)} 個")
            console.print(f"📖 物語要素: {len(story_elements)} 個")

            # 検証リクエストを作成
            request = ThemeUniquenessVerificationRequest(
                project_root=session.project_root,
                episode_number=session.episode_number,
                plot_content=plot_content,
                theme_elements=theme_elements,
                story_elements=story_elements,
                character_descriptions=character_descriptions
            )

            # テーマ性・独自性検証を実行
            response = await self.verification_use_case.execute(request)

            if not response.success:
                console.print(f"❌ [bold red]検証エラー: {response.error_message}[/bold red]")
                return StepExecutionResult(
                    success=False,
                    step_number=self.step_number,
                    output_content="",
                    metadata={
                        "error": response.error_message,
                        "step_name": "テーマ性・独自性検証"
                    }
                )

            # 結果を表示
            self._display_verification_results(response)

            # セッションに結果を保存
            verification_data = {
                "uniqueness_evaluation": response.uniqueness_evaluation.to_dict() if response.uniqueness_evaluation else {},
                "theme_consistency_score": response.theme_consistency_score,
                "recommendations": response.recommendations,
                "verification_passed": response.uniqueness_evaluation.meets_quality_threshold() if response.uniqueness_evaluation else False
            }

            session.add_step_result(
                step_number=self.step_number,
                step_name="テーマ性・独自性検証",
                content=verification_data,
                metadata={
                    "overall_uniqueness_score": response.uniqueness_evaluation.overall_uniqueness_score if response.uniqueness_evaluation else 0.0,
                    "theme_consistency_score": response.theme_consistency_score,
                    "quality_threshold_met": verification_data["verification_passed"]
                }
            )

            return StepExecutionResult(
                success=True,
                step_number=self.step_number,
                output_content=self._format_output_content(response),
                metadata=verification_data
            )

        except Exception as e:
            console.print(f"❌ [bold red]STEP 3実行エラー: {e!s}[/bold red]")
            return StepExecutionResult(
                success=False,
                step_number=self.step_number,
                output_content="",
                metadata={
                    "error": str(e),
                    "step_name": "テーマ性・独自性検証"
                }
            )

    def validate_prerequisites(self, session: InteractiveWritingSession) -> bool:
        """前提条件の検証"""

        # STEP 2 (構造分析) の完了を確認
        if not session.has_step_result(step_number=2):
            console.print("⚠️  [yellow]STEP 2 (構造分析) が完了していません[/yellow]")
            return False

        # プロット情報の存在確認
        if not hasattr(session, "plot_data") or not session.plot_data:
            console.print("⚠️  [yellow]プロット情報が設定されていません[/yellow]")
            return False

        # プロジェクト設定の確認
        project_config_path = session.project_root / "config" / "novel_config.yaml"
        if not project_config_path.exists():
            console.print("⚠️  [yellow]プロジェクト設定ファイルが見つかりません[/yellow]")
            return False

        return True

    def get_step_name(self) -> str:
        """ステップ名取得"""
        return "テーマ性・独自性検証"

    def _extract_plot_content(self, session: InteractiveWritingSession) -> str:
        """セッションからプロット内容を抽出"""
        if hasattr(session, "plot_data") and session.plot_data:
            if isinstance(session.plot_data, dict):
                return str(session.plot_data.get("content", ""))
            return str(session.plot_data)
        return ""

    def _extract_theme_elements(self, session: InteractiveWritingSession, context: dict[str, Any] | None) -> list[str]:
        """テーマ要素を抽出"""
        theme_elements = []

        # セッションからテーマ情報を抽出
        if hasattr(session, "plot_data") and isinstance(session.plot_data, dict):
            themes = session.plot_data.get("themes", [])
            if isinstance(themes, list):
                theme_elements.extend(themes)
            elif isinstance(themes, str):
                theme_elements.append(themes)

        # コンテキストからも抽出
        if context:
            context_themes = context.get("theme_elements", [])
            if isinstance(context_themes, list):
                theme_elements.extend(context_themes)

        # STEP 2の結果からテーマ要素を抽出
        step2_result = session.get_step_result(step_number=2)
        if step2_result and isinstance(step2_result.content, dict):
            structural_themes = step2_result.content.get("themes", [])
            if isinstance(structural_themes, list):
                theme_elements.extend(structural_themes)

        return list(set(theme_elements)) if theme_elements else ["成長と学び", "知識の価値", "創造性の重要性"]

    def _extract_story_elements(self, session: InteractiveWritingSession, _context: dict[str, Any] | None = None) -> list[str]:
        """物語要素を抽出"""
        story_elements = []

        # セッションから物語要素を抽出
        if hasattr(session, "plot_data") and isinstance(session.plot_data, dict):
            elements = session.plot_data.get("story_elements", [])
            if isinstance(elements, list):
                story_elements.extend(elements)

        # STEP 2の結果から物語要素を抽出
        step2_result = session.get_step_result(step_number=2)
        if step2_result and isinstance(step2_result.content, dict):
            structural_elements = step2_result.content.get("story_elements", [])
            if isinstance(structural_elements, list):
                story_elements.extend(structural_elements)

        return list(set(story_elements)) if story_elements else ["現代知識活用", "異世界適応", "技術革新"]

    def _extract_character_descriptions(self, session: InteractiveWritingSession, _context: dict[str, Any] | None = None) -> list[str]:
        """キャラクター描写を抽出"""
        character_descriptions = []

        # セッションからキャラクター情報を抽出
        if hasattr(session, "character_data") and session.character_data:
            if isinstance(session.character_data, list):
                for char in session.character_data:
                    if isinstance(char, dict):
                        desc = char.get("description", "")
                        if desc:
                            character_descriptions.append(desc)
            elif isinstance(session.character_data, dict):
                for char_name, char_data in session.character_data.items():
                    if isinstance(char_data, dict):
                        desc = char_data.get("description", "")
                        if desc:
                            character_descriptions.append(f"{char_name}: {desc}")

        return character_descriptions

    def _display_verification_results(self, response: ThemeUniquenessVerificationResponse) -> None:
        """検証結果を表示"""
        if not response.uniqueness_evaluation:
            return

        evaluation = response.uniqueness_evaluation

        console.print("\n📈 [bold green]検証結果サマリー[/bold green]")
        console.print(f"🎯 総合独自性スコア: {evaluation.overall_uniqueness_score:.1f}/100")
        console.print(f"🎨 テーマ一貫性スコア: {evaluation.theme_consistency_score:.1f}/100")
        console.print(f"✅ 品質基準: {'合格' if evaluation.meets_quality_threshold() else '要改善'}")

        if evaluation.comparisons:
            console.print(f"\n📚 [bold blue]Golden Sample比較結果[/bold blue] ({len(evaluation.comparisons)}作品)")
            for i, comparison in enumerate(evaluation.comparisons[:3], 1):
                console.print(f"  {i}. 「{comparison.sample.title}」")
                console.print(f"     独自性: {comparison.uniqueness_score:.1f}/100")
                console.print(f"     差別化要素: {len(comparison.differentiation_elements)}個")

        if response.recommendations:
            console.print("\n💡 [bold yellow]改善提案[/bold yellow]")
            for i, rec in enumerate(response.recommendations, 1):
                console.print(f"  {i}. {rec}")

    def _format_output_content(self, response: ThemeUniquenessVerificationResponse) -> str:
        """出力内容をフォーマット"""
        if not response.uniqueness_evaluation:
            return "テーマ性・独自性検証が完了しましたが、評価データが生成されませんでした。"

        evaluation = response.uniqueness_evaluation

        output_lines = [
            "# テーマ性・独自性検証結果",
            "",
            "## 評価サマリー",
            f"- 総合独自性スコア: {evaluation.overall_uniqueness_score:.1f}/100",
            f"- テーマ一貫性スコア: {evaluation.theme_consistency_score:.1f}/100",
            f"- 品質基準: {'合格' if evaluation.meets_quality_threshold() else '要改善'}",
            "",
            "## Golden Sample比較分析",
        ]

        if evaluation.comparisons:
            for comparison in evaluation.comparisons:
                output_lines.extend([
                    f"### 「{comparison.sample.title}」との比較",
                    f"- 独自性スコア: {comparison.uniqueness_score:.1f}/100",
                    f"- 共通要素: {len(comparison.common_elements)}個",
                    f"- 差別化要素: {len(comparison.differentiation_elements)}個",
                    ""
                ])

        if response.recommendations:
            output_lines.extend([
                "## 改善提案",
                ""
            ])
            for i, rec in enumerate(response.recommendations, 1):
                output_lines.append(f"{i}. {rec}")

        return "\n".join(output_lines)
