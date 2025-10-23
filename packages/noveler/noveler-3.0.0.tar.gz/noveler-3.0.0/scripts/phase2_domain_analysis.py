#!/usr/bin/env python3
"""Phase 2: Domain層Infrastructure依存分析スクリプト

B20準拠性修正Phase 2のための詳細分析を実行。
Phase 1成功を踏まえ、残り24ファイルの依存関係解消を支援。
"""

import re
from pathlib import Path


def find_domain_infrastructure_dependencies() -> dict[str, list[tuple[int, str]]]:
    """Domain層のInfrastructure依存を検出"""

    domain_violations: dict[str, list[tuple[int, str]]] = {}
    domain_path = Path("src/noveler/domain")

    if not domain_path.exists():
        print(f"❌ Domain層パスが見つかりません: {domain_path}")
        return domain_violations

    # Infrastructure依存のパターン
    infra_patterns = [
        r"from\s+noveler\.infrastructure",
        r"import\s+noveler\.infrastructure",
        r"from\s+scripts\.infrastructure",
        r"import\s+scripts\.infrastructure",
    ]

    compiled_patterns = [re.compile(pattern) for pattern in infra_patterns]

    for py_file in domain_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, encoding="utf-8") as f:
                lines = f.readlines()

            violations = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                for pattern in compiled_patterns:
                    if pattern.search(line):
                        violations.append((line_num, line))

            if violations:
                rel_path = str(py_file.relative_to(Path.cwd()))
                domain_violations[rel_path] = violations

        except Exception as e:
            print(f"⚠️  ファイル読み込みエラー: {py_file} - {e}")

    return domain_violations


def analyze_violation_patterns(violations: dict[str, list[tuple[int, str]]]) -> dict[str, int]:
    """違反パターンの分析"""

    pattern_counts = {}

    for file_path, file_violations in violations.items():
        for _, line in file_violations:
            # 具体的なインポートモジュールを抽出
            import_match = re.search(r"from\s+(noveler\.infrastructure\.[^\s]+)|import\s+(noveler\.infrastructure\.[^\s]+)", line)
            if import_match:
                module = import_match.group(1) or import_match.group(2)
                module_base = module.split(".")[2] if len(module.split(".")) > 2 else "unknown"
                pattern_counts[module_base] = pattern_counts.get(module_base, 0) + 1

    return pattern_counts


def prioritize_files(violations: dict[str, list[tuple[int, str]]]) -> list[tuple[str, int, str]]:
    """ファイルを優先度順にソート

    Returns:
        List of (file_path, violation_count, priority_level)
    """

    prioritized = []

    for file_path, file_violations in violations.items():
        violation_count = len(file_violations)

        # 優先度決定ロジック
        if "repository" in file_path.lower():
            priority = "HIGH"      # Repository は DDD的に最重要
        elif "service" in file_path.lower():
            priority = "MEDIUM"    # Service は中優先度
        elif "entity" in file_path.lower() or "value_object" in file_path.lower():
            priority = "CRITICAL"  # Entity/ValueObjectは純粋であるべき
        else:
            priority = "MEDIUM"

        prioritized.append((file_path, violation_count, priority))

    # 優先度とバイオレーション数でソート
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    prioritized.sort(key=lambda x: (priority_order[x[2]], -x[1]))

    return prioritized


def generate_phase2_report(violations: dict[str, list[tuple[int, str]]]) -> None:
    """Phase 2レポート生成"""

    if not violations:
        print("🎉 Domain層にInfrastructure依存は発見されませんでした！")
        return

    print("=" * 80)
    print("📋 Phase 2: Domain層Infrastructure依存分析レポート")
    print("=" * 80)

    total_files = len(violations)
    total_violations = sum(len(v) for v in violations.values())

    print("📊 分析結果サマリー:")
    print(f"  - 違反ファイル数: {total_files}")
    print(f"  - 総違反行数: {total_violations}")

    # パターン分析
    patterns = analyze_violation_patterns(violations)
    if patterns:
        print("\n🔍 違反パターン分析:")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            print(f"  - {pattern}: {count}件")

    # 優先度付きファイル一覧
    prioritized = prioritize_files(violations)

    print("\n🎯 優先度別修正対象 (上位10ファイル):")
    for i, (file_path, count, priority) in enumerate(prioritized[:10], 1):
        priority_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }[priority]
        print(f"  {i:2d}. {priority_emoji} [{priority}] {file_path} ({count}件)")

    # 詳細違反情報（上位5ファイル）
    print("\n📝 詳細違反情報 (上位5ファイル):")
    for file_path, count, priority in prioritized[:5]:
        print(f"\n📄 {file_path} [{priority}]:")
        for line_num, line in violations[file_path]:
            print(f"  L{line_num:3d}: {line}")

    print("\n" + "=" * 80)
    print("💡 Phase 2実装推奨アクション:")
    print("1. CRITICAL/HIGHファイルの優先修正")
    print("2. 共通パターンの自動化スクリプト作成")
    print("3. Interface抽出とDI Adapter実装")
    print("4. Repository Interface統一化")
    print("=" * 80)


def main():
    """メイン実行"""
    print("🚀 Phase 2: Domain層Infrastructure依存分析開始...")

    violations = find_domain_infrastructure_dependencies()
    generate_phase2_report(violations)

    print("\n✅ Phase 2分析完了")


if __name__ == "__main__":
    main()
