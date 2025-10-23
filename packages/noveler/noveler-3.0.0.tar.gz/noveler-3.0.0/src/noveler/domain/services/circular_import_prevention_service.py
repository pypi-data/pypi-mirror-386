#!/usr/bin/env python3

"""Domain.services.circular_import_prevention_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""循環インポート予防ドメインサービス

仕様書: SPEC-CIRCULAR-IMPORT-DETECTION-001
"""


from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from noveler.domain.entities.circular_import_detector import CircularDetectionResult, CircularImportDetector
from noveler.domain.value_objects.import_statement import ImportStatement

# B20準拠: logger依存削除（純粋関数化）


@dataclass
class ASTAnalysisResult:
    """AST解析結果"""
    imports: list[ImportStatement]
    functions: list[str]
    classes: list[str]


class ASTAnalysisPort(Protocol):
    """AST解析アダプタープロトコル"""

    def analyze_file(self, file_path: Path) -> ASTAnalysisResult:
        """単一ファイルの分析"""
        ...

    def analyze_project(self, include_patterns: list[str] | None = None) -> dict[Path, ASTAnalysisResult]:
        """プロジェクト全体の分析"""
        ...


@dataclass
class PreventionAnalysisRequest:
    """予防分析リクエスト"""

    target_files: list[Path] | None = None  # 特定ファイルのみ分析
    include_external: bool = False  # 外部モジュール依存も含める
    risk_threshold: float = 50.0  # リスクしきい値
    generate_fixes: bool = True  # 修正提案を生成するか


@dataclass
class PreventionAnalysisResult:
    """予防分析結果"""

    detection_result: CircularDetectionResult
    prevention_recommendations: list[str]
    implementation_safety_score: float  # 0-100
    critical_issues: list[str]
    automated_fixes: list[dict[str, str]]  # ファイル → 修正内容

    def is_safe_to_implement(self) -> bool:
        """実装安全性の判定"""
        return (
            self.implementation_safety_score >= 70.0
            and len(self.critical_issues) == 0
            and len(self.detection_result.get_critical_paths()) == 0
        )


