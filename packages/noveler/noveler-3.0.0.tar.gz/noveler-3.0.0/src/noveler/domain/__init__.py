# domain/__init__.py
"""Expose domain-layer primitives for narrative depth evaluation."""

from noveler.domain.repositories.narrative_repositories import (
    EpisodeTextRepository,
    EvaluationResultRepository,
    PlotDataRepository,
)
from noveler.domain.services.narrative_depth_services import NarrativeDepthAnalyzer, ViewpointAwareEvaluator
from noveler.domain.value_objects.narrative_depth_models import (
    DepthLayer,
    DepthPattern,
    LayerScore,
    NarrativeDepthScore,
    TextSegment,
)

__all__ = [
    "DepthLayer",
    "DepthPattern",
    "EpisodeTextRepository",
    "EvaluationResultRepository",
    "LayerScore",
    "NarrativeDepthAnalyzer",
    "NarrativeDepthScore",
    "PlotDataRepository",
    "TextSegment",
    "ViewpointAwareEvaluator",
]

import sys as _sys

_sys.modules.setdefault("domain", _sys.modules[__name__])
