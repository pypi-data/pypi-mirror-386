#!/usr/bin/env bash
# File: scripts/create_repository.sh
# Purpose: Generate Repository interface and implementation with proper naming conventions
# Usage: ./scripts/create_repository.sh <technology> <entity>
#        Example: ./scripts/create_repository.sh yaml character

set -euo pipefail

# Input validation
if [ $# -ne 2 ]; then
    echo "Usage: $0 <technology> <entity>"
    echo "Example: $0 yaml character"
    echo ""
    echo "Supported technologies: yaml, file, json, markdown"
    exit 1
fi

TECH=$1
ENTITY=$2
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Capitalize first letter
capitalize() {
    echo "$1" | sed 's/./\U&/'
}

ENTITY_CAPITALIZED=$(capitalize "$ENTITY")
TECH_CAPITALIZED=$(capitalize "$TECH")

# File paths
DOMAIN_INTERFACE="${ROOT_DIR}/src/noveler/domain/repositories/${ENTITY}_repository.py"
INFRA_IMPL="${ROOT_DIR}/src/noveler/infrastructure/repositories/${TECH}_${ENTITY}_repository.py"
DOMAIN_TEST="${ROOT_DIR}/tests/unit/domain/repositories/test_${ENTITY}_repository.py"
INFRA_TEST="${ROOT_DIR}/tests/unit/infrastructure/repositories/test_${TECH}_${ENTITY}_repository.py"

# Check if files already exist
if [ -f "$DOMAIN_INTERFACE" ]; then
    echo "❌ Error: Domain interface already exists: $DOMAIN_INTERFACE"
    exit 1
fi

if [ -f "$INFRA_IMPL" ]; then
    echo "❌ Error: Infrastructure implementation already exists: $INFRA_IMPL"
    exit 1
fi

# Create directories if needed
mkdir -p "$(dirname "$DOMAIN_INTERFACE")"
mkdir -p "$(dirname "$INFRA_IMPL")"
mkdir -p "$(dirname "$DOMAIN_TEST")"
mkdir -p "$(dirname "$INFRA_TEST")"

# Generate Domain interface
cat > "$DOMAIN_INTERFACE" << EOF
# File: src/noveler/domain/repositories/${ENTITY}_repository.py
# Purpose: Repository interface for ${ENTITY_CAPITALIZED} aggregate
# Context: DDD Repository pattern - defines persistence contract

from abc import ABC, abstractmethod
from typing import Optional

from noveler.domain.entities.${ENTITY} import ${ENTITY_CAPITALIZED}


class ${ENTITY_CAPITALIZED}Repository(ABC):
    """${ENTITY_CAPITALIZED}集約の永続化インターフェース

    DDD Repository pattern implementation for ${ENTITY_CAPITALIZED} aggregate.
    Infrastructure layer provides concrete implementations.
    """

    @abstractmethod
    def save(self, ${ENTITY}: ${ENTITY_CAPITALIZED}) -> ${ENTITY_CAPITALIZED}:
        """${ENTITY_CAPITALIZED}を永続化する

        Args:
            ${ENTITY}: 永続化対象の${ENTITY_CAPITALIZED}集約

        Returns:
            永続化後の${ENTITY_CAPITALIZED}集約（IDが付与される）

        Raises:
            RepositoryError: 永続化に失敗した場合
        """
        pass

    @abstractmethod
    def find_by_id(self, ${ENTITY}_id: str) -> Optional[${ENTITY_CAPITALIZED}]:
        """IDで${ENTITY_CAPITALIZED}を検索する

        Args:
            ${ENTITY}_id: 検索対象のID

        Returns:
            見つかった${ENTITY_CAPITALIZED}、存在しない場合はNone

        Raises:
            RepositoryError: 検索処理に失敗した場合
        """
        pass

    @abstractmethod
    def delete(self, ${ENTITY}_id: str) -> bool:
        """${ENTITY_CAPITALIZED}を削除する

        Args:
            ${ENTITY}_id: 削除対象のID

        Returns:
            削除成功時True、対象が存在しない場合False

        Raises:
            RepositoryError: 削除処理に失敗した場合
        """
        pass
EOF

# Generate Infrastructure implementation
cat > "$INFRA_IMPL" << EOF
# File: src/noveler/infrastructure/repositories/${TECH}_${ENTITY}_repository.py
# Purpose: ${TECH_CAPITALIZED}-based implementation of ${ENTITY_CAPITALIZED}Repository
# Context: Concrete repository using ${TECH_CAPITALIZED} for persistence

from pathlib import Path
from typing import Optional

from noveler.domain.entities.${ENTITY} import ${ENTITY_CAPITALIZED}
from noveler.domain.repositories.${ENTITY}_repository import ${ENTITY_CAPITALIZED}Repository
from noveler.infrastructure.exceptions import RepositoryError


class ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository(${ENTITY_CAPITALIZED}Repository):
    """${TECH_CAPITALIZED}形式での${ENTITY_CAPITALIZED}永続化実装

    Implements ${ENTITY_CAPITALIZED}Repository using ${TECH_CAPITALIZED} file format.
    Follows Repository pattern with Infrastructure layer implementation.
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base storage path

        Args:
            base_path: Base directory for ${TECH} file storage
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save(self, ${ENTITY}: ${ENTITY_CAPITALIZED}) -> ${ENTITY_CAPITALIZED}:
        """${ENTITY_CAPITALIZED}を${TECH_CAPITALIZED}形式で永続化する"""
        try:
            # TODO: Implement ${TECH} serialization
            raise NotImplementedError("${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository.save() not implemented")
        except Exception as e:
            raise RepositoryError(f"Failed to save ${ENTITY}: {e}") from e

    def find_by_id(self, ${ENTITY}_id: str) -> Optional[${ENTITY_CAPITALIZED}]:
        """IDで${ENTITY_CAPITALIZED}を検索する"""
        try:
            # TODO: Implement ${TECH} deserialization
            raise NotImplementedError("${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository.find_by_id() not implemented")
        except FileNotFoundError:
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to find ${ENTITY} {${ENTITY}_id}: {e}") from e

    def delete(self, ${ENTITY}_id: str) -> bool:
        """${ENTITY_CAPITALIZED}を削除する"""
        try:
            # TODO: Implement file deletion
            raise NotImplementedError("${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository.delete() not implemented")
        except FileNotFoundError:
            return False
        except Exception as e:
            raise RepositoryError(f"Failed to delete ${ENTITY} {${ENTITY}_id}: {e}") from e
EOF

# Generate Domain test
cat > "$DOMAIN_TEST" << EOF
# File: tests/unit/domain/repositories/test_${ENTITY}_repository.py
# Purpose: Contract tests for ${ENTITY_CAPITALIZED}Repository interface
# Context: Verify Repository pattern contract compliance

import pytest

from noveler.domain.repositories.${ENTITY}_repository import ${ENTITY_CAPITALIZED}Repository


class Test${ENTITY_CAPITALIZED}RepositoryContract:
    """${ENTITY_CAPITALIZED}Repository contract tests

    Verifies that Repository implementations follow DDD Repository pattern.
    """

    def test_interface_definition(self) -> None:
        """Verify interface has required abstract methods"""
        required_methods = ["save", "find_by_id", "delete"]
        for method_name in required_methods:
            assert hasattr(${ENTITY_CAPITALIZED}Repository, method_name)
            method = getattr(${ENTITY_CAPITALIZED}Repository, method_name)
            assert callable(method)
EOF

# Generate Infrastructure test
cat > "$INFRA_TEST" << EOF
# File: tests/unit/infrastructure/repositories/test_${TECH}_${ENTITY}_repository.py
# Purpose: Tests for ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository implementation
# Context: Verify ${TECH_CAPITALIZED}-based persistence behavior

import pytest
from pathlib import Path

from noveler.infrastructure.repositories.${TECH}_${ENTITY}_repository import ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository


@pytest.fixture
def repository(tmp_path: Path) -> ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository:
    """Create repository instance with temporary storage"""
    return ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository(base_path=tmp_path)


class Test${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository:
    """${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository implementation tests"""

    def test_initialization(self, repository: ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository) -> None:
        """Verify repository initializes correctly"""
        assert repository is not None
        assert repository._base_path.exists()

    @pytest.mark.skip(reason="Not implemented yet")
    def test_save(self, repository: ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository) -> None:
        """Verify save operation"""
        # TODO: Implement test after save() is implemented
        pass

    @pytest.mark.skip(reason="Not implemented yet")
    def test_find_by_id(self, repository: ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository) -> None:
        """Verify find_by_id operation"""
        # TODO: Implement test after find_by_id() is implemented
        pass

    @pytest.mark.skip(reason="Not implemented yet")
    def test_delete(self, repository: ${TECH_CAPITALIZED}${ENTITY_CAPITALIZED}Repository) -> None:
        """Verify delete operation"""
        # TODO: Implement test after delete() is implemented
        pass
EOF

echo "✅ Repository files created successfully:"
echo "   Domain interface: $DOMAIN_INTERFACE"
echo "   Infrastructure implementation: $INFRA_IMPL"
echo "   Domain test: $DOMAIN_TEST"
echo "   Infrastructure test: $INFRA_TEST"
echo ""
echo "📝 Next steps:"
echo "   1. Implement Entity class: src/noveler/domain/entities/${ENTITY}.py"
echo "   2. Implement serialization in: $INFRA_IMPL"
echo "   3. Complete tests: $DOMAIN_TEST and $INFRA_TEST"
echo "   4. Run: python -m importlinter"
echo "   5. Run: make test"
