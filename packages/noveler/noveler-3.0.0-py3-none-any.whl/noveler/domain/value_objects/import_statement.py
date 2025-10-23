"""Domain.value_objects.import_statement
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""インポート文Value Object

仕様書: SPEC-CIRCULAR-IMPORT-DETECTION-001
"""


from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ImportType(Enum):
    """インポートタイプ"""

    STANDARD = "standard"  # import module
    FROM = "from"  # from module import name
    DYNAMIC = "dynamic"  # __import__, importlib
    RELATIVE = "relative"  # from noveler.domain.value_objects import, from noveler.domain import


class ImportScope(Enum):
    """インポート範囲"""

    BUILTIN = "builtin"  # 組み込みモジュール
    STANDARD_LIB = "standard"  # 標準ライブラリ
    THIRD_PARTY = "third_party"  # サードパーティ
    LOCAL = "local"  # ローカルプロジェクト
    RELATIVE = "relative"  # 相対インポート


@dataclass(frozen=True)
class ImportStatement:
    """インポート文を表すValue Object"""

    # 基本情報
    module_name: str
    imported_names: list[str]
    import_type: ImportType
    import_scope: ImportScope

    # ソース情報
    source_file: Path
    line_number: int
    statement_text: str

    # 相対インポート情報
    relative_level: int = 0  # ドット数 (from noveler.domain import の場合は2)
    # 解析結果
    resolved_module_path: Path | None = None
    is_circular_risk: bool = False

    def get_absolute_module_name(self, source_root: Path) -> str:
        """絶対モジュール名の取得"""
        if self.import_type == ImportType.RELATIVE:
            return self._resolve_relative_import(source_root)
        return self.module_name

    def _resolve_relative_import(self, source_root: Path) -> str:
        """相対インポートの絶対パス変換"""
        if self.relative_level == 0:
            return self.module_name

        # 現在のファイルからの相対位置を計算
        current_package_path = self.source_file.relative_to(source_root).parent

        # レベル分だけ親ディレクトリに遡る
        target_package_path = current_package_path
        for _ in range(self.relative_level - 1):
            target_package_path = target_package_path.parent

        # モジュール名を結合
        if self.module_name:
            target_package_path = target_package_path / self.module_name

        # Pythonモジュール名に変換
        return str(target_package_path).replace("/", ".")

    def get_potential_circular_targets(self) -> set[str]:
        """循環インポートの可能性があるターゲットモジュール"""
        targets = set()

        # メインモジュール
        targets.add(self.module_name)

        # インポートされた名前がモジュールの場合
        for name in self.imported_names:
            if "." not in name:  # 単純名の場合:
                targets.add(f"{self.module_name}.{name}")

        return targets

    def is_ddd_layer_violation(self, target_layer: str) -> bool:
        """DDD層違反チェック"""
        layer_hierarchy = {"domain": 0, "application": 1, "infrastructure": 2, "presentation": 3}

        # インポート文から層を推測
        source_layer = self._infer_layer_from_path(self.source_file)
        import_layer = self._infer_layer_from_module(self.module_name)

        if source_layer and import_layer:
            source_level = layer_hierarchy.get(source_layer, 999)
            import_level = layer_hierarchy.get(import_layer, 999)

            # 下位層から上位層へのインポートは違反
            return source_level > import_level

        return False

    def _infer_layer_from_path(self, file_path: Path) -> str | None:
        """ファイルパスから層を推測"""
        path_parts = file_path.parts

        for part in path_parts:
            if part in ["domain", "application", "infrastructure", "presentation"]:
                return part

        return None

    def _infer_layer_from_module(self, module_name: str) -> str | None:
        """モジュール名から層を推測"""
        if module_name.startswith("noveler."):
            parts = module_name.split(".")
            if len(parts) >= 2:
                layer_candidate = parts[1]
                if layer_candidate in ["domain", "application", "infrastructure", "presentation"]:
                    return layer_candidate

        return None

    def suggest_fix(self) -> str | None:
        """修正提案の生成"""
        suggestions = []

        # 相対インポートの絶対インポート化
        if self.import_type == ImportType.RELATIVE:
            abs_module = self.get_absolute_module_name(Path("scripts"))
            suggestions.append(
                f"相対インポートを絶対インポートに変更: from {abs_module} import {', '.join(self.imported_names)}"
            )

        # scriptsプレフィックスの追加
        if not self.module_name.startswith("noveler.") and self.import_scope == ImportScope.LOCAL:
            suggestions.append(
                f"scriptsプレフィックスを追加: from noveler.{self.module_name} import {', '.join(self.imported_names)}"
            )

        # DDD層違反の修正
        if self.is_ddd_layer_violation(""):
            suggestions.append("DDD層違反: 依存関係を見直し、Protocol-based DIの使用を検討してください")

        return "; ".join(suggestions) if suggestions else None


@dataclass(frozen=True)
class ImportAnalysisResult:
    """インポート分析結果"""

    total_imports: int
    by_type: dict[ImportType, int]
    by_scope: dict[ImportScope, int]
    violations: list[ImportStatement]
    circular_risks: list[ImportStatement]
    suggestions: list[str]

    def get_quality_score(self) -> float:
        """品質スコアの計算 (0-100)"""
        if self.total_imports == 0:
            return 100.0

        violation_ratio = len(self.violations) / self.total_imports
        risk_ratio = len(self.circular_risks) / self.total_imports

        # 違反とリスクに重み付けして評価
        score = 100.0 * (1 - (violation_ratio * 0.6 + risk_ratio * 0.4))

        return max(0.0, min(100.0, score))
