#!/usr/bin/env python3
"""Analyze comment audit results to extract unique files and violation counts."""

import subprocess
import sys
from collections import Counter
from pathlib import Path

def main():
    # Run the audit script
    result = subprocess.run(
        [sys.executable, "scripts/comment_header_audit.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    lines = result.stderr.splitlines()

    # Extract file paths and violation types
    file_violations = {}
    violation_types = Counter()

    for line in lines:
        if ".py:" in line and not line.startswith("[FAIL]") and not line.startswith("Total"):
            try:
                # Parse: C:\...\file.py:lineno: message
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[0].strip()
                    message = parts[2].strip()

                    # Normalize path for display
                    try:
                        rel_path = Path(file_path).relative_to(Path.cwd() / "src")
                        display_path = f"src/{rel_path}"
                    except ValueError:
                        display_path = file_path

                    if display_path not in file_violations:
                        file_violations[display_path] = []
                    file_violations[display_path].append(message)

                    # Count violation types
                    if "Missing header comment" in message:
                        violation_types["Missing header comment"] += 1
                    elif "Purpose:" in message:
                        violation_types["Missing Purpose section"] += 1
                    elif "Args:" in message:
                        violation_types["Missing Args section"] += 1
                    elif "Returns:" in message:
                        violation_types["Missing Returns section"] += 1
                    elif "Raises:" in message:
                        violation_types["Missing Raises section"] += 1
                    elif "Side Effects:" in message or "side effects" in message.lower():
                        violation_types["Missing Side Effects section"] += 1
                    elif "lacks docstring" in message:
                        violation_types["Missing docstring"] += 1
            except Exception as e:
                continue

    # Print summary
    print("=" * 80)
    print(f"DOCSTRING/COMMENT COMPLIANCE AUDIT SUMMARY")
    print("=" * 80)
    print()
    print(f"Total files with violations: {len(file_violations)}")
    print(f"Total violations: {sum(len(v) for v in file_violations.values())}")
    print()

    print("Violation types:")
    for vtype, count in violation_types.most_common():
        print(f"  - {vtype}: {count}")
    print()

    print("=" * 80)
    print("FILES WITH MOST VIOLATIONS (Top 20):")
    print("=" * 80)
    print()

    sorted_files = sorted(file_violations.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (file_path, violations) in enumerate(sorted_files[:20], 1):
        print(f"{i:2d}. {file_path}")
        print(f"    {len(violations)} violations")

        # Show unique violation types for this file
        unique_types = set()
        for v in violations:
            if "Missing header comment" in v:
                unique_types.add("No header")
            elif "Purpose:" in v:
                unique_types.add("No Purpose")
            elif "lacks docstring" in v:
                unique_types.add("No docstring")
            elif "Args:" in v:
                unique_types.add("No Args")
            elif "Returns:" in v:
                unique_types.add("No Returns")
            elif "Side Effects:" in v or "side effects" in v.lower():
                unique_types.add("No Side Effects")

        print(f"    Types: {', '.join(sorted(unique_types))}")
        print()

    print("=" * 80)
    print(f"Full list saved to: reports/audit_violations.txt")
    print("=" * 80)

    # Save full list
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "audit_violations.txt", "w", encoding="utf-8") as f:
        for file_path in sorted(file_violations.keys()):
            f.write(f"\n{file_path}\n")
            f.write("=" * len(file_path) + "\n")
            for violation in file_violations[file_path]:
                f.write(f"  - {violation}\n")

if __name__ == "__main__":
    main()
