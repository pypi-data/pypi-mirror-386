"""Preview configuration value objects with validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from noveler.domain.exceptions.base import DomainValidationError


class PreviewStyle(Enum):
    """Supported preview styles for episode summaries."""

    SUMMARY = "summary"
    EXCERPT = "excerpt"
    TEASER = "teaser"
    DIALOGUE_FOCUS = "dialogue_focus"


class ContentFilter(Enum):
    """Available content filters used when generating previews."""

    DIALOGUE = "dialogue"
    ACTION = "action"
    EMOTION = "emotion"
    DESCRIPTION = "description"


@dataclass(frozen=True)
class QualityThreshold:
    """Represents quality metrics constraints used during preview generation."""

    metric_name: str
    min_value: float = 0.7
    max_value: float = 1.0
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.metric_name:
            raise DomainValidationError("QualityThreshold", "metric_name", "metric_nameは空にできません", self.metric_name)
        if not 0.0 <= self.min_value <= 1.0:
            raise DomainValidationError(
                "QualityThreshold",
                "min_value",
                "min_valueは0.0から1.0の範囲である必要があります",
                self.min_value,
            )
        if not 0.0 <= self.max_value <= 1.0:
            raise DomainValidationError(
                "QualityThreshold",
                "max_value",
                "max_valueは0.0から1.0の範囲である必要があります",
                self.max_value,
            )
        if self.min_value > self.max_value:
            raise DomainValidationError(
                "QualityThreshold",
                "min_value",
                "min_valueはmax_value以下である必要があります",
                self.min_value,
            )
        if self.weight <= 0:
            raise DomainValidationError(
                "QualityThreshold",
                "weight",
                "weightは正の値である必要があります",
                self.weight,
            )

    def to_dict(self) -> dict[str, float | str]:
        return {
            "metric_name": self.metric_name,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class StyleSettings:
    """Formatting tweaks applied while composing previews."""

    emphasis_marker: str = "**"
    ellipsis: str = "……"
    line_break: str = "\n"
    quote_style: str = "「」"

    def __post_init__(self) -> None:
        if not self.emphasis_marker:
            raise DomainValidationError("StyleSettings", "emphasis_marker", "emphasis_markerは空にできません")
        if not self.ellipsis:
            raise DomainValidationError("StyleSettings", "ellipsis", "ellipsisは空にできません")
        if not self.line_break:
            raise DomainValidationError("StyleSettings", "line_break", "line_breakは空にできません")
        if not self.quote_style:
            raise DomainValidationError("StyleSettings", "quote_style", "quote_styleは空にできません")


@dataclass(frozen=True)
class PreviewConfiguration:
    """Validated configuration bundle for episode previews."""

    max_length: int = 200
    sentence_count: int = 3
    preview_style: PreviewStyle = PreviewStyle.SUMMARY
    content_filters: Sequence[ContentFilter] = field(default_factory=tuple)
    style_settings: StyleSettings = field(default_factory=StyleSettings)
    quality_thresholds: Sequence[QualityThreshold] = field(default_factory=tuple)
    preserve_formatting: bool = False
    include_metadata: bool = True
    description: str | None = None

    def __post_init__(self) -> None:
        if self.max_length <= 0:
            raise DomainValidationError("PreviewConfiguration", "max_length", "max_lengthは正の値である必要があります", self.max_length)
        if self.max_length > 1000:
            raise DomainValidationError("PreviewConfiguration", "max_length", "max_lengthは1000文字以下である必要があります", self.max_length)
        if self.sentence_count <= 0:
            raise DomainValidationError(
                "PreviewConfiguration",
                "sentence_count",
                "sentence_countは正の値である必要があります",
                self.sentence_count,
            )
        if self.sentence_count > 20:
            raise DomainValidationError(
                "PreviewConfiguration",
                "sentence_count",
                "sentence_countは20以下である必要があります",
                self.sentence_count,
            )
        if not isinstance(self.preview_style, PreviewStyle):
            raise DomainValidationError(
                "PreviewConfiguration",
                "preview_style",
                "preview_styleは有効なPreviewStyleである必要があります",
                self.preview_style,
            )

        content_filters = list(self.content_filters)
        for filt in content_filters:
            if not isinstance(filt, ContentFilter):
                raise DomainValidationError(
                    "PreviewConfiguration",
                    "content_filters",
                    "content_filtersは有効なContentFilterのリストである必要があります",
                    filt,
                )

        quality_thresholds = list(self.quality_thresholds)
        for threshold in quality_thresholds:
            if not isinstance(threshold, QualityThreshold):
                raise DomainValidationError(
                    "PreviewConfiguration",
                    "quality_thresholds",
                    "quality_thresholdsは有効なQualityThresholdのリストである必要があります",
                    threshold,
                )

        object.__setattr__(self, "content_filters", list(content_filters))
        object.__setattr__(self, "quality_thresholds", list(quality_thresholds))

    # ---- style helpers -------------------------------------------------
    def is_summary_style(self) -> bool:
        return self.preview_style == PreviewStyle.SUMMARY

    def is_excerpt_style(self) -> bool:
        return self.preview_style == PreviewStyle.EXCERPT

    def is_teaser_style(self) -> bool:
        return self.preview_style == PreviewStyle.TEASER

    def is_dialogue_focus_style(self) -> bool:
        return self.preview_style == PreviewStyle.DIALOGUE_FOCUS

    # ---- filter helpers ------------------------------------------------
    def has_content_filter(self, filt: ContentFilter) -> bool:
        return filt in self.content_filters

    def should_include_dialogue(self) -> bool:
        return self.has_content_filter(ContentFilter.DIALOGUE)

    def should_include_action(self) -> bool:
        return self.has_content_filter(ContentFilter.ACTION)

    def should_include_emotion(self) -> bool:
        return self.has_content_filter(ContentFilter.EMOTION)

    def should_include_description(self) -> bool:
        return self.has_content_filter(ContentFilter.DESCRIPTION)

    # ---- quality helpers -----------------------------------------------
    def get_quality_threshold(self, metric_name: str) -> QualityThreshold | None:
        for threshold in self.quality_thresholds:
            if threshold.metric_name == metric_name:
                return threshold
        return None

    def get_minimum_quality_score(self) -> float:
        if not self.quality_thresholds:
            return 0.7
        numerator = sum(th.min_value * th.weight for th in self.quality_thresholds)
        denominator = sum(th.weight for th in self.quality_thresholds)
        return numerator / denominator if denominator else 0.7

    # ---- serialisation helpers ----------------------------------------
    def to_dict(self) -> dict[str, object]:
        return {
            "max_length": self.max_length,
            "sentence_count": self.sentence_count,
            "preview_style": self.preview_style.value,
            "content_filters": [filt.value for filt in self.content_filters],
            "style_settings": {
                "emphasis_marker": self.style_settings.emphasis_marker,
                "ellipsis": self.style_settings.ellipsis,
                "line_break": self.style_settings.line_break,
                "quote_style": self.style_settings.quote_style,
            },
            "quality_thresholds": [threshold.to_dict() for threshold in self.quality_thresholds],
            "preserve_formatting": self.preserve_formatting,
            "include_metadata": self.include_metadata,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PreviewConfiguration":
        style_dict = data.get("style_settings", {})
        thresholds = [
            QualityThreshold(**threshold_data)  # type: ignore[arg-type]
            for threshold_data in data.get("quality_thresholds", [])
        ]
        filters = [ContentFilter(filter_name) for filter_name in data.get("content_filters", [])]
        preview_style = data.get("preview_style", PreviewStyle.SUMMARY)
        if isinstance(preview_style, str):
            preview_style = PreviewStyle(preview_style)

        return cls(
            max_length=int(data.get("max_length", 200)),
            sentence_count=int(data.get("sentence_count", 3)),
            preview_style=preview_style,  # type: ignore[arg-type]
            content_filters=filters,
            style_settings=StyleSettings(
                emphasis_marker=style_dict.get("emphasis_marker", "**"),
                ellipsis=style_dict.get("ellipsis", "……"),
                line_break=style_dict.get("line_break", "\n"),
                quote_style=style_dict.get("quote_style", "「」"),
            ),
            quality_thresholds=thresholds,
            preserve_formatting=bool(data.get("preserve_formatting", False)),
            include_metadata=bool(data.get("include_metadata", True)),
            description=data.get("description"),
        )

    # ---- factory helpers ----------------------------------------------
    @classmethod
    def create_default(cls) -> "PreviewConfiguration":
        thresholds = (
            QualityThreshold("readability", 0.7, 1.0, 1.0),
            QualityThreshold("engagement", 0.6, 1.0, 1.0),
            QualityThreshold("consistency", 0.65, 1.0, 0.8),
        )
        return cls(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=(ContentFilter.DIALOGUE, ContentFilter.ACTION, ContentFilter.EMOTION),
            quality_thresholds=thresholds,
            preserve_formatting=False,
            include_metadata=True,
        )

    @classmethod
    def create_teaser(cls) -> "PreviewConfiguration":
        return cls(
            max_length=150,
            sentence_count=2,
            preview_style=PreviewStyle.TEASER,
            content_filters=(ContentFilter.DIALOGUE, ContentFilter.ACTION),
            style_settings=StyleSettings(ellipsis="…?", line_break="\n\n", emphasis_marker="**", quote_style="「」"),
            preserve_formatting=True,
            include_metadata=False,
        )

    @classmethod
    def create_dialogue_focus(cls) -> "PreviewConfiguration":
        return cls(
            max_length=250,
            sentence_count=4,
            preview_style=PreviewStyle.DIALOGUE_FOCUS,
            content_filters=(ContentFilter.DIALOGUE, ContentFilter.EMOTION),
            preserve_formatting=True,
            include_metadata=True,
        )
