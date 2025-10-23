#!/usr/bin/env python3
"""
File: scripts/diagnostics/test_anemic_detection.py
Purpose: Test anemic domain detection on existing codebase
Context: Validate detection accuracy before pre-commit integration
"""

import sys
from pathlib import Path

# Import the detector
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.hooks.check_anemic_domain import check_file


def main():
    """Test on known domain files"""

    # Test files
    test_cases = [
        # Real Value Objects (should pass if they have __post_init__)
        ("src/noveler/domain/value_objects/episode_number.py", "OK"),
        ("src/noveler/domain/value_objects/error_response.py", "OK"),
        ("src/noveler/domain/value_objects/prompt_save_result.py", "OK"),

        # Real Entities (should have business logic)
        ("src/noveler/domain/entities/episode_prompt.py", "OK"),

        # DTOs (should be excluded even without business logic)
        ("tests/fixtures/domain/value_objects/dto_example.py", "OK"),

        # Immutable Value Objects with dataclass auto-generated __eq__
        ("tests/fixtures/domain/value_objects/immutable_vo_example.py", "ISSUES"),  # NoEqValue should fail
    ]

    print("=== Anemic Domain Detection Test ===\n")

    passed = 0
    failed = 0

    for test_file, expected in test_cases:
        file_path = Path(test_file)
        if not file_path.exists():
            print(f"[SKIP] {test_file} (not found)")
            continue

        issues = check_file(file_path)
        actual = "ISSUES" if issues else "OK"

        if actual == expected:
            print(f"[PASS] {test_file} - Expected: {expected}, Got: {actual}")
            passed += 1
        else:
            print(f"[FAIL] {test_file} - Expected: {expected}, Got: {actual}")
            failed += 1

        if issues:
            for line, code, message in issues:
                print(f"       [{code}] {message}")
        print()

    print("\n=== Summary ===")
    print(f"Passed: {passed}/{passed + failed}")
    print(f"Failed: {failed}/{passed + failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
