"""Domain.services.enhanced_plot_generation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from noveler.domain.utils.domain_console import console

"Enhanced Plot Generation Service\n\nSPEC-PLOT-004: Enhanced Claude Code Integration Phase 2\nコンテキスト駆動プロット生成のドメインサービス\n"
from typing import Any

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.contextual_plot_generation import (
    ContextualPlotGeneration,
    ContextualPlotResult,
    PlotGenerationConfig,
    QualityIndicators,
)
from noveler.domain.interfaces.claude_session_interface import (
    ClaudeSessionExecutorInterface,
    EnvironmentDetectorInterface,
)
from noveler.domain.services.claude_plot_generation_service import ClaudePlotGenerationService
from noveler.domain.value_objects.chapter_number import ChapterNumber
from noveler.domain.value_objects.episode_number import EpisodeNumber


class ClaudeCodeSessionError(Exception):
    """Claude Codeセッションエラー"""


def is_claude_code_environment(config_manager=None) -> bool:
    """Claude Code環境かどうかを判定

    B30準拠: Configuration Manager経由で環境判定
    DDD準拠: 依存性注入で設定管理を受け取る
    """
    if config_manager is None:
        import os

        claude_code_enabled = os.getenv("CLAUDE_CODE_ENABLED", "false").lower() == "true"
        api_key_configured = os.getenv("ANTHROPIC_API_KEY") is not None
        return claude_code_enabled or api_key_configured
    claude_code_enabled = config_manager.get("claude_code_enabled", False)
    api_key_configured = config_manager.get("anthropic_api_key") is not None
    return claude_code_enabled or api_key_configured


def get_character_development_service() -> Any:
    """キャラクター開発サービスの取得（フォールバック実装）"""

    class MockCharacterDevelopmentService:
        def get_hero_info(self) -> None:
            return None

        def get_heroine_info(self) -> None:
            return None

    return MockCharacterDevelopmentService()


def create_claude_session_executor() -> Any:
    """Claude セッション実行器の作成（フォールバック実装）"""

    class MockSessionExecutor:
        def execute_prompt(self, prompt: str, response_format: str = "yaml") -> dict[str, Any]:
            return {"success": False, "error": "Mock implementation"}

    return MockSessionExecutor()


class EnhancedPlotGenerationService:
    """拡張プロット生成サービス

    SPEC-PLOT-004準拠のコンテキスト駆動プロット生成機能。
    既存のClaudePlotGenerationServiceを拡張し、品質指標と
    コンテキスト情報を統合したプロット生成を提供する。
    """

    def __init__(
        self,
        claude_service: ClaudePlotGenerationService | None = None,
        session_executor: ClaudeSessionExecutorInterface | None = None,
        environment_detector: EnvironmentDetectorInterface | None = None,
    ) -> None:
        """拡張プロット生成サービス初期化 - DDD準拠版

        Args:
            claude_service: 既存のClaude生成サービス(Dependency Injection)
            session_executor: セッション実行インターフェース
            environment_detector: 環境検出インターフェース
        """
        if claude_service is not None:
            self._claude_service = claude_service
        elif session_executor is not None and environment_detector is not None:
            self._claude_service = ClaudePlotGenerationService(session_executor, environment_detector)
        else:
            self._claude_service = None
        self._session_executor = session_executor
        self._environment_detector = environment_detector

    def generate_contextual_plot(
        self, episode_number: EpisodeNumber, chapter_plot: ChapterPlot, config: PlotGenerationConfig | None = None
    ) -> ContextualPlotResult:
        """コンテキスト駆動プロット生成

        Args:
            episode_number: 対象エピソード番号
            chapter_plot: 章プロット情報
            config: プロット生成設定(省略時はデフォルト設定)

        Returns:
            ContextualPlotResult: 生成されたコンテキスト駆動プロット結果

        Raises:
            ValueError: 無効な設定や入力データ
            PlotGenerationError: プロット生成処理エラー
        """
        generation_config: dict[str, Any] = config or PlotGenerationConfig()
        if not generation_config.is_valid():
            msg = f"Invalid plot generation config: {generation_config}"
            raise ValueError(msg)
        contextual_generation = ContextualPlotGeneration(episode_number=episode_number, config=generation_config)
        try:
            chapter_context = self._extract_chapter_context(chapter_plot, episode_number)
            contextual_generation.set_chapter_context(chapter_context)
            previous_context = self._get_previous_episodes_context(episode_number, chapter_plot)
            if previous_context:
                contextual_generation.update_context(previous_context)
            contextual_generation.start_generation()
            enhanced_prompt = self._build_enhanced_prompt(contextual_generation, chapter_plot)
            generated_plot = self._execute_enhanced_generation(enhanced_prompt, episode_number, chapter_plot)
            quality_indicators = self._calculate_quality_indicators(generated_plot, contextual_generation, chapter_plot)
            result = contextual_generation.create_result(
                generated_content=self._format_generated_content(generated_plot),
                quality_indicators=quality_indicators,
                metadata={
                    "generation_method": "enhanced_contextual",
                    "claude_code_integration": is_claude_code_environment(),
                    "chapter_number": chapter_plot.chapter_number.value,
                    "config": generation_config.to_dict(),
                },
            )
            contextual_generation.complete_generation(result)
            return result
        except Exception as e:
            contextual_generation.fail_generation(str(e))
            raise

    def _extract_chapter_context(self, chapter_plot: ChapterPlot, episode_number: EpisodeNumber) -> dict[str, Any]:
        """章コンテキスト情報の抽出

        Args:
            chapter_plot: 章プロット情報
            episode_number: エピソード番号

        Returns:
            Dict[str, Any]: 抽出された章コンテキスト
        """
        return {
            "chapter_number": chapter_plot.chapter_number.value,
            "chapter_theme": getattr(chapter_plot, "central_theme", "テーマ未設定"),
            "key_events": getattr(chapter_plot, "key_events", []),
            "technical_focus": self._extract_technical_focus(chapter_plot),
            "viewpoint_management": getattr(chapter_plot, "viewpoint_management", {}),
            "episode_position": self._calculate_episode_position(episode_number, chapter_plot),
        }

    def _extract_technical_focus(self, chapter_plot: ChapterPlot) -> list[str]:
        """技術フォーカス要素の抽出

        Args:
            chapter_plot: 章プロット情報

        Returns:
            list[str]: 技術フォーカス要素リスト
        """
        technical_elements = []
        key_events = getattr(chapter_plot, "key_events", [])
        for event in key_events:
            if isinstance(event, str):
                if "デバッグ" in event or "DEBUG" in event:
                    technical_elements.append("デバッグ手法")
                if "アサート" in event or "assert" in event:
                    technical_elements.append("アサーション")
                if "ログ" in event or "log" in event:
                    technical_elements.append("ログ解析")
                if "エラー" in event or "error" in event:
                    technical_elements.append("例外処理")
        return list(set(technical_elements)) if technical_elements else ["プログラミング基礎"]

    def _calculate_episode_position(self, episode_number: EpisodeNumber, chapter_plot: ChapterPlot) -> dict[str, Any]:
        """エピソード位置情報の計算

        Args:
            episode_number: エピソード番号
            chapter_plot: 章プロット情報

        Returns:
            Dict[str, Any]: エピソード位置情報
        """
        episodes = getattr(chapter_plot, "episodes", [])
        total_episodes = len(episodes)
        episode_index = None
        for i, ep in enumerate(episodes):
            if isinstance(ep, dict) and ep.get("episode_number") == episode_number.value:
                episode_index = i
                break
        if episode_index is not None:
            return {
                "position": episode_index + 1,
                "total": total_episodes,
                "is_first": episode_index == 0,
                "is_last": episode_index == total_episodes - 1,
            }
        return {"position": 1, "total": 1, "is_first": True, "is_last": True}

    def _get_previous_episodes_context(
        self, episode_number: EpisodeNumber, chapter_plot: ChapterPlot
    ) -> dict[str, Any] | None:
        """前エピソードコンテキストの取得

        Args:
            episode_number: 現在のエピソード番号
            chapter_plot: 章プロット情報

        Returns:
            Optional[Dict[str, Any]]: 前エピソードコンテキスト(存在しない場合はNone)
        """
        if episode_number.value <= 1:
            return None
        previous_episode_number = episode_number.value - 1
        episodes = getattr(chapter_plot, "episodes", [])
        for ep in episodes:
            if isinstance(ep, dict) and ep.get("episode_number") == previous_episode_number:
                return {
                    f"episode_{previous_episode_number}": {
                        "title": ep.get("title", "タイトル未設定"),
                        "summary": ep.get("summary", "概要未設定"),
                        "technical_elements": self._extract_technical_elements_from_episode(ep),
                        "character_development": self._extract_character_development(ep),
                    }
                }
        return None

    def _extract_technical_elements_from_episode(self, episode_data: dict[str, Any]) -> list[str]:
        """エピソードデータから技術要素を抽出

        Args:
            episode_data: エピソードデータ

        Returns:
            list[str]: 技術要素リスト
        """
        technical_elements = []
        text_content = f"{episode_data.get('title', '')} {episode_data.get('summary', '')}"
        if "デバッグ" in text_content or "DEBUG" in text_content:
            technical_elements.append("デバッグログ")
        if "アサート" in text_content:
            technical_elements.append("アサーション")
        if "ペア" in text_content:
            technical_elements.append("ペアプログラミング")
        if "テスト" in text_content:
            technical_elements.append("テスト手法")
        return technical_elements if technical_elements else ["基本プログラミング"]

    def _extract_character_development(self, episode_data: dict[str, Any]) -> dict[str, Any]:
        """キャラクター成長段階の抽出（新構造対応）

        Args:
            episode_data: エピソードデータ

        Returns:
            Dict[str, Any]: キャラクター成長段階（新構造）
        """
        try:
            char_service = get_character_development_service()
            hero_info = char_service.get_hero_info()
            heroine_info = char_service.get_heroine_info()
            return {
                "main_characters": {
                    "hero": {
                        "name": hero_info.name if hero_info else "直人",
                        "character_type": "hero",
                        "growth_stage": "成長段階継続",
                        "development_focus": "技術的向上と内面的成熟",
                    },
                    "heroine": {
                        "name": heroine_info.name if heroine_info else "あすか",
                        "character_type": "heroine",
                        "growth_stage": "理論応用期",
                        "development_focus": "自信獲得と積極性向上",
                    },
                },
                "supporting_characters": {
                    "mentor": {
                        "name": "レガシー先輩",
                        "character_type": "mentor",
                        "growth_stage": "指導者としての成長",
                        "development_focus": "次世代への技術継承",
                    }
                },
                "legacy_character_arcs": {"直人": "成長段階継続", "あすか": "理論応用期"},
            }
        except Exception:
            return {"直人": "成長段階継続", "あすか": "理論応用期"}

    def _build_enhanced_prompt(self, contextual_generation: ContextualPlotGeneration, chapter_plot: ChapterPlot) -> str:
        """拡張プロンプトの構築

        Args:
            contextual_generation: コンテキスト駆動プロット生成エンティティ
            chapter_plot: 章プロット情報

        Returns:
            str: 構築された拡張プロンプト
        """
        config = contextual_generation.config
        chapter_context = contextual_generation.chapter_context
        context_data: dict[str, Any] = contextual_generation.context_data
        return f"""# SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2\n## コンテキスト駆動エピソードプロット生成\n\n### 基本設定\n- **エピソード番号**: {contextual_generation.episode_number.value}\n- **目標文字数**: {config.target_word_count}文字\n- **技術精度要求**: {("有効" if config.technical_accuracy_required else "無効")}\n- **キャラクター一貫性チェック**: {("有効" if config.character_consistency_check else "無効")}\n- **シーン構造拡張**: {("有効" if config.scene_structure_enhanced else "無効")}\n\n### 章コンテキスト情報\n- **章番号**: {chapter_context.get("chapter_number", "不明")}\n- **章テーマ**: {chapter_context.get("chapter_theme", "テーマ未設定")}\n- **主要イベント**: {", ".join(chapter_context.get("key_events", []))}\n- **技術フォーカス**: {", ".join(chapter_context.get("technical_focus", []))}\n- **エピソード位置**: {chapter_context.get("episode_position", {}).get("position", 1)}/{chapter_context.get("episode_position", {}).get("total", 1)}\n\n### 前エピソードコンテキスト\n{self._format_previous_context(context_data)}\n\n### 品質要求基準\n1. **技術精度**: プログラミング概念の正確な表現\n2. **キャラクター一貫性**: 既存キャラクター設定との整合性\n3. **プロット連結性**: 前後エピソードとの自然な繋がり\n4. **シーン構造**: 三幕構成に基づく展開\n\n### 生成要求\n以下のYAML構造でエピソードプロットを生成してください:\n\n```yaml\nepisode_number: {contextual_generation.episode_number.value}\ntitle: "第{contextual_generation.episode_number.value:03d}話 [具体的なタイトル]"\nsummary: "[約200文字のエピソード概要]"\nscenes:\n  - scene_title: "[シーン1タイトル]"\n    description: "[シーン1の詳細描写(約{config.target_word_count // 6}文字)]"\n  - scene_title: "[シーン2タイトル]"\n    description: "[シーン2の詳細描写(約{config.target_word_count // 6}文字)]"\n  # [必要に応じて追加シーン]\nkey_events:\n  - "[重要イベント1]"\n  - "[重要イベント2]"\nviewpoint: "[視点情報]"\ntone: "[エピソードの雰囲気・トーン]"\nconflict: "[主要コンフリクト]"\nresolution: "[解決方法]"\ntechnical_elements:\n  - "[技術要素1]"\n  - "[技術要素2]"\ncharacter_development:\n  直人: "[直人の成長・変化]"\n  あすか: "[あすかの成長・変化]"\n```\n\n**重要**: 生成内容は {config.target_word_count}文字相当の詳細度を持ち、技術要素「{", ".join(chapter_context.get("technical_focus", []))}」を適切に組み込んでください。\n"""

    def _format_previous_context(self, context_data: dict[str, Any]) -> str:
        """前コンテキスト情報のフォーマット

        Args:
            context_data: コンテキストデータ

        Returns:
            str: フォーマットされたコンテキスト情報
        """
        if not context_data:
            return "- 前エピソード情報なし(初回エピソード)"
        lines = []
        for episode_key, episode_info in context_data.items():
            if isinstance(episode_info, dict):
                lines.append(f"- **{episode_key}**:")
                lines.append(f"  - タイトル: {episode_info.get('title', '未設定')}")
                lines.append(f"  - 概要: {episode_info.get('summary', '未設定')}")
                lines.append(f"  - 技術要素: {', '.join(episode_info.get('technical_elements', []))}")
                lines.append(f"  - キャラクター発達: {episode_info.get('character_development', {})}")
        return "\n".join(lines) if lines else "- コンテキスト情報なし"

    def _execute_enhanced_generation(
        self, enhanced_prompt: str, episode_number: EpisodeNumber, chapter_plot: ChapterPlot
    ) -> dict[str, Any]:
        """拡張生成の実行

        Args:
            enhanced_prompt: 拡張プロンプト
            episode_number: エピソード番号
            chapter_plot: 章プロット情報

        Returns:
            Dict[str, Any]: 生成されたプロット データ
        """
        try:
            if is_claude_code_environment():
                return self._execute_claude_code_generation(enhanced_prompt)
            if self._claude_service is not None:
                return self._claude_service._call_claude_code(enhanced_prompt, episode_number.value, chapter_plot)
            console.print("⚠️ Claude generation service not available, using fallback plot generation")
            return self._generate_fallback_plot(episode_number.value, chapter_plot)
        except Exception as e:
            console.print(f"Enhanced plot generation failed for episode {episode_number.value}: {e}")
            import traceback

            console.print(f"Traceback: {traceback.format_exc()}")
            if self._claude_service is not None:
                return self._claude_service._generate_high_quality_plot_mock_response(
                    episode_number.value, chapter_plot
                )
            return self._generate_fallback_plot(episode_number.value, chapter_plot)

    def _execute_claude_code_generation(self, prompt: str) -> dict[str, Any]:
        """Claude Code環境での直接生成

        Args:
            prompt: 生成プロンプト

        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            session_executor = create_claude_session_executor()
            response = session_executor.execute_prompt(prompt=prompt, response_format="yaml")
            if response.get("success", False) and "data" in response:
                import yaml

                return yaml.safe_load(str(response["data"]))
            msg = f"Generation failed: {response.get('error', 'Unknown error')}"
            raise ClaudeCodeSessionError(msg)
        except Exception as e:
            msg = f"Claude Code generation error: {e}"
            raise ClaudeCodeSessionError(msg) from e

    def _calculate_quality_indicators(
        self, generated_plot: dict[str, Any], contextual_generation: ContextualPlotGeneration, chapter_plot: ChapterPlot
    ) -> QualityIndicators:
        """品質指標の計算

        Args:
            generated_plot: 生成されたプロットデータ
            contextual_generation: コンテキスト駆動プロット生成エンティティ
            chapter_plot: 章プロット情報

        Returns:
            QualityIndicators: 計算された品質指標
        """
        technical_accuracy = self._evaluate_technical_accuracy(
            generated_plot, contextual_generation.get_technical_focus()
        )
        character_consistency = self._evaluate_character_consistency(generated_plot, contextual_generation.context_data)
        plot_coherence = self._evaluate_plot_coherence(generated_plot, contextual_generation.chapter_context)
        return QualityIndicators(
            technical_accuracy=technical_accuracy,
            character_consistency=character_consistency,
            plot_coherence=plot_coherence,
        )

    def _evaluate_technical_accuracy(self, generated_plot: dict[str, Any], technical_focus: list[str]) -> float:
        """技術精度の評価

        Args:
            generated_plot: 生成プロット
            technical_focus: 技術フォーカス要素

        Returns:
            float: 技術精度スコア(0-100)
        """
        score = 85.0
        technical_elements = generated_plot.get("technical_elements", [])
        if technical_elements:
            score += 10.0
            matching_count = sum(1 for focus in technical_focus if any(focus in elem for elem in technical_elements))
            if matching_count > 0:
                score += 5.0 * (matching_count / len(technical_focus))
        scenes = generated_plot.get("scenes", [])
        technical_mentions = 0
        for scene in scenes:
            description = scene.get("description", "")
            if any(focus in description for focus in technical_focus):
                technical_mentions += 1
        if technical_mentions > 0:
            score += 5.0 * (technical_mentions / len(scenes))
        return min(100.0, score)

    def _evaluate_character_consistency(self, generated_plot: dict[str, Any], context_data: dict[str, Any]) -> float:
        """キャラクター一貫性の評価

        Args:
            generated_plot: 生成プロット
            context_data: コンテキストデータ

        Returns:
            float: キャラクター一貫性スコア(0-100)
        """
        score = 80.0
        character_development = generated_plot.get("character_development", {})
        if character_development:
            score += 15.0
            main_characters = ["直人", "あすか"]
            mentioned_characters = [char for char in main_characters if char in character_development]
            if mentioned_characters:
                score += 5.0 * (len(mentioned_characters) / len(main_characters))
        return min(100.0, score)

    def _evaluate_plot_coherence(self, generated_plot: dict[str, Any], chapter_context: dict[str, Any]) -> float:
        """プロット連結性の評価

        Args:
            generated_plot: 生成プロット
            chapter_context: 章コンテキスト

        Returns:
            float: プロット連結性スコア(0-100)
        """
        score = 75.0
        chapter_theme = chapter_context.get("chapter_theme", "")
        episode_summary = generated_plot.get("summary", "")
        if chapter_theme and episode_summary:
            theme_keywords = chapter_theme.split()
            matching_keywords = sum(1 for keyword in theme_keywords if keyword in episode_summary)
            if matching_keywords > 0:
                score += 10.0 * (matching_keywords / len(theme_keywords))
        required_fields = ["episode_number", "title", "summary", "scenes", "key_events"]
        complete_fields = sum(1 for field in required_fields if field in generated_plot)
        score += 15.0 * (complete_fields / len(required_fields))
        return min(100.0, score)

    def _generate_fallback_plot(self, episode_number: int, chapter_plot: ChapterPlot | None) -> dict[str, Any]:
        """フォールバック用の高品質プロット生成

        Args:
            episode_number: エピソード番号
            chapter_plot: 章プロット情報

        Returns:
            dict[str, Any]: 詳細なプロットデータ（物語に沿った高品質版）
        """
        episode_title = self._determine_episode_title(episode_number, chapter_plot)
        story_context = self._extract_story_context(episode_number, chapter_plot)
        technical_elements = self._determine_technical_elements(episode_number, chapter_plot)
        character_development = self._determine_character_development(episode_number, story_context)
        detailed_scenes = self._generate_detailed_scenes(episode_number, story_context, technical_elements)
        key_events = self._generate_key_events(episode_number, story_context, technical_elements)
        (conflict, resolution) = self._generate_conflict_resolution(episode_number, story_context)
        return {
            "episode_number": episode_number,
            "title": episode_title,
            "summary": self._generate_detailed_summary(episode_number, story_context, technical_elements),
            "scenes": detailed_scenes,
            "key_events": key_events,
            "viewpoint": "三人称単元視点（直人）",
            "tone": self._determine_tone(episode_number, story_context),
            "conflict": conflict,
            "resolution": resolution,
            "technical_elements": technical_elements,
            "character_development": character_development,
        }

    def _determine_episode_title(self, episode_number: int, chapter_plot: ChapterPlot | None) -> str:
        """エピソードタイトルを決定（複数ソースから取得）"""
        if chapter_plot and hasattr(chapter_plot, "episodes"):
            for ep in getattr(chapter_plot, "episodes", []):
                if isinstance(ep, dict) and ep.get("episode_number") == episode_number:
                    if ep.get("title"):
                        return ep["title"]
        if hasattr(self, "_path_service") and self._path_service:
            try:
                existing_title = self._path_service.get_episode_title(episode_number)
                if existing_title:
                    return f"第{episode_number:03d}話_{existing_title}"
            except Exception:
                pass
        return self._generate_title_by_episode_number(episode_number)

    def _generate_title_by_episode_number(self, episode_number: int) -> str:
        """エピソード番号に基づくタイトル生成"""
        title_patterns = {
            1: "入学式クライシス",
            2: "初めての魔法プログラミング",
            3: "DEBUGログの秘密",
            4: "レガシーライブラリの違和感",
            5: "クラスメイトとの衝突",
            6: "ペアプログラミング入門",
            7: "あすかとの協力関係",
            8: "魔法デバッグの応用",
            9: "実技試験への準備",
            10: "中間試験の挑戦",
            11: "新たな発見",
            12: "調査の深化",
        }
        base_title = title_patterns.get(episode_number, f"第{episode_number}話の展開")
        return f"第{episode_number:03d}話_{base_title}"

    def _extract_story_context(self, episode_number: int, chapter_plot: ChapterPlot | None) -> dict[str, Any]:
        """物語コンテキストの抽出"""
        context = {
            "episode_number": episode_number,
            "chapter_number": 1,
            "story_phase": self._determine_story_phase(episode_number),
            "main_theme": "DEBUGログ能力の成長と学園生活",
            "character_focus": ["直人", "あすか"],
            "setting": "魔法プログラミング学園",
        }
        if chapter_plot:
            context["chapter_number"] = getattr(chapter_plot, "chapter_number", ChapterNumber(1)).value
            context["main_theme"] = getattr(chapter_plot, "central_theme", context["main_theme"])
            key_events = getattr(chapter_plot, "key_events", [])
            if key_events:
                context["key_themes"] = self._extract_themes_from_events(key_events)
        return context

    def _determine_story_phase(self, episode_number: int) -> str:
        """エピソード番号に基づく物語フェーズの決定"""
        if episode_number <= 3:
            return "導入期"
        if episode_number <= 8:
            return "発展期"
        if episode_number <= 12:
            return "深化期"
        return "展開期"

    def _determine_technical_elements(self, episode_number: int, chapter_plot: ChapterPlot | None) -> list[str]:
        """技術要素の決定（エピソード番号とコンテキスト基準）"""
        technical_mapping = {
            1: ["基本魔法", "学園システム"],
            2: ["魔法プログラミング基礎", "初歩的デバッグ"],
            3: ["DEBUGログ解析", "魔法ログ調査"],
            4: ["レガシーライブラリ", "古代魔法技術"],
            5: ["魔法衝突解決", "協調プログラミング"],
            6: ["ペアプログラミング", "協力魔法"],
            7: ["シンクロ魔法", "連携技術"],
            8: ["応用デバッグ", "高度ログ解析"],
            9: ["実技評価", "魔法テスト技法"],
            10: ["中間試験技術", "総合デバッグ"],
            11: ["新発見技術", "未知の魔法原理"],
            12: ["調査技法", "情報収集魔法"],
        }
        base_elements = technical_mapping.get(episode_number, ["基本プログラミング", "魔法基礎"])
        if chapter_plot:
            chapter_technical = self._extract_technical_focus(chapter_plot)
            all_elements = list(set(base_elements + chapter_technical))
            return all_elements[:4]
        return base_elements

    def _determine_character_development(self, episode_number: int, story_context: dict[str, Any]) -> dict[str, str]:
        """キャラクター成長段階の決定"""
        story_phase = story_context.get("story_phase", "導入期")
        development_patterns = {
            "導入期": {"直人": "DEBUGログ能力の基礎習得期", "あすか": "理論魔法の基礎固め期"},
            "発展期": {"直人": "能力応用と自信獲得期", "あすか": "実践魔法への挑戦期"},
            "深化期": {"直人": "高度技術習得と指導力育成期", "あすか": "独自技法確立と協力関係深化期"},
            "展開期": {"直人": "技術統合とリーダーシップ発揮期", "あすか": "専門性確立と自立成長期"},
        }
        base_development = development_patterns.get(story_phase, development_patterns["導入期"])
        episode_adjustments = {
            4: {"直人": "古代技術への興味と探究心", "あすか": "調査協力と分析力向上"},
            7: {"直人": "協力技術の習得", "あすか": "パートナーシップ構築"},
            10: {"直人": "試験への準備と総合力", "あすか": "理論応用力の完成"},
            12: {"直人": "情報収集能力の向上", "あすか": "調査分析の専門性"},
        }
        if episode_number in episode_adjustments:
            return episode_adjustments[episode_number]
        return base_development

    def _generate_detailed_scenes(
        self, episode_number: int, story_context: dict[str, Any], technical_elements: list[str]
    ) -> list[dict[str, str]]:
        """詳細なシーン生成"""
        story_phase = story_context.get("story_phase", "導入期")
        scene_structures = {
            "導入期": ["学園生活導入", "能力発見・基礎習得", "初期課題の解決"],
            "発展期": ["新しい挑戦", "技術習得・実践", "成功と次への準備"],
            "深化期": ["高度な課題発生", "専門技術の応用", "協力関係の深化"],
            "展開期": ["複雑な状況", "総合技術の活用", "成長の実感"],
        }
        base_scenes = scene_structures.get(story_phase, scene_structures["導入期"])
        detailed_scenes = []
        for i, scene_title in enumerate(base_scenes):
            description = self._generate_scene_description(
                episode_number, scene_title, technical_elements, i + 1, len(base_scenes)
            )
            detailed_scenes.append({"scene_title": scene_title, "description": description})
        return detailed_scenes

    def _generate_scene_description(
        self, episode_number: int, scene_title: str, technical_elements: list[str], scene_pos: int, total_scenes: int
    ) -> str:
        """シーン説明の生成"""
        tech_focus = technical_elements[0] if technical_elements else "基本魔法"
        if scene_pos == 1:
            return f"第{episode_number}話の開始。{tech_focus}に関わる新しい状況や課題が提示される。直人とあすかの現在の状況と目標が明確になる。"
        if scene_pos == total_scenes:
            return f"第{episode_number}話の締めくくり。{tech_focus}を通じた成長と達成が描かれ、次のエピソードへの期待感が醸成される。"
        return f"第{episode_number}話の中心展開。{tech_focus}を活用した実践的な挑戦と学習が描かれ、キャラクターの成長が進む。"

    def _generate_key_events(
        self, episode_number: int, story_context: dict[str, Any], technical_elements: list[str]
    ) -> list[str]:
        """重要イベントの生成"""
        events = []
        for tech_element in technical_elements[:2]:
            events.append(f"{tech_element}の習得・応用")
        episode_events = {
            1: ["学園入学と環境適応"],
            2: ["初回魔法プログラミング実習"],
            3: ["DEBUGログ能力の本格発見"],
            4: ["古代ライブラリ調査開始"],
            5: ["クラスメイトとの関係構築"],
            6: ["ペアワーク初体験"],
            7: ["あすかとの本格協力"],
            8: ["応用技術の実践"],
            9: ["実技試験対策"],
            10: ["中間評価への挑戦"],
            11: ["新技術の発見"],
            12: ["本格的な調査活動"],
        }
        specific_events = episode_events.get(episode_number, [f"第{episode_number}話の特別な出来事"])
        events.extend(specific_events)
        return events[:4]

    def _generate_conflict_resolution(self, episode_number: int, story_context: dict[str, Any]) -> tuple[str, str]:
        """コンフリクトと解決の生成"""
        story_phase = story_context.get("story_phase", "導入期")
        conflict_patterns = {
            "導入期": f"第{episode_number}話での新環境・新技術への適応課題",
            "発展期": f"第{episode_number}話での技術習得と実践応用の困難",
            "深化期": f"第{episode_number}話での高度技術と協力関係の複雑な課題",
            "展開期": f"第{episode_number}話での総合的能力と責任の重い課題",
        }
        resolution_patterns = {
            "導入期": f"基礎技術習得と環境適応による第{episode_number}話の小さな成功",
            "発展期": f"実践経験と協力関係による第{episode_number}話の技術的突破",
            "深化期": f"専門技術と深い協力による第{episode_number}話の顕著な成長",
            "展開期": f"統合技術と自立的判断による第{episode_number}話の大きな達成",
        }
        conflict = conflict_patterns.get(story_phase, conflict_patterns["導入期"])
        resolution = resolution_patterns.get(story_phase, resolution_patterns["導入期"])
        return (conflict, resolution)

    def _generate_detailed_summary(
        self, episode_number: int, story_context: dict[str, Any], technical_elements: list[str]
    ) -> str:
        """詳細な概要生成"""
        main_tech = technical_elements[0] if technical_elements else "魔法技術"
        story_phase = story_context.get("story_phase", "導入期")
        summary_templates = {
            "導入期": f"第{episode_number}話では、直人が{main_tech}との出会いを通じて新たな学園生活の局面を迎える。基礎的な能力習得と環境適応が主な焦点となり、あすかとの関係も徐々に発展していく。",
            "発展期": f"第{episode_number}話では、{main_tech}を中心とした実践的な挑戦が描かれる。直人の能力向上とあすかとの協力関係が深まり、学園での存在感も高まっていく。",
            "深化期": f"第{episode_number}話では、{main_tech}の高度な応用が展開される。直人とあすかの連携が本格化し、より複雑な課題への取り組みを通じて大きな成長を遂げる。",
            "展開期": f"第{episode_number}話では、{main_tech}を駆使した総合的な挑戦が繰り広げられる。これまでの学習と経験を統合し、新たな段階への準備が進む。",
        }
        return summary_templates.get(story_phase, summary_templates["導入期"])

    def _determine_tone(self, episode_number: int, story_context: dict[str, Any]) -> str:
        """エピソードトーンの決定"""
        story_phase = story_context.get("story_phase", "導入期")
        tone_mapping = {
            "導入期": "学園コメディ・成長",
            "発展期": "挑戦・協力・発見",
            "深化期": "成熟・探究・絆",
            "展開期": "統合・達成・展望",
        }
        base_tone = tone_mapping.get(story_phase, "学園・成長")
        episode_tone_adjustments = {
            4: "探究・ミステリー・好奇心",
            7: "協力・シンクロ・信頼",
            10: "緊張・集中・試練",
            12: "調査・発見・深化",
        }
        return episode_tone_adjustments.get(episode_number, base_tone)

    def _extract_themes_from_events(self, key_events: list) -> list[str]:
        """キーイベントからテーマを抽出"""
        themes = []
        for event in key_events:
            if isinstance(event, str):
                if "デバッグ" in event or "DEBUG" in event:
                    themes.append("デバッグ技術")
                if "協力" in event or "ペア" in event:
                    themes.append("協力関係")
                if "成長" in event:
                    themes.append("キャラクター成長")
                if "学園" in event:
                    themes.append("学園生活")
        return list(set(themes)) if themes else ["学園・成長・技術"]

    def _format_generated_content(self, generated_plot: dict[str, Any]) -> dict[str, Any] | str:
        """生成コンテンツのフォーマット

        Args:
            generated_plot: 生成プロット

        Returns:
            dict[str, Any] | str: フォーマットされたコンテンツ（YAML統合対応により辞書として返す）
        """
        try:
            if isinstance(generated_plot, dict):
                return generated_plot
            return str(generated_plot)
        except Exception:
            return str(generated_plot)
