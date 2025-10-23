# File: src/noveler/domain/services/quality/core/quality_configuration_manager.py
# Purpose: Manage quality check configuration and thresholds
# Context: Centralized configuration for all quality aspects

from typing import Dict, List, Optional
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityConfiguration,
    QualityStandards,
    QualityThreshold
)


class QualityConfigurationManager:
    """Manage quality check configuration"""

    def __init__(self):
        """Initialize with default configuration"""
        self._configurations = {}
        self._default_config = self._create_default_config()

    def get_configuration(self, config_name: str = 'default') -> QualityConfiguration:
        """Get configuration by name"""
        if config_name in self._configurations:
            return self._configurations[config_name]
        return self._default_config

    def set_configuration(self, config_name: str, config: QualityConfiguration):
        """Set a named configuration"""
        self._configurations[config_name] = config

    def get_thresholds(self, aspect: str, config_name: str = 'default') -> Dict[str, float]:
        """Get thresholds for a specific aspect"""
        config = self.get_configuration(config_name)
        for threshold in config.thresholds:
            if threshold.aspect == aspect:
                return threshold.values
        return {}

    def _create_default_config(self) -> QualityConfiguration:
        """Create default configuration"""
        return QualityConfiguration(
            name='default',
            standards=QualityStandards(
                name='なろう小説',
                description='Web小説投稿サイト向け標準',
                target_score=80
            ),
            thresholds=[
                QualityThreshold(
                    aspect='rhythm',
                    values={
                        'long_sentence_threshold': 45,
                        'short_sentence_threshold': 10,
                        'dialogue_ratio_min': 0.25,
                        'dialogue_ratio_max': 0.75
                    }
                ),
                QualityThreshold(
                    aspect='readability',
                    values={
                        'max_sentence_length': 45,
                        'min_sentence_length': 10
                    }
                ),
                QualityThreshold(
                    aspect='grammar',
                    values={
                        'max_commas': 3,
                        'max_consecutive_punctuation': 1
                    }
                ),
                QualityThreshold(
                    aspect='style',
                    values={
                        'max_consecutive_empty_lines': 2,
                        'allow_tabs': False
                    }
                )
            ],
            enabled_checks=['rhythm', 'readability', 'grammar', 'style']
        )