"""Environment 列挙型

SPEC-CONFIGURATION-001準拠
"""

from enum import Enum


class Environment(Enum):
    """実行環境列挙型"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
