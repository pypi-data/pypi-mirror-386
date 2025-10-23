#!/usr/bin/env python3
"""
Content Quality Service - Pure Domain Service

Responsible for basic content quality evaluation including word count,
text structure, and expression analysis.
"""

from typing import Any

from noveler.domain.value_objects.quality_types import QualityIssue, QualityScore, QualitySeverity


class ContentQualityService:
    """
    Domain service for basic content quality evaluation

    Responsibilities:
    - Word count analysis and validation
    - Text structure evaluation
    - Expression quality assessment
    - Basic readability checks
    """

    def __init__(self) -> None:
        """Initialize content quality service"""
        self._quality_rules = self._load_default_rules()

    def evaluate_word_count(self, content: str) -> QualityScore:
        """Evaluate content word count quality

        Args:
            content: Content to analyze

        Returns:
            QualityScore: Word count quality assessment
        """
        word_count = len(content)
        issues = []

        if word_count < self._quality_rules["word_count_min"]:
            issues.append(
                QualityIssue(
                    type="word_count",
                    severity=QualitySeverity.WARNING,
                    message=f"Word count insufficient: {word_count} characters",
                    suggestion=f"Target word count is {self._quality_rules['word_count_target']} characters or more",
                )
            )
            score = 30.0
        elif word_count < 2000:
            score = 70.0
        elif word_count < 3000:
            score = 85.0
        else:
            score = 100.0

        return QualityScore(category="Word Count", score=score, max_score=100.0, percentage=score, issues=issues)

    def evaluate_text_structure(self, content: str) -> QualityScore:
        """Evaluate text structure quality

        Args:
            content: Content to analyze

        Returns:
            QualityScore: Text structure quality assessment
        """
        issues = []
        score = 80.0  # Base score

        # Paragraph analysis
        paragraphs = content.split("\n\n")
        if len(paragraphs) < self._quality_rules["paragraph_min"]:
            issues.append(
                QualityIssue(
                    type="structure",
                    severity=QualitySeverity.INFO,
                    message="Paragraph count may be insufficient",
                    suggestion="Consider appropriate paragraph breaks based on content",
                )
            )
            score -= 10

        # Dialogue presence check
        if self._quality_rules["dialogue_required"] and "「" not in content:
            issues.append(
                QualityIssue(
                    type="structure",
                    severity=QualitySeverity.INFO,
                    message="No dialogue found in content",
                    suggestion="Including dialogue can improve readability and engagement",
                )
            )
            score -= 5

        return QualityScore(
            category="Text Structure", score=max(score, 0), max_score=100.0, percentage=max(score, 0), issues=issues
        )

    def evaluate_expression_quality(self, content: str) -> QualityScore:
        """Evaluate expression quality and variety

        Args:
            content: Content to analyze

        Returns:
            QualityScore: Expression quality assessment
        """
        issues = []
        score = 75.0  # Base score

        # Repetition analysis
        words = content.split()
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Exclude short words:
                word_freq[word] = word_freq.get(word, 0) + 1

        repeated_words = [word for word, freq in word_freq.items() if freq > 5]
        if repeated_words:
            issues.append(
                QualityIssue(
                    type="expression",
                    severity=QualitySeverity.WARNING,
                    message=f"Repeated expressions found: {', '.join(repeated_words[:3])}",
                    suggestion="Consider increasing expression variety",
                )
            )
            score -= 10

        # Sentence variety check
        sentences = content.split("。")
        if len(sentences) > 1:
            sentence_lengths = [len(sentence) for sentence in sentences if sentence.strip()]
            if sentence_lengths:
                avg_length = sum(sentence_lengths) / len(sentence_lengths)
                if avg_length < 15:
                    issues.append(
                        QualityIssue(
                            type="expression",
                            severity=QualitySeverity.INFO,
                            message="Sentence length variety could be improved",
                            suggestion="Mix short and long sentences for better flow",
                        )
                    )
                    score -= 5

        return QualityScore(
            category="Expression Quality", score=max(score, 0), max_score=100.0, percentage=max(score, 0), issues=issues
        )

    def evaluate_content_comprehensively(self, content: str, context: dict[str, Any] | None = None) -> list[QualityScore]:
        """Perform comprehensive content quality evaluation

        Args:
            content: Content to analyze
            context: Additional context for evaluation

        Returns:
            list[QualityScore]: List of quality scores for different aspects
        """
        scores = []

        # Basic content quality checks
        scores.append(self.evaluate_word_count(content))
        scores.append(self.evaluate_text_structure(content))
        scores.append(self.evaluate_expression_quality(content))

        # Additional context-based checks if provided
        if context:
            scores.extend(self._evaluate_contextual_quality(content, context))

        return scores

    def _evaluate_contextual_quality(self, content: str, context: dict[str, Any]) -> list[QualityScore]:
        """Evaluate quality based on specific context

        Args:
            content: Content to analyze
            context: Context information

        Returns:
            list[QualityScore]: Context-specific quality scores
        """
        scores = []

        # Genre-specific checks
        if context.get("genre"):
            genre_score = self._evaluate_genre_appropriateness(content, context["genre"])
            scores.append(genre_score)

        # Episode-specific checks
        if context.get("episode_number"):
            episode_score = self._evaluate_episode_consistency(content, context)
            scores.append(episode_score)

        return scores

    def _evaluate_genre_appropriateness(self, content: str, genre: str) -> QualityScore:
        """Evaluate genre appropriateness

        Args:
            content: Content to analyze
            genre: Target genre

        Returns:
            QualityScore: Genre appropriateness score
        """
        # Simplified implementation
        return QualityScore(category="Genre Appropriateness", score=80.0, max_score=100.0, percentage=80.0, issues=[])

    def _evaluate_episode_consistency(self, content: str, context: dict[str, Any]) -> QualityScore:
        """Evaluate consistency with episode context

        Args:
            content: Content to analyze
            context: Episode context

        Returns:
            QualityScore: Episode consistency score
        """
        # Simplified implementation
        return QualityScore(category="Episode Consistency", score=85.0, max_score=100.0, percentage=85.0, issues=[])

    def _load_default_rules(self) -> dict[str, Any]:
        """Load default quality rules

        Returns:
            Dict[str, Any]: Default quality rules
        """
        return {
            "word_count_min": 1000,
            "word_count_target": 3000,
            "paragraph_min": 3,
            "dialogue_required": True,
            "max_repetition_threshold": 5,
            "min_sentence_variety": 15,
        }

    def update_quality_rules(self, new_rules: dict[str, Any]) -> None:
        """Update quality evaluation rules

        Args:
            new_rules: New rules to apply
        """
        self._quality_rules.update(new_rules)

    def get_quality_rules(self) -> dict[str, Any]:
        """Get current quality rules

        Returns:
            Dict[str, Any]: Current quality rules
        """
        return self._quality_rules.copy()
