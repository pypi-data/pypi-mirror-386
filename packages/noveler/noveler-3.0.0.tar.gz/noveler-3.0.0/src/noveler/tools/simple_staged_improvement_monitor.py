#!/usr/bin/env python3
"""簡易版段階的改善監視システム

Phase 3 Week 13-16: 継続監視システム構築
16週間改善ロードマップの進捗監視（簡易実装）
"""

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class PhaseMetrics:
    """フェーズ別メトリクス"""

    phase_name: str
    week_range: str
    completion_percentage: float
    quality_score: float
    architecture_violations: int
    dependency_violations: int
    last_updated: datetime


@dataclass
class StagedImprovementStatus:
    """段階的改善の全体状況"""

    overall_progress: float
    phase_metrics: list[PhaseMetrics]
    critical_issues: list[str]
    next_actions: list[str]
    generated_at: datetime


class SimpleStagedImprovementMonitor:
    """簡易版段階的改善監視システム"""

    def __init__(self, project_root: Path, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化"""
        self.project_root = project_root
        self.cache_dir = project_root / "temp" / "staged_improvement"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Phase定義（16週間ロードマップ）
        self.phases = {
            "phase1": {
                "name": "緊急修正",
                "weeks": "Week 1-4",
                "targets": ["domain_purity", "episode_splitting", "di_injection"],
            },
            "phase2": {"name": "構造改善", "weeks": "Week 5-12", "targets": ["bounded_context", "architecture_tests"]},
            "phase3": {
                "name": "品質向上",
                "weeks": "Week 13-16",
                "targets": ["continuous_monitoring", "performance_optimization"],
            },
        }

        self.logger_service = logger_service
        self.console_service = console_service
    def monitor_staged_improvements(self) -> StagedImprovementStatus:
        """段階的改善の監視実行"""
        self.console_service.print("🔍 段階的改善監視を開始...")

        start_time = time.time()

        # 各フェーズのメトリクス収集
        phase_metrics = []
        for phase_id, phase_config in self.phases.items():
            metrics = self._analyze_phase_progress(phase_id, phase_config)
            phase_metrics.append(metrics)

        # 重要な問題の特定
        critical_issues = self._identify_critical_issues(phase_metrics)

        # 次のアクション提案
        next_actions = self._suggest_next_actions(phase_metrics)

        # 全体進捗の計算
        overall_progress = self._calculate_overall_progress(phase_metrics)

        # 結果の統合
        status = StagedImprovementStatus(
            overall_progress=overall_progress,
            phase_metrics=phase_metrics,
            critical_issues=critical_issues,
            next_actions=next_actions,
            generated_at=project_now().datetime,
        )

        # 結果の保存
        self._save_monitoring_results(status)

        execution_time = time.time() - start_time
        self.console_service.print(f"✅ 段階的改善監視完了 (実行時間: {execution_time:.3f}秒)")

        return status

    def _analyze_phase_progress(self, phase_id: str, phase_config: dict) -> PhaseMetrics:
        """フェーズ進捗の分析"""
        phase_name = phase_config["name"]
        week_range = phase_config["weeks"]

        # フェーズ固有のターゲット評価
        completion_percentage = self._evaluate_phase_targets(phase_config["targets"])

        # 品質スコア計算（簡易版）
        quality_score = self._calculate_simple_quality_score()

        # 違反数の集計（ファイル存在チェックベース）
        arch_violations, dep_violations = self._count_simple_violations()

        return PhaseMetrics(
            phase_name=phase_name,
            week_range=week_range,
            completion_percentage=completion_percentage,
            quality_score=quality_score,
            architecture_violations=arch_violations,
            dependency_violations=dep_violations,
            last_updated=project_now().datetime,
        )

    def _evaluate_phase_targets(self, targets: list[str]) -> float:
        """フェーズターゲットの評価"""
        total_score = 0
        target_scores = {
            "domain_purity": self._check_domain_purity(),
            "episode_splitting": self._check_episode_splitting(),
            "di_injection": self._check_di_injection(),
            "bounded_context": self._check_bounded_context(),
            "architecture_tests": self._check_architecture_tests(),
            "continuous_monitoring": self._check_continuous_monitoring(),
            "performance_optimization": self._check_performance_optimization(),
        }

        for target in targets:
            if target in target_scores:
                total_score += target_scores[target]

        return total_score / len(targets) if targets else 0.0

    def _check_domain_purity(self) -> float:
        """Domain純粋性の検証（ファイルベース）"""
        # domain/entities/配下のPythonファイルをチェック
        domain_entities_dir = self.project_root / "scripts" / "domain" / "entities"
        if not domain_entities_dir.exists():
            return 0.0

        python_files = list(domain_entities_dir.glob("*.py"))
        if not python_files:
            return 50.0

        # infrastructure直接インポートをチェック
        violation_count = 0
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if "from noveler.infrastructure" in content:
                    violation_count += 1
            except Exception:
                continue

        if violation_count == 0:
            return 100.0
        if violation_count <= 2:
            return 80.0
        return 50.0

    def _check_episode_splitting(self) -> float:
        """Episode分割実装の検証"""
        required_files = [
            "noveler/domain/entities/episode.py",
            "noveler/domain/entities/episode_publisher.py",
            "noveler/domain/entities/episode_quality.py",
            "noveler/domain/entities/episode_metadata.py",
        ]

        existing_files = sum(1 for file in required_files if (self.project_root / file).exists())

        return (existing_files / len(required_files)) * 100

    def _check_di_injection(self) -> float:
        """依存性注入の検証"""
        di_container_file = self.project_root / "scripts" / "infrastructure" / "di" / "simple_di_container.py"
        cli_main_file = self.project_root / "scripts" / "presentation" / "cli" / "novel_cli.py"

        if not di_container_file.exists():
            return 0.0

        if not cli_main_file.exists():
            return 50.0

        try:
            content = cli_main_file.read_text(encoding="utf-8")
            if "configure_dependencies" in content:
                return 100.0
            return 75.0
        except Exception:
            return 50.0

    def _check_bounded_context(self) -> float:
        """境界コンテキストの検証"""
        # 設計ドキュメントの存在確認
        design_doc = self.project_root / "docs" / "architecture" / "bounded_context_redesign_phase2.md"
        return 100.0 if design_doc.exists() else 25.0

    def _check_architecture_tests(self) -> float:
        """アーキテクチャテストの検証"""
        # pytest-archonテストファイルの存在確認
        test_file = self.project_root / "tests" / "architecture" / "test_ddd_architecture_rules.py"
        file_exists = test_file.exists()

        # import-linter設定の確認
        import_linter_config = self.project_root / ".importlinter"
        config_exists = import_linter_config.exists()

        if file_exists and config_exists:
            return 100.0
        if file_exists or config_exists:
            return 50.0
        return 0.0

    def _check_continuous_monitoring(self) -> float:
        """継続監視システムの検証"""
        # このファイル自体とDDD統合システムの存在確認
        ddd_engine_file = self.project_root / "scripts" / "infrastructure" / "services" / "ddd_compliance_engine.py"
        quality_check_file = self.project_root / "scripts" / "tools" / "check_tdd_ddd_compliance.py"

        if ddd_engine_file.exists() and quality_check_file.exists():
            return 100.0
        if ddd_engine_file.exists() or quality_check_file.exists():
            return 70.0
        return 30.0

    def _check_performance_optimization(self) -> float:
        """パフォーマンス最適化の検証"""
        # キャッシュシステムの存在確認
        cache_file = self.project_root / "scripts" / "infrastructure" / "services" / "ddd_compliance_cache.py"
        return 80.0 if cache_file.exists() else 40.0

    def _calculate_simple_quality_score(self) -> float:
        """品質スコアの簡易計算"""
        score = 85.0  # ベーススコア

        # Pythonファイルの構文エラーチェック
        python_files = list(self.project_root.glob("noveler/**/*.py"))
        syntax_errors = 0

        for file_path in python_files[:20]:  # サンプル20ファイルをチェック
            try:
                content = file_path.read_text(encoding="utf-8")
                compile(content, str(file_path), "exec")
            except SyntaxError:
                syntax_errors += 1
            except Exception:
                continue

        # 構文エラーによる減点
        penalty = min(syntax_errors * 10, 50)
        return max(score - penalty, 30.0)

    def _count_simple_violations(self) -> tuple[int, int]:
        """簡易違反カウント"""
        arch_violations = 0
        dep_violations = 0

        # Domain層からのInfrastructure直接参照をチェック
        domain_dir = self.project_root / "scripts" / "domain"
        if domain_dir.exists():
            for py_file in domain_dir.glob("**/*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "from noveler.infrastructure" in content:
                        dep_violations += 1
                    if "from noveler.presentation" in content:
                        arch_violations += 1
                    if "from noveler.application" in content:
                        arch_violations += 1
                except Exception:
                    continue

        return arch_violations, dep_violations

    def _identify_critical_issues(self, phase_metrics: list[PhaseMetrics]) -> list[str]:
        """重要な問題の特定"""
        issues = []

        for metrics in phase_metrics:
            if metrics.completion_percentage < 50:
                issues.append(f"{metrics.phase_name}の進捗が50%未満 ({metrics.completion_percentage:.1f}%)")

            if metrics.architecture_violations > 5:
                issues.append(f"{metrics.phase_name}でアーキテクチャ違反が多数 ({metrics.architecture_violations}件)")

            if metrics.quality_score < 70:
                issues.append(f"{metrics.phase_name}の品質スコアが低下 ({metrics.quality_score:.1f}点)")

        return issues

    def _suggest_next_actions(self, phase_metrics: list[PhaseMetrics]) -> list[str]:
        """次のアクション提案"""
        actions = []

        for metrics in phase_metrics:
            if metrics.completion_percentage < 80:
                actions.append(f"{metrics.phase_name}: 残りタスクの優先実行を推奨")

        if not actions:
            actions.append("全フェーズ順調に進捗中。継続監視を維持")

        return actions

    def _calculate_overall_progress(self, phase_metrics: list[PhaseMetrics]) -> float:
        """全体進捗の計算"""
        if not phase_metrics:
            return 0.0

        total_progress = sum(m.completion_percentage for m in phase_metrics)
        return total_progress / len(phase_metrics)

    def _save_monitoring_results(self, status: StagedImprovementStatus) -> None:
        """監視結果の保存"""
        result_file = self.cache_dir / "latest_status.json"
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(asdict(status), f, indent=2, ensure_ascii=False, default=str)


def main():
    """メイン実行"""

    parser = argparse.ArgumentParser(description="簡易版段階的改善監視システム")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--output", type=Path, help="結果出力ファイル")

    args = parser.parse_args()

    monitor = SimpleStagedImprovementMonitor(args.project_root)
    status = monitor.monitor_staged_improvements()

    # 結果の表示
    logger = get_logger(__name__)
    logger.info("\n🎯 段階的改善監視結果")
    logger.info(f"全体進捗: {status.overall_progress:.1f}%")
    logger.info(f"フェーズ数: {len(status.phase_metrics)}")
    logger.info(f"重要な問題: {len(status.critical_issues)}件")

    for i, metrics in enumerate(status.phase_metrics, 1):
        logger.info(f"\nPhase {i}: {metrics.phase_name} ({metrics.week_range})")
        logger.info(f"  進捗: {metrics.completion_percentage:.1f}%")
        logger.info(f"  品質: {metrics.quality_score:.1f}点")
        logger.info(f"  違反: {metrics.architecture_violations + metrics.dependency_violations}件")

    if status.critical_issues:
        logger.warning("\n⚠️ 重要な問題:")
        for issue in status.critical_issues:
            logger.warning(f"  - {issue}")

    if status.next_actions:
        logger.info("\n📋 推奨アクション:")
        for action in status.next_actions:
            logger.info(f"  - {action}")

    # ファイル出力
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as f:
            json.dump(asdict(status), f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"\n💾 結果をファイルに保存: {args.output}")


if __name__ == "__main__":
    main()
