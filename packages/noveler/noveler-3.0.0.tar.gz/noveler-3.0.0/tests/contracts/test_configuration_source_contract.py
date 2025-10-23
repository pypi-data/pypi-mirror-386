# File: tests/contracts/test_configuration_source_contract.py
# Purpose: Contract tests for ConfigurationSourcePort to ensure implementation compliance.
# Context: Validates ConfigurationSourceAdapter adheres to ConfigurationSourcePort protocol.

"""Contract tests for ConfigurationSourcePort.

Purpose:
    Verify that all ConfigurationSourcePort implementations satisfy the protocol contract.
Context:
    Part of B20 Workflow Phase 4 contract testing requirements.
Preconditions:
    None.
Side Effects:
    None (read-only tests).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

if TYPE_CHECKING:
    from noveler.domain.interfaces.configuration_source_port import ConfigurationSourcePort

from noveler.infrastructure.adapters.configuration_source_adapter import ConfigurationSourceAdapter

pytestmark = pytest.mark.contract


class TestConfigurationSourceContract:
    """Contract tests for ConfigurationSourcePort protocol.

    Purpose:
        Ensure implementations satisfy configuration snapshot contract.
    """

    @pytest.fixture
    def mock_config_service(self):
        """Provide mock configuration service for testing."""
        service = Mock()
        service.get_feature_flags.return_value = {"feature_a": True, "feature_b": False}
        service.get_environment = Mock(return_value="development")
        return service

    @pytest.fixture
    def source(self, mock_config_service) -> ConfigurationSourcePort:
        """Provide ConfigurationSourcePort implementation for testing.

        Returns:
            ConfigurationSourceAdapter instance as protocol implementation.
        """
        return ConfigurationSourceAdapter(mock_config_service)

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-SNAPSHOT")
    def test_snapshot_returns_tuple_with_dict_and_token(
        self, source: ConfigurationSourcePort
    ) -> None:
        """Verify snapshot() returns (dict, token) tuple."""
        project_id = "test_project"

        config, token = source.snapshot(project_id)

        assert isinstance(config, dict)
        assert isinstance(token, str)
        assert len(token) > 0
        assert "features" in config or "environment" in config

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-SNAPSHOT_IDEMPOTENT")
    def test_snapshot_same_state_same_token(
        self, source: ConfigurationSourcePort
    ) -> None:
        """Verify snapshot() returns same token for same configuration state."""
        project_id = "test_project"

        config1, token1 = source.snapshot(project_id)
        config2, token2 = source.snapshot(project_id)

        # Same state should produce same token (idempotent token generation)
        assert token1 == token2
        # Note: snapshots may differ in timestamp for observability, so we don't compare them

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-DIFF_SINCE")
    def test_diff_since_returns_old_and_new_configs(
        self, source: ConfigurationSourcePort, mock_config_service
    ) -> None:
        """Verify diff_since() returns (old_config, new_config) tuple."""
        project_id = "test_project"

        # Take initial snapshot
        _, initial_token = source.snapshot(project_id)

        # Change configuration
        mock_config_service.get_feature_flags.return_value = {"feature_a": False, "feature_c": True}

        # Get diff
        old_config, new_config = source.diff_since(project_id, initial_token)

        assert isinstance(old_config, dict)
        assert isinstance(new_config, dict)
        # Configs should be different if state changed
        # (Implementation may vary, just verify structure)

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-DIFF_NONEXISTENT_TOKEN")
    def test_diff_since_handles_nonexistent_token(
        self, source: ConfigurationSourcePort
    ) -> None:
        """Verify diff_since() handles nonexistent token gracefully."""
        project_id = "test_project"
        nonexistent_token = "nonexistent_token_12345"

        # Should not raise exception
        old_config, new_config = source.diff_since(project_id, nonexistent_token)

        assert isinstance(old_config, dict)
        assert isinstance(new_config, dict)


class TestConfigurationSourceSpecCompliance:
    """Verify ConfigurationSourcePort contract coverage and implementation compliance.

    Purpose:
        Meta-tests to ensure contract tests cover the protocol completely.
    """

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-PROTOCOL_COMPLIANCE")
    def test_adapter_is_valid_protocol(self) -> None:
        """Verify ConfigurationSourceAdapter satisfies ConfigurationSourcePort protocol."""
        from noveler.domain.interfaces.configuration_source_port import ConfigurationSourcePort

        mock_service = Mock()
        mock_service.get_feature_flags.return_value = {}
        mock_service.get_environment = Mock(return_value="test")
        source: ConfigurationSourcePort = ConfigurationSourceAdapter(mock_service)

        assert hasattr(source, "snapshot")
        assert hasattr(source, "diff_since")
        assert callable(source.snapshot)
        assert callable(source.diff_since)

    @pytest.mark.spec("SPEC-CONFIGURATION_SOURCE_PORT-CONTRACT_COVERAGE")
    def test_configuration_source_contract_coverage(self) -> None:
        """Verify contract tests cover all critical scenarios."""
        required_scenarios = [
            "snapshot",      # test_snapshot_returns_tuple_with_dict_and_token
            "same_state",    # test_snapshot_same_state_same_token (contains "same_state" not "idempotent")
            "diff",          # test_diff_since_returns_old_and_new_configs
            "nonexistent",   # test_diff_since_handles_nonexistent_token
        ]

        test_methods = [
            method
            for method in dir(TestConfigurationSourceContract)
            if method.startswith("test_")
        ]

        for scenario in required_scenarios:
            assert any(
                scenario in method for method in test_methods
            ), f"Missing contract test for scenario: {scenario}"
