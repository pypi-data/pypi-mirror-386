"""
Unit tests for ErrorClassificationService

Tests the pure domain logic for error classification without external dependencies.


仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest

from noveler.domain.services.error_classification_service import (
    ErrorCategory,
    ErrorClassificationService,
    ErrorSeverity,
)


class TestErrorClassificationService:
    """Test ErrorClassificationService domain logic"""

    def setup_method(self):
        """Setup test fixture"""
        self.service = ErrorClassificationService()

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_classify_validation_errors(self):
        """Test classification of validation errors"""
        # Test ValueError
        error = ValueError("Invalid input")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.VALIDATION

        # Test AssertionError
        error = AssertionError("Assertion failed")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.VALIDATION

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_classify_infrastructure_errors(self):
        """Test classification of infrastructure errors"""
        # Test FileNotFoundError
        error = FileNotFoundError("File not found")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.INFRASTRUCTURE

        # Test PermissionError
        error = PermissionError("Permission denied")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.INFRASTRUCTURE

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_classify_external_service_errors(self):
        """Test classification of external service errors"""
        # Test ConnectionError
        error = ConnectionError("Connection failed")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.EXTERNAL_SERVICE

        # Test TimeoutError
        error = TimeoutError("Request timeout")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.EXTERNAL_SERVICE

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_classify_business_logic_errors(self):
        """Test classification of business logic errors"""

        # Create mock domain exception
        class DomainError(Exception):
            def __init__(self, message) -> None:
                super().__init__(message)
                self.__module__ = "noveler.domain.entities.episode"

        error = DomainError("Business rule violation")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.BUSINESS_LOGIC

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_classify_system_errors(self):
        """Test classification of system errors"""
        # Test unknown error type
        error = RuntimeError("Unknown runtime error")
        category = self.service.classify_error(error)
        assert category == ErrorCategory.SYSTEM

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_determine_severity_by_category(self):
        """Test severity determination based on category"""
        # Test different error types that map to different categories
        validation_error = ValueError("Test validation error")
        severity = self.service.determine_severity(validation_error)
        assert severity == ErrorSeverity.MEDIUM

        # Business logic errors are determined by exception's module
        # Create a mock exception with domain module
        class DomainError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.__module__ = "noveler.domain.services.something"

        business_error = DomainError("Test business error")
        severity = self.service.determine_severity(business_error)
        assert severity == ErrorSeverity.HIGH

        # System errors - unexpected types
        system_error = RuntimeError("Test system error")
        severity = self.service.determine_severity(system_error)
        assert severity == ErrorSeverity.CRITICAL

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_determine_severity_critical_exceptions(self):
        """Test severity override for critical exceptions"""
        # Test KeyboardInterrupt
        error = KeyboardInterrupt()
        severity = self.service.determine_severity(error)
        assert severity == ErrorSeverity.CRITICAL

        # Test SystemExit
        error = SystemExit()
        severity = self.service.determine_severity(error)
        assert severity == ErrorSeverity.CRITICAL

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_determine_severity_high_impact_exceptions(self):
        """Test severity override for high impact exceptions"""
        # Test FileNotFoundError
        error = FileNotFoundError("File missing")
        severity = self.service.determine_severity(error)
        assert severity == ErrorSeverity.HIGH

        # Test ImportError
        error = ImportError("Module not found")
        severity = self.service.determine_severity(error)
        assert severity == ErrorSeverity.HIGH

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_is_recoverable_error(self):
        """Test recoverability assessment"""
        # Test non-recoverable critical errors
        error = KeyboardInterrupt()
        severity = self.service.determine_severity(error)
        recoverable = self.service.is_recoverable_error(severity)
        assert not recoverable

        error = SystemExit()
        severity = self.service.determine_severity(error)
        recoverable = self.service.is_recoverable_error(severity)
        assert not recoverable

        # Test recoverable errors
        error = ValueError("Invalid input")
        severity = self.service.determine_severity(error)
        recoverable = self.service.is_recoverable_error(severity)
        assert recoverable

        error = ConnectionError("Network issue")
        severity = self.service.determine_severity(error)
        recoverable = self.service.is_recoverable_error(severity)
        assert recoverable

        # Test business logic errors - RuntimeError classified as SYSTEM -> CRITICAL -> not recoverable
        error = RuntimeError("Business rule error")
        severity = self.service.determine_severity(error)
        recoverable = self.service.is_recoverable_error(severity)
        assert not recoverable

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_get_business_context(self):
        """Test business context generation"""
        error = FileNotFoundError("test.txt not found")
        category = ErrorCategory.INFRASTRUCTURE

        context = self.service.get_business_context(error, category)

        assert context["exception_type"] == "FileNotFoundError"
        assert context["category"] == "infrastructure"
        assert "business_impact" in context
        assert context["resource_type"] == "file_system"
        assert context["user_action_required"] == "verify_file_path"

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_get_business_context_import_error(self):
        """Test business context for import errors"""
        error = ImportError("Module 'missing' not found")
        category = ErrorCategory.INFRASTRUCTURE

        context = self.service.get_business_context(error, category)

        assert context["resource_type"] == "python_module"
        assert context["user_action_required"] == "install_dependencies"

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_business_impact_descriptions(self):
        """Test business impact descriptions"""
        service = ErrorClassificationService()

        # Test all categories have descriptions
        for category in ErrorCategory:
            description = service._get_business_impact_description(category)
            assert isinstance(description, str)
            assert len(description) > 0

        # Test specific descriptions
        description = service._get_business_impact_description(ErrorCategory.SYSTEM)
        assert "critical" in description.lower() or "system" in description.lower()

        description = service._get_business_impact_description(ErrorCategory.VALIDATION)
        assert "user" in description.lower() or "input" in description.lower()


@pytest.mark.integration
class TestErrorClassificationServiceIntegration:
    """Integration tests for ErrorClassificationService"""

    @pytest.mark.spec("SPEC-DOMAIN-SERVICES")
    def test_full_classification_workflow(self):
        """Test complete classification workflow"""
        service = ErrorClassificationService()

        # Test complete workflow with various errors
        test_cases = [
            (ValueError("Invalid data"), ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, True),
            (FileNotFoundError("Missing file"), ErrorCategory.INFRASTRUCTURE, ErrorSeverity.HIGH, True),
            (ConnectionError("Network down"), ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM, True),
            (KeyboardInterrupt(), ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL, False),
        ]

        for error, expected_category, expected_severity, expected_recoverable in test_cases:
            # Test classification
            category = service.classify_error(error)
            assert category == expected_category

            # Test severity determination
            severity = service.determine_severity(error)
            assert severity == expected_severity

            # Test recoverability
            recoverable = service.is_recoverable_error(severity)
            assert recoverable == expected_recoverable

            # Test business context
            context = service.get_business_context(error, category)
            assert context["category"] == category.value
            assert isinstance(context["business_impact"], str)
