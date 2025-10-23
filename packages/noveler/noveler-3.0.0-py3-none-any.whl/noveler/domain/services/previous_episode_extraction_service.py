"""Domain.services.previous_episode_extraction_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

"前話情報抽出ドメインサービス"
import collections.abc as cabc
import re
from pathlib import Path

from noveler.domain.value_objects.path_configuration import get_default_manuscript_dir

from noveler.domain.entities.previous_episode_context import (
    CharacterState,
    PreviousEpisodeContext,
    StoryProgressionState,
    TechnicalLearningState,
)
from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager
from noveler.domain.value_objects.episode_number import EpisodeNumber


def create_path_service(project_root: Path) -> IPathService:
    """PathServiceの作成（フォールバック実装）

    DDD準拠: 依存性注入により具象実装を外部から提供すべき
    ここでは一時的なフォールバック実装のみ提供
    """

    class FallbackPathService:
        def __init__(self, root: Path) -> None:
            self.root = root

        def get_episode_file_path(self, episode_number: int) -> Path | None:
            """エピソードファイルパス取得のフォールバック"""
            possible_paths = [
                self.root / "episodes" / f"episode_{episode_number:03d}.md",
                self.root / "episodes" / f"{episode_number:03d}.md",
                self.root / f"{episode_number:03d}.md",
            ]
            for path in possible_paths:
                if path.exists():
                    return path
            return None

        def get_manuscript_dir(self) -> Path:
            """原稿ディレクトリのフォールバック実装 (40_原稿)"""
            return get_default_manuscript_dir(self.root)

    try:
        manager = get_path_service_manager()
        return manager.create_common_path_service(project_root=project_root)
    except Exception:
        return FallbackPathService(project_root)


class PreviousEpisodeExtractionService:
    """前話情報抽出ドメインサービス

    既存の原稿ファイルから前話の詳細情報を抽出し、
    構造化されたコンテキストとして提供する。

    抽出対象:
    - キャラクター状態と感情の変化
    - ストーリー進行状況
    - 技術要素の学習進捗
    - 未解決要素と伏線
    - シーン継続性情報
    """

    def __init__(self) -> None:
        """サービス初期化"""
        self._character_pattern = re.compile("(?:直人|あすか|先生|教授)(?:は|が|の)")
        # より包括的な感情表現（語幹マッチを含む）
        self._emotion_pattern = re.compile("(?:嬉|悲|驚|困|喜|怒|焦|安心|満足|緊張|達成感|不安|困惑)")
        self._technical_pattern = re.compile("(?:プログラミング|魔法|コード|アルゴリズム|デバッグ)")
        self._foreshadowing_pattern = re.compile("(?:いずれ|やがて|きっと|次回|後日)")

    def extract_previous_episode_context(
        self,
        current_episode_number: EpisodeNumber,
        project_root: Path,
        *,
        log: cabc.Callable[[str, str], None] | None = None,
    ) -> PreviousEpisodeContext:
        """前話情報コンテキスト抽出

        Args:
            current_episode_number: 現在のエピソード番号
            project_root: プロジェクトルートパス

        Returns:
            抽出された前話情報コンテキスト
        """
        context = PreviousEpisodeContext(current_episode_number)
        log_messages: list[dict[str, str]] = []
        if current_episode_number.value <= 1:
            context.log_messages = log_messages
            return context
        previous_episode_number = current_episode_number.previous()
        manuscript_path = self._find_previous_manuscript(
            previous_episode_number,
            project_root,
            log_messages,
            log,
        )
        if not manuscript_path:
            context.log_messages = log_messages
            return context
        context.source_manuscript_path = manuscript_path
        manuscript_content = self._read_manuscript_content(manuscript_path, log_messages, log)
        if not manuscript_content:
            context.log_messages = log_messages
            return context
        self._extract_character_states(manuscript_content, context)
        self._extract_story_progression(manuscript_content, context)
        self._extract_technical_learning(manuscript_content, context)
        self._extract_emotional_flow(manuscript_content, context)
        self._extract_unresolved_elements(manuscript_content, context)
        self._extract_scene_continuity(manuscript_content, context)
        context.log_messages = log_messages
        return context

    def _find_previous_manuscript(
        self,
        episode_number: EpisodeNumber,
        project_root: Path,
        log_messages: list[dict[str, str]],
        log: cabc.Callable[[str, str], None] | None,
    ) -> Path | None:
        """前話原稿ファイルの検索

        Args:
            episode_number: 前話エピソード番号
            project_root: プロジェクトルートパス

        Returns:
            前話原稿ファイルパス、または None
        """
        try:
            path_service = create_path_service(project_root)
            manuscript_dir = path_service.get_manuscript_dir()
            patterns = [
                f"第{episode_number.value:03d}話*.md",
                f"第{episode_number.value}話*.md",
                f"{episode_number.value:03d}*.md",
                f"episode_{episode_number.value:03d}*.md",
            ]
            for pattern in patterns:
                files = list(manuscript_dir.glob(pattern))
                if files:
                    return files[0]

            # フォールバック: 共通パスサービスの原稿ディレクトリも探索
            try:
                manager = get_path_service_manager()
                cps = manager.create_common_path_service()
                alt_dir = Path(cps.get_manuscript_dir())
                for pattern in patterns:
                    files = list(alt_dir.glob(pattern))
                    if files:
                        return files[0]
            except Exception:
                pass
            return None
        except Exception as e:
            self._emit_log(log_messages, "error", f"前話原稿ファイル検索エラー: {e}", log)
            return None

    def _read_manuscript_content(
        self,
        manuscript_path: Path,
        log_messages: list[dict[str, str]],
        log: cabc.Callable[[str, str], None] | None,
    ) -> str | None:
        """原稿コンテンツ読み込み

        Args:
            manuscript_path: 原稿ファイルパス

        Returns:
            原稿コンテンツ文字列、または None
        """
        try:
            return manuscript_path.read_text(encoding="utf-8")
        except Exception as e:
            self._emit_log(log_messages, "error", f"原稿読み込みエラー: {e}", log)
            return None

    def _extract_character_states(self, content: str, context: PreviousEpisodeContext) -> None:
        """キャラクター状態抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        characters = ["直人", "あすか", "先生", "教授"]
        for character_name in characters:
            if character_name in content:
                emotional_state = self._analyze_character_emotion(content, character_name)
                relationships = self._extract_character_relationships(content, character_name)
                development_stage = self._analyze_character_development(content, character_name)
                key_attributes = self._extract_character_attributes(content, character_name)
                character_state = CharacterState(
                    character_name=character_name,
                    emotional_state=emotional_state,
                    current_relationships=relationships,
                    character_development_stage=development_stage,
                    key_attributes=key_attributes,
                )
                context.add_character_state(character_state)

    def _analyze_character_emotion(self, content: str, character_name: str) -> str:
        """キャラクター感情分析

        Args:
            content: 原稿コンテンツ
            character_name: キャラクター名

        Returns:
            感情状態文字列
        """
        character_sections = self._extract_character_sections(content, character_name)
        emotions = []
        for section in character_sections:
            emotion_matches = self._emotion_pattern.findall(section)
            emotions.extend(emotion_matches)
        if emotions:
            return emotions[-1]
        return "平静"

    def _extract_character_relationships(self, content: str, character_name: str) -> dict[str, str]:
        """キャラクター関係性抽出

        Args:
            content: 原稿コンテンツ
            character_name: 対象キャラクター名

        Returns:
            関係性辞書
        """
        relationships = {}
        other_characters = ["直人", "あすか", "先生", "教授"]
        other_characters = [c for c in other_characters if c != character_name]
        for other_char in other_characters:
            if character_name in content and other_char in content:
                if "一緒に" in content or "協力" in content:
                    relationships[other_char] = "協力的"
                elif "教える" in content or "指導" in content:
                    relationships[other_char] = "師弟関係"
                elif "友達" in content or "親友" in content:
                    relationships[other_char] = "友好的"
                else:
                    relationships[other_char] = "中立"
        return relationships

    @staticmethod
    def _emit_log(
        log_messages: list[dict[str, str]],
        level: str,
        message: str,
        log: cabc.Callable[[str, str], None] | None,
    ) -> None:
        """Record diagnostic entries and forward them when a callback is provided."""
        log_messages.append({"level": level, "message": message})
        if log is None:
            return
        if isinstance(log, cabc.Callable):  # type: ignore[arg-type]
            log(level, message)

    def _analyze_character_development(self, content: str, character_name: str) -> str:
        """キャラクター成長段階分析

        Args:
            content: 原稿コンテンツ
            character_name: キャラクター名

        Returns:
            成長段階文字列
        """
        character_sections = self._extract_character_sections(content, character_name)
        growth_keywords = {
            "初心者": ["初めて", "わからない", "教えて"],
            "理解段階": ["理解", "わかった", "なるほど"],
            "実践段階": ["やってみる", "実際に", "練習"],
            "熟練段階": ["できる", "得意", "上手"],
        }
        for stage, keywords in growth_keywords.items():
            for section in character_sections:
                if any(keyword in section for keyword in keywords):
                    return stage
        return "成長中"

    def _extract_character_attributes(self, content: str, character_name: str) -> list[str]:
        """キャラクター属性抽出

        Args:
            content: 原稿コンテンツ
            character_name: キャラクター名

        Returns:
            属性リスト
        """
        attributes = []
        character_sections = self._extract_character_sections(content, character_name)
        attribute_patterns = {
            "真面目": ["真面目", "丁寧", "きちんと"],
            "積極的": ["積極的", "やる気", "頑張"],
            "慎重": ["慎重", "気をつけ", "確認"],
            "協調性": ["みんなと", "一緒に", "協力"],
        }
        for attribute, patterns in attribute_patterns.items():
            for section in character_sections:
                if any(pattern in section for pattern in patterns):
                    attributes.append(attribute)
                    break
        return list(set(attributes))

    def _extract_character_sections(self, content: str, character_name: str) -> list[str]:
        """キャラクター関連セクション抽出

        Args:
            content: 原稿コンテンツ
            character_name: キャラクター名

        Returns:
            キャラクター関連セクションのリスト
        """
        lines = content.split("\n")
        sections = []
        current_section = []
        for line in lines:
            if character_name in line:
                current_section.append(line)
            elif current_section:
                if len(current_section) < 5:
                    current_section.append(line)
                else:
                    sections.append("\n".join(current_section))
                    current_section = []
        if current_section:
            sections.append("\n".join(current_section))
        return sections

    def _extract_story_progression(self, content: str, context: PreviousEpisodeContext) -> None:
        """ストーリー進行状態抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        main_plot_developments = self._extract_main_plot_developments(content)
        subplot_progressions = self._extract_subplot_progressions(content)
        resolved_conflicts = self._extract_resolved_conflicts(content)
        active_foreshadowing = self._extract_active_foreshadowing(content)
        story_momentum = self._estimate_story_momentum(content)
        story_progression = StoryProgressionState(
            main_plot_developments=main_plot_developments,
            subplot_progressions=subplot_progressions,
            resolved_conflicts=resolved_conflicts,
            active_foreshadowing=active_foreshadowing,
            story_momentum=story_momentum,
        )
        context.update_story_progression(story_progression)

    def _extract_main_plot_developments(self, content: str) -> list[str]:
        """メインプロット展開抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            メインプロット展開リスト
        """
        developments = []
        development_patterns = ["ついに(.+)した", "重要な(.+)を", "新たな(.+)が", "(.+)を解決した"]
        for pattern in development_patterns:
            matches = re.findall(pattern, content)
            developments.extend([match.strip() for match in matches])
        return developments[:5]

    def _extract_subplot_progressions(self, content: str) -> dict[str, str]:
        """サブプロット進行抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            サブプロット進行辞書
        """
        subplots = {}
        if "プログラミング" in content or "魔法" in content:
            tech_progress = "進行中"
            if "マスター" in content or "理解した" in content:
                tech_progress = "進展"
            subplots["技術学習"] = tech_progress
        if "友達" in content or "関係" in content:
            relationship_progress = "進行中"
            if "深まった" in content or "親密" in content:
                relationship_progress = "進展"
            subplots["人間関係"] = relationship_progress
        return subplots

    def _extract_resolved_conflicts(self, content: str) -> list[str]:
        """解決された衝突抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            解決された衝突リスト
        """
        resolved = []
        resolution_patterns = ["(.+)を解決した", "(.+)問題が解消", "(.+)を乗り越えた"]
        for pattern in resolution_patterns:
            matches = re.findall(pattern, content)
            resolved.extend([match.strip() for match in matches])
        return resolved

    def _extract_active_foreshadowing(self, content: str) -> list[str]:
        """アクティブ伏線抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            アクティブ伏線リスト
        """
        foreshadowing = []
        foreshadowing_matches = self._foreshadowing_pattern.findall(content)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in foreshadowing_matches):
                context_lines = lines[max(0, i - 1) : i + 2]
                foreshadowing.append(" ".join(context_lines).strip())
        return foreshadowing[:3]

    def _estimate_story_momentum(self, content: str) -> str:
        """ストーリーモメンタム推定

        Args:
            content: 原稿コンテンツ

        Returns:
            モメンタムレベル文字列
        """
        excitement_keywords = ["驚く", "すごい", "素晴らしい", "興奮", "感動", "衝撃"]
        excitement_count = sum(1 for keyword in excitement_keywords if keyword in content)
        if excitement_count >= 3:
            return "climactic"
        if excitement_count >= 2:
            return "high"
        if excitement_count >= 1:
            return "normal"
        return "low"

    def _extract_technical_learning(self, content: str, context: PreviousEpisodeContext) -> None:
        """技術学習状態抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        mastered_concepts = self._extract_mastered_concepts(content)
        current_learning_focus = self._extract_current_learning_focus(content)
        difficulty_level = self._estimate_difficulty_level(content)
        practical_applications = self._extract_practical_applications(content)
        next_learning_targets = self._extract_next_learning_targets(content)
        technical_learning = TechnicalLearningState(
            mastered_concepts=mastered_concepts,
            current_learning_focus=current_learning_focus,
            difficulty_level=difficulty_level,
            practical_applications=practical_applications,
            next_learning_targets=next_learning_targets,
        )
        context.update_technical_learning(technical_learning)

    def _extract_mastered_concepts(self, content: str) -> list[str]:
        """習得概念抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            習得概念リスト
        """
        mastered = []
        mastery_patterns = ["(.+)をマスターした", "(.+)を理解した", "(.+)ができるようになった"]
        for pattern in mastery_patterns:
            matches = re.findall(pattern, content)
            mastered.extend([match.strip() for match in matches])
        return mastered

    def _extract_current_learning_focus(self, content: str) -> str:
        """現在の学習フォーカス抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            学習フォーカス文字列
        """
        tech_elements = ["プログラミング", "魔法", "アルゴリズム", "デバッグ", "コード"]
        element_counts = {}
        for element in tech_elements:
            element_counts[element] = content.count(element)
        if element_counts:
            return max(element_counts, key=element_counts.get)
        return ""

    def _estimate_difficulty_level(self, content: str) -> str:
        """難易度レベル推定

        Args:
            content: 原稿コンテンツ

        Returns:
            難易度レベル文字列
        """
        difficulty_indicators = {
            "beginner": ["初心者", "基礎", "入門", "簡単"],
            "intermediate": ["中級", "応用", "実践", "チャレンジ"],
            "advanced": ["上級", "高度", "複雑", "マスター"],
        }
        for level, keywords in difficulty_indicators.items():
            if any(keyword in content for keyword in keywords):
                return level
        return "beginner"

    def _extract_practical_applications(self, content: str) -> list[str]:
        """実践的応用抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            実践的応用リスト
        """
        applications = []
        application_patterns = ["(.+)に応用", "(.+)で使用", "実際に(.+)した"]
        for pattern in application_patterns:
            matches = re.findall(pattern, content)
            applications.extend([match.strip() for match in matches])
        return applications[:5]

    def _extract_next_learning_targets(self, content: str) -> list[str]:
        """次の学習目標抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            次の学習目標リスト
        """
        targets = []
        target_patterns = ["次は(.+)を", "今度(.+)したい", "将来(.+)になりたい"]
        for pattern in target_patterns:
            matches = re.findall(pattern, content)
            targets.extend([match.strip() for match in matches])
        return targets

    def _extract_emotional_flow(self, content: str, context: PreviousEpisodeContext) -> None:
        """感情的流れ抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        emotional_transitions = self._extract_emotional_transitions(content)
        for transition in emotional_transitions:
            context.add_emotional_flow_element(transition)

    def _extract_emotional_transitions(self, content: str) -> list[str]:
        """感情変化抽出

        Args:
            content: 原稿コンテンツ

        Returns:
            感情変化リスト
        """
        transitions = []
        transition_patterns = ["(.+)から(.+)な気持ち", "最初は(.+)だったが(.+)", "(.+)になって(.+)した"]
        for pattern in transition_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    transition = f"{match[0]} → {match[1]}"
                    transitions.append(transition)
        return transitions

    def _extract_unresolved_elements(self, content: str, context: PreviousEpisodeContext) -> None:
        """未解決要素抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        unresolved_patterns = ["まだ(.+)していない", "(.+)は未解決", "(.+)が残っている"]
        for pattern in unresolved_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                context.add_unresolved_element(match.strip())

    def _extract_scene_continuity(self, content: str, context: PreviousEpisodeContext) -> None:
        """シーン継続性情報抽出

        Args:
            content: 原稿コンテンツ
            context: コンテキストオブジェクト
        """
        location_mentions = re.findall("(?:教室|図書館|実習室|廊下|校庭)で", content)
        if location_mentions:
            context.add_scene_continuity_note(f"前話の主要場所: {', '.join(set(location_mentions))}")
        time_mentions = re.findall("(?:朝|昼|夕方|夜|放課後)(?:に|の)", content)
        if time_mentions:
            context.add_scene_continuity_note(f"前話の時間帯: {', '.join(set(time_mentions))}")
        continuity_patterns = ["続きは(.+)", "次回(.+)予定", "(.+)することになった"]
        for pattern in continuity_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                context.add_scene_continuity_note(f"継続要素: {match.strip()}")
