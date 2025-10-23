"""Infrastructure.services.ddd_compliance_engine
Where: Infrastructure service enforcing DDD compliance rules.
What: Analyses project structure, detects violations, and produces reports.
Why: Helps maintain architectural boundaries over time.
"""

from noveler.presentation.shared.shared_utilities import console

"DDD準拠性検証エンジン\n\n仕様書: SPEC-DDD-AUTO-COMPLIANCE-001\n包括的DDD準拠性検証エンジンの実装\n"
import ast
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_unified_file_storage import FileContentType
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.ddd_compliance_cache import DDDComplianceCacheManager
from noveler.infrastructure.storage import UnifiedFileStorageService


class ViolationSeverity(Enum):
    """違反重要度"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ValidationLevel(Enum):
    """検証レベル"""

    STRICT = "STRICT"
    MODERATE = "MODERATE"
    BASIC = "BASIC"


@dataclass
class DDDViolation:
    """DDD違反情報"""

    file_path: str
    line_number: int
    violation_type: str
    severity: ViolationSeverity
    description: str
    recommendation: str
    rule_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """DDD準拠性レポート"""

    timestamp: datetime
    project_root: str
    validation_level: ValidationLevel
    total_files_analyzed: int
    violations: list[DDDViolation]
    compliance_percentage: float
    layer_compliance: dict[str, float]
    summary: dict[str, Any]


class LayerType(Enum):
    """DDD層タイプ"""

    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"
    TOOLS = "tools"
    UTILITIES = "utilities"
    UNKNOWN = "unknown"


class DDDComplianceEngine:
    """DDD準拠性検証エンジン

    責務:
        - 包括的DDD準拠性検証
        - 層間依存関係分析
        - インターフェース抽象化チェック
        - リアルタイム違反検出
        - 品質メトリクス算出

    設計原則:
        - 厳密なDDD原則遵守
        - 拡張可能なルールシステム
        - パフォーマンス効率性
    """

    def __init__(self, project_root: Path, validation_level: ValidationLevel = ValidationLevel.STRICT) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            validation_level: 検証レベル
        """
        self.project_root = project_root
        self.validation_level = validation_level
        self.logger = get_logger(__name__)
        config_manager = get_configuration_manager()
        self.config = config_manager.get_configuration()
        self.layer_directories = {
            LayerType.DOMAIN: ["noveler/domain", "scripts/domain"],
            LayerType.APPLICATION: ["noveler/application", "scripts/application"],
            LayerType.INFRASTRUCTURE: ["noveler/infrastructure", "scripts/infrastructure"],
            LayerType.PRESENTATION: ["noveler/presentation", "scripts/presentation"],
            LayerType.TOOLS: ["noveler/tools", "scripts/tools"],
            LayerType.UTILITIES: ["noveler/utilities", "scripts/utilities"],
        }
        self._initialize_dependency_rules()
        self._initialize_required_interfaces()

    def _generate_candidate_paths(self, relative_path: str) -> list[Path]:
        """候補となるディレクトリパスを生成"""
        candidates = []
        bases = [
            self.project_root,
            self.project_root / "src",
            self.project_root / "00_ガイド",
            self.project_root / "00_ガイド" / "src",
        ]
        for base in bases:
            candidate = base / relative_path
            candidates.append(candidate)
        return candidates

    def _initialize_dependency_rules(self) -> None:
        """依存関係ルールの初期化"""
        self.dependency_rules = {
            LayerType.DOMAIN: {
                "allowed_patterns": [
                    "^typing",
                    "^dataclasses",
                    "^abc",
                    "^enum",
                    "^pathlib",
                    "^scripts\.domain",
                    "^noveler\.domain",
                    "^datetime",
                    "^uuid",
                    "^decimal",
                ],
                "forbidden_patterns": [
                    "^scripts\.application",
                    "^noveler\.application",
                    "^scripts\.infrastructure",
                    "^noveler\.infrastructure",
                    "^scripts\.presentation",
                    "^noveler\.presentation",
                    "^scripts\.tools",
                    "^noveler\.tools",
                    "^scripts\.utilities",
                    "^noveler\.utilities",
                ],
            },
            LayerType.APPLICATION: {
                "allowed_patterns": [
                    "^scripts\.domain",
                    "^noveler\.domain",
                    "^typing",
                    "^dataclasses",
                    "^abc",
                    "^asyncio",
                    "^logging",
                ],
                "forbidden_patterns": [
                    "^scripts\.infrastructure\.(?!factories|adapters)",
                    "^noveler\.infrastructure\.(?!factories|adapters)",
                    "^scripts\.presentation",
                    "^noveler\.presentation",
                    "^scripts\.tools",
                    "^noveler\.tools",
                ],
            },
            LayerType.INFRASTRUCTURE: {
                "allowed_patterns": [
                    "^scripts\.domain",
                    "^noveler\.domain",
                    "^scripts\.application",
                    "^noveler\.application",
                    ".*",
                ],
                "forbidden_patterns": [
                    "^scripts\.presentation",
                    "^noveler\.presentation",
                ],
            },
            LayerType.PRESENTATION: {
                "allowed_patterns": [
                    "^scripts\.application",
                    "^noveler\.application",
                    "^scripts\.domain\.interfaces",
                    "^noveler\.domain\.interfaces",
                    "^scripts\.infrastructure\.factories",
                    "^noveler\.infrastructure\.factories",
                    "^rich",
                    "^click",
                    "^argparse",
                ],
                "forbidden_patterns": [
                    "^scripts\.infrastructure\.services",
                    "^noveler\.infrastructure\.services",
                    "^scripts\.infrastructure\.adapters",
                    "^noveler\.infrastructure\.adapters",
                    "^scripts\.tools",
                    "^noveler\.tools",
                ],
            },
        }

    def _initialize_required_interfaces(self) -> None:
        """必須インターフェースの初期化"""
        self.required_interfaces = [
            {
                "candidate_paths": [
                    "noveler/domain/interfaces/repository_protocol.py",
                    "scripts/domain/interfaces/repository_protocol.py",
                ],
                "interface_name": "IRepository",
                "description": "リポジトリ抽象化インターフェース",
            },
            {
                "candidate_paths": [
                    "noveler/domain/interfaces/event_publisher_protocol.py",
                    "scripts/domain/interfaces/event_publisher_protocol.py",
                ],
                "interface_name": "IEventPublisher",
                "description": "イベント発行者インターフェース",
            },
            {
                "candidate_paths": [
                    "noveler/domain/interfaces/path_service_protocol.py",
                    "scripts/domain/interfaces/path_service_protocol.py",
                ],
                "interface_name": "IPathService",
                "description": "パスサービス抽象化",
            },
        ]

    async def analyze_project_compliance(self) -> ComplianceReport:
        """プロジェクト全体のDDD準拠性分析

        Returns:
            ComplianceReport: 準拠性レポート
        """
        console.print(f"DDD準拠性分析開始 - レベル: {self.validation_level.value}")
        violations: list[Any] = []
        total_files = 0
        layer_compliance = {}
        for layer_type, rel_paths in self.layer_directories.items():
            layer_violations: list[DDDViolation] = []
            layer_file_count = 0
            for rel_path in rel_paths:
                for candidate in self._generate_candidate_paths(rel_path):
                    if candidate.exists():
                        layer_viols, file_count = await self._analyze_layer(candidate, layer_type)
                        layer_violations.extend(layer_viols)
                        layer_file_count += file_count
            if layer_file_count > 0:
                total_files += layer_file_count
                layer_compliance[layer_type.value] = self._calculate_layer_compliance(layer_violations, layer_file_count)
                violations.extend(layer_violations)
        interface_violations = await self._check_interface_abstractions()
        violations.extend(interface_violations)
        di_violations = await self._check_di_compliance()
        violations.extend(di_violations)
        compliance_percentage = self._calculate_overall_compliance(violations, total_files)
        return ComplianceReport(
            timestamp=datetime.now(timezone.utc),
            project_root=str(self.project_root),
            validation_level=self.validation_level,
            total_files_analyzed=total_files,
            violations=violations,
            compliance_percentage=compliance_percentage,
            layer_compliance=layer_compliance,
            summary=self._generate_summary(violations, layer_compliance),
        )

    async def _analyze_layer(self, layer_dir: Path, layer_type: LayerType) -> tuple[list[DDDViolation], int]:
        """特定層の分析

        Args:
            layer_dir: 層ディレクトリ
            layer_type: 層タイプ

        Returns:
            違反リストとファイル数のタプル
        """
        violations: list[Any] = []
        file_count = 0
        for py_file in layer_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            file_count += 1
            file_violations = await self._analyze_file(py_file, layer_type)
            violations.extend(file_violations)
        return (violations, file_count)

    async def _analyze_file(self, file_path: Path, layer_type: LayerType) -> list[DDDViolation]:
        """単一ファイルの分析

        Args:
            file_path: ファイルパス
            layer_type: 層タイプ

        Returns:
            違反リスト
        """
        cache_manager = DDDComplianceCacheManager(self.project_root)
        if cache_manager.is_file_cached(file_path):
            cached_violations = cache_manager.get_cached_violations(file_path)
            console.print(f"キャッシュヒット: {file_path}")
            return cached_violations
        start_time = time.time()
        violations: list[Any] = []
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            violations.extend(self._analyze_dependencies(file_path, tree, layer_type))
            violations.extend(self._analyze_class_design(file_path, tree, layer_type))
            violations.extend(self._analyze_function_design(file_path, tree, layer_type))
        except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
            console.print(f"ファイル分析エラー: {file_path} - {e}")
        analysis_duration = time.time() - start_time
        cache_manager.cache_file_analysis(file_path, violations, analysis_duration)
        return violations

    def _analyze_dependencies(self, file_path: Path, tree: ast.AST, layer_type: LayerType) -> list[DDDViolation]:
        """依存関係分析

        Args:
            file_path: ファイルパス
            tree: ASTツリー
            layer_type: 層タイプ

        Returns:
            依存関係違反リスト
        """
        violations: list[Any] = []
        rules = self.dependency_rules.get(layer_type, {})
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                violation = self._check_import_compliance(file_path, node, layer_type, rules)
                if violation:
                    violations.append(violation)
            elif isinstance(node, ast.Import):
                # ast.Import ノードも処理
                for alias in node.names:
                    violation = self._check_import_name_compliance(file_path, alias.name, node.lineno, layer_type, rules)
                    if violation:
                        violations.append(violation)
        return violations

    def _check_import_compliance(
        self, file_path: Path, import_node: ast.ImportFrom, layer_type: LayerType, rules: dict[str, list[str]]
    ) -> DDDViolation | None:
        """インポート準拠性チェック

        Args:
            file_path: ファイルパス
            import_node: インポートノード
            layer_type: 層タイプ
            rules: 依存関係ルール

        Returns:
            違反情報（違反がない場合はNone）
        """
        module_name = import_node.module
        if module_name is None:
            return None
        for forbidden_pattern in rules.get("forbidden_patterns", []):
            if re.match(forbidden_pattern, module_name):
                severity = self._determine_violation_severity(layer_type, module_name)
                try:
                    relative_path = file_path.relative_to(self.project_root)
                except ValueError:
                    relative_path = file_path
                return DDDViolation(
                    file_path=str(relative_path),
                    line_number=import_node.lineno,
                    violation_type="FORBIDDEN_DEPENDENCY",
                    severity=severity,
                    description=f"{layer_type.value}層から{module_name}への依存は禁止されています",
                    recommendation=self._get_dependency_recommendation(layer_type, module_name),
                    rule_id=f"DEP_{layer_type.value.upper()}_001",
                    metadata={
                        "imported_module": module_name,
                        "layer": layer_type.value,
                        "pattern_matched": forbidden_pattern,
                    },
                )
        return None

    def _check_import_name_compliance(
        self, file_path: Path, module_name: str, line_number: int, layer_type: LayerType, rules: dict[str, list[str]]
    ) -> DDDViolation | None:
        """インポート名準拠性チェック（ast.Import用）

        Args:
            file_path: ファイルパス
            module_name: モジュール名
            line_number: 行番号
            layer_type: 層タイプ
            rules: 依存関係ルール

        Returns:
            違反情報（違反がない場合はNone）
        """
        for forbidden_pattern in rules.get("forbidden_patterns", []):
            if re.match(forbidden_pattern, module_name):
                severity = self._determine_violation_severity(layer_type, module_name)
                try:
                    relative_path = file_path.relative_to(self.project_root)
                except ValueError:
                    relative_path = file_path
                return DDDViolation(
                    file_path=str(relative_path),
                    line_number=line_number,
                    violation_type="FORBIDDEN_DEPENDENCY",
                    severity=severity,
                    description=f"{layer_type.value}層から{module_name}への依存は禁止されています",
                    recommendation=self._get_dependency_recommendation(layer_type, module_name),
                    rule_id=f"DEP_{layer_type.value.upper()}_001",
                    metadata={
                        "imported_module": module_name,
                        "layer": layer_type.value,
                        "pattern_matched": forbidden_pattern,
                    },
                )
        return None

    def _analyze_class_design(self, file_path: Path, tree: ast.AST, layer_type: LayerType) -> list[DDDViolation]:
        """クラス設計分析

        Args:
            file_path: ファイルパス
            tree: ASTツリー
            layer_type: 層タイプ

        Returns:
            クラス設計違反リスト
        """
        violations: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if layer_type == LayerType.DOMAIN:
                    violations.extend(self._check_domain_class_compliance(file_path, node))
                elif layer_type == LayerType.APPLICATION:
                    violations.extend(self._check_application_service_compliance(file_path, node))
        return violations

    def _check_domain_class_compliance(self, file_path: Path, class_node: ast.ClassDef) -> list[DDDViolation]:
        """ドメインクラス準拠性チェック

        Args:
            file_path: ファイルパス
            class_node: クラスノード

        Returns:
            ドメインクラス違反リスト
        """
        violations: list[Any] = []
        has_mutable_methods = False
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("set_") or any(
                    "=" in ast.unparse(stmt) for stmt in node.body if isinstance(stmt, ast.Assign)
                ):
                    has_mutable_methods = True
                    break
        if has_mutable_methods and "Entity" not in class_node.name:
            violations.append(
                DDDViolation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=class_node.lineno,
                    violation_type="DOMAIN_MUTABILITY",
                    severity=ViolationSeverity.MEDIUM,
                    description=f"ドメインクラス{class_node.name}に可変メソッドが検出されました",
                    recommendation="値オブジェクトは不変にし、エンティティの状態変更は意味のあるメソッドで行ってください",
                    rule_id="DOM_001",
                    metadata={"class_name": class_node.name},
                )
            )
        return violations

    def _check_application_service_compliance(self, file_path: Path, class_node: ast.ClassDef) -> list[DDDViolation]:
        """アプリケーションサービス準拠性チェック

        Args:
            file_path: ファイルパス
            class_node: クラスノード

        Returns:
            アプリケーションサービス違反リスト
        """
        violations: list[Any] = []
        if "UseCase" in class_node.name or "Service" in class_node.name:
            has_proper_di = False
            for node in ast.walk(class_node):
                if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                    if len(node.args.args) > 1:
                        has_proper_di = True
                    break
            if not has_proper_di:
                violations.append(
                    DDDViolation(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=class_node.lineno,
                        violation_type="MISSING_DEPENDENCY_INJECTION",
                        severity=ViolationSeverity.HIGH,
                        description=f"アプリケーションサービス{class_node.name}で依存性注入パターンが使用されていません",
                        recommendation="コンストラクタで依存関係を注入し、インターフェースに依存するようにしてください",
                        rule_id="APP_001",
                        metadata={"class_name": class_node.name},
                    )
                )
        return violations

    def _analyze_function_design(self, file_path: Path, tree: ast.AST, layer_type: LayerType) -> list[DDDViolation]:
        """関数設計分析

        Args:
            file_path: ファイルパス
            tree: ASTツリー
            layer_type: 層タイプ

        Returns:
            関数設計違反リスト
        """
        violations: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if layer_type == LayerType.DOMAIN:
                    violations.extend(self._check_function_purity(file_path, node))
        return violations

    def _check_function_purity(self, file_path: Path, func_node: ast.FunctionDef) -> list[DDDViolation]:
        """関数純粋性チェック

        Args:
            file_path: ファイルパス
            func_node: 関数ノード

        Returns:
            関数純粋性違反リスト
        """
        violations: list[Any] = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["print", "open", "input"]:
                        violations.append(
                            DDDViolation(
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=node.lineno,
                                violation_type="IMPURE_FUNCTION",
                                severity=ViolationSeverity.MEDIUM,
                                description=f"ドメイン関数{func_node.name}で副作用のある操作{node.func.id}が検出されました",
                                recommendation="ドメインロジックは純粋関数として実装し、副作用は外部に委譲してください",
                                rule_id="DOM_002",
                                metadata={"function_name": func_node.name, "impure_operation": node.func.id},
                            )
                        )
        return violations

    async def _check_interface_abstractions(self) -> list[DDDViolation]:
        """インターフェース抽象化チェック

        Returns:
            インターフェース抽象化違反リスト
        """
        violations: list[Any] = []
        for interface_info in self.required_interfaces:
            candidate_paths = []
            for rel_path in interface_info["candidate_paths"]:
                candidate_paths.extend(self._generate_candidate_paths(rel_path))
            if not any(path.exists() for path in candidate_paths):
                violations.append(
                    DDDViolation(
                        file_path=interface_info["candidate_paths"][0],
                        line_number=1,
                        violation_type="MISSING_INTERFACE",
                        severity=ViolationSeverity.HIGH,
                        description=f"必須インターフェース{interface_info['interface_name']}が存在しません",
                        recommendation=f"{interface_info['description']}を実装してください",
                        rule_id="INT_001",
                        metadata=interface_info,
                    )
                )
        return violations

    async def _check_di_compliance(self) -> list[DDDViolation]:
        """DI準拠性チェック

        Returns:
            DI準拠性違反リスト
        """
        violations: list[Any] = []
        candidate_dirs = []
        for rel_path in ["noveler/infrastructure/factories", "scripts/infrastructure/factories"]:
            candidate_dirs.extend(self._generate_candidate_paths(rel_path))
        if not any(directory.exists() for directory in candidate_dirs):
            violations.append(
                DDDViolation(
                    file_path="noveler/infrastructure/factories",
                    line_number=1,
                    violation_type="MISSING_FACTORY_PATTERN",
                    severity=ViolationSeverity.MEDIUM,
                    description="DIコンテナ/ファクトリーパターンの実装が見つかりません",
                    recommendation="noveler/infrastructure/factoriesディレクトリにファクトリークラスを実装してください",
                    rule_id="DI_001",
                    metadata={},
                )
            )
        return violations

    def _determine_violation_severity(self, layer_type: LayerType, module_name: str) -> ViolationSeverity:
        """違反重要度の決定

        Args:
            layer_type: 層タイプ
            module_name: モジュール名

        Returns:
            違反重要度
        """
        critical_patterns = [
            (LayerType.DOMAIN, "^scripts\.infrastructure"),
            (LayerType.DOMAIN, "^noveler\.infrastructure"),
            (LayerType.DOMAIN, "^scripts\.presentation"),
            (LayerType.DOMAIN, "^noveler\.presentation"),
            (LayerType.APPLICATION, "^scripts\.infrastructure\.services"),
            (LayerType.APPLICATION, "^noveler\.infrastructure\.services"),
        ]
        for pattern_layer, pattern in critical_patterns:
            if layer_type == pattern_layer and re.match(pattern, module_name):
                return ViolationSeverity.CRITICAL
        if layer_type == LayerType.PRESENTATION and any(keyword in module_name for keyword in ("noveler.infrastructure.services", "scripts.infrastructure.services")):
            return ViolationSeverity.HIGH
        return ViolationSeverity.MEDIUM

    def _get_dependency_recommendation(self, layer_type: LayerType, module_name: str) -> str:
        """依存関係推奨事項の取得

        Args:
            layer_type: 層タイプ
            module_name: モジュール名

        Returns:
            推奨事項
        """
        recommendations = {
            LayerType.DOMAIN: {
                "noveler.infrastructure": "ドメインインターフェースを定義し、インフラ層でアダプターとして実装してください",
                "noveler.application": "ドメインサービスとして実装するか、アプリケーションサービスに移動してください",
                "noveler.presentation": "プレゼンテーション関連のロジックをドメインから分離してください",
            },
            LayerType.APPLICATION: {
                "noveler.infrastructure.services": "インターフェース経由でアクセスし、DIコンテナで注入してください",
                "noveler.presentation": "プレゼンテーション層からアプリケーション層を呼び出すよう変更してください",
            },
            LayerType.PRESENTATION: {
                "noveler.infrastructure.services": "アプリケーション層経由でアクセスするか、DIファクトリーを使用してください"
            },
        }
        layer_recommendations = recommendations.get(layer_type, {})
        for pattern, recommendation in layer_recommendations.items():
            if pattern in module_name:
                return recommendation
        return f"{layer_type.value}層から{module_name}への直接依存を避け、適切な抽象化を行ってください"

    def _calculate_layer_compliance(self, violations: list[DDDViolation], file_count: int) -> float:
        """層別準拠率計算

        Args:
            violations: 違反リスト
            file_count: ファイル数

        Returns:
            準拠率（0.0-1.0）
        """
        if file_count == 0:
            return 1.0
        violation_weight = 0.0
        for violation in violations:
            if violation.severity == ViolationSeverity.CRITICAL:
                violation_weight += 1.0
            elif violation.severity == ViolationSeverity.HIGH:
                violation_weight += 0.7
            elif violation.severity == ViolationSeverity.MEDIUM:
                violation_weight += 0.4
            else:
                violation_weight += 0.1
        max_possible_violations = file_count * 1.0
        normalized_violations = min(violation_weight, max_possible_violations)
        return max(0.0, 1.0 - normalized_violations / max_possible_violations)

    def _calculate_overall_compliance(self, violations: list[DDDViolation], total_files: int) -> float:
        """全体準拠率計算

        Args:
            violations: 全違反リスト
            total_files: 総ファイル数

        Returns:
            全体準拠率（0.0-100.0）
        """
        if total_files == 0:
            return 100.0
        compliance = self._calculate_layer_compliance(violations, total_files)
        return compliance * 100.0

    def _generate_summary(self, violations: list[DDDViolation], layer_compliance: dict[str, float]) -> dict[str, Any]:
        """サマリー生成

        Args:
            violations: 違反リスト
            layer_compliance: 層別準拠率

        Returns:
            サマリー情報
        """
        severity_counts = {
            ViolationSeverity.CRITICAL.value: 0,
            ViolationSeverity.HIGH.value: 0,
            ViolationSeverity.MEDIUM.value: 0,
            ViolationSeverity.LOW.value: 0,
        }
        violation_types = {}
        for violation in violations:
            severity_counts[violation.severity.value] += 1
            if violation.violation_type not in violation_types:
                violation_types[violation.violation_type] = 0
            violation_types[violation.violation_type] += 1
        return {
            "total_violations": len(violations),
            "severity_breakdown": severity_counts,
            "violation_types": violation_types,
            "layer_compliance": layer_compliance,
            "validation_level": self.validation_level.value,
            "recommendations": self._generate_recommendations(violations),
        }

    def _generate_recommendations(self, violations: list[DDDViolation]) -> list[str]:
        """推奨事項生成

        Args:
            violations: 違反リスト

        Returns:
            推奨事項リスト
        """
        recommendations = []
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        if critical_violations:
            recommendations.append(f"クリティカル違反 {len(critical_violations)} 件の即座な修正が必要です")
        violation_patterns = {}
        for violation in violations:
            if violation.violation_type not in violation_patterns:
                violation_patterns[violation.violation_type] = 0
            violation_patterns[violation.violation_type] += 1
        for violation_type, count in violation_patterns.items():
            if count >= 3:
                recommendations.append(f"{violation_type}が{count}件検出されました。体系的な修正を検討してください")
        return recommendations

    async def export_report(self, report: ComplianceReport, output_path: Path, format_type: str = "json") -> None:
        """レポートエクスポート

        Args:
            report: 準拠性レポート
            output_path: 出力パス
            format_type: フォーマット（json/markdown）
        """
        if format_type == "json":
            await self._export_json_report(report, output_path)
        elif format_type == "markdown":
            await self._export_markdown_report(report, output_path)
        else:
            console.print(f"フォーマット {format_type} は未実装のため、markdownで出力します")
            await self._export_markdown_report(report, output_path)

    async def _export_json_report(self, report: ComplianceReport, output_path: Path) -> None:
        """JSONレポートエクスポート"""
        report_data: dict[str, Any] = {
            "timestamp": report.timestamp.isoformat(),
            "project_root": report.project_root,
            "validation_level": report.validation_level.value,
            "total_files_analyzed": report.total_files_analyzed,
            "compliance_percentage": report.compliance_percentage,
            "layer_compliance": report.layer_compliance,
            "summary": report.summary,
            "violations": [
                {
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "violation_type": v.violation_type,
                    "severity": v.severity.value,
                    "description": v.description,
                    "recommendation": v.recommendation,
                    "rule_id": v.rule_id,
                    "metadata": v.metadata,
                }
                for v in report.violations
            ],
        }
        # UnifiedFileStorageServiceを使用してJSONレポートを保存
        storage_service = UnifiedFileStorageService()
        storage_service.save(
            file_path=output_path,
            content=report_data,
            content_type=FileContentType.API_RESPONSE,
            metadata={
                "report_type": "ddd_compliance_json",
                "validation_level": report.validation_level.value,
                "compliance_percentage": report.compliance_percentage,
                "total_violations": len(report.violations),
            },
        )
        console.print(f"JSONレポートを出力しました: {output_path}")

    async def _export_markdown_report(self, report: ComplianceReport, output_path: Path) -> None:
        """Markdownレポートエクスポート"""
        markdown_content = f"# DDD準拠性レポート\n\n**生成日時**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n**プロジェクト**: {report.project_root}\n**検証レベル**: {report.validation_level.value}\n**分析ファイル数**: {report.total_files_analyzed}\n\n## 📊 準拠性サマリー\n\n**全体準拠率**: {report.compliance_percentage:.1f}%\n\n### 層別準拠率\n{self._format_layer_compliance_markdown(report.layer_compliance)}\n\n### 違反概要\n{self._format_violation_summary_markdown(report.summary)}\n\n## 🚨 検出された違反\n\n{self._format_violations_markdown(report.violations)}\n\n## 💡 推奨事項\n\n{self._format_recommendations_markdown(report.summary.get('recommendations', []))}\n"
        # UnifiedFileStorageServiceを使用してMarkdownレポートを保存
        storage_service = UnifiedFileStorageService()
        storage_service.save(
            file_path=output_path,
            content=markdown_content,
            content_type=FileContentType.MANUSCRIPT,
            metadata={
                "report_type": "ddd_compliance_markdown",
                "validation_level": report.validation_level.value,
                "compliance_percentage": report.compliance_percentage,
                "total_violations": len(report.violations),
            },
        )
        console.print(f"Markdownレポートを出力しました: {output_path}")

    def _format_layer_compliance_markdown(self, layer_compliance: dict[str, float]) -> str:
        """層別準拠率のMarkdown形式フォーマット"""
        lines = []
        for layer, compliance in layer_compliance.items():
            percentage = compliance * 100
            emoji = "✅" if percentage >= 95 else "⚠️" if percentage >= 80 else "❌"
            lines.append(f"- {emoji} **{layer}**: {percentage:.1f}%")
        return "\n".join(lines)

    def _format_violation_summary_markdown(self, summary: dict[str, Any]) -> str:
        """違反サマリーのMarkdown形式フォーマット"""
        severity_breakdown = summary.get("severity_breakdown", {})
        lines = []
        for severity, count in severity_breakdown.items():
            if count > 0:
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                lines.append(f"- {emoji} **{severity}**: {count}件")
        return "\n".join(lines) if lines else "- ✅ 違反は検出されませんでした"

    def _format_violations_markdown(self, violations: list[DDDViolation]) -> str:
        """違反詳細のMarkdown形式フォーマット"""
        if not violations:
            return "違反は検出されませんでした。"
        lines = []
        for violation in violations:
            severity_emoji = {
                ViolationSeverity.CRITICAL: "🔴",
                ViolationSeverity.HIGH: "🟠",
                ViolationSeverity.MEDIUM: "🟡",
                ViolationSeverity.LOW: "🟢",
            }.get(violation.severity, "⚪")
            lines.append(
                f"### {severity_emoji} {violation.violation_type}\n\n**ファイル**: `{violation.file_path}:{violation.line_number}`\n**重要度**: {violation.severity.value}\n**説明**: {violation.description}\n**推奨事項**: {violation.recommendation}\n**ルールID**: {violation.rule_id}\n"
            )
        return "\n".join(lines)

    def _format_recommendations_markdown(self, recommendations: list[str]) -> str:
        """推奨事項のMarkdown形式フォーマット"""
        if not recommendations:
            return "- 🎉 現在のコードベースは良好な状態です。"
        return "\n".join(f"- {rec}" for rec in recommendations)
