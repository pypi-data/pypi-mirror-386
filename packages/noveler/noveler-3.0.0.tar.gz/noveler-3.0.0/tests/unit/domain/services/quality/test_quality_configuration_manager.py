# File: tests/unit/domain/services/quality/test_quality_configuration_manager.py
# Purpose: Test QualityConfigurationManager - TDD RED phase
# Context: B20-compliant test-first implementation for configuration management

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# These imports will fail initially (RED phase)
from src.noveler.domain.services.quality.core.quality_configuration_manager import (
    QualityConfigurationManager
)
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityStandards,
    QualityThreshold,
    QualityConfiguration
)


class TestQualityConfigurationManager:
    """Test suite for quality configuration management"""

    def setup_method(self):
        """Setup test dependencies"""
        self.config_manager = QualityConfigurationManager()

    @pytest.mark.spec("SPEC-QUALITY-CONFIG-001")
    def test_configuration_manager_exists(self):
        """Verify QualityConfigurationManager exists"""
        assert self.config_manager is not None
        assert hasattr(self.config_manager, 'get_configuration')
        assert hasattr(self.config_manager, 'set_configuration')

    @pytest.mark.spec("SPEC-QUALITY-CONFIG-002")
    def test_get_default_configuration(self):
        """Test retrieval of default configuration"""
        config = self.config_manager.get_configuration()

        assert isinstance(config, QualityConfiguration)
        assert config.name == 'default'
        assert config.standards.name == 'なろう小説'
        assert len(config.thresholds) > 0
        assert 'rhythm' in config.enabled_checks

    @pytest.mark.spec("SPEC-QUALITY-CONFIG-003")
    def test_set_custom_configuration(self):
        """Test setting custom configuration"""
        custom_config = QualityConfiguration(
            name='custom',
            standards=QualityStandards(
                name='Custom Standard',
                description='Custom test standard',
                target_score=85
            ),
            thresholds=[],
            enabled_checks=['rhythm']
        )

        self.config_manager.set_configuration('custom', custom_config)
        retrieved = self.config_manager.get_configuration('custom')

        assert retrieved.name == 'custom'
        assert retrieved.standards.target_score == 85

    @pytest.mark.spec("SPEC-QUALITY-CONFIG-004")
    def test_get_thresholds(self):
        """Test retrieval of thresholds for specific aspect"""
        thresholds = self.config_manager.get_thresholds('rhythm')

        assert isinstance(thresholds, dict)
        assert 'long_sentence_threshold' in thresholds
        assert thresholds['long_sentence_threshold'] == 45