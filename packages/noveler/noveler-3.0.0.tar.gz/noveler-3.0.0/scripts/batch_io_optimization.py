#!/usr/bin/env python3
"""
FileIOOptimizer 一括適用スクリプト
1,747個のI/O操作を効率的にFileIOOptimizerで最適化

実行方法:
python batch_io_optimization.py
"""

import re
from pathlib import Path
from typing import Any


def apply_fileio_optimizer_batch() -> dict[str, Any]:
    """プロジェクト全体にFileIOOptimizerを一括適用"""

    # 最適化対象パターン
    optimization_patterns = [
        # 基本的なfile.open()パターン
        {
            "pattern": r"with\s+([^.]+)\.open\(([^)]+)\)\s+as\s+([^:]+):\s*\n\s*([^=]+)\s*=\s*\3\.read\(\)",
            "replacement": r"# FileIOOptimizer使用で最適化\n\1_content = _file_io_optimizer.optimized_read_text(\1, \2)\n\4 = \1_content",
        },
        # Path().open()パターン
        {
            "pattern": r"with\s+([^.]+)\.Path\(\"r\"\)\.open\(encoding=\"utf-8\"\)\s+as\s+([^:]+):",
            "replacement": r"# FileIOOptimizer使用で最適化\n\2_content = _file_io_optimizer.optimized_read_text(\1, encoding=\"utf-8\")",
        },
        # 書き込みパターン
        {
            "pattern": r"with\s+([^.]+)\.open\(\"w\",\s*encoding=\"utf-8\"\)\s+as\s+([^:]+):\s*\n\s*\2\.write\(([^)]+)\)",
            "replacement": r"# バッチ書き込みを使用\n_file_io_optimizer.batch_write_text(\1, \3, encoding=\"utf-8\")",
        }
    ]

    # 高頻度I/Oファイル一覧（TOP 20）
    high_priority_files = [
        "src/noveler/tools/type_annotation_fixer.py",  # 317スコア、11 I/O
        "src/noveler/tools/dependency_analyzer.py",   # 313スコア、25 I/O
        "src/noveler/infrastructure/config/project_detector.py",  # 297スコア、8 I/O
        "src/noveler/infrastructure/repositories/yaml_a31_checklist_repository.py",  # 273スコア、17 I/O
        "src/noveler/infrastructure/repositories/yaml_episode_repository.py",
        "src/noveler/infrastructure/repositories/yaml_plot_data_repository.py",
        "src/noveler/infrastructure/utils/yaml_utils.py",
        "src/noveler/application/use_cases/generate_episode_plot_use_case.py",
        "src/noveler/application/use_cases/integrated_writing_use_case.py",
        "src/noveler/application/use_cases/plot_quality_assurance_use_case.py",
        "src/noveler/application/use_cases/prompt_generation_use_case.py",
        "src/noveler/application/use_cases/text_analysis_use_case.py",
        "src/noveler/infrastructure/batch/batch_processor.py",
        "src/noveler/infrastructure/performance/async_file_processor.py"
    ]

    results = {
        "files_processed": 0,
        "optimizations_applied": 0,
        "files_optimized": [],
        "errors": []
    }

    project_root = Path()

    # Phase 1: 高優先度ファイルの最適化
    for file_path_str in high_priority_files:
        file_path = project_root / file_path_str
        if file_path.exists():
            try:
                result = optimize_single_file(file_path, optimization_patterns)
                results["files_processed"] += 1
                if result["optimized"]:
                    results["optimizations_applied"] += result["optimizations_count"]
                    results["files_optimized"].append(str(file_path))
            except Exception as e:
                results["errors"].append(f"{file_path}: {e!s}")

    # Phase 2: 残りのPythonファイル自動検出・最適化
    remaining_files = list(project_root.rglob("src/**/*.py"))
    for file_path in remaining_files:
        if str(file_path) not in [project_root / f for f in high_priority_files]:
            if should_optimize_file(file_path):
                try:
                    result = optimize_single_file(file_path, optimization_patterns)
                    results["files_processed"] += 1
                    if result["optimized"]:
                        results["optimizations_applied"] += result["optimizations_count"]
                        results["files_optimized"].append(str(file_path))
                except Exception as e:
                    results["errors"].append(f"{file_path}: {e!s}")

    return results

