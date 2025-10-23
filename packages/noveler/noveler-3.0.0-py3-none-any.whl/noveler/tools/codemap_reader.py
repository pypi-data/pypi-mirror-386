"""
CODEMAP.yaml読み取りユーティリティ

CODEMAP.yamlを単一信頼源とした共通基盤コンポーネント定義の取得を提供。
動的コンプライアンス検証システムの基盤クラス。

Version: 1.0.0
Author: Claude Code
Date: 2025-09-09
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)

@dataclass
class ComponentDefinition:
    """共通基盤コンポーネント定義"""
    primary_module: str
    primary_function: str
    singleton: bool = False
    description: str = ""
    usage_pattern: str = ""
    alternatives: list[dict[str, str]] = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []

@dataclass
class ForbiddenPattern:
    """禁止パターン定義"""
    pattern: str
    severity: str
    message: str
    exceptions: list[str]
    suggested_fix: str = ""

@dataclass
class ComplianceThresholds:
    """コンプライアンス基準値"""
    console_shared_usage_rate: float
    logger_unified_usage_rate: float
    path_service_usage_rate: float
    error_handling_unified_rate: float
    console_duplication_max: int
    legacy_logging_max: int
    path_hardcoding_max: int

@dataclass
class MCPServerExceptions:
    """MCPサーバー例外定義"""
    path: str
    relaxed_thresholds: dict[str, float]
    allowed_patterns: list[str]

class CODEMAPReader:
    """
    CODEMAP.yaml読み取り・解析クラス

    共通基盤コンポーネント定義の動的取得を提供し、
    テストケースやチェックツールがCODEMAPを単一信頼源として使用できるようにする。
    """

    def __init__(self, codemap_path: Path | None = None) -> None:
        """
        CODEMAPReaderを初期化

        Args:
            codemap_path: CODEMAP.yamlのパス。指定されない場合はプロジェクトルートから自動検出
        """
        self.codemap_path = codemap_path or self._find_codemap_path()
        self._codemap_data: dict[str, Any] | None = None
        self._common_foundation: dict[str, Any] | None = None

    def _find_codemap_path(self) -> Path:
        """プロジェクトルートのCODEMAP.yamlを自動検出"""
        current_path = Path(__file__).resolve()

        # プロジェクトルートまで遡って検索
        for parent in current_path.parents:
            codemap_path = parent / "CODEMAP.yaml"
            if codemap_path.exists():
                logger.debug(f"CODEMAP.yaml found at: {codemap_path}")
                return codemap_path

        # フォールバック: 相対パスでの検索
        fallback_paths = [
            Path("CODEMAP.yaml"),
            Path("../CODEMAP.yaml"),
            Path("../../CODEMAP.yaml"),
            Path("../../../CODEMAP.yaml")
        ]

        for path in fallback_paths:
            if path.exists():
                logger.debug(f"CODEMAP.yaml found at fallback: {path.resolve()}")
                return path.resolve()

        msg = "CODEMAP.yaml not found. Please specify codemap_path explicitly."
        raise FileNotFoundError(
            msg
        )

    def _load_codemap(self) -> dict[str, Any]:
        """CODEMAP.yamlをロード（キャッシュ機能付き）"""
        if self._codemap_data is None:
            try:
                with open(self.codemap_path, encoding="utf-8") as f:
                    self._codemap_data = yaml.safe_load(f)
                logger.info(f"CODEMAP loaded from: {self.codemap_path}")
            except Exception as e:
                logger.exception(f"Failed to load CODEMAP.yaml: {e}")
                raise

        return self._codemap_data

    def _get_common_foundation(self) -> dict[str, Any]:
        """共通基盤セクションを取得（キャッシュ機能付き）"""
        if self._common_foundation is None:
            codemap = self._load_codemap()
            self._common_foundation = codemap.get("common_foundation", {})

            if not self._common_foundation:
                logger.warning("common_foundation section not found in CODEMAP.yaml")
                return {}

        return self._common_foundation

    def get_component_definition(self, component_name: str) -> ComponentDefinition | None:
        """
        指定されたコンポーネントの定義を取得

        Args:
            component_name: コンポーネント名（console, logger, path_service, error_handler）

        Returns:
            ComponentDefinition または None（見つからない場合）
        """
        common_foundation = self._get_common_foundation()
        components = common_foundation.get("components", {})

        if component_name not in components:
            logger.warning(f"Component '{component_name}' not found in CODEMAP")
            return None

        comp_data = components[component_name]
        return ComponentDefinition(
            primary_module=comp_data.get("primary_module", ""),
            primary_function=comp_data.get("primary_function", ""),
            singleton=comp_data.get("singleton", False),
            description=comp_data.get("description", ""),
            usage_pattern=comp_data.get("usage_pattern", ""),
            alternatives=comp_data.get("alternatives", [])
        )

    def get_all_component_definitions(self) -> dict[str, ComponentDefinition]:
        """全ての共通基盤コンポーネント定義を取得"""
        common_foundation = self._get_common_foundation()
        components = common_foundation.get("components", {})

        result = {}
        for name, comp_data in components.items():
            result[name] = ComponentDefinition(
                primary_module=comp_data.get("primary_module", ""),
                primary_function=comp_data.get("primary_function", ""),
                singleton=comp_data.get("singleton", False),
                description=comp_data.get("description", ""),
                usage_pattern=comp_data.get("usage_pattern", ""),
                alternatives=comp_data.get("alternatives", [])
            )

        return result

    def get_forbidden_patterns(self, component_name: str) -> list[ForbiddenPattern]:
        """
        指定されたコンポーネントの禁止パターンを取得

        Args:
            component_name: コンポーネント名

        Returns:
            ForbiddenPatternのリスト
        """
        common_foundation = self._get_common_foundation()
        forbidden_patterns = common_foundation.get("forbidden_patterns", {})

        if component_name not in forbidden_patterns:
            return []

        patterns = []
        for pattern_data in forbidden_patterns[component_name]:
            patterns.append(ForbiddenPattern(
                pattern=pattern_data.get("pattern", ""),
                severity=pattern_data.get("severity", "warning"),
                message=pattern_data.get("message", ""),
                exceptions=pattern_data.get("exceptions", []),
                suggested_fix=pattern_data.get("suggested_fix", "")
            ))

        return patterns

    def get_all_forbidden_patterns(self) -> dict[str, list[ForbiddenPattern]]:
        """全ての禁止パターンを取得"""
        common_foundation = self._get_common_foundation()
        forbidden_patterns = common_foundation.get("forbidden_patterns", {})

        result = {}
        for component_name, patterns in forbidden_patterns.items():
            component_patterns = []
            for pattern_data in patterns:
                component_patterns.append(ForbiddenPattern(
                    pattern=pattern_data.get("pattern", ""),
                    severity=pattern_data.get("severity", "warning"),
                    message=pattern_data.get("message", ""),
                    exceptions=pattern_data.get("exceptions", []),
                    suggested_fix=pattern_data.get("suggested_fix", "")
                ))
            result[component_name] = component_patterns

        return result

    def get_compliance_thresholds(self) -> ComplianceThresholds:
        """コンプライアンス基準値を取得"""
        common_foundation = self._get_common_foundation()
        thresholds = common_foundation.get("compliance_thresholds", {})

        return ComplianceThresholds(
            console_shared_usage_rate=thresholds.get("console_shared_usage_rate", 0.85),
            logger_unified_usage_rate=thresholds.get("logger_unified_usage_rate", 0.80),
            path_service_usage_rate=thresholds.get("path_service_usage_rate", 0.70),
            error_handling_unified_rate=thresholds.get("error_handling_unified_rate", 0.60),
            console_duplication_max=thresholds.get("console_duplication_max", 0),
            legacy_logging_max=thresholds.get("legacy_logging_max", 0),
            path_hardcoding_max=thresholds.get("path_hardcoding_max", 0)
        )

    def get_mcp_server_exceptions(self) -> MCPServerExceptions | None:
        """MCPサーバー例外定義を取得"""
        common_foundation = self._get_common_foundation()
        mcp_exceptions = common_foundation.get("mcp_server_exceptions", {})

        if not mcp_exceptions:
            return None

        return MCPServerExceptions(
            path=mcp_exceptions.get("path", "src/mcp_servers"),
            relaxed_thresholds=mcp_exceptions.get("relaxed_thresholds", {}),
            allowed_patterns=mcp_exceptions.get("allowed_patterns", [])
        )

    def is_file_in_mcp_server_path(self, file_path: str) -> bool:
        """指定されたファイルパスがMCPサーバーディレクトリ内かどうかを判定"""
        mcp_exceptions = self.get_mcp_server_exceptions()
        if not mcp_exceptions:
            return False

        return mcp_exceptions.path in file_path

    def is_pattern_allowed_for_file(self, pattern: str, file_path: str, component_name: str) -> bool:
        """
        指定されたファイルに対して特定のパターンが許可されているかをチェック

        Args:
            pattern: チェック対象パターン
            file_path: ファイルパス
            component_name: コンポーネント名

        Returns:
            True if allowed, False otherwise
        """
        # MCPサーバー例外チェック
        if self.is_file_in_mcp_server_path(file_path):
            mcp_exceptions = self.get_mcp_server_exceptions()
            if mcp_exceptions and pattern in mcp_exceptions.allowed_patterns:
                return True

        # 禁止パターンの例外チェック
        forbidden_patterns = self.get_forbidden_patterns(component_name)
        for forbidden in forbidden_patterns:
            if forbidden.pattern == pattern:
                # ファイル名ベースの例外チェック
                file_name = Path(file_path).name
                return file_name in forbidden.exceptions

        return False

    def get_allowed_modules(self, component_name: str) -> set[str]:
        """指定されたコンポーネントで許可されているモジュールのセットを取得"""
        definition = self.get_component_definition(component_name)
        if not definition:
            return set()

        allowed = {definition.primary_module}

        # 代替モジュールも追加
        for alt in definition.alternatives:
            if "module" in alt:
                allowed.add(alt["module"])

        return allowed

    def validate_import_compliance(self, import_statement: str, file_path: str) -> dict[str, Any]:
        """
        インポート文のコンプライアンスをチェック

        Args:
            import_statement: チェック対象のインポート文
            file_path: ファイルパス

        Returns:
            Dict containing validation results
        """
        violations = []

        # 各コンポーネントの禁止パターンをチェック
        all_patterns = self.get_all_forbidden_patterns()

        for component_name, patterns in all_patterns.items():
            for pattern in patterns:
                if pattern.pattern in import_statement:
                    # 例外チェック
                    if not self.is_pattern_allowed_for_file(
                        pattern.pattern, file_path, component_name
                    ):
                        violations.append({
                            "component": component_name,
                            "pattern": pattern.pattern,
                            "severity": pattern.severity,
                            "message": pattern.message,
                            "suggested_fix": pattern.suggested_fix,
                            "file_path": file_path
                        })

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "import_statement": import_statement
        }


def create_codemap_reader(codemap_path: Path | None = None) -> CODEMAPReader:
    """
    CODEMAPReaderのファクトリ関数

    Args:
        codemap_path: CODEMAP.yamlのパス（オプション）

    Returns:
        CODEMAPReader instance
    """
    return CODEMAPReader(codemap_path)