class CircularImportPreventionService:
    """循環インポート予防ドメインサービス"""

    def __init__(self, project_root: Path, ast_analyzer: ASTAnalysisPort) -> None:
        """初期化"""
        self.project_root = project_root
        self.ast_analyzer = ast_analyzer
        self.detector = CircularImportDetector(project_root)

    def analyze_current_state(self, request: PreventionAnalysisRequest) -> PreventionAnalysisResult:
        """現在の状態分析 - B20準拠純粋関数化"""

        # インポート文の抽出
        import_statements = self._extract_import_statements(request)

        # 循環検出
        detection_result = self.detector.detect_circular_imports(import_statements, cache_key="current_state_analysis")

        # 予防推奨事項の生成
        recommendations = self._generate_prevention_recommendations(detection_result)

        # 安全性スコアの計算
        safety_score = self._calculate_implementation_safety_score(detection_result)

        # 重要問題の特定
        critical_issues = self._identify_critical_issues(detection_result)

        # 自動修正の生成
        automated_fixes = self._generate_automated_fixes(detection_result) if request.generate_fixes else []

        return PreventionAnalysisResult(
            detection_result=detection_result,
            prevention_recommendations=recommendations,
            implementation_safety_score=safety_score,
            critical_issues=critical_issues,
            automated_fixes=automated_fixes,
        )

        # B20準拠: ログ出力は上位層の責務

    def validate_new_implementation(
        self, implementation_plan: dict[str, str], target_layer: str = "domain"
    ) -> tuple[bool, list[str], float]:
        """新規実装の事前検証"""
        # B20準拠: 副作用をImperative Shellに委譲

        validation_results = []
        overall_risk_score = 0.0

        # 既存のインポート文を取得
        existing_imports = self._get_existing_imports()

        # 各実装ファイルに対して検証
        for file_path_str, implementation_content in implementation_plan.items():
            file_path = Path(file_path_str)  # TODO: IPathServiceを使用するように修正

            # 実装内容から予想インポート文を抽出
            predicted_imports = self._predict_imports_from_content(implementation_content, file_path)

            # 各予想インポートのリスク評価
            for predicted_import in predicted_imports:
                risk_score, warnings = self.detector.predict_new_import_risk(predicted_import, existing_imports)

                overall_risk_score = max(overall_risk_score, risk_score)

                if risk_score > 70.0:
                    validation_results.extend(warnings)
                    validation_results.append(
                        f"⚠️ 高リスクインポート: {predicted_import.module_name} (リスク: {risk_score:.1f})"
                    )

        # DDD層配置の検証
        layer_validation = self._validate_layer_placement(implementation_plan, target_layer)
        validation_results.extend(layer_validation)

        is_safe = overall_risk_score < 50.0 and len(validation_results) == 0

        return is_safe, validation_results, overall_risk_score

    def suggest_safe_implementation_pattern(
        self, feature_name: str, required_dependencies: list[str], target_layer: str
    ) -> dict[str, str]:
        """安全な実装パターンの提案"""
        # B20準拠: パターン提案は純粋関数として実装

        patterns = {}

        # DDD層別の安全パターン
        if target_layer == "domain":
            patterns.update(self._suggest_domain_patterns(feature_name, required_dependencies))
        elif target_layer == "application":
            patterns.update(self._suggest_application_patterns(feature_name, required_dependencies))
        elif target_layer == "infrastructure":
            patterns.update(self._suggest_infrastructure_patterns(feature_name, required_dependencies))

        # 共通の安全パターン
        patterns.update(self._suggest_common_safe_patterns(feature_name))

        return patterns

    def generate_prevention_checklist(self, implementation_context: dict[str, str]) -> list[dict[str, str]]:
        """予防チェックリストの生成"""
        checklist = [
            {
                "category": "インポート設計",
                "item": "scriptsプレフィックスの使用確認",
                "description": "全てのローカルインポートでscripts.プレフィックスを使用",
            },
            {
                "category": "インポート設計",
                "item": "相対インポート回避確認",
                "description": "from noveler.domain.services import を使わず、絶対インポートを使用",
            },
            {
                "category": "DDD準拠",
                "item": "層間依存関係確認",
                "description": "上位層から下位層のみ依存することを確認",
            },
            {
                "category": "DDD準拠",
                "item": "Protocol-based DI検討",
                "description": "直接クラス依存ではなく、プロトコル経由での依存注入を検討",
            },
            {
                "category": "循環予防",
                "item": "双方向依存チェック",
                "description": "AとBが相互に依存していないかチェック",
            },
            {
                "category": "循環予防",
                "item": "共通基底の抽出検討",
                "description": "循環リスクがある場合は共通インターフェースの抽出を検討",
            },
        ]

        # 実装コンテキストに応じたカスタマイズ
        for file_path in implementation_context:
            if "service" in file_path.lower():
                checklist.append(
                    {
                        "category": "サービス設計",
                        "item": f"{file_path}の責務単一化",
                        "description": "サービスクラスが単一責務を持つことを確認",
                    }
                )

        return checklist

    def _extract_import_statements(self, request: PreventionAnalysisRequest) -> list[ImportStatement]:
        """インポート文の抽出"""
        import_statements = []

        if request.target_files:
            # 指定ファイルのみ分析
            for file_path in request.target_files:
                if file_path.exists() and file_path.suffix == ".py":
                    analysis_result = self.ast_analyzer.analyze_file(file_path)
                    import_statements.extend(analysis_result.imports)
        else:
            # プロジェクト全体を分析
            analysis_results = self.ast_analyzer.analyze_project()
            for file_result in analysis_results.values():
                import_statements.extend(file_result.imports)

        # 外部モジュールのフィルタリング
        if not request.include_external:
            import_statements = [
                stmt for stmt in import_statements if stmt.import_scope in ["LOCAL", "RELATIVE"]
            ]

        return import_statements

    def _generate_prevention_recommendations(self, detection_result: CircularDetectionResult) -> list[str]:
        """予防推奨事項の生成"""
        recommendations = []

        if not detection_result.circular_paths:
            recommendations.append("✅ 現在循環依存は検出されていません")
            recommendations.append("💡 このまま適切な設計パターンを維持してください")
        else:
            recommendations.append(f"⚠️ {len(detection_result.circular_paths)}件の循環依存を検出")

            # 高リスク循環への対応
            critical_paths = detection_result.get_critical_paths()
            if critical_paths:
                recommendations.append(f"🚨 {len(critical_paths)}件の高リスク循環を優先修正してください")
                for path in critical_paths:
                    recommendations.append(f"   • {' → '.join(path.modules)}")

        # 一般的な予防策
        recommendations.extend(
            [
                "🏗️ Protocol-based依存注入の活用を推奨",
                "📐 DDD層アーキテクチャの厳守",
                "🔍 実装前のCODEMAP確認の徹底",
                "⚡ CI/CDでの循環検出自動化",
            ]
        )

        return recommendations

    def _calculate_implementation_safety_score(self, detection_result: CircularDetectionResult) -> float:
        """実装安全性スコアの計算"""
        base_score = 100.0

        # 循環パス数に応じた減点
        cycles_penalty = len(detection_result.circular_paths) * 15.0
        base_score -= cycles_penalty

        # 高リスク循環の追加減点
        critical_cycles_penalty = len(detection_result.get_critical_paths()) * 25.0
        base_score -= critical_cycles_penalty

        # 全体的なリスクレベルに応じた減点
        overall_risk_penalty = detection_result.get_total_risk_score()
        base_score -= overall_risk_penalty

        return max(0.0, base_score)

    def _identify_critical_issues(self, detection_result: CircularDetectionResult) -> list[str]:
        """重要問題の特定"""
        critical_issues = []

        # 高リスク循環
        critical_paths = detection_result.get_critical_paths()
        for path in critical_paths:
            critical_issues.append(f"高リスク循環({path.risk_level}/5): {' → '.join(path.modules)}")

        # 層違反を含む循環
        for path in detection_result.circular_paths:
            has_layer_violation = any(self._is_layer_violation_import(stmt) for stmt in path.import_chain)

            if has_layer_violation:
                critical_issues.append(f"DDD層違反循環: {' → '.join(path.modules)}")

        return critical_issues

    def _generate_automated_fixes(self, detection_result: CircularDetectionResult) -> list[dict[str, str]]:
        """自動修正の生成"""
        fixes = []

        for path in detection_result.circular_paths:
            for suggestion in path.fix_suggestions:
                if "相対インポート" in suggestion:
                    fixes.append({"type": "relative_to_absolute", "description": suggestion, "modules": path.modules})
                elif "scriptsプレフィックス" in suggestion:
                    fixes.append({"type": "add_scripts_prefix", "description": suggestion, "modules": path.modules})

        return fixes

    def _get_existing_imports(self) -> list[ImportStatement]:
        """既存インポート文の取得"""
        analysis_results = self.ast_analyzer.analyze_project()
        all_imports = []
        for result in analysis_results.values():
            all_imports.extend(result.imports)
        return all_imports

    def _predict_imports_from_content(self, content: str, file_path: Path) -> list[ImportStatement]:
        """実装内容から予想インポート文を抽出"""
        # 簡易的な実装（実際にはより高度な解析が必要）
        predicted_imports = []

        # 一般的なインポートパターンをチェック

        for line_no, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line.startswith(("from ", "import ")):
                # 基本的なインポート文の解析
                if "from " in line and " import " in line:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] == "from" and parts[2] == "import":
                        module_name = parts[1]
                        imported_names = [parts[3]]  # 簡易版

                        predicted_imports.append(
                            ImportStatement(
                                module_name=module_name,
                                imported_names=imported_names,
                                import_type="FROM",
                                import_scope=self._determine_scope(module_name),
                                source_file=file_path,
                                line_number=line_no,
                                statement_text=line,
                            )
                        )

        return predicted_imports

    def _determine_scope(self, module_name: str) -> str:
        """モジュール名からスコープを判定"""
        if module_name.startswith("noveler."):
            return "LOCAL"
        if module_name.startswith("."):
            return "RELATIVE"
        return "THIRD_PARTY"

    def _validate_layer_placement(self, implementation_plan: dict[str, str], target_layer: str) -> list[str]:
        """層配置の検証"""
        violations = []

        layer_hierarchy = {"domain": 0, "application": 1, "infrastructure": 2, "presentation": 3}
        layer_hierarchy.get(target_layer, 999)

        for file_path_str in implementation_plan:
            # ファイルパスから配置層を推測
            if f"/{target_layer}/" not in file_path_str:
                violations.append(f"⚠️ ファイル配置層不一致: {file_path_str} (期待: {target_layer}層)")

        return violations

    def _suggest_domain_patterns(self, feature_name: str, dependencies: list[str]) -> dict[str, str]:
        """Domain層安全パターン"""
        return {
            "interface_segregation": "必要最小限のインターフェースのみ依存",
            "value_object_immutability": "Value Objectの不変性確保",
            "aggregate_consistency": "集約内部での一貫性保証",
        }

    def _suggest_application_patterns(self, feature_name: str, dependencies: list[str]) -> dict[str, str]:
        """Application層安全パターン"""
        return {
            "use_case_orchestration": "UseCase による処理フロー制御",
            "repository_abstraction": "Repositoryインターフェース経由のデータアクセス",
            "domain_service_delegation": "Domain Service への処理委譲",
        }

    def _suggest_infrastructure_patterns(self, feature_name: str, dependencies: list[str]) -> dict[str, str]:
        """Infrastructure層安全パターン"""
        return {
            "adapter_pattern": "外部システムとのアダプター実装",
            "repository_implementation": "Repository インターフェース実装",
            "dependency_injection": "DIコンテナによる依存注入",
        }

    def _suggest_common_safe_patterns(self, feature_name: str) -> dict[str, str]:
        """共通安全パターン"""
        return {
            "protocol_based_di": "Protocol-basedの依存注入活用",
            "factory_pattern": "Factoryパターンによるインスタンス生成",
            "observer_pattern": "イベント駆動による疎結合",
        }

    def _is_layer_violation_import(self, import_stmt: ImportStatement) -> bool:
        """層違反インポートの判定"""
        # import_statement.py の is_ddd_layer_violation を利用
        return import_stmt.is_ddd_layer_violation("")
