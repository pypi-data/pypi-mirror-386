"""Domain.services.episode_preview_generation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
EpisodePreviewGenerationService

エピソードプレビューの生成・最適化を行うドメインサービスです。
テキスト解析、重要文抽出、品質評価、プレビュー最適化を担当します。
"""


import re
from typing import Any, ClassVar

from noveler.domain.exceptions import DomainValidationError
from noveler.domain.value_objects.preview_configuration import (
    ContentFilter,
    PreviewConfiguration,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class PreviewResult:
    """プレビュー生成結果を表現するクラス"""

    def __init__(
        self,
        preview_text: str,
        metadata: dict[str, Any],
        quality_score: float = 0.0,
        applied_config: PreviewConfiguration | None = None,
        generation_warnings: list[str] | None = None,
    ) -> None:
        self.preview_text = preview_text
        self.metadata = metadata
        self.quality_score = quality_score
        self.applied_config = applied_config
        self.generation_warnings = generation_warnings or []
        self.generation_timestamp = project_now().datetime.isoformat()

    def is_high_quality(self) -> bool:
        """高品質なプレビューかチェック"""
        return self.quality_score >= self.applied_config.get_minimum_quality_score()

    def has_warnings(self) -> bool:
        """警告があるかチェック"""
        return len(self.generation_warnings) > 0


class QualityValidationResult:
    """品質検証結果を表現するクラス"""

    def __init__(
        self,
        is_valid: bool,
        quality_score: float,
        issues: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        self.is_valid = is_valid
        self.quality_score = quality_score
        self.issues = issues or []
        self.suggestions = suggestions or []
        self.validation_timestamp = project_now().datetime.isoformat()


class EpisodePreviewGenerationService:
    """エピソードプレビュー生成を行うドメインサービス"""

    METADATA_SCHEMA_VERSION: ClassVar[str] = "1.1.0"

    def __init__(self) -> None:
        self._sentiment_keywords = {
            "positive": ["嬉しい", "楽しい", "幸せ", "希望", "勇気", "愛", "笑顔", "感動"],
            "negative": ["悲しい", "怒り", "恐怖", "絶望", "不安", "憎しみ", "涙", "孤独"],
            "action": ["戦い", "走る", "飛ぶ", "攻撃", "守る", "逃げる", "追う", "闘う"],
            "mystery": ["謎", "秘密", "不思議", "隠された", "真実", "陰謀", "正体", "暗号"],
        }

    def generate_preview(
        self,
        episode_content: str,
        config: PreviewConfiguration,
        episode_metadata: dict[str, Any] | None = None,
    ) -> PreviewResult:
        """エピソードプレビューを生成"""
        if not episode_content or not episode_content.strip():
            msg = "エピソードコンテンツが空です"
            raise DomainValidationError(
                "EpisodePreview",
                "episode_content",
                msg,
                episode_content,
            )

        if not isinstance(config, PreviewConfiguration):
            msg = "設定はPreviewConfigurationのインスタンスである必要があります"
            raise DomainValidationError(
                "EpisodePreview",
                "config",
                msg,
                config,
            )

        warnings = []

        # コンテンツの前処理
        cleaned_content = self._clean_content(episode_content)
        if len(cleaned_content) < 50:
            warnings.append("コンテンツが短すぎます(50文字未満)")

        # 重要な文を抽出
        important_sentences = self._extract_important_sentences(cleaned_content, config)
        if len(important_sentences) == 0:
            warnings.append("重要な文を抽出できませんでした")
            important_sentences = self._fallback_sentence_extraction(cleaned_content, config)

        # プレビューテキストを生成
        preview_text = self._create_preview_text(important_sentences, config)
        preview_text = self._ensure_teaser_suffix(preview_text, config)

        # 品質スコアを計算
        quality_score = self._calculate_quality_score(preview_text, cleaned_content, config)

        # メタデータを生成
        metadata = self._generate_preview_metadata(
            original_content=cleaned_content,
            preview_text=preview_text,
            quality_score=quality_score,
            config=config,
            episode_metadata=episode_metadata,
        )

        return PreviewResult(
            preview_text=preview_text,
            metadata=metadata,
            quality_score=quality_score,
            applied_config=config,
            generation_warnings=warnings,
        )

    def optimize_preview_content(self, preview_result: PreviewResult) -> PreviewResult:
        """プレビューコンテンツを最適化"""
        if not isinstance(preview_result, PreviewResult):
            msg = "プレビュー結果はPreviewResultのインスタンスである必要があります"
            raise DomainValidationError(
                "EpisodePreview",
                "preview_result",
                msg,
                preview_result,
            )

        preview_text = preview_result.preview_text
        config = preview_result.applied_config
        warnings = preview_result.generation_warnings.copy()

        # 読みやすさの向上
        optimized_text = self._improve_readability(preview_text, config)

        # 魅力度の向上
        optimized_text = self._enhance_appeal(optimized_text, config)

        # 最終調整
        optimized_text = self._final_adjustments(optimized_text, config)

        # 品質スコアの再計算
        quality_score = self._calculate_quality_score(optimized_text, preview_text, config)

        # 最適化の効果をチェック
        if quality_score <= preview_result.quality_score:
            warnings.append("最適化による品質向上が確認できませんでした")

        return PreviewResult(
            preview_text=optimized_text,
            metadata=preview_result.metadata,
            quality_score=quality_score,
            applied_config=config,
            generation_warnings=warnings,
        )

    def validate_preview_quality(self, preview_result: PreviewResult) -> QualityValidationResult:
        """プレビューの品質を検証"""
        if not isinstance(preview_result, PreviewResult):
            msg = "プレビュー結果はPreviewResultのインスタンスである必要があります"
            raise DomainValidationError(
                "EpisodePreview",
                "preview_result",
                msg,
                preview_result,
            )

        preview_text = preview_result.preview_text
        config = preview_result.applied_config

        issues = []
        suggestions = []

        # 長さのチェック
        if len(preview_text) > config.max_length:
            issues.append(f"プレビューが長すぎます({len(preview_text)}文字 > {config.max_length}文字)")

        if len(preview_text) < config.max_length * 0.3:
            suggestions.append("プレビューがやや短いです。より多くの内容を含めることを検討してください")

        # 品質基準のチェック
        quality_score = preview_result.quality_score
        min_quality = config.get_minimum_quality_score()

        if quality_score < min_quality:
            issues.append(f"品質スコアが基準を下回っています({quality_score} < {min_quality})")

        # コンテンツ特有のチェック
        content_issues, content_suggestions = self._validate_content_specific_quality(preview_text, config)
        issues.extend(content_issues)
        suggestions.extend(content_suggestions)

        # 読みやすさのチェック
        readability_issues = self._check_readability(preview_text)
        suggestions.extend(readability_issues)

        return QualityValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
        )

    def batch_generate_previews(
        self, episodes_data: list[dict[str, Any]], config: PreviewConfiguration
    ) -> list[PreviewResult]:
        """複数エピソードのプレビューを一括生成"""
        if not episodes_data:
            return []

        if not isinstance(config, PreviewConfiguration):
            msg = "設定はPreviewConfigurationのインスタンスである必要があります"
            raise DomainValidationError(
                "EpisodePreview",
                "config",
                msg,
                config,
            )

        results: list[Any] = []

        for episode_data in episodes_data:
            try:
                content = episode_data.get("content", "")
                metadata = episode_data.get("metadata", {})

                preview_result = self.generate_preview(content, config)

                # エピソードIDとメタデータを追加
                preview_result.metadata["episode_id"] = episode_data.get("id", "unknown")
                preview_result.metadata.update(metadata)

                results.append(preview_result)

            except Exception as e:
                # エラーが発生した場合もPreviewResultとして記録
                error_result = PreviewResult(
                    preview_text="",
                    metadata={
                        "episode_id": episode_data.get("id", "unknown"),
                        "error": str(e),
                    },
                    quality_score=0.0,
                    applied_config=config,
                    generation_warnings=[f"プレビュー生成エラー: {e!s}"],
                )

                results.append(error_result)

        return results

    def _clean_content(self, content: str) -> str:
        """コンテンツをクリーニング"""
        # Markdownマークアップの削除
        content = re.sub(r"[#*_`]", "", content)
        # HTMLタグの削除
        content = re.sub(r"<[^>]+>", "", content)
        # 複数の空白を単一に
        content = re.sub(r"\s+", " ", content)
        # 前後の空白を削除
        return content.strip()

    def _extract_important_sentences(self, content: str, config: PreviewConfiguration) -> list[str]:
        """重要な文を抽出"""
        sentences = self._split_sentences(content)

        if not sentences:
            return []

        # 文の重要度を計算
        scored_sentences = []
        for sentence in sentences:
            score = self._calculate_sentence_importance(sentence, config)
            scored_sentences.append((sentence, score))

        # スコア順にソート
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # 設定に基づいて文を選択
        max_sentences = min(config.sentence_count, len(scored_sentences))
        selected_sentences = []

        # フィルター条件に合う文を優先選択
        for sentence, _ in scored_sentences:
            if len(selected_sentences) >= max_sentences:
                break

            if self._meets_filter_criteria(sentence, config):
                selected_sentences.append(sentence)

        # フィルター条件で足りない場合は高スコア文を追加
        if len(selected_sentences) < max_sentences:
            for sentence, _ in scored_sentences:
                if len(selected_sentences) >= max_sentences:
                    break
                if sentence not in selected_sentences:
                    selected_sentences.append(sentence)

        return selected_sentences

    def _fallback_sentence_extraction(self, content: str, config: PreviewConfiguration) -> list[str]:
        """フォールバック文抽出"""
        sentences = self._split_sentences(content)

        if not sentences:
            return [content[: config.max_length] + config.style_settings.ellipsis]

        # 最初の数文を返す
        return sentences[: min(config.sentence_count, len(sentences))]

    def _create_preview_text(self, sentences: list[str], config: PreviewConfiguration) -> str:
        """プレビューテキストを作成"""
        if not sentences:
            return ""

        # スタイルに応じた結合方法
        if config.is_teaser_style():
            # ティザーは断片的に
            preview = " ... ".join(sentences)
        elif config.is_dialogue_focus_style():
            # 会話重視は改行で区切る
            preview = config.style_settings.line_break.join(sentences)
        else:
            # その他は自然な接続
            preview = " ".join(sentences)

        # 長さ制限の適用
        if len(preview) > config.max_length:
            truncate_pos = config.max_length - len(config.style_settings.ellipsis)
            preview = preview[:truncate_pos] + config.style_settings.ellipsis

        return preview

    def _ensure_teaser_suffix(self, text: str, config: PreviewConfiguration) -> str:
        """ティザースタイルの末尾を整形"""

        if not text or not config.is_teaser_style():
            return text

        ellipsis = config.style_settings.ellipsis
        if text.endswith(ellipsis):
            return text

        trimmed = text.rstrip("。!?！？")
        return f"{trimmed}{ellipsis}" if trimmed else ellipsis

    def _generate_preview_metadata(
        self,
        original_content: str,
        preview_text: str,
        quality_score: float,
        config: PreviewConfiguration,
        episode_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """プレビューメタデータを生成"""

        original_sentences = self._split_sentences(original_content)
        preview_sentences = self._split_sentences(preview_text)

        original_char_count = len(original_content)
        preview_char_count = len(preview_text)
        original_sentence_count = len(original_sentences)
        preview_sentence_count = len(preview_sentences)

        dialogue_sentence_count = sum(1 for sentence in original_sentences if self._is_dialogue(sentence))
        preview_dialogue_sentence_count = sum(1 for sentence in preview_sentences if self._is_dialogue(sentence))

        action_sentence_count = sum(1 for sentence in original_sentences if self._contains_action_words(sentence))
        emotion_sentence_count = sum(1 for sentence in original_sentences if self._contains_emotion_words(sentence))
        mystery_sentence_count = sum(1 for sentence in original_sentences if self._contains_mystery_elements(sentence))

        dominant_sentiment, sentiment_distribution = self._analyze_sentiment_details(original_content, original_sentences)

        original_reading_time = self._estimate_reading_time(original_content)
        preview_reading_time = self._estimate_reading_time(preview_text)
        quality_minimum = config.get_minimum_quality_score()
        hook = self._derive_preview_hook(preview_sentences, preview_text, config)

        source_statistics = {
            "character_count": original_char_count,
            "sentence_count": original_sentence_count,
            "dialogue_sentence_count": dialogue_sentence_count,
            "action_sentence_count": action_sentence_count,
            "emotion_sentence_count": emotion_sentence_count,
            "mystery_sentence_count": mystery_sentence_count,
            "has_dialogue": dialogue_sentence_count > 0,
            "reading_time_seconds": original_reading_time,
            "sentiment_distribution": sentiment_distribution,
            "content_filter_hits": self._calculate_content_filter_hits(original_sentences, config),
        }

        preview_statistics = {
            "character_count": preview_char_count,
            "sentence_count": preview_sentence_count,
            "reading_time_seconds": preview_reading_time,
            "contains_dialogue": preview_dialogue_sentence_count > 0,
            "dialogue_sentence_count": preview_dialogue_sentence_count,
            "hook": hook,
            "ends_with_ellipsis": preview_text.endswith(config.style_settings.ellipsis),
        }

        config_snapshot = {
            "preview_style": config.preview_style.value,
            "sentence_count": config.sentence_count,
            "max_length": config.max_length,
            "content_filters": [f.value for f in config.content_filters],
            "preserve_formatting": config.preserve_formatting,
            "quality_thresholds": [threshold.to_dict() for threshold in config.quality_thresholds],
        }

        quality_summary = {
            "score": quality_score,
            "minimum_required": quality_minimum,
            "passed": quality_score >= quality_minimum,
        }

        metadata: dict[str, Any] = {
            "schema_version": self.METADATA_SCHEMA_VERSION,
            "original_word_count": original_char_count,
            "original_character_count": original_char_count,
            "sentence_count": original_sentence_count,
            "has_dialogue": source_statistics["has_dialogue"],
            "dialogue_sentence_count": dialogue_sentence_count,
            "estimated_reading_time": original_reading_time,
            "preview_word_count": preview_char_count,
            "preview_character_count": preview_char_count,
            "preview_sentence_count": preview_sentence_count,
            "preview_estimated_reading_time": preview_reading_time,
            "preview_style": config_snapshot["preview_style"],
            "content_filters": config_snapshot["content_filters"],
            "dominant_sentiment": dominant_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "hook": hook,
            "quality_score": quality_score,
            "quality_minimum_threshold": quality_minimum,
            "quality_passed": quality_summary["passed"],
            "source": source_statistics,
            "preview": preview_statistics,
            "config": config_snapshot,
            "quality": quality_summary,
        }

        if episode_metadata:
            episode_info: dict[str, Any] = {}
            title = episode_metadata.get("title") or episode_metadata.get("episode_title")
            if title:
                episode_info["episode_title"] = title
            if "episode_number" in episode_metadata:
                episode_info["episode_number"] = episode_metadata["episode_number"]
            if "genre" in episode_metadata:
                episode_info["genre"] = episode_metadata["genre"]
            if "tags" in episode_metadata:
                episode_info["tags"] = episode_metadata["tags"]
            if episode_info:
                metadata["episode"] = episode_info
                metadata.update(episode_info)

        return metadata

    def _calculate_sentence_importance(self, sentence: str, config: PreviewConfiguration) -> float:
        """文の重要度を計算"""
        score = self._calculate_basic_importance(sentence)
        score += self._calculate_content_importance(sentence, config)
        score += self._calculate_style_importance(sentence, config)
        return score

    def _calculate_basic_importance(self, sentence: str) -> float:
        """基本的な重要度を計算"""
        return 0.1 if len(sentence) > 10 else 0.0

    def _calculate_content_importance(self, sentence: str, config: PreviewConfiguration) -> float:
        """コンテンツフィルターに基づく重要度を計算"""
        score = 0.0

        if config.should_include_dialogue() and self._is_dialogue(sentence):
            score += 0.5
        if config.should_include_action() and self._contains_action_words(sentence):
            score += 0.4
        if config.should_include_emotion() and self._contains_emotion_words(sentence):
            score += 0.3
        if config.should_include_description() and self._is_descriptive(sentence):
            score += 0.2

        return score

    def _calculate_style_importance(self, sentence: str, config: PreviewConfiguration) -> float:
        """スタイル特有の重要度を計算"""
        if config.is_teaser_style():
            return 0.6 if self._contains_mystery_elements(sentence) else 0.0
        if config.is_dialogue_focus_style() and self._is_dialogue(sentence):
            base_score = 0.7
            character_bonus = 0.3 if self._has_character_voice(sentence) else 0.0
            return base_score + character_bonus
        return 0.0

    def _calculate_content_filter_hits(self, sentences: list[str], config: PreviewConfiguration) -> dict[str, int]:
        """コンテンツフィルターごとのマッチ数を算出"""

        return {
            "dialogue": sum(1 for sentence in sentences if self._is_dialogue(sentence)),
            "action": sum(1 for sentence in sentences if self._contains_action_words(sentence)),
            "emotion": sum(1 for sentence in sentences if self._contains_emotion_words(sentence)),
            "description": sum(1 for sentence in sentences if self._is_descriptive(sentence)),
            "active_filters": [f.value for f in config.content_filters],
        }

    def _meets_filter_criteria(self, sentence: str, config: PreviewConfiguration) -> bool:
        """フィルター条件を満たすかチェック"""
        if not config.content_filters:
            return True

        meets_criteria = False

        for content_filter in config.content_filters:
            if (
                (content_filter == ContentFilter.DIALOGUE and self._is_dialogue(sentence))
                or (content_filter == ContentFilter.ACTION and self._contains_action_words(sentence))
                or (content_filter == ContentFilter.EMOTION and self._contains_emotion_words(sentence))
                or (content_filter == ContentFilter.DESCRIPTION and self._is_descriptive(sentence))
            ):
                meets_criteria = True

        return meets_criteria

    def _improve_readability(self, text: str, _config: PreviewConfiguration) -> str:
        """読みやすさを向上"""
        # 適切な句読点の調整
        text = re.sub(r"([。!?])([^「」\s])", r"\1 \2", text)

        # 冗長な表現の簡潔化
        text = re.sub(r"である。", "だ。", text)
        text = re.sub(r"でありました", "でした", text)

        # 敬語の統一
        text = re.sub(r"です。", "だ。", text)

        return text.strip()

    def _enhance_appeal(self, text: str, config: PreviewConfiguration) -> str:
        """魅力度を向上"""
        # キーワードの強調
        appeal_keywords = ["転生", "異世界", "魔法", "冒険", "恋愛", "戦闘", "謎", "秘密"]

        for keyword in appeal_keywords:
            if keyword in text:
                emphasis = config.style_settings.emphasis_marker
                text = text.replace(keyword, f"{emphasis}{keyword}{emphasis}", 1)
                break  # 1つだけ強調

        # ティザースタイル特有の処理
        if config.is_teaser_style():
            ellipsis = config.style_settings.ellipsis
            if not text.endswith(ellipsis):
                text = text.rstrip()
                text = text.rstrip("。!?！？")
                text += ellipsis

        return text

    def _final_adjustments(self, text: str, config: PreviewConfiguration) -> str:
        """最終調整"""
        # 余分な空白の削除
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # 文末の調整
        ellipsis = config.style_settings.ellipsis
        if config.is_teaser_style():
            if text.endswith(ellipsis * 2):
                text = text[: -len(ellipsis)]
            if not text.endswith(ellipsis):
                text = text.rstrip("。!?！？")
                text += ellipsis
        else:
            if not text.endswith(("。", "!", "！", "?", "？")):
                text += "。"

        # 長さの最終確認
        if len(text) > config.max_length:
            truncate_pos = config.max_length - len(config.style_settings.ellipsis)
            text = text[:truncate_pos].rstrip() + config.style_settings.ellipsis

        return text

    def _calculate_quality_score(
        self, preview_text: str, _original_content: str, config: PreviewConfiguration
    ) -> float:
        """品質スコアを計算

        Strategy パターンを使用して特定の評価指標を組み合わせる。
        """
        if not preview_text:
            return 0.0

        calculator = QualityScoreCalculator(preview_text, config)
        calculator.set_service(self)  # サービスの参照を設定
        return calculator.calculate_total_score()

    def _derive_preview_hook(
        self, preview_sentences: list[str], preview_text: str, config: PreviewConfiguration
    ) -> str:
        """プレビュー用のフック文を推定"""

        if preview_sentences:
            for sentence in preview_sentences:
                trimmed = sentence.strip()
                if not trimmed:
                    continue
                if trimmed.endswith(("?", "？")):
                    return self._truncate_hook(trimmed, config)
                if config.is_teaser_style() and trimmed.endswith(config.style_settings.ellipsis):
                    return self._truncate_hook(trimmed, config)

            candidate = preview_sentences[0].strip()
        else:
            candidate = preview_text.strip()

        return self._truncate_hook(candidate, config)

    def _truncate_hook(self, text: str, config: PreviewConfiguration, limit: int = 80) -> str:
        """フック文を指定文字数に収める"""

        if len(text) <= limit:
            return text

        ellipsis = config.style_settings.ellipsis
        truncate_position = max(limit - len(ellipsis), 0)
        return text[:truncate_position].rstrip() + ellipsis

    def _validate_content_specific_quality(
        self, preview_text: str, config: PreviewConfiguration
    ) -> tuple[list[str], list[str]]:
        """コンテンツ固有の品質検証"""
        issues = []
        suggestions = []

        # スタイル固有のチェック
        if config.is_dialogue_focus_style():
            if not self._contains_dialogue(preview_text):
                issues.append("会話重視スタイルですが、会話が含まれていません")

        elif config.is_teaser_style():
            if not self._contains_mystery_elements(preview_text):
                suggestions.append("ティザースタイルでは、より謎めいた要素を含めることを推奨します")

        # 感情表現のチェック
        if not self._contains_emotion_words(preview_text):
            suggestions.append("感情表現を含めると、より魅力的なプレビューになります")

        return issues, suggestions

    # ヘルパーメソッド群
    def _split_sentences(self, text: str) -> list[str]:
        """文を分割"""
        pattern = re.compile(r"[^。！？!?…]+(?:[。！？!?…]+)?")
        sentences = [s.strip() for s in pattern.findall(text) if s.strip()]
        return sentences

    def _is_dialogue(self, sentence: str) -> bool:
        """会話文かチェック"""
        return "「" in sentence or "」" in sentence

    def _contains_dialogue(self, text: str) -> bool:
        """会話が含まれているかチェック"""
        return "「" in text or "」" in text

    def _contains_action_words(self, text: str) -> bool:
        """アクション語を含むかチェック"""
        return any(word in text for word in self._sentiment_keywords["action"])

    def _contains_emotion_words(self, text: str) -> bool:
        """感情語を含むかチェック"""
        emotion_words = self._sentiment_keywords["positive"] + self._sentiment_keywords["negative"]

        return any(word in text for word in emotion_words)

    def _contains_mystery_elements(self, text: str) -> bool:
        """ミステリー要素を含むかチェック"""
        return any(word in text for word in self._sentiment_keywords["mystery"])

    def _is_descriptive(self, sentence: str) -> bool:
        """描写的な文かチェック"""
        descriptive_patterns = [
            r"[は|が].+[色|音|匂い|感触]",
            r"[は|が].+[美しい|綺麗|暖かい|冷たい|明るい|暗い]",
            r"[風景|景色|空|雲|山|海|森]",
        ]
        return any(re.search(pattern, sentence) for pattern in descriptive_patterns)

    def _has_character_voice(self, sentence: str) -> bool:
        """キャラクターの個性が表れているかチェック"""
        voice_indicators = ["だぜ", "だよね", "ですわ", "である", "なのだ", "じゃ"]
        return any(indicator in sentence for indicator in voice_indicators)

    def _analyze_sentiment_details(
        self, text: str, sentences: list[str] | None = None
    ) -> tuple[str, dict[str, int]]:
        """感情分析の詳細情報を返す"""

        if sentences is None:
            sentences = self._split_sentences(text)

        positive_keywords = self._sentiment_keywords["positive"]
        negative_keywords = self._sentiment_keywords["negative"]

        positive_sentence_count = sum(1 for sentence in sentences if any(word in sentence for word in positive_keywords))
        negative_sentence_count = sum(1 for sentence in sentences if any(word in sentence for word in negative_keywords))
        neutral_sentence_count = max(len(sentences) - positive_sentence_count - negative_sentence_count, 0)

        if positive_sentence_count > negative_sentence_count:
            dominant = "positive"
        elif negative_sentence_count > positive_sentence_count:
            dominant = "negative"
        else:
            dominant = "neutral"

        distribution = {
            "positive": positive_sentence_count,
            "negative": negative_sentence_count,
            "neutral": neutral_sentence_count,
        }

        return dominant, distribution

    def _analyze_sentiment(self, text: str) -> str:
        """感情分析"""
        dominant, _ = self._analyze_sentiment_details(text)
        return dominant

    def _estimate_reading_time(self, text: str) -> int:
        """読書時間を推定(秒)"""
        chars_per_minute = 600  # 日本語の平均読書速度
        return int((len(text) / chars_per_minute) * 60)

    def _check_readability(self, text: str) -> list[str]:
        """読みやすさをチェック"""
        issues = []

        # 長すぎる文のチェック
        sentences = self._split_sentences(text)
        for sentence in sentences:
            if len(sentence) > 100:
                issues.append("長すぎる文があります(100文字以上)")
                break

        # 繰り返し語のチェック
        words = text.split()
        word_count = {}
        for word in words:
            if len(word) > 2:
                word_count[word] = word_count.get(word, 0) + 1

        repeated_words = [word for word, count in word_count.items() if count > 2]
        if repeated_words:
            issues.append("繰り返し表現があります")

        return issues

    def _assess_readability(self, text: str) -> float:
        """読みやすさを評価"""
        score = 1.0

        # 平均文長
        sentences = self._split_sentences(text)
        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            if avg_length > 50:
                score -= 0.3
            elif avg_length < 20:
                score -= 0.1

        # 漢字率
        kanji_count = len(re.findall(r"[一-龯]", text))
        kanji_ratio = kanji_count / len(text) if text else 0
        if kanji_ratio > 0.4:  # 40%以上は読みにくい:
            score -= 0.2

        return max(score, 0.0)

    def _assess_appeal(self, text: str) -> float:
        """魅力度を評価"""
        score = 0.0

        # 感情語の存在
        if self._contains_emotion_words(text):
            score += 0.3

        # アクション語の存在
        if self._contains_action_words(text):
            score += 0.3

        # 会話の存在
        if self._contains_dialogue(text):
            score += 0.2

        # ミステリー要素
        if self._contains_mystery_elements(text):
            score += 0.2

        return min(score, 1.0)


class QualityScoreCalculator:
    """品質スコア計算器

    複数の評価指標を組み合わせて総合スコアを算出。
    各評価指標は独立したメソッドで処理し、可読性と保守性を向上させる。
    """

    # 各評価指標の重み付け
    WEIGHTS: ClassVar[dict[str, float]] = {
        "length": 0.3,  # 長さの適切性
        "diversity": 0.2,  # 文の多様性
        "filters": 0.25,  # コンテンツフィルター適合度
        "readability": 0.15,  # 読みやすさ
        "appeal": 0.1,  # 魅力度
    }

    def __init__(self, preview_text: str, config: PreviewConfiguration) -> None:
        self.preview_text = preview_text
        self.config = config
        self.service = None  # サービスの参照を保持(必要に応じて設定)

    def set_service(self, service: EpisodePreviewGenerationService) -> None:
        """サービスインスタンスを設定"""
        self.service = service

    def calculate_total_score(self) -> float:
        """総合スコアを計算"""
        scores = {
            "length": self._calculate_length_score(),
            "diversity": self._calculate_diversity_score(),
            "filters": self._calculate_filter_score(),
            "readability": self._calculate_readability_score(),
            "appeal": self._calculate_appeal_score(),
        }

        total_score = sum(scores[metric] * self.WEIGHTS[metric] for metric in scores)

        return min(total_score, 1.0)

    def _calculate_length_score(self) -> float:
        """長さの適切性スコアを計算"""
        length_ratio = len(self.preview_text) / self.config.max_length

        if 0.5 <= length_ratio <= 1.0:
            return 1.0  # 最適な長さ
        if length_ratio > 0.3:
            return 0.5  # やや短いが許容範囲
        return 0.0  # 短すぎる

    def _calculate_diversity_score(self) -> float:
        """文の多様性スコアを計算"""
        if not self.service:
            return 0.0

        sentences = self.service._split_sentences(self.preview_text)

        if len(sentences) >= self.config.sentence_count:
            return 1.0  # 目標数以上
        if len(sentences) >= 2:
            return 0.5  # 最低限の多様性
        return 0.0  # 単一文のみ

    def _calculate_filter_score(self) -> float:
        """コンテンツフィルター適合度スコアを計算"""
        if not self.config.content_filters or not self.service:
            return 0.0

        matching_filters = 0
        for content_filter in self.config.content_filters:
            if self._matches_content_filter(content_filter):
                matching_filters += 1

        return matching_filters / len(self.config.content_filters)

    def _matches_content_filter(self, content_filter: ContentFilter) -> bool:
        """コンテンツフィルターにマッチするか判定"""
        filter_mapping = {
            ContentFilter.DIALOGUE: self.service._contains_dialogue,
            ContentFilter.ACTION: self.service._contains_action_words,
            ContentFilter.EMOTION: self.service._contains_emotion_words,
            ContentFilter.DESCRIPTION: self.service._is_descriptive,
        }

        checker = filter_mapping.get(content_filter)
        return checker(self.preview_text) if checker else False

    def _calculate_readability_score(self) -> float:
        """読みやすさスコアを計算"""
        if not self.service:
            return 0.0
        return self.service._assess_readability(self.preview_text)

    def _calculate_appeal_score(self) -> float:
        """魅力度スコアを計算"""
        if not self.service:
            return 0.0
        return self.service._assess_appeal(self.preview_text)
