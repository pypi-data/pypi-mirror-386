"""循環インポート分析ツール

DDD違反と循環インポートの根本原因を分析します。
"""

import ast
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import console



class CircularImportAnalyzer:
    """循環インポート分析クラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化"""
        self.scripts_dir = Path("scripts")
        self.layer_mapping = {
            "domain": ["entities", "services", "repositories", "value_objects", "interfaces"],
            "application": ["use_cases", "orchestrators"],
            "infrastructure": ["adapters", "factories", "repositories", "services", "integrations"],
            "presentation": ["cli", "api", "web"],
        }
        self.logger_service = logger_service
        self.console_service = console_service

    def analyze_layer_violations(self) -> dict[str, list[str]]:
        """レイヤー違反を分析

        Returns:
            レイヤー違反のマッピング
        """
        violations = {
            "application_to_presentation": [],
            "domain_to_application": [],
            "domain_to_infrastructure": [],
            "domain_to_presentation": [],
        }
        app_files = list((self.scripts_dir / "application").rglob("*.py"))
        for file_path in app_files:
            imports = self._extract_imports(file_path)
            for imp in imports:
                if "presentation" in imp:
                    violations["application_to_presentation"].append(
                        f"{file_path.relative_to(self.scripts_dir)} -> {imp}"
                    )
        domain_files = list((self.scripts_dir / "domain").rglob("*.py"))
        for file_path in domain_files:
            imports = self._extract_imports(file_path)
            for imp in imports:
                if "application" in imp:
                    violations["domain_to_application"].append(f"{file_path.relative_to(self.scripts_dir)} -> {imp}")
                elif "infrastructure" in imp and "interfaces" not in str(file_path):
                    violations["domain_to_infrastructure"].append(f"{file_path.relative_to(self.scripts_dir)} -> {imp}")
                elif "presentation" in imp:
                    violations["domain_to_presentation"].append(f"{file_path.relative_to(self.scripts_dir)} -> {imp}")
        return violations

    def _extract_imports(self, file_path: Path) -> list[str]:
        """ファイルからインポート文を抽出

        Args:
            file_path: 対象ファイル

        Returns:
            インポート文のリスト
        """
        imports = []
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("scripts"):
                        imports.append(node.module)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("scripts"):
                            imports.append(alias.name)
        except Exception:
            pass
        return imports

    def find_delayed_imports(self) -> dict[str, int]:
        """遅延インポートを検出

        Returns:
            ファイルごとの遅延インポート数
        """
        delayed_imports = {}
        for py_file in self.scripts_dir.rglob("*.py"):
            count = 0
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        for child in ast.walk(node):
                            if isinstance(child, ast.Import | ast.ImportFrom):
                                count += 1
                if count > 0:
                    delayed_imports[str(py_file.relative_to(self.scripts_dir))] = count
            except Exception:
                pass
        return delayed_imports

    def suggest_solutions(self, violations: dict[str, list[str]]) -> list[str]:
        """解決策を提案

        Args:
            violations: レイヤー違反

        Returns:
            解決策のリスト
        """
        solutions = []
        if violations["application_to_presentation"]:
            solutions.append(
                "1. **依存性注入の導入**:\n   - PathServiceインターフェースをドメイン層に定義\n   - 実装はインフラ層に配置\n   - アプリケーション層はインターフェース経由で使用"
            )
        if violations["domain_to_application"] or violations["domain_to_infrastructure"]:
            solutions.append(
                "2. **ドメインサービスの再設計**:\n   - ドメイン層の純粋性を保つ\n   - 外部依存はインターフェース経由\n   - リポジトリパターンの徹底"
            )
        solutions.append(
            "3. **イベント駆動アーキテクチャの検討**:\n   - レイヤー間の直接依存を削減\n   - メディエーターパターンの活用\n   - 非同期メッセージングの導入"
        )
        return solutions


def main():
    """メイン処理"""
    analyzer = CircularImportAnalyzer()
    console.print("=== 循環インポート・DDD違反分析レポート ===\n")
    violations = analyzer.analyze_layer_violations()
    console.print("## レイヤー違反の検出結果\n")
    for violation_type, items in violations.items():
        if items:
            console.print(f"### {violation_type.replace('_', ' ').title()}: {len(items)}件")
            for item in items[:5]:
                console.print(f"  - {item}")
            if len(items) > 5:
                console.print(f"  ... 他 {len(items) - 5}件\n")
        else:
            console.print(f"### {violation_type.replace('_', ' ').title()}: 違反なし ✅")
    console.print("\n## 遅延インポートの使用状況\n")
    delayed_imports = analyzer.find_delayed_imports()
    sorted_delayed = sorted(delayed_imports.items(), key=lambda x: x[1], reverse=True)
    total_delayed = sum(delayed_imports.values())
    console.print(f"合計: {len(delayed_imports)}ファイル、{total_delayed}箇所の遅延インポート\n")
    console.print("### 上位ファイル:")
    for file_path, count in sorted_delayed[:10]:
        console.print(f"  - {file_path}: {count}箇所")
    console.print("\n## 推奨される解決策\n")
    solutions = analyzer.suggest_solutions(violations)
    for solution in solutions:
        console.print(solution)
        console.print()
    console.print("## 実装アクションプラン\n")
    console.print("### Phase 1: インターフェース定義（1-2日）")
    console.print("- [ ] IPathServiceインターフェースの作成")
    console.print("- [ ] IConfigurationServiceインターフェースの作成")
    console.print("- [ ] ILoggerServiceインターフェースの作成")
    console.print()
    console.print("### Phase 2: 依存性注入コンテナ（2-3日）")
    console.print("- [ ] DIコンテナの実装")
    console.print("- [ ] サービスプロバイダーの作成")
    console.print("- [ ] ファクトリーパターンの統一")
    console.print()
    console.print("### Phase 3: レイヤー分離の修正（3-5日）")
    console.print("- [ ] アプリケーション層の修正")
    console.print("- [ ] プレゼンテーション層への依存削除")
    console.print("- [ ] テストの更新")


if __name__ == "__main__":
    main()
