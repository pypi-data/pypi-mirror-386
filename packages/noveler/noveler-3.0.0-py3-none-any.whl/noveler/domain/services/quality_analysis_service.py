#!/usr/bin/env python3
"""
Quality Analysis Service - Pure Domain Service

Responsible for advanced quality analysis including character consistency,
foreshadowing analysis, narrative depth, and adaptive quality checking.
"""

from typing import Any

from noveler.domain.value_objects.quality_types import (
    QualityIssue,
    QualityScore,
    QualitySeverity,
)


class QualityAnalysisService:
    """
    Domain service for advanced quality analysis

    Responsibilities:
    - Character consistency analysis
    - Foreshadowing quality evaluation
    - Narrative depth assessment
    - Adaptive quality pattern learning
    - Viewpoint-aware analysis
    """

    def __init__(self) -> None:
        """Initialize quality analysis service"""
        self._analysis_patterns = {}
        self._character_tracking = {}
        self._foreshadowing_database = {}

    def analyze_character_consistency(
        self, content: str, project_name: str, episode_number: int | None = None
    ) -> QualityScore:
        """Analyze character consistency within content

        Args:
            content: Content to analyze
            project_name: Project identifier
            episode_number: Episode number for context

        Returns:
            QualityScore: Character consistency assessment
        """
        issues = []
        score = 85.0  # Base score for character consistency

        # Extract character references
        character_mentions = self._extract_character_mentions(content)

        # Check consistency with previous episodes
        if project_name in self._character_tracking:
            consistency_issues = self._check_character_consistency(
                character_mentions, self._character_tracking[project_name]
            )

            if consistency_issues:
                issues.extend(consistency_issues)
                score -= len(consistency_issues) * 5

        # Update character tracking
        self._update_character_tracking(project_name, character_mentions)

        return QualityScore(
            category="Character Consistency",
            score=max(score, 0),
            max_score=100.0,
            percentage=max(score, 0),
            issues=issues,
        )

    def analyze_foreshadowing_quality(
        self, content: str, project_name: str, episode_number: int | None = None
    ) -> QualityScore:
        """Analyze foreshadowing elements and their effectiveness

        Args:
            content: Content to analyze
            project_name: Project identifier
            episode_number: Episode number for context

        Returns:
            QualityScore: Foreshadowing quality assessment
        """
        issues = []
        score = 75.0  # Base score for foreshadowing

        # Detect potential foreshadowing elements
        foreshadowing_elements = self._detect_foreshadowing_elements(content)

        # Evaluate foreshadowing effectiveness
        if foreshadowing_elements:
            effectiveness_score = self._evaluate_foreshadowing_effectiveness(
                foreshadowing_elements, project_name, episode_number
            )

            score = (score + effectiveness_score) / 2
        # No foreshadowing detected
        elif episode_number and episode_number > 1:
            issues.append(
                QualityIssue(
                    type="foreshadowing",
                    severity=QualitySeverity.INFO,
                    message="No foreshadowing elements detected",
                    suggestion="Consider adding subtle hints for future plot developments",
                )
            )
            score -= 10

        # Update foreshadowing database
        self._update_foreshadowing_database(project_name, episode_number, foreshadowing_elements)

        return QualityScore(
            category="Foreshadowing Quality",
            score=max(score, 0),
            max_score=100.0,
            percentage=max(score, 0),
            issues=issues,
        )

    def analyze_narrative_depth(self, content: str) -> QualityScore:
        """Analyze narrative depth and complexity

        Args:
            content: Content to analyze

        Returns:
            QualityScore: Narrative depth assessment
        """
        issues = []
        score = 80.0  # Base score for narrative depth

        # Internal monologue analysis
        internal_thoughts = self._analyze_internal_thoughts(content)
        if internal_thoughts < 0.1:  # Less than 10% internal thoughts:
            issues.append(
                QualityIssue(
                    type="narrative_depth",
                    severity=QualitySeverity.INFO,
                    message="Limited internal character development",
                    suggestion="Consider adding more character introspection and internal thoughts",
                )
            )
            score -= 15

        # Emotional depth analysis
        emotional_indicators = self._analyze_emotional_depth(content)
        if emotional_indicators < 0.2:  # Less than 20% emotional content:
            issues.append(
                QualityIssue(
                    type="narrative_depth",
                    severity=QualitySeverity.WARNING,
                    message="Limited emotional depth in narrative",
                    suggestion="Enhance emotional expression and character feelings",
                )
            )
            score -= 10

        # Sensory description analysis
        sensory_richness = self._analyze_sensory_descriptions(content)
        if sensory_richness < 0.15:  # Less than 15% sensory descriptions:
            issues.append(
                QualityIssue(
                    type="narrative_depth",
                    severity=QualitySeverity.INFO,
                    message="Limited sensory descriptions",
                    suggestion="Add more descriptive elements using the five senses",
                )
            )
            score -= 5

        return QualityScore(
            category="Narrative Depth", score=max(score, 0), max_score=100.0, percentage=max(score, 0), issues=issues
        )

    def perform_adaptive_analysis(
        self,
        content: str,
        project_name: str,
        episode_number: int | None = None,
        learning_context: dict[str, Any] | None = None,
    ) -> QualityScore:
        """Perform adaptive quality analysis based on learning patterns

        Args:
            content: Content to analyze
            project_name: Project identifier
            episode_number: Episode number for context
            learning_context: Additional learning context

        Returns:
            QualityScore: Adaptive analysis assessment
        """
        issues = []
        score = 85.0  # Base score for adaptive analysis

        # Retrieve learning patterns for this project
        patterns = self._get_project_patterns(project_name)

        # Apply learned patterns to analysis
        if patterns:
            pattern_compliance = self._evaluate_pattern_compliance(content, patterns)
            score = (score + pattern_compliance) / 2

            # Generate pattern-specific issues
            pattern_issues = self._generate_pattern_issues(content, patterns)
            issues.extend(pattern_issues)

        # Update learning patterns
        self._update_learning_patterns(project_name, content, episode_number)

        return QualityScore(
            category="Adaptive Analysis", score=max(score, 0), max_score=100.0, percentage=max(score, 0), issues=issues
        )

    def perform_viewpoint_analysis(self, content: str, viewpoint_info: dict[str, Any]) -> QualityScore:
        """Perform viewpoint-aware quality analysis

        Args:
            content: Content to analyze
            viewpoint_info: Viewpoint configuration

        Returns:
            QualityScore: Viewpoint analysis assessment
        """
        issues = []
        score = 80.0  # Base score for viewpoint analysis

        viewpoint_type = viewpoint_info.get("type", "single")
        viewpoint_character = viewpoint_info.get("character", "protagonist")

        # Viewpoint consistency check
        consistency_score = self._check_viewpoint_consistency(content, viewpoint_type, viewpoint_character)
        score = (score + consistency_score) / 2

        # Generate viewpoint-specific recommendations
        viewpoint_issues = self._generate_viewpoint_issues(content, viewpoint_info)
        issues.extend(viewpoint_issues)

        return QualityScore(
            category="Viewpoint Analysis", score=max(score, 0), max_score=100.0, percentage=max(score, 0), issues=issues
        )

    def _extract_character_mentions(self, content: str) -> dict[str, int]:
        """Extract character mentions from content

        Args:
            content: Content to analyze

        Returns:
            Dict[str, int]: Character mention counts
        """
        # Simplified implementation - in practice would use NLP
        character_patterns = ["主人公", "ヒロイン", "敵", "友人", "先生"]
        mentions = {}

        for character in character_patterns:
            count = content.count(character)
            if count > 0:
                mentions[character] = count

        return mentions

    def _check_character_consistency(
        self, current_mentions: dict[str, int], historical_data: dict[str, Any]
    ) -> list[QualityIssue]:
        """Check character consistency with historical data

        Args:
            current_mentions: Current character mentions
            historical_data: Historical character data

        Returns:
            list[QualityIssue]: Consistency issues found
        """
        issues = []

        # Simplified consistency check
        for character, count in current_mentions.items():
            if character in historical_data:
                expected_range = historical_data[character].get("expected_frequency", (1, 10))
                if count < expected_range[0] or count > expected_range[1]:
                    issues.append(
                        QualityIssue(
                            type="character_consistency",
                            severity=QualitySeverity.INFO,
                            message=f"Character {character} frequency unusual: {count}",
                            suggestion=f"Consider balancing character presence (expected: {expected_range})",
                        )
                    )

        return issues

    def _update_character_tracking(self, project_name: str, mentions: dict[str, int]) -> None:
        """Update character tracking data

        Args:
            project_name: Project identifier
            mentions: Character mentions to record
        """
        if project_name not in self._character_tracking:
            self._character_tracking[project_name] = {}

        for character, count in mentions.items():
            if character not in self._character_tracking[project_name]:
                self._character_tracking[project_name][character] = {
                    "total_mentions": 0,
                    "episode_count": 0,
                    "expected_frequency": (1, 10),
                }

            char_data: dict[str, Any] = self._character_tracking[project_name][character]
            char_data["total_mentions"] += count
            char_data["episode_count"] += 1

    def _detect_foreshadowing_elements(self, content: str) -> list[dict[str, Any]]:
        """Detect potential foreshadowing elements

        Args:
            content: Content to analyze

        Returns:
            list[Dict[str, Any]]: Detected foreshadowing elements
        """
        # Simplified implementation - would use more sophisticated analysis
        foreshadowing_keywords = ["予感", "不安", "暗示", "兆し", "気配"]
        elements = []

        for keyword in foreshadowing_keywords:
            if keyword in content:
                elements.append(
                    {"type": "keyword", "element": keyword, "context": f"Found foreshadowing keyword: {keyword}"}
                )

        return elements

    def _evaluate_foreshadowing_effectiveness(
        self, elements: list[dict[str, Any]], project_name: str, episode_number: int | None
    ) -> float:
        """Evaluate effectiveness of foreshadowing elements

        Args:
            elements: Foreshadowing elements to evaluate
            project_name: Project identifier
            episode_number: Episode number

        Returns:
            float: Effectiveness score (0-100)
        """
        # Simplified effectiveness calculation
        base_score = 70.0
        element_bonus = min(len(elements) * 5, 20)  # Max 20 bonus points

        return min(base_score + element_bonus, 100.0)

    def _update_foreshadowing_database(
        self, project_name: str, episode_number: int | None, elements: list[dict[str, Any]]
    ) -> None:
        """Update foreshadowing database

        Args:
            project_name: Project identifier
            episode_number: Episode number
            elements: Foreshadowing elements to record
        """
        if project_name not in self._foreshadowing_database:
            self._foreshadowing_database[project_name] = {}

        if episode_number:
            self._foreshadowing_database[project_name][episode_number] = elements

    def _analyze_internal_thoughts(self, content: str) -> float:
        """Analyze presence of internal thoughts and monologue

        Args:
            content: Content to analyze

        Returns:
            float: Ratio of internal thought content (0-1)
        """
        # Simplified analysis - look for thought indicators
        thought_indicators = ["思った", "考えた", "感じた", "心の中で"]
        thought_count = sum(content.count(indicator) for indicator in thought_indicators)

        total_sentences = len(content.split("。"))
        return min(thought_count / max(total_sentences, 1), 1.0)

    def _analyze_emotional_depth(self, content: str) -> float:
        """Analyze emotional depth in content

        Args:
            content: Content to analyze

        Returns:
            float: Ratio of emotional content (0-1)
        """
        # Simplified analysis - look for emotion words
        emotion_words = ["嬉しい", "悲しい", "怒り", "恐怖", "驚き", "愛", "憎しみ"]
        emotion_count = sum(content.count(word) for word in emotion_words)

        total_words = len(content.split())
        return min(emotion_count / max(total_words, 1), 1.0)

    def _analyze_sensory_descriptions(self, content: str) -> float:
        """Analyze richness of sensory descriptions

        Args:
            content: Content to analyze

        Returns:
            float: Ratio of sensory content (0-1)
        """
        # Simplified analysis - look for sensory words
        sensory_words = ["見た", "聞いた", "嗅いだ", "触った", "味わった", "色", "音", "香り"]
        sensory_count = sum(content.count(word) for word in sensory_words)

        total_words = len(content.split())
        return min(sensory_count / max(total_words, 1), 1.0)

    def _get_project_patterns(self, project_name: str) -> dict[str, Any]:
        """Get learned patterns for a project

        Args:
            project_name: Project identifier

        Returns:
            Dict[str, Any]: Learned patterns
        """
        return self._analysis_patterns.get(project_name, {})

    def _evaluate_pattern_compliance(self, content: str, patterns: dict[str, Any]) -> float:
        """Evaluate compliance with learned patterns

        Args:
            content: Content to analyze
            patterns: Learned patterns

        Returns:
            float: Compliance score (0-100)
        """
        # Simplified pattern compliance check
        return 80.0  # Base compliance score

    def _generate_pattern_issues(self, content: str, patterns: dict[str, Any]) -> list[QualityIssue]:
        """Generate issues based on pattern analysis

        Args:
            content: Content to analyze
            patterns: Learned patterns

        Returns:
            list[QualityIssue]: Pattern-based issues
        """
        # Simplified pattern issue generation
        return []

    def _update_learning_patterns(self, project_name: str, content: str, episode_number: int | None) -> None:
        """Update learning patterns based on new content

        Args:
            project_name: Project identifier
            content: Content to learn from
            episode_number: Episode number
        """
        if project_name not in self._analysis_patterns:
            self._analysis_patterns[project_name] = {"writing_style": {}, "common_patterns": [], "quality_trends": []}

    def _check_viewpoint_consistency(self, content: str, viewpoint_type: str, viewpoint_character: str) -> float:
        """Check viewpoint consistency in content

        Args:
            content: Content to analyze
            viewpoint_type: Type of viewpoint (single, multiple, etc.)
            viewpoint_character: Main viewpoint character

        Returns:
            float: Consistency score (0-100)
        """
        # Simplified viewpoint consistency check
        return 85.0

    def _generate_viewpoint_issues(self, content: str, viewpoint_info: dict[str, Any]) -> list[QualityIssue]:
        """Generate viewpoint-specific issues

        Args:
            content: Content to analyze
            viewpoint_info: Viewpoint configuration

        Returns:
            list[QualityIssue]: Viewpoint-related issues
        """
        # Simplified viewpoint issue generation
        return []
