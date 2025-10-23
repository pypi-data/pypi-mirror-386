#!/usr/bin/env python3
# verify_template_migration.py

from pathlib import Path
import sys

def verify_migration():
    """移行後の構造を検証"""
    errors = []

    # 必須ディレクトリ
    required_dirs = [
        "templates/writing",
        "templates/quality/checks",
        "templates/quality/analysis",
        "templates/plot",
        "templates/special",
        "templates/legacy"
    ]

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            errors.append(f"Missing directory: {dir_path}")

    # 必須ファイルのサンプリング
    required_files = [
        ("templates/writing/write_step00_scope_definition.yaml", "write_step00"),
        ("templates/quality/checks/check_step01_typo_check.yaml", "check_step01"),
        ("templates/quality/analysis/comprehensive.yaml", "comprehensive"),
        ("templates/plot/章別プロットテンプレート.yaml", "章別プロット"),
        ("templates/special/stage5_品質確認テンプレート.yaml", "stage5"),
        ("templates/legacy/debug.yaml", "debug"),
    ]

    for file_path, identifier in required_files:
        if not Path(file_path).exists():
            errors.append(f"Missing file: {file_path}")

    # ファイル数の確認
    expected_counts = {
        "writing": 19,
        "quality/checks": 12,
        "quality/analysis": 7,
        "plot": 4,
        "special": 3,
        "legacy": 2
    }

    for dir_name, expected_count in expected_counts.items():
        dir_path = Path(f"templates/{dir_name}")
        if dir_path.exists():
            actual_count = len(list(dir_path.glob("*.yaml")))
            if actual_count != expected_count:
                errors.append(f"File count mismatch in {dir_name}: expected {expected_count}, got {actual_count}")

    # ルート直下に残留ファイルがないか確認
    root_yaml = list(Path("templates").glob("*.yaml"))
    if root_yaml:
        print(f"Warning: Files remaining in root: {[f.name for f in root_yaml]}")

    if errors:
        print("❌ Verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ All verifications passed!")
    print(f"Total files verified: {sum(expected_counts.values())}")
    return True

if __name__ == "__main__":
    sys.exit(0 if verify_migration() else 1)
