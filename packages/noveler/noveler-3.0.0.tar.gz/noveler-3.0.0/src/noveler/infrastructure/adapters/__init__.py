"""Infrastructure adapters bridging legacy code with the DDD structure."""

from noveler.infrastructure.adapters.cli_adapter import CLIAdapter

# Legacy adapters completely removed - migrated to modern DDD architecture
from noveler.infrastructure.adapters.yaml_validator_adapter import YAMLValidatorAdapter

__all__ = [
    "CLIAdapter",
    "YAMLValidatorAdapter",
]
