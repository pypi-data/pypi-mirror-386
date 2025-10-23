#!/usr/bin/env python3
"""Refactor UI system imports to use DDD-compliant adapters.

Replaces BatchProcessingSystem/WritingAnalyticsSystem imports from presentation.ui
with adapter patterns that isolate presentation layer dependencies.
"""

import re
from pathlib import Path


def refactor_file(file_path: Path) -> bool:
    """Refactor a single file to use adapter pattern for UI systems.

    Args:
        file_path: Path to file to refactor

    Returns:
        bool: True if file was modified
    """
    content = file_path.read_text(encoding="utf-8")
    original = content

    # Pattern 1: BatchProcessingSystem import and instantiation
    # Replace:
    #   from noveler.presentation.ui.batch_processor import BatchProcessingSystem
    #   batch_processor = BatchProcessingSystem(project_root)
    # With:
    #   from noveler.infrastructure.adapters.batch_processing_adapter import BatchProcessingAdapter
    #   batch_processor = BatchProcessingAdapter(project_root)

    content = re.sub(
        r"from noveler\.presentation\.ui\.batch_processor import BatchProcessingSystem",
        "from noveler.infrastructure.adapters.batch_processing_adapter import BatchProcessingAdapter",
        content,
    )

    content = re.sub(
        r"batch_processor = BatchProcessingSystem\(project_root\)",
        "batch_processor = BatchProcessingAdapter(project_root)",
        content,
    )

    # Pattern 2: WritingAnalyticsSystem import and instantiation
    # Replace:
    #   from noveler.presentation.ui.analytics_system import WritingAnalyticsSystem
    #   analytics_system = WritingAnalyticsSystem(project_root)
    # With:
    #   from noveler.infrastructure.adapters.analytics_adapter import AnalyticsAdapter
    #   analytics_system = AnalyticsAdapter(project_root)

    content = re.sub(
        r"from noveler\.presentation\.ui\.analytics_system import WritingAnalyticsSystem",
        "from noveler.infrastructure.adapters.analytics_adapter import AnalyticsAdapter",
        content,
    )

    content = re.sub(
        r"analytics_system = WritingAnalyticsSystem\(project_root\)",
        "analytics_system = AnalyticsAdapter(project_root)",
        content,
    )

    # Only write if changed
    if content != original:
        file_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """Main execution."""
    project_root = Path(__file__).parent.parent
    target_file = (
        project_root
        / "src"
        / "noveler"
        / "infrastructure"
        / "json"
        / "mcp"
        / "servers"
        / "json_conversion_server.py"
    )

    if not target_file.exists():
        print(f"❌ Target file not found: {target_file}")
        return 1

    print(f"🔧 Refactoring UI system imports in: {target_file.name}")

    if refactor_file(target_file):
        print(f"✅ Refactored: {target_file}")
        print("   - BatchProcessingSystem → BatchProcessingAdapter")
        print("   - WritingAnalyticsSystem → AnalyticsAdapter")
    else:
        print(f"ℹ️  No changes needed: {target_file}")

    return 0


if __name__ == "__main__":
    exit(main())
