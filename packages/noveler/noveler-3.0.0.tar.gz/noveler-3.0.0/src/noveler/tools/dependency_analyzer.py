"""
依存関係分析ツール - CODEMAP.yamlのdependency_map自動生成

使用方法:
    python scripts/tools/dependency_analyzer.py --output CODEMAP.yaml
"""

import argparse
import ast
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.services.codemap_parallel_processor import CodeMapParallelProcessor
from noveler.presentation.shared.shared_utilities import console


class DependencyAnalyzer:
    """Pythonプロジェクトの依存関係を分析"""

    def __init__(self, project_root: Path, _logger_service: Any | None = None, _console_service: Any | None = None) -> None:
        self.project_root = project_root
        self.dependencies: dict[str, set[str]] = defaultdict(set)
        self.reverse_dependencies: dict[str, set[str]] = defaultdict(set)
        self.module_paths: dict[str, Path] = {}

        # 未使用引数を削除：共有コンポーネントのconsoleを直接使用


        # 未使用引数を削除：共有コンポーネントのconsoleを直接使用

    def analyze_file(self, file_path: Path) -> None:
        """単一ファイルの依存関係を分析"""
        try:
            content = self.file_io_optimizer.optimized_read_text(file_path, encoding="utf-8")
            tree = ast.parse(content)

            module_name = self._path_to_module(file_path)
            self.module_paths[module_name] = file_path

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported = alias.name
                        if imported.startswith("scripts"):
                            self.dependencies[module_name].add(imported)
                            self.reverse_dependencies[imported].add(module_name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("scripts"):
                        base_module = node.module
                        for alias in node.names:
                            imported = f"{base_module}.{alias.name}" if alias.name != "*" else base_module
                            self.dependencies[module_name].add(imported)
                            self.reverse_dependencies[imported].add(module_name)

        except Exception as e:
            console.print(f"Error analyzing {file_path}: {e}", file=sys.stderr)

    def _path_to_module(self, file_path: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        relative = file_path.relative_to(self.project_root)
        parts = list(relative.parts)

        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                parts = parts[:-1]

        return ".".join(parts)

    def analyze_project(self) -> None:
        """プロジェクト全体を分析"""
        scripts_dir = self.project_root / "scripts"
        if not scripts_dir.exists():
            msg = f"Scripts directory not found: {scripts_dir}"
            raise ValueError(msg)

        for py_file in scripts_dir.rglob("*.py"):
            # テストファイルとマイグレーションは除外
            if "test" not in str(py_file) and "migration" not in str(py_file):
                self.analyze_file(py_file)

    def detect_circular_dependencies(self) -> list[list[str]]:
        """循環依存を検出"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(module: str, path: list[str]) -> None:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for dep in self.dependencies.get(module, []):
                if dep not in visited:
                    dfs(dep, path.copy())
                elif dep in rec_stack and dep in path:
                    # 循環を発見
                    cycle_start = path.index(dep)
                    cycle = [*path[cycle_start:], dep]
                    if len(cycle) > 1 and cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.remove(module)

        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])

        return cycles

    def calculate_statistics(self) -> dict:
        """依存関係の統計情報を計算"""
        import_counts = defaultdict(int)
        for module, deps in self.dependencies.items():
            for dep in deps:
                import_counts[dep] += 1

        most_imported = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # カップリングスコアを計算
        coupling_scores = {}
        for module, deps in self.dependencies.items():
            if len(deps) > 0:
                coupling_scores[module] = len(deps) / len(self.dependencies)

        high_coupling = [(mod, score) for mod, score in coupling_scores.items() if score > 0.5]

        return {
            "total_modules": len(self.dependencies),
            "max_dependency_depth": self._calculate_max_depth(),
            "circular_dependencies_found": len(self.detect_circular_dependencies()),
            "most_imported_modules": [{"module": mod, "import_count": count} for mod, count in most_imported],
            "high_coupling": high_coupling,
        }

    def _calculate_max_depth(self) -> int:
        """最大依存深度を計算"""

        def get_depth(module: str, visited: set[str]) -> int:
            if module in visited:
                return 0
            visited.add(module)

            deps = self.dependencies.get(module, [])
            if not deps:
                return 1

            max_child_depth = 0
            for dep in deps:
                child_depth = get_depth(dep, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)

            return 1 + max_child_depth

        max_depth = 0
        for module in self.dependencies:
            depth = get_depth(module, set())
            max_depth = max(max_depth, depth)

        return max_depth

    def generate_dependency_map(self) -> dict:
        """CODEMAP.yaml用の依存関係マップを生成"""
        core_modules = {}

        # 重要なモジュールのみ詳細情報を含める
        important_patterns = [
            "noveler.domain.entities",
            "noveler.application.use_cases",
            "noveler.infrastructure.adapters",
            "noveler.presentation.cli",
        ]

        for module in self.dependencies:
            for pattern in important_patterns:
                if module.startswith(pattern):
                    imports = sorted(self.dependencies[module])
                    imported_by = sorted(self.reverse_dependencies.get(module, []))

                    # scriptsで始まるもののみフィルタ
                    imports = [imp for imp in imports if imp.startswith("scripts")]
                    imported_by = [imp for imp in imported_by if imp.startswith("scripts")]

                    if imports or imported_by:
                        core_modules[module] = {"imports": imports, "imported_by": imported_by}
                    break

        return {
            "version": "1.0.0",
            "generated_at": self._get_timestamp(),
            "generation_tool": "noveler/tools/dependency_analyzer.py",
            "core_dependencies": core_modules,
            "dependency_statistics": self.calculate_statistics(),
            "dependency_issues": self._analyze_issues(),
        }

    def _analyze_issues(self) -> dict:
        """依存関係の問題を分析"""
        issues = {"high_coupling": [], "layer_violations": [], "unused_imports": []}

        # 高結合度モジュールを検出
        for module, deps in self.dependencies.items():
            if len(deps) > 10:
                coupling_score = len(deps) / len(self.dependencies)
                if coupling_score > 0.5:
                    issues["high_coupling"].append(
                        {
                            "module": module,
                            "coupling_score": round(coupling_score, 2),
                            "recommendation": "Consider splitting into smaller modules",
                        }
                    )

        # レイヤー違反を検出
        layer_order = ["domain", "application", "infrastructure", "presentation"]
        for module, deps in self.dependencies.items():
            module_layer = self._get_layer(module)
            for dep in deps:
                dep_layer = self._get_layer(dep)
                if module_layer and dep_layer:
                    module_idx = layer_order.index(module_layer)
                    dep_idx = layer_order.index(dep_layer)
                    if module_idx < dep_idx:
                        issues["layer_violations"].append(
                            {"from": module, "to": dep, "violation": f"{module_layer} -> {dep_layer}"}
                        )

        return issues

    def _get_layer(self, module: str) -> str | None:
        """モジュールのレイヤーを判定"""
        if "domain" in module:
            return "domain"
        if "application" in module:
            return "application"
        if "infrastructure" in module:
            return "infrastructure"
        if "presentation" in module:
            return "presentation"
        return None

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""

        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class QualityMetricsAnalyzer:
    """品質メトリクスを収集・分析"""

    def __init__(self, project_root: Path, _logger_service: Any | None = None, _console_service: Any | None = None) -> None:
        self.project_root = project_root

        # 未使用引数を削除：共有コンポーネントのconsoleを直接使用

    def collect_coverage(self) -> dict:
        """テストカバレッジ情報を収集"""
        try:
            # pytest-covを実行
            subprocess.run(
                ["pytest", "--cov=scripts", "--cov-report=json", "--quiet"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            coverage_file = self.project_root / ".coverage.json"
            if coverage_file.exists():
                with coverage_file.open(encoding="utf-8") as f:
                    data = json.load(f)

                return self._parse_coverage_data(data)
        except Exception as e:
            console.print(f"Coverage collection failed: {e}", file=sys.stderr)
            # エラーログ追加

        # デフォルト値を返す
        return {"overall": {"line_coverage": 0, "branch_coverage": 0, "function_coverage": 0}, "by_layer": {}}

    def collect_lint_scores(self) -> dict:
        """リントスコアを収集"""
        try:
            # ruffを実行
            result = subprocess.run(
                ["ruff", "check", "scripts", "--format=json"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                issues = json.loads(result.stdout)
                return self._parse_lint_data(issues)
        except Exception as e:
            console.print(f"Lint collection failed: {e}", file=sys.stderr)
            # エラーログ追加

        return {"overall_score": 100, "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0}}

    def collect_type_checking(self) -> dict:
        """型チェック結果を収集"""
        try:
            # mypyを実行
            subprocess.run(
                ["mypy", "scripts", "--json-report", "."],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            report_file = self.project_root / "mypy_report.json"
            if report_file.exists():
                with report_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                return self._parse_mypy_data(data)
        except Exception as e:
            console.print(f"Type checking failed: {e}", file=sys.stderr)
            # エラーログ追加

        return {"mypy_score": 0, "files_checked": 0, "files_with_errors": 0}

    def _parse_coverage_data(self, data: dict) -> dict:
        """カバレッジデータを解析"""
        totals = data.get("totals", {})
        files = data.get("files", {})

        # レイヤー別に集計
        by_layer = defaultdict(lambda: {"files": [], "total_lines": 0, "covered_lines": 0})

        for file_path, file_data in files.items():
            layer = self._get_layer_from_path(file_path)
            if layer:
                by_layer[layer]["files"].append(file_path)
                by_layer[layer]["total_lines"] += file_data.get("num_statements", 0)
                by_layer[layer]["covered_lines"] += file_data.get("num_executed_lines", 0)

        # パーセンテージを計算
        layer_coverage = {}
        for layer, data in by_layer.items():
            coverage = data["covered_lines"] / data["total_lines"] * 100 if data["total_lines"] > 0 else 0
            layer_coverage[layer] = {"line_coverage": round(coverage, 1)}

        return {
            "overall": {
                "line_coverage": round(totals.get("percent_covered", 0), 1),
                "branch_coverage": round(totals.get("percent_branch_covered", 0), 1),
                "function_coverage": 0,  # 別途計算が必要
            },
            "by_layer": layer_coverage,
        }

    def _parse_lint_data(self, issues: list[dict]) -> dict:
        """リントデータを解析"""
        severity_count = defaultdict(int)
        for issue in issues:
            severity = issue.get("severity", "low").lower()
            severity_count[severity] += 1

        # スコアを計算（重み付け）
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_weight = sum(weights[sev] * count for sev, count in severity_count.items())
        max_score = 100
        score = max(0, max_score - total_weight)

        return {
            "overall_score": score,
            "issues_by_severity": dict(severity_count),
            "top_issues": issues[:5] if issues else [],
        }

    def _parse_mypy_data(self, data: dict) -> dict:
        """mypyデータを解析"""
        summary = data.get("summary", {})

        return {
            "mypy_score": 100 - (summary.get("error_rate", 0) * 100),
            "files_checked": summary.get("files_checked", 0),
            "files_with_errors": summary.get("files_with_errors", 0),
            "errors_by_type": summary.get("errors_by_type", {}),
        }

    def _get_layer_from_path(self, path: str) -> str | None:
        """パスからレイヤーを判定"""
        if "domain" in path:
            return "domain"
        if "application" in path:
            return "application"
        if "infrastructure" in path:
            return "infrastructure"
        if "presentation" in path:
            return "presentation"
        return None

    def generate_quality_metrics(self) -> dict:
        """品質メトリクスマップを生成"""
        return {
            "version": "1.0.0",
            "generated_at": self._get_timestamp(),
            "generation_tools": {"coverage": "pytest-cov", "lint": "ruff", "complexity": "radon", "type_check": "mypy"},
            "test_coverage": self.collect_coverage(),
            "lint_scores": self.collect_lint_scores(),
            "type_checking": self.collect_type_checking(),
        }

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""

        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def update_codemap(
    project_root: Path, output_path: Path, split_files: bool = False, incremental: bool = False, parallel: bool = False
) -> None:
    """CODEMAP.yamlを更新

    Phase 3対応: 並列処理とインクリメンタル更新の最適化

    Args:
        project_root: プロジェクトルートパス
        output_path: 出力ファイルパス
        split_files: 分割ファイルを生成するか
        incremental: インクリメンタル更新を行うか
        parallel: 並列処理を使用するか（Phase 3）
    """

    # 既存のCODEMAPを読み込み
    if output_path.exists():
        with output_path.open(encoding="utf-8") as f:
            codemap = yaml.safe_load(f) or {}
    else:
        codemap = {}

    # インクリメンタル更新の場合
    if incremental and output_path.exists():
        console.print("Performing incremental update...")
        changed_files = get_changed_files_since_last_update(project_root, codemap)
        if not changed_files:
            console.print("No changes detected, skipping update")
            return

        console.print(f"Found {len(changed_files)} changed files")

        # Phase 3: 並列インクリメンタル解析
        if parallel:
            console.print("Using parallel incremental analysis...")
            codemap = analyze_incremental_changes(project_root, changed_files, codemap)
        else:
            # 従来の逐次処理
            dep_analyzer = DependencyAnalyzer(project_root)
            dep_analyzer.analyze_project()
            dependency_map = dep_analyzer.generate_dependency_map()
            codemap["dependency_map"] = dependency_map

    # フル更新の場合
    else:
        console.print("Performing full update...")

        if parallel:
            # Phase 3: 並列フル解析
            console.print("Using parallel analysis...")

            processor = CodeMapParallelProcessor(project_root)

            # 全Pythonファイルを収集
            py_files = [f for f in project_root.rglob("*.py") if "__pycache__" not in str(f)]
            console.print(f"Analyzing {len(py_files)} Python files in parallel...")

            analysis_result = processor.analyze_parallel(py_files, "full")

            # 結果をCODEMAPに反映
            codemap["dependency_map"] = analysis_result["dependency_map"]
            codemap["quality_metrics"] = analysis_result["quality_metrics"]
            codemap["performance"] = analysis_result["performance"]

        else:
            # 従来の逐次処理
            console.print("Analyzing dependencies...")
            dep_analyzer = DependencyAnalyzer(project_root)
            dep_analyzer.analyze_project()
            dependency_map = dep_analyzer.generate_dependency_map()

            # 品質メトリクス収集
            console.print("Collecting quality metrics...")
            quality_analyzer = QualityMetricsAnalyzer(project_root)
            quality_metrics = quality_analyzer.generate_quality_metrics()

            codemap["dependency_map"] = dependency_map
            codemap["quality_metrics"] = quality_metrics

    # 自動更新設定を追加
    if "automation_config" not in codemap:
        codemap["automation_config"] = {
            "update_schedule": "0 0 * * *",
            "dependency_map_generation": {
                "tool": "noveler/tools/dependency_analyzer.py",
                "options": ["--include-tests", "--detect-circular", "--export-graphviz", "--parallel"],
            },
            "quality_metrics_generation": {
                "coverage": {"command": "pytest --cov=scripts --cov-report=json", "output": ".coverage.json"},
                "lint": {"command": "ruff check scripts --format=json", "output": ".ruff.json"},
            },
        }

    # 分割ファイル生成
    if split_files:
        generate_split_files(project_root, codemap)
        console.print("Generated split files: _core.yaml, _violations.yaml, _stats.yaml")

    # YAMLファイルに書き込み
    with output_path.open("w", encoding="utf-8") as f:
        yaml.dump(codemap, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # インデックスファイル生成
    generate_index_file(project_root, codemap.get("dependency_map", {}))
    console.print(f"Updated {output_path}")


def get_changed_files_since_last_update(project_root: Path, codemap: dict) -> list[Path]:
    """前回更新以降の変更ファイルを取得"""

    last_update = codemap.get("dependency_map", {}).get("generated_at", "")
    if not last_update:
        return []

    try:
        # Git履歴から変更ファイルを取得
        result = subprocess.run(
            ["git", "diff", "--name-only", f"--since={last_update}"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        changed_files = []
        for line in result.stdout.strip().split("\n"):
            if line.endswith(".py") and line.startswith("noveler/"):
                changed_files.append(project_root / line)

        return changed_files
    except subprocess.CalledProcessError:
        return []


def analyze_incremental_changes(project_root: Path, changed_files: list[Path], existing_codemap: dict) -> dict:
    """変更ファイルのみを解析して既存CODEMAPを更新

    Phase 3: インクリメンタル更新の最適化

    Args:
        project_root: プロジェクトルート
        changed_files: 変更されたファイルリスト
        existing_codemap: 既存のCODEMAP

    Returns:
        更新されたCODEMAP
    """

    # 並列処理でchangedファイルを解析
    processor = CodeMapParallelProcessor(project_root)
    analysis_result = processor.analyze_parallel(changed_files, "full")

    # 既存のCODEMAPをコピー
    updated_codemap = existing_codemap.copy()
    dependency_map = updated_codemap.get("dependency_map", {})

    # 変更されたモジュールの依存関係を更新
    for module_name, dependencies in analysis_result["dependency_map"]["core_dependencies"].items():
        dependency_map["core_dependencies"][module_name] = dependencies

    # 削除されたファイルを検出して削除
    existing_modules = set(dependency_map.get("core_dependencies", {}).keys())
    current_modules = set()

    for py_file in project_root.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            module_name = str(py_file.relative_to(project_root))
            module_name = module_name.replace("/", ".").replace(".py", "")
            current_modules.add(module_name)

    deleted_modules = existing_modules - current_modules
    for module in deleted_modules:
        dependency_map["core_dependencies"].pop(module, None)

    # 違反情報を更新
    dependency_map["dependency_issues"] = analysis_result["dependency_map"]["dependency_issues"]

    # 統計を再計算
    dependency_map["dependency_statistics"] = {
        "total_modules": len(dependency_map["core_dependencies"]),
        "max_dependency_depth": calculate_max_depth(dependency_map["core_dependencies"]),
        "circular_dependencies_found": len(detect_circular_dependencies_in_map(dependency_map["core_dependencies"])),
        "total_violations": len(dependency_map["dependency_issues"].get("layer_violations", [])),
    }

    # メトリクスを更新
    if "quality_metrics" in analysis_result:
        updated_codemap["quality_metrics"] = analysis_result["quality_metrics"]

    # タイムスタンプを更新
    dependency_map["generated_at"] = datetime.now(timezone.utc).isoformat()

    updated_codemap["dependency_map"] = dependency_map

    return updated_codemap


def calculate_max_depth(dependencies: dict) -> int:
    """依存関係の最大深度を計算"""

    def get_depth(module: str, visited: set, current_depth: int = 0) -> int:
        if module in visited:
            return current_depth
        visited.add(module)

        if module not in dependencies:
            return current_depth

        imports = dependencies[module].get("imports", [])
        if not imports:
            return current_depth

        max_child_depth = current_depth
        for imported in imports:
            # scriptsモジュールのみを対象
            if imported.startswith("noveler."):
                child_depth = get_depth(imported, visited.copy(), current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    max_depth = 0
    for module in dependencies:
        depth = get_depth(module, set())
        max_depth = max(max_depth, depth)

    return max_depth


def detect_circular_dependencies_in_map(dependencies: dict) -> list:
    """依存関係マップから循環依存を検出"""
    circular_deps = []

    def has_cycle(module: str, path: list, visited: set) -> bool:
        if module in path:
            # 循環を検出
            cycle_start = path.index(module)
            cycle = [*path[cycle_start:], module]
            circular_deps.append(cycle)
            return True

        if module in visited:
            return False

        visited.add(module)

        if module not in dependencies:
            return False

        imports = dependencies[module].get("imports", [])
        for imported in imports:
            if imported.startswith("noveler."):
                if has_cycle(imported, [*path, module], visited.copy()):
                    return True

        return False

    visited_global = set()
    for module in dependencies:
        if module not in visited_global:
            has_cycle(module, [], visited_global)

    # 重複を削除
    unique_cycles = []
    for cycle in circular_deps:
        # 循環を正規化（最小の要素から開始）
        min_idx = cycle.index(min(cycle))
        normalized = cycle[min_idx:] + cycle[:min_idx]
        if normalized not in unique_cycles:
            unique_cycles.append(normalized)

    return unique_cycles


def generate_split_files(project_root: Path, codemap: dict) -> None:
    """分割ファイルを生成"""
    dependency_map = codemap.get("dependency_map", {})

    # Core dependencies
    core_file = project_root / "CODEMAP_dependencies_core.yaml"
    core_data = {
        "dependency_map": {
            "version": dependency_map.get("version"),
            "generated_at": dependency_map.get("generated_at"),
            "generation_tool": dependency_map.get("generation_tool"),
            "core_dependencies": dependency_map.get("core_dependencies", {}),
        }
    }
    with core_file.open("w", encoding="utf-8") as f:
        yaml.dump(core_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Violations
    violations_file = project_root / "CODEMAP_dependencies_violations.yaml"
    violations_data = {
        "dependency_map": {
            "version": dependency_map.get("version"),
            "generated_at": dependency_map.get("generated_at"),
            "dependency_issues": dependency_map.get("dependency_issues", {}),
        }
    }
    with violations_file.open("w", encoding="utf-8") as f:
        yaml.dump(violations_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Statistics
    stats_file = project_root / "CODEMAP_dependencies_stats.yaml"
    stats_data = {
        "dependency_map": {
            "version": dependency_map.get("version"),
            "generated_at": dependency_map.get("generated_at"),
            "dependency_statistics": dependency_map.get("dependency_statistics", {}),
        },
        "quality_metrics": codemap.get("quality_metrics", {}),
        "automation_config": codemap.get("automation_config", {}),
    }
    with stats_file.open("w", encoding="utf-8") as f:
        yaml.dump(stats_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def generate_index_file(project_root: Path, dependency_map: dict, dep_analyzer: "DependencyAnalyzer" = None) -> None:
    """高速検索用インデックスファイルを生成"""

    index_file = project_root / ".codemap_cache" / "codemap.index.json"
    index_file.parent.mkdir(exist_ok=True)

    # インデックスデータ構築
    index_data = {
        "version": dependency_map.get("version"),
        "generated_at": dependency_map.get("generated_at"),
        "module_count": len(dependency_map.get("core_dependencies", {})),
        "layer_modules": {},
        "high_coupling_modules": [],
        "violation_modules": [],
    }

    # レイヤー別モジュール集計
    for module_name in dependency_map.get("core_dependencies", {}):
        layer = None
        if "domain" in module_name:
            layer = "domain"
        elif "application" in module_name:
            layer = "application"
        elif "infrastructure" in module_name:
            layer = "infrastructure"
        elif "presentation" in module_name:
            layer = "presentation"

        if layer:
            if layer not in index_data["layer_modules"]:
                index_data["layer_modules"][layer] = []
            index_data["layer_modules"][layer].append(module_name)

    # 高結合度モジュール
    issues = dependency_map.get("dependency_issues", {})
    for item in issues.get("high_coupling", []):
        index_data["high_coupling_modules"].append(item.get("module"))

    # 違反モジュール
    for violation in issues.get("layer_violations", []):
        index_data["violation_modules"].append(violation.get("from"))

    # インデックスファイル書き込み
    with index_file.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)

    # 循環依存の警告
    if dep_analyzer:
        cycles = dep_analyzer.detect_circular_dependencies()
        if cycles:
            console.print("\nWarning: Circular dependencies detected:")
            for cycle in cycles:
                console.print(f"  {' -> '.join(cycle)}")


def main():
    parser = argparse.ArgumentParser(description="Analyze project dependencies and quality metrics")
    parser.add_argument(
        "--output", type=Path, default=Path("CODEMAP_dependencies.yaml"), help="Output CODEMAP dependencies path"
    )

    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")

    parser.add_argument("--include-tests", action="store_true", help="Include test files in analysis")

    parser.add_argument("--detect-circular", action="store_true", help="Detect circular dependencies")

    parser.add_argument("--export-graphviz", action="store_true", help="Export dependency graph as Graphviz DOT file")

    parser.add_argument("--split-files", action="store_true", help="Generate split files (_core, _violations, _stats)")

    parser.add_argument("--incremental", action="store_true", help="Perform incremental update (only changed files)")

    parser.add_argument("--parallel", action="store_true", help="Use parallel processing for analysis (Phase 3)")

    args = parser.parse_args()

    try:
        update_codemap(
            args.project_root,
            args.output,
            split_files=args.split_files,
            incremental=args.incremental,
            parallel=args.parallel,
        )
    except Exception as e:
        console.print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