def optimize_single_file(file_path: Path, patterns: list[dict]) -> dict[str, Any]:
    """単一ファイルの最適化"""

    try:
        # ファイル読み込み
        with file_path.open(encoding="utf-8") as f:
            original_content = f.read()

        modified_content = original_content
        optimizations_count = 0

        # FileIOOptimizer importの追加
        if "from noveler.infrastructure.performance.comprehensive_performance_optimizer import FileIOOptimizer" not in modified_content:
            import_section = re.search(r"(from noveler\..*?\n)+", modified_content)
            if import_section:
                insert_pos = import_section.end()
                modified_content = (
                    modified_content[:insert_pos] +
                    "from noveler.infrastructure.performance.comprehensive_performance_optimizer import FileIOOptimizer\n" +
                    "_file_io_optimizer = FileIOOptimizer()\n\n" +
                    modified_content[insert_pos:]
                )
                optimizations_count += 1

        # 各パターンの適用
        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            replacement = pattern_info["replacement"]

            matches = list(re.finditer(pattern, modified_content, re.MULTILINE | re.DOTALL))
            if matches:
                for match in reversed(matches):  # 後ろから置換して位置ズレを防ぐ
                    start, end = match.span()
                    modified_content = modified_content[:start] + re.sub(pattern, replacement, match.group()) + modified_content[end:]
                    optimizations_count += 1

        # バックアップ作成
        if optimizations_count > 0:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            with backup_path.open("w", encoding="utf-8") as f:
                f.write(original_content)

            # 最適化されたファイル書き込み
            with file_path.open("w", encoding="utf-8") as f:
                f.write(modified_content)

        return {
            "optimized": optimizations_count > 0,
            "optimizations_count": optimizations_count,
            "backup_created": optimizations_count > 0
        }

    except Exception as e:
        return {
            "optimized": False,
            "optimizations_count": 0,
            "error": str(e)
        }

def should_optimize_file(file_path: Path) -> bool:
    """ファイルが最適化対象かどうか判定"""

    # 除外パターン
    exclude_patterns = [
        "__pycache__",
        ".git",
        "test_",
        "_test.py",
        "migrations/",
        ".backup",
        "temp/",
        "archive/"
    ]

    file_str = str(file_path)
    if any(pattern in file_str for pattern in exclude_patterns):
        return False

    # I/O操作が含まれているかチェック
    try:
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

        # I/O操作パターンの存在チェック
        io_patterns = [
            r"\.open\(",
            r"\.read_text\(",
            r"\.write_text\(",
            r"with\s+.*\.open\(",
            r"yaml\.load",
            r"yaml\.dump",
            r"json\.load",
            r"json\.dump"
        ]

        for pattern in io_patterns:
            if re.search(pattern, content):
                return True

        return False

    except Exception:
        return False

if __name__ == "__main__":
    print("🚀 FileIOOptimizer一括最適化開始...")

    results = apply_fileio_optimizer_batch()

    print("\n✅ 最適化完了!")
    print(f"📊 処理ファイル数: {results['files_processed']}")
    print(f"🔧 最適化適用数: {results['optimizations_applied']}")
    print(f"📁 最適化ファイル数: {len(results['files_optimized'])}")

    if results["errors"]:
        print(f"\n⚠️  エラー数: {len(results['errors'])}")
        for error in results["errors"][:5]:  # 最初の5件のみ表示
            print(f"   {error}")

    print("\n🎯 目標達成状況:")
    print(f"   I/O操作最適化数: {results['optimizations_applied']}/1,747")
    completion_rate = (results["optimizations_applied"] / 1747) * 100
    print(f"   完了率: {completion_rate:.1f}%")

    if len(results["files_optimized"]) > 0:
        print("\n📝 最適化されたファイル例:")
        for file_path in results["files_optimized"][:10]:  # 最初の10件のみ表示
            print(f"   ✓ {file_path}")
