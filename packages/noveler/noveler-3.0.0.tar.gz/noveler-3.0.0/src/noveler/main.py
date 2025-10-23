#!/usr/bin/env python3
"""Noveler CLI entrypoint delegating to the presentation facade.

This module intentionally contains only a thin delegation layer.
"""

from __future__ import annotations

import sys

from noveler.presentation.cli.cli_adapter import run
# Backward-compatible export for tests and internal callers
# Re-export execute_18_step_writing from the CLI adapter
try:
    from noveler.presentation.cli.cli_adapter import execute_18_step_writing  # type: ignore[F401]
except Exception:
    # Keep CLI functional even if the adapter signature changes; tests may fail loud instead
    pass


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())


# Test compatibility facade for legacy "novel" module reference
class NovelFacade:
    """Legacy compatibility facade for tests that reference noveler.main.novel"""

    @staticmethod
    def scene_add(category: str, scene_id: str) -> None:
        """Minimal scene_add implementation for test compatibility

        Args:
            category: Scene category identifier
            scene_id: Scene identifier

        Raises:
            NotImplementedError: This is a stub for test compatibility only
        """
        # This is a minimal stub for test compatibility
        # Real implementation would delegate to appropriate use cases
        from noveler.infrastructure.factories.repository_factory import get_repository_factory  # noqa: PLC0415
        from noveler.application.use_cases.scene_management_use_case import SceneManagementUseCase  # noqa: PLC0415

        try:
            factory = get_repository_factory()
            scene_repo = factory.get_scene_management_repository()
            use_case = SceneManagementUseCase(scene_repo)

            # Basic scene creation (minimal implementation)
            use_case.create_scene(scene_id, {"category": category})

        except Exception as e:
            # For test compatibility, raise with descriptive message
            raise NotImplementedError(f"scene_add stub failed: {e}") from e


# Expose novel facade for backward compatibility
novel = NovelFacade()

# Expose dependencies for test patching compatibility
try:
    from noveler.infrastructure.repositories.yaml_scene_management_repository import YamlSceneManagementRepository  # type: ignore[F401]
    from noveler.application.use_cases.scene_management_use_case import SceneManagementUseCase  # type: ignore[F401]
    from noveler.presentation.cli.shared_utilities.error_handler import handle_error  # type: ignore[F401]
except ImportError:
    # Dependencies not available - tests will need to handle gracefully
    pass

# Mock input function for test compatibility
try:
    input = input  # Expose built-in input for potential test patching
except NameError:
    pass
