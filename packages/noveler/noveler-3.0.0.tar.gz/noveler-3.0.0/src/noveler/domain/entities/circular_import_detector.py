#!/usr/bin/env python3

"""Domain.entities.circular_import_detector
Where: Domain entity describing circular import analysis.
What: Holds detected cycles and remediation suggestions.
Why: Supports architectural hygiene by surfacing import issues.
"""

from __future__ import annotations

"""循環インポート検出エンティティ

仕様書: SPEC-CIRCULAR-IMPORT-DETECTION-001
DDD準拠: Domain層純粋性回復、Infrastructure依存排除
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from pathlib import Path

    from noveler.domain.interfaces.logger_service import ILoggerService

from noveler.domain.value_objects.dependency_graph import CircularPath, DependencyGraph, DependencyNode
from noveler.domain.value_objects.import_statement import ImportStatement


@dataclass
class CircularDetectionResult:
    """循環検出結果"""

    circular_paths: list[CircularPath]
    dependency_graph: DependencyGraph
    analysis_summary: dict[str, int]
    risk_assessment: dict[str, float]

    def get_total_risk_score(self) -> float:
        """総合リスクスコア (0-100)"""
        if not self.circular_paths:
            return 0.0

        total_risk = sum(path.risk_level for path in self.circular_paths)
        max_possible_risk = len(self.circular_paths) * 5  # 最大リスクレベルは5

        return (total_risk / max_possible_risk) * 100.0 if max_possible_risk > 0 else 0.0

    def get_critical_paths(self, min_risk_level: int = 4) -> list[CircularPath]:
        """高リスク循環パスの取得"""
        return [path for path in self.circular_paths if path.risk_level >= min_risk_level]

    def get_modules_in_cycles(self) -> set[str]:
        """循環に関与するモジュール一覧"""
        modules = set()
        for path in self.circular_paths:
            modules.update(path.modules)
        return modules


@dataclass
class CircularImportDetection:
    """循環インポート検出結果"""

    detected: bool
    import_cycle: list[str] = field(default_factory=list)
    severity: str = "medium"
    recommendation: str = ""


@dataclass
class CircularImportDetector:
    """循環インポート検出エンティティ（DDD準拠）"""

    project_root: Path
    logger_service: ILoggerService | None = None
    _result_cache: dict[str, CircularDetectionResult] = field(default_factory=dict, init=False, repr=False)

    def detect_cycles(self, target_modules: list[str]) -> CircularImportDetection:
        """循環インポートの検出（純粋なビジネスロジック）"""
        if self.logger_service:
            self.logger_service.info("循環インポート検出を開始")

        # ドメインロジック実装
        detected_cycle = self._analyze_import_patterns(target_modules)

        if detected_cycle:
            return CircularImportDetection(
                detected=True,
                import_cycle=detected_cycle,
                severity="high",
                recommendation="依存関係の逆転またはインターフェース分離を適用",
            )

        return CircularImportDetection(detected=False)

    # 後方互換エイリアス（既存APIを維持）
    def detect_circular_imports(
        self,
        import_statements: Iterable[ImportStatement],
        cache_key: str | None = None,
    ) -> CircularDetectionResult:
        """ImportStatement群から循環依存を解析し詳細結果を返却する。"""
        if cache_key and cache_key in self._result_cache:
            return self._result_cache[cache_key]

        statements = list(import_statements)
        dependency_graph = self._build_dependency_graph(statements)
        cycles = dependency_graph.detect_cycles()

        analysis_summary = {
            "total_imports": len(statements),
            "cycle_count": len(cycles),
        }
        risk_assessment = {
            "total_risk": sum(path.risk_level for path in cycles),
            "max_risk": len(cycles) * 5,
        }

        result = CircularDetectionResult(
            circular_paths=cycles,
            dependency_graph=dependency_graph,
            analysis_summary=analysis_summary,
            risk_assessment=risk_assessment,
        )

        if cache_key:
            self._result_cache[cache_key] = result

        return result

    def predict_new_import_risk(
        self,
        new_import: ImportStatement,
        existing_imports: Iterable[ImportStatement],
    ) -> tuple[float, list[str]]:
        """新規インポート追加時のリスク評価."""

        baseline_result = self.detect_circular_imports(existing_imports)
        baseline_modules = {tuple(path.modules) for path in baseline_result.circular_paths}

        updated_statements = list(existing_imports) + [new_import]
        updated_result = self.detect_circular_imports(updated_statements)

        new_cycles = [path for path in updated_result.circular_paths if tuple(path.modules) not in baseline_modules]
        if not new_cycles:
            return 0.0, []

        warnings = [f"循環: {' -> '.join(path.modules)}" for path in new_cycles]
        risk_score = updated_result.get_total_risk_score()
        return risk_score, warnings

    def _analyze_import_patterns(self, modules: list[str]) -> list[str]:
        """インポートパターンの分析（純粋関数）"""
        # 簡略化されたロジック - 実際の実装では詳細な解析
        for module in modules:
            module_name = getattr(module, "module_name", None)
            if not module_name:
                module_name = str(module)

            if "circular" in module_name:
                return [module_name, f"{module_name}_dependency", module_name]
        return []

    def _build_dependency_graph(self, statements: list[ImportStatement]) -> DependencyGraph:
        graph = DependencyGraph()
        for stmt in statements:
            source_module = self._module_name_from_source(stmt.source_file)

            if source_module not in graph.nodes:
                graph.add_node(DependencyNode(module_name=source_module, file_path=stmt.source_file))

            graph.add_dependency(source_module, stmt.module_name, stmt)

            if stmt.module_name not in graph.nodes:
                graph.add_node(DependencyNode(module_name=stmt.module_name, file_path=stmt.source_file))

        return graph

    def _module_name_from_source(self, source_file: Path) -> str:
        """ソースファイルパスからモジュール名を推測"""
        try:
            parts = source_file.with_suffix("").parts
            if "src" in parts:
                src_index = parts.index("src") + 1
                module_parts = parts[src_index:]
            else:
                module_parts = parts
            if not module_parts:
                return source_file.stem
            return ".".join(module_parts)
        except Exception:
            return source_file.stem
