"""Domain.services.content_quality_enhancer
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

# 統一ロギング統合 - console出力はDomain層では使用しません

"Content Quality Enhancer サービス\n\nTDD GREEN段階: テストを通すための最小限の実装\n開発ガイドの実践例として、コメント付きで詳細に実装\n\nTDD実践のポイント:\n1. まず最小限の実装でテストを通す(GREEN段階)\n2. 後でリファクタリングして品質を向上(REFACTOR段階)\n3. 仕様書の要件を段階的に実装\n"
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from noveler.domain.exceptions import DomainException
    from noveler.domain.value_objects.quality_score import QualityScore
except ImportError:

    class DomainError(Exception):
        """ドメイン層の基底例外"""

    class QualityScore:
        """品質スコア値オブジェクト"""

        def __init__(self, score: float) -> None:
            self.score = score


class EmptyTextError(DomainException):
    """空文字列エラー"""


class TextTooLongError(DomainException):
    """文字数上限超過エラー"""


class InvalidEncodingError(DomainException):
    """不正な文字エンコーディングエラー"""


class ProperNounExtractionError(DomainException):
    """固有名詞抽出エラー"""


class QualityAnalysisError(DomainException):
    """品質分析エラー"""


class EnhancementError(DomainException):
    """改善処理エラー"""


class ProjectSettingsNotFoundError(DomainException):
    """プロジェクト設定未存在エラー"""


class InvalidTargetScoreError(DomainException):
    """不正な目標スコアエラー"""


@dataclass
class ImprovementSuggestion:
    """改善提案"""

    category: str
    original_text: str
    improved_text: str
    reason: str
    priority: int


@dataclass
class EnhancementResult:
    """改善結果"""

    original_text: str
    enhanced_text: str
    improvements: list[ImprovementSuggestion]
    quality_score_before: float
    quality_score_after: float
    success: bool
    error_message: str | None = None


ContentEnhancementResult = EnhancementResult
QualityAnalysisResult = EnhancementResult


class ContentQualityEnhancer:
    """文章品質自動改善サービス

    新ワークフローの実践例:
    - 仕様書の要件を段階的に実装
    - TDD GREEN段階: テストを通すための最小実装
    - コメント付きで学習しやすい実装
    """

    def __init__(self) -> None:
        """初期化

        TDD実践のポイント:
        - 最小限の初期化で開始
        - 後でリファクタリング時に依存関係を整理
        """
        self._emotion_patterns = {
            "悲しかった": ["涙が頬を伝った", "目頭が熱くなった", "喉の奥が詰まった"],
            "嬉しかった": ["頬が緩んだ", "心が躍った", "胸が温かくなった"],
            "怒っていた": ["拳を握りしめた", "血管が浮き上がった", "眉間に深いしわが刻まれた"],
            "疲れていた": ["肩が重く沈んだ", "足取りが重くなった", "深いため息をついた"],
            "困っていた": ["眉をひそめた", "頭を掻いた", "唇を噛んだ"],
        }
        self._ending_variations = {
            "た。": ["た。", "ていた。", "のだった。", "。", "たのだ。"],
            "だった。": ["だった。", "であった。", "なのだった。", "。"],
        }
        self._proper_nouns_cache: dict[str, list[str]] = {}

    def enhance_text(
        self, text: str, target_score: float = 80.0, project_path: str | None = None
    ) -> EnhancementResult:
        """文章の品質を自動改善

        仕様3.1の主要な振る舞いを実装

        Args:
            text: 改善対象のテキスト
            target_score: 目標品質スコア(0-100)
            project_path: プロジェクト設定へのパス

        Returns:
            EnhancementResult: 改善結果

        Raises:
            EmptyTextError: 空文字列入力
            TextTooLongError: 文字数上限超過
            InvalidTargetScoreError: 不正な目標スコア
            ProjectSettingsNotFoundError: プロジェクト設定未存在
        """
        try:
            self._validate_input(text, target_score, project_path)
            quality_score_before = self._calculate_quality_score(text)
            protected_nouns = []
            if project_path:
                protected_nouns = self.protect_proper_nouns(text, project_path)
            improvements = []
            enhanced_text = text
            (enhanced_text, emotion_improvements) = self._enhance_emotions(enhanced_text, protected_nouns)
            improvements.extend(emotion_improvements)
            (enhanced_text, style_improvements) = self._enhance_style(enhanced_text, protected_nouns)
            improvements.extend(style_improvements)
            (enhanced_text, dialogue_improvements) = self._enhance_dialogue(enhanced_text, protected_nouns)
            improvements.extend(dialogue_improvements)
            (enhanced_text, description_improvements) = self._enhance_description(enhanced_text, protected_nouns)
            improvements.extend(description_improvements)
            quality_score_after = self._calculate_quality_score(enhanced_text)
            improvements.sort(key=lambda x: x.priority)
            return EnhancementResult(
                original_text=text,
                enhanced_text=enhanced_text,
                improvements=improvements,
                quality_score_before=quality_score_before,
                quality_score_after=quality_score_after,
                success=True,
            )
        except (EmptyTextError, TextTooLongError, InvalidTargetScoreError, ProjectSettingsNotFoundError):
            raise
        except Exception as e:
            return EnhancementResult(
                original_text=text,
                enhanced_text=text,
                improvements=[],
                quality_score_before=0.0,
                quality_score_after=0.0,
                success=False,
                error_message=str(e),
            )

    def suggest_improvements(self, text: str) -> list[ImprovementSuggestion]:
        """改善提案を生成

        仕様3.2の品質スコア向上提案機能を実装

        Args:
            text: 分析対象のテキスト

        Returns:
            list[ImprovementSuggestion]: 優先度順の改善提案リスト
        """
        suggestions = []
        for emotion, replacements in self._emotion_patterns.items():
            if emotion in text:
                suggestions.append(
                    ImprovementSuggestion(
                        category="emotion",
                        original_text=emotion,
                        improved_text=replacements[0],
                        reason=f"抽象的な感情表現「{emotion}」を具体的な描写に変更",
                        priority=1,
                    )
                )
        ta_count = text.count("た。")
        if ta_count >= 3:
            suggestions.append(
                ImprovementSuggestion(
                    category="style",
                    original_text="た。",
                    improved_text="ていた。",
                    reason=f"「た。」が{ta_count}回使用されています。文末表現を多様化しましょう",
                    priority=2,
                )
            )
        if "」と彼は言った。" in text or "」と彼女は言った。" in text:
            suggestions.append(
                ImprovementSuggestion(
                    category="dialogue",
                    original_text="」と彼は言った。",
                    improved_text="」",
                    reason="会話文の地の文を簡潔にして、テンポを改善",
                    priority=3,
                )
            )
        if "風が吹いた" in text or "雨が降っていた" in text:
            suggestions.append(
                ImprovementSuggestion(
                    category="description",
                    original_text="風が吹いた",
                    improved_text="冷たい風が頬を撫でた",
                    reason="単調な描写を五感を使った表現に変更",
                    priority=4,
                )
            )
        long_sentences = self._find_long_sentences(text)
        if long_sentences:
            suggestions.append(
                ImprovementSuggestion(
                    category="readability",
                    original_text=long_sentences[0][:20] + "...",
                    improved_text="文を分割して読みやすく",
                    reason="長文を短文に分割して可読性を向上",
                    priority=5,
                )
            )
        suggestions.sort(key=lambda x: x.priority)
        return suggestions

    def protect_proper_nouns(self, _text: str, project_path: str | None) -> list[str]:
        """固有名詞を保護対象として抽出

        仕様3.3の固有名詞保護機能を実装

        Args:
            text: 対象テキスト
            project_path: プロジェクト設定へのパス

        Returns:
            list[str]: 保護対象の固有名詞リスト

        Raises:
            ProjectSettingsNotFoundError: プロジェクト設定未存在
        """
        try:
            if project_path in self._proper_nouns_cache:
                return self._proper_nouns_cache[project_path]
            project_dir = Path(project_path)  # TODO: IPathServiceを使用するように修正
            if not project_dir.exists():
                msg = f"プロジェクト設定が見つからない: {project_path}"
                raise ProjectSettingsNotFoundError(msg)
            proper_nouns = []
            character_file = project_dir / "キャラクター.yaml"
            if character_file.exists():
                with Path(character_file).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                    character_data: dict[str, Any] = yaml.safe_load(f)
                    if character_data:
                        proper_nouns.extend(self._extract_names_from_character_data(character_data))
            world_file = project_dir / "世界観.yaml"
            if world_file.exists():
                with Path(world_file).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                    world_data: dict[str, Any] = yaml.safe_load(f)
                    if world_data:
                        proper_nouns.extend(self._extract_names_from_world_data(world_data))
            terms_file = project_dir / "用語集.yaml"
            if terms_file.exists():
                with Path(terms_file).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                    terms_data: dict[str, Any] = yaml.safe_load(f)
                    if terms_data:
                        proper_nouns.extend(self._extract_names_from_terms_data(terms_data))
            unique_proper_nouns = list(set(proper_nouns))
            self._proper_nouns_cache[project_path] = unique_proper_nouns
            return unique_proper_nouns
        except Exception as e:
            msg = f"固有名詞の抽出に失敗: {e!s}"
            raise ProperNounExtractionError(msg) from e

    def _validate_input(self, text: str, target_score: float, project_path: str | None = None) -> None:
        """入力バリデーション

        仕様5. エラーハンドリング に対応
        """
        if not text or text.strip() == "":
            msg = "空文字列または空白のみの入力は処理できません"
            raise EmptyTextError(msg)
        if len(text) > 10000:
            msg = "10,000文字を超えるテキストは処理できません"
            raise TextTooLongError(msg)
        if not 0.0 <= target_score <= 100.0:
            msg = "目標スコアは0-100の範囲で指定してください"
            raise InvalidTargetScoreError(msg)
        if project_path and (not Path(project_path).exists()):  # TODO: IPathServiceを使用するように修正
            msg = f"プロジェクト設定が見つからない: {project_path}"
            raise ProjectSettingsNotFoundError(msg)

    def _calculate_quality_score(self, text: str) -> float:
        """品質スコアを計算

        TDD GREEN段階: 最小限の実装
        実際の品質チェッカーとの統合は REFACTOR段階で実装
        """
        base_score = 50.0
        if 100 <= len(text) <= 1000:
            base_score += 10.0
        abstract_emotions = ["悲しかった", "嬉しかった", "怒っていた", "疲れていた"]
        abstract_count = sum(1 for emotion in abstract_emotions if emotion in text)
        if abstract_count == 0:
            base_score += 20.0
        else:
            base_score -= abstract_count * 5.0
        ta_count = text.count("た。")
        if ta_count <= 2:
            base_score += 15.0
        else:
            base_score -= (ta_count - 2) * 3.0
        if "「" in text and "」" in text:
            base_score += 10.0
        return max(0.0, min(100.0, base_score))

    def _enhance_emotions(self, text: str, protected_nouns: list[str]) -> tuple[str, list[ImprovementSuggestion]]:
        """感情表現の具体化

        仕様3.1の感情表現改善機能を実装
        """
        enhanced_text = text
        improvements = []
        for emotion, replacements in self._emotion_patterns.items():
            if emotion in enhanced_text:
                if not any(noun in enhanced_text for noun in protected_nouns):
                    replacement = replacements[0]
                    enhanced_text = enhanced_text.replace(emotion, replacement, 1)
                    improvements.append(
                        ImprovementSuggestion(
                            category="emotion",
                            original_text=emotion,
                            improved_text=replacement,
                            reason="抽象的な感情表現を具体的な描写に変更",
                            priority=1,
                        )
                    )
        return (enhanced_text, improvements)

    def _enhance_style(self, text: str, protected_nouns: list[str]) -> tuple[str, list[ImprovementSuggestion]]:
        """文末表現の多様化

        仕様3.1の文末表現改善機能を実装
        """
        enhanced_text = text
        improvements = []
        ta_positions = []
        for i, _char in enumerate(enhanced_text):
            if i > 0 and enhanced_text[i - 1 : i + 1] == "た。":
                ta_positions.append(i - 1)
        if len(ta_positions) >= 2:
            variations = ["ていた。", "のだった。", "ことにした。"]
            for idx, pos in enumerate(reversed(ta_positions[1:])):
                context = enhanced_text[max(0, pos - 10) : pos + 10]
                if not any(noun in context for noun in protected_nouns):
                    variation = variations[idx % len(variations)]
                    if variation == "ていた。":
                        enhanced_text = enhanced_text[:pos] + "てい" + enhanced_text[pos:]
                    elif variation == "のだった。":
                        enhanced_text = enhanced_text[: pos + 1] + "のだっ" + enhanced_text[pos + 1 :]
                    else:
                        enhanced_text = enhanced_text[:pos] + "ることにし" + enhanced_text[pos:]
                    improvements.append(
                        ImprovementSuggestion(
                            category="style",
                            original_text="た。",
                            improved_text=variation,
                            reason="文末表現を多様化して単調さを改善",
                            priority=2,
                        )
                    )
                    break
        return (enhanced_text, improvements)

    def _enhance_dialogue(self, text: str, protected_nouns: list[str]) -> tuple[str, list[ImprovementSuggestion]]:
        """会話文の改善

        仕様3.1の会話文改善機能を実装
        """
        enhanced_text = text
        improvements = []
        patterns = [("」と彼は言った。", "」"), ("」と彼女は言った。", "」"), ("」と言った。", "」")]
        for original, replacement in patterns:
            if original in enhanced_text:
                context_start = enhanced_text.find(original)
                if context_start != -1:
                    context = enhanced_text[max(0, context_start - 20) : context_start + 20]
                    if not any(noun in context for noun in protected_nouns):
                        enhanced_text = enhanced_text.replace(original, replacement, 1)
                        improvements.append(
                            ImprovementSuggestion(
                                category="dialogue",
                                original_text=original,
                                improved_text=replacement,
                                reason="会話文を簡潔にしてテンポを改善",
                                priority=3,
                            )
                        )
                        break
        return (enhanced_text, improvements)

    def _enhance_description(self, text: str, protected_nouns: list[str]) -> tuple[str, list[ImprovementSuggestion]]:
        """描写の改善

        仕様3.1の描写改善機能を実装
        """
        enhanced_text = text
        improvements = []
        description_patterns = {
            "風が吹いた": "冷たい風が頬を撫でた",
            "雨が降っていた": "雨粒が窓を叩いていた",
            "雪が降った": "雪片が静かに舞い落ちた",
            "朝が来た": "朝日が部屋を照らした",
            "夜が来た": "夜の静寂が辺りを包んだ",
        }
        for original, replacement in description_patterns.items():
            if original in enhanced_text:
                context_start = enhanced_text.find(original)
                if context_start != -1:
                    context = enhanced_text[max(0, context_start - 15) : context_start + 15]
                    if not any(noun in context for noun in protected_nouns):
                        enhanced_text = enhanced_text.replace(original, replacement, 1)
                        improvements.append(
                            ImprovementSuggestion(
                                category="description",
                                original_text=original,
                                improved_text=replacement,
                                reason="単調な描写を五感を使った表現に変更",
                                priority=4,
                            )
                        )
                        break
        return (enhanced_text, improvements)

    def _find_long_sentences(self, text: str) -> list[str]:
        """長文を検出

        読みやすさ改善のヘルパー関数
        """
        sentences = re.split("[。!?]", text)
        return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 50]

    def _extract_names_from_character_data(self, character_data: dict[str, Any]) -> list[str]:
        """キャラクター.yaml から人名を抽出

        固有名詞保護機能のヘルパー関数
        """
        names: list[str] = []
        if isinstance(character_data, dict):
            names.extend(self._extract_names_from_dict(character_data))
        elif isinstance(character_data, list):
            names.extend(self._extract_names_from_list(character_data))
        elif isinstance(character_data, str):
            names.extend(self._extract_names_from_string(character_data))
        return self._clean_and_deduplicate_names(names)

    def _extract_names_from_dict(self, data: dict[str, Any]) -> list[str]:
        """辞書形式のキャラクターデータから名前を抽出"""
        names: list[str] = []
        for key, value in data.items():
            if isinstance(value, dict):
                name = self._extract_name_from_dict_item(value, key)
                if name:
                    names.append(name)
        return names

    def _extract_names_from_list(self, data: list[Any]) -> list[str]:
        """リスト形式のキャラクターデータから名前を抽出"""
        names: list[str] = []
        for item in data:
            if isinstance(item, dict):
                name = self._extract_name_from_dict_item(item)
                if name:
                    names.append(name)
            elif isinstance(item, str) and len(item) > 0:
                names.append(item)
        return names

    def _extract_names_from_string(self, data: str) -> list[str]:
        """文字列形式のキャラクターデータから名前を抽出"""
        names: list[str] = []
        normalized_data: dict[str, Any] = data.replace("、", ",").replace(",", ",")
        for name in normalized_data.split(","):
            cleaned_name = name.strip()
            if len(cleaned_name) > 0:
                names.append(cleaned_name)
        return names

    def _extract_name_from_dict_item(self, item: dict[str, Any], fallback_key: str) -> str:
        """辞書アイテムから名前フィールドを抽出"""
        if "名前" in item:
            return item["名前"]
        if "name" in item:
            return item["name"]
        if isinstance(fallback_key, str) and len(fallback_key) > 0:
            return fallback_key
        return ""

    def _clean_and_deduplicate_names(self, names: list[str]) -> list[str]:
        """名前リストの重複削除と空文字除去"""
        unique_names: list[str] = []
        for name in names:
            if isinstance(name, str) and len(name) > 0 and (name not in unique_names):
                unique_names.append(name)
        return unique_names

    def _extract_names_from_world_data(self, world_data: dict[str, Any]) -> list[str]:
        """世界観.yaml から地名・組織名を抽出"""
        names: list[str] = []
        if "組織" in world_data:
            org_data: dict[str, Any] = world_data["組織"]
            if isinstance(org_data, dict):
                names.extend(org_data.keys())
            elif isinstance(org_data, list):
                names.extend(org_data)
        if "地名" in world_data:
            place_data: dict[str, Any] = world_data["地名"]
            if isinstance(place_data, dict):
                names.extend(place_data.keys())
            elif isinstance(place_data, list):
                names.extend(place_data)
        if "施設" in world_data:
            facility_data: dict[str, Any] = world_data["施設"]
            if isinstance(facility_data, dict):
                names.extend(facility_data.keys())
            elif isinstance(facility_data, list):
                names.extend(facility_data)
        return names

    def _extract_names_from_terms_data(self, terms_data: dict[str, Any]) -> list[str]:
        """用語集.yaml から専門用語を抽出"""
        names: list[str] = []
        if isinstance(terms_data, dict):
            names.extend(terms_data.keys())
        elif isinstance(terms_data, list):
            names.extend(terms_data)
        return names