#!/usr/bin/env python3
"""依存関係分析 Functional Core
B20準拠: 純粋関数による依存関係分析ロジック
Functional Core/Imperative Shell パターン適用
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ViolationType(Enum):
    """違反タイプ定義"""
    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    EXTERNAL_DEPENDENCY = "external_dependency"


@dataclass
class AnalysisMetrics:
    """分析メトリクス（不変データ）"""
    total_violations: int
    layer_violations: int
    circular_dependencies: int
    external_dependencies: int

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（純粋関数）"""
        return {
            "total_violations": self.total_violations,
            "layer_violations": self.layer_violations,
            "circular_dependencies": self.circular_dependencies,
            "external_dependencies": self.external_dependencies,
            "analysis_types": ["layer", "circular", "external"]
        }


class DependencyAnalyzer:
    """依存関係分析純粋関数クラス

    Functional Core原則:
    - 副作用なし
    - 決定論的（同じ入力→同じ出力）
    - 外部依存なし
    """

    @staticmethod
    def is_pure_function() -> bool:
        """このクラスが純粋関数であることを示すマーカー"""
        return True

    @staticmethod
    def calculate_metrics(analysis_results: dict) -> AnalysisMetrics:
        """分析結果からメトリクスを計算（純粋関数）

        Args:
            analysis_results: 分析結果の辞書

        Returns:
            AnalysisMetrics: 計算されたメトリクス
        """
        layer_violations = 0
        circular_dependencies = 0
        external_dependencies = 0

        for result in analysis_results.values():
            violations = result.get("violations", [])
            for violation in violations:
                violation_type = violation.get("type")
                if violation_type == ViolationType.LAYER_VIOLATION.value:
                    layer_violations += 1
                elif violation_type == ViolationType.CIRCULAR_DEPENDENCY.value:
                    circular_dependencies += 1
                elif violation_type == ViolationType.EXTERNAL_DEPENDENCY.value:
                    external_dependencies += 1

        total_violations = layer_violations + circular_dependencies + external_dependencies

        return AnalysisMetrics(
            total_violations=total_violations,
            layer_violations=layer_violations,
            circular_dependencies=circular_dependencies,
            external_dependencies=external_dependencies
        )

    @staticmethod
    def format_report_data(results: dict, metrics: AnalysisMetrics) -> dict[str, Any]:
        """レポート用データを整形（純粋関数）

        Args:
            results: 分析結果
            metrics: メトリクス

        Returns:
            dict: 整形されたレポートデータ
        """
        return {
            "summary": {
                "total_violations": metrics.total_violations,
                "by_type": {
                    "layer": metrics.layer_violations,
                    "circular": metrics.circular_dependencies,
                    "external": metrics.external_dependencies
                }
            },
            "details": results,
            "recommendations": DependencyAnalyzer._generate_recommendations(metrics)
        }

    @staticmethod
    def _generate_recommendations(metrics: AnalysisMetrics) -> list[str]:
        """推奨事項を生成（純粋関数）

        Args:
            metrics: 分析メトリクス

        Returns:
            list[str]: 推奨事項リスト
        """
        recommendations = []

        if metrics.layer_violations > 0:
            recommendations.append("レイヤー違反を修正してください（必須）")

        if metrics.circular_dependencies > 0:
            recommendations.append("循環依存を解決してください（必須）")

        if metrics.external_dependencies > 0:
            recommendations.append("ドメイン層の外部依存を削減してください（推奨）")

        if metrics.total_violations == 0:
            recommendations.append("🎉 依存関係の問題は検出されませんでした！")

        return recommendations

    @staticmethod
    def determine_severity(violation_type: ViolationType) -> str:
        """違反の重要度を判定（純粋関数）

        Args:
            violation_type: 違反タイプ

        Returns:
            str: 重要度（error/warning）
        """
        if violation_type in (ViolationType.LAYER_VIOLATION, ViolationType.CIRCULAR_DEPENDENCY):
            return "error"
        return "warning"
