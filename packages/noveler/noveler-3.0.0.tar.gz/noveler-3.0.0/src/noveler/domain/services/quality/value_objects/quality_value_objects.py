# File: src/noveler/domain/services/quality/value_objects/quality_value_objects.py
# Purpose: Value objects for unified quality service
# Context: Pure data structures with no service dependencies (DDD principle)

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class QualityAspect(Enum):
    """Quality check aspects"""
    RHYTHM = "rhythm"
    READABILITY = "readability"
    GRAMMAR = "grammar"
    STYLE = "style"


class IssueSeverity(Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class QualityCheckRequest:
    """Request for quality check"""
    text: str
    episode_number: int
    check_types: List[str]
    weights: Optional[Dict[str, float]] = None
    threshold: Optional[float] = None
    preset: str = "narou"

    def __post_init__(self):
        """Validate request parameters"""
        if not self.text:
            object.__setattr__(self, 'text', '')
        if not self.check_types:
            raise ValueError("At least one check type must be specified")


@dataclass
class QualityIssue:
    """Single quality issue"""
    aspect: str
    severity: IssueSeverity
    line_number: Optional[int]
    description: str
    suggestion: Optional[str] = None
    reason_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'aspect': self.aspect,
            'severity': self.severity.value,
            'line_number': self.line_number,
            'description': self.description,
            'suggestion': self.suggestion,
            'reason_code': self.reason_code
        }


@dataclass
class QualityScore:
    """Quality score for an aspect"""
    aspect: str
    score: float
    max_score: float = 100.0

    def __post_init__(self):
        """Validate score"""
        if self.score < 0:
            self.score = 0
        if self.score > self.max_score:
            self.score = self.max_score

    @property
    def percentage(self) -> float:
        """Get score as percentage"""
        return (self.score / self.max_score) * 100


@dataclass
class QualityCheckResult:
    """Result of quality check"""
    total_score: float
    aspect_scores: Dict[str, float]
    issues: List[QualityIssue]
    check_types: List[str]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Ensure total score is in valid range"""
        if self.total_score < 0:
            self.total_score = 0
        if self.total_score > 100:
            self.total_score = 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'total_score': self.total_score,
            'aspect_scores': self.aspect_scores,
            'issues': [issue.to_dict() for issue in self.issues],
            'check_types': self.check_types,
            'metadata': self.metadata or {}
        }

    @property
    def passed(self) -> bool:
        """Check if quality check passed (score >= 80)"""
        return self.total_score >= 80
    
    @property
    def overall_score(self) -> float:
        """Alias for total_score for backward compatibility"""
        return self.total_score


@dataclass
class QualityThreshold:
    """Quality threshold configuration"""
    aspect: str
    values: Dict[str, Any]
    min_score: float = 60
    warning_score: float = 80

    def __post_init__(self):
        """Validate thresholds"""
        if self.min_score < 0 or self.min_score > 100:
            raise ValueError("min_score must be between 0 and 100")
        if self.warning_score < self.min_score:
            raise ValueError("warning_score must be >= min_score")


@dataclass
class QualityStandards:
    """Quality standards for checks"""
    name: str
    description: str
    target_score: float = 80.0
    preset: str = 'default'
    rhythm_threshold: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(60, 80)
    )
    readability_threshold: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(60, 80)
    )
    grammar_threshold: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(70, 85)
    )
    style_threshold: QualityThreshold = field(
        default_factory=lambda: QualityThreshold(60, 80)
    )

    def get_threshold(self, aspect: str) -> QualityThreshold:
        """Get threshold for specific aspect"""
        threshold_map = {
            'rhythm': self.rhythm_threshold,
            'readability': self.readability_threshold,
            'grammar': self.grammar_threshold,
            'style': self.style_threshold
        }
        return threshold_map.get(aspect, QualityThreshold(60, 80))


@dataclass
class QualityConfiguration:
    """Quality check configuration"""
    name: str
    standards: QualityStandards
    thresholds: List[QualityThreshold]
    enabled_checks: List[str]
    preset: str = 'default'
    weights: Optional[Dict[str, float]] = None
    version: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            'name': self.name,
            'preset': self.preset,
            'thresholds': [
                {
                    'aspect': t.aspect,
                    'values': t.values,
                    'min': t.min_score,
                    'warning': t.warning_score
                }
                for t in self.thresholds
            ],
            'weights': self.weights,
            'version': self.version,
            'enabled_checks': self.enabled_checks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityConfiguration':
        """Create from dictionary"""
        thresholds = [
            QualityThreshold(
                aspect=t['aspect'],
                values=t.get('values', {}),
                min_score=t.get('min', 60),
                warning_score=t.get('warning', 80)
            )
            for t in data.get('thresholds', [])
        ]
        
        # Create standards from data
        standards = QualityStandards(
            name=data.get('name', 'default'),
            description=data.get('description', ''),
            target_score=data.get('target_score', 80)
        )
        
        return cls(
            name=data.get('name', 'default'),
            standards=standards,
            thresholds=thresholds,
            enabled_checks=data.get('enabled_checks', []),
            preset=data.get('preset', 'default'),
            weights=data.get('weights'),
            version=data.get('version', 2)
        )