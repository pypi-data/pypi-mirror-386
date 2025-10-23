"""Infrastructure.tools.api_discovery_scanner
Where: Infrastructure tool for scanning API definitions.
What: Parses project files to discover API endpoints and generate metadata.
Why: Supports tooling that relies on up-to-date API discovery information.
"""

from __future__ import annotations

from noveler.presentation.shared.shared_utilities import console

"\n既存API発見ツール: 実装前の重複チェック自動化\n\nこのツールはNIH症候群（Not Invented Here）を防ぐため、\n新規実装前に既存の類似APIを発見・提示します。\n"
import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml


class FunctionType(Enum):
    """関数の分類タイプ"""

    CRUD_OPERATION = "crud"
    DATA_VALIDATION = "validation"
    DATA_TRANSFORMATION = "transformation"
    FILE_OPERATION = "file_io"
    SERVICE_COORDINATION = "service"
    UTILITY_FUNCTION = "utility"
    FACTORY_CREATION = "factory"


@dataclass(frozen=True)
class ExistingAPI:
    """既存APIの情報"""

    file_path: Path
    function_name: str
    class_name: str | None
    function_type: FunctionType
    parameters: list[str]
    return_type: str | None
    docstring: str | None
    line_number: int
    complexity_score: int


@dataclass(frozen=True)
class SimilarityMatch:
    """類似度マッチング結果"""

    existing_api: ExistingAPI
    similarity_score: float
    similarity_reasons: list[str]


class APIDiscoveryScanner:
    """
    既存API発見・重複チェック自動化ツール

    機能:
    - 新規実装予定機能の仕様から既存API検索
    - 機能名・パラメータ・戻り値の類似度判定
    - NIH症候群パターンの自動検出
    - 推奨される既存APIの提案
    """

    FUNCTION_PATTERNS: ClassVar[dict[FunctionType, list[str]]] = {
        FunctionType.CRUD_OPERATION: [
            "(create|save|insert|add)_",
            "(get|find|fetch|load|retrieve)_",
            "(update|modify|change)_",
            "(delete|remove|destroy)_",
        ],
        FunctionType.DATA_VALIDATION: ["(validate|check|verify)_", "is_valid", "(ensure|assert)_"],
        FunctionType.DATA_TRANSFORMATION: ["(convert|transform|parse|format)_", "to_", "from_", "_(to|from)_"],
        FunctionType.FILE_OPERATION: ["(read|write|load|save)_file", "(export|import)_", "file_(read|write|load|save)"],
        FunctionType.SERVICE_COORDINATION: ["(execute|process|handle)_", "(coordinate|orchestrate)_", "_service$"],
        FunctionType.FACTORY_CREATION: ["create_", "build_", "make_", "_factory"],
        FunctionType.UTILITY_FUNCTION: ["(calculate|compute)_", "(format|normalize)_", "(extract|collect)_"],
    }
    KEYWORD_WEIGHTS: ClassVar[dict[str, float]] = {
        "episode": 0.9,
        "plot": 0.9,
        "quality": 0.8,
        "check": 0.8,
        "validate": 0.8,
        "repository": 0.7,
        "service": 0.7,
        "manager": 0.6,
        "utility": 0.5,
        "helper": 0.5,
    }

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """
        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root
        self.scripts_root = project_root / "scripts"
        self.existing_apis: list[ExistingAPI] = []
        if logger_service is None:
            from noveler.infrastructure.di.container import resolve_service

            try:
                self.logger_service = resolve_service("ILogger")
            except ValueError:
                from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter

                self.logger_service = DomainLoggerAdapter()
        else:
            self.logger_service = logger_service
        if console_service is None:
            from noveler.infrastructure.di.container import resolve_service

            try:
                self.console_service = resolve_service("IConsoleService")
            except ValueError:
                from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

                self.console_service = ConsoleServiceAdapter()
        else:
            self.console_service = console_service

    def scan_existing_apis(self) -> list[ExistingAPI]:
        """
        プロジェクト内の既存APIをスキャン

        Returns:
            発見された既存APIのリスト
        """
        self.existing_apis.clear()
        python_files = list(self.scripts_root.rglob("*.py"))
        for python_file in python_files:
            try:
                self._scan_file(python_file)
            except Exception as e:
                self.console_service.print(f"⚠️ {python_file}: スキャンエラー - {e}")
        return self.existing_apis

    def find_similar_apis(
        self,
        function_name: str,
        parameters: list[str] | None = None,
        description: str | None = None,
        threshold: float = 0.5,
    ) -> list[SimilarityMatch]:
        """
        指定された機能仕様に類似する既存APIを検索

        Args:
            function_name: 実装予定の関数名
            parameters: パラメータリスト
            description: 機能の説明
            threshold: 類似度の閾値（0.0-1.0）

        Returns:
            類似度の高い順にソートされたマッチング結果
        """
        matches = []
        for api in self.existing_apis:
            (similarity_score, reasons) = self._calculate_similarity(function_name, parameters or [], description, api)
            if similarity_score >= threshold:
                matches.append(
                    SimilarityMatch(existing_api=api, similarity_score=similarity_score, similarity_reasons=reasons)
                )
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches

    def detect_nih_patterns(self, new_function_spec: dict[str, Any]) -> list[str]:
        """
        NIH症候群パターンの検出

        Args:
            new_function_spec: 新規関数の仕様

        Returns:
            検出されたNIHパターンのリスト
        """
        nih_warnings = []
        function_name = new_function_spec.get("name", "")
        common_patterns = ["Manager", "Service", "Repository", "Utility", "Helper"]
        for pattern in common_patterns:
            if pattern.lower() in function_name.lower():
                similar_count = len(
                    [
                        api
                        for api in self.existing_apis
                        if pattern.lower() in api.function_name.lower()
                        or (api.class_name and pattern.lower() in api.class_name.lower())
                    ]
                )
                if similar_count > 0:
                    nih_warnings.append(
                        f"⚠️ {pattern}パターンは既に{similar_count}箇所で実装されています。統合を検討してください"
                    )
        matches = self.find_similar_apis(
            function_name, new_function_spec.get("parameters", []), new_function_spec.get("description"), threshold=0.7
        )
        if matches:
            nih_warnings.append(
                f"🔄 高い類似度({matches[0].similarity_score:.1%})の既存実装が見つかりました: {matches[0].existing_api.file_path}:{matches[0].existing_api.line_number}"
            )
        return nih_warnings

    def _scan_file(self, file_path: Path) -> None:
        """単一ファイルのAPIスキャン"""
        content = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._extract_function_api(file_path, node)
            elif isinstance(node, ast.ClassDef):
                self._extract_class_methods(file_path, node)

    def _extract_function_api(self, file_path: Path, node: ast.FunctionDef, class_name: str | None = None) -> None:
        """関数定義からAPI情報を抽出"""
        if node.name.startswith("_"):
            return
        parameters = [arg.arg for arg in node.args.args if arg.arg != "self"]
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        docstring = ast.get_docstring(node)
        function_type = self._classify_function_type(node.name, docstring)
        complexity_score = self._calculate_complexity(node)
        api = ExistingAPI(
            file_path=file_path,
            function_name=node.name,
            class_name=class_name,
            function_type=function_type,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            line_number=node.lineno,
            complexity_score=complexity_score,
        )
        self.existing_apis.append(api)

    def _extract_class_methods(self, file_path: Path, node: ast.ClassDef) -> None:
        """クラス内のメソッドを抽出"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._extract_function_api(file_path, item, node.name)

    def _classify_function_type(self, function_name: str, docstring: str | None) -> FunctionType:
        """関数名とdocstringから機能タイプを分類"""
        function_text = f"{function_name} {docstring or ''}".lower()
        for func_type, patterns in self.FUNCTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, function_text):
                    return func_type
        return FunctionType.UTILITY_FUNCTION

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """関数の複雑度を計算（1-10スケール）"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For):
                complexity += 1
            elif isinstance(child, ast.Try | ast.AsyncFunctionDef):
                complexity += 2
        return min(complexity, 10)

    def _calculate_similarity(
        self, target_name: str, target_params: list[str], target_description: str | None, api: ExistingAPI
    ) -> tuple[float, list[str]]:
        """類似度計算"""
        similarity_score = 0.0
        reasons = []
        name_similarity = self._string_similarity(target_name, api.function_name)
        similarity_score += name_similarity * 0.4
        if name_similarity > 0.5:
            reasons.append(f"関数名が類似 ({name_similarity:.1%})")
        param_similarity = self._list_similarity(target_params, api.parameters)
        similarity_score += param_similarity * 0.3
        if param_similarity > 0.3:
            reasons.append(f"パラメータが類似 ({param_similarity:.1%})")
        if target_description and api.docstring:
            desc_similarity = self._string_similarity(target_description, api.docstring)
            similarity_score += desc_similarity * 0.2
            if desc_similarity > 0.3:
                reasons.append(f"機能説明が類似 ({desc_similarity:.1%})")
        keyword_score = self._keyword_matching(target_name, api.function_name)
        similarity_score += keyword_score * 0.1
        if keyword_score > 0.0:
            reasons.append("重要キーワードが一致")
        return (similarity_score, reasons)

    def _string_similarity(self, str1: str, str2: str) -> float:
        """文字列の類似度計算（Levenshtein距離ベース）"""
        (str1, str2) = (str1.lower(), str2.lower())
        if str1 == str2:
            return 1.0
        if str1 in str2 or str2 in str1:
            return 0.7
        common_chars = set(str1) & set(str2)
        total_chars = set(str1) | set(str2)
        if not total_chars:
            return 0.0
        return len(common_chars) / len(total_chars)

    def _list_similarity(self, list1: list[str], list2: list[str]) -> float:
        """リストの類似度計算"""
        if not list1 and (not list2):
            return 1.0
        if not list1 or not list2:
            return 0.0
        (set1, set2) = (set(list1), set(list2))
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0.0

    def _keyword_matching(self, str1: str, str2: str) -> float:
        """重要キーワードのマッチング"""
        score = 0.0
        (str1, str2) = (str1.lower(), str2.lower())
        for keyword, weight in self.KEYWORD_WEIGHTS.items():
            if keyword in str1 and keyword in str2:
                score += weight
        return min(score / len(self.KEYWORD_WEIGHTS), 1.0)

    def export_scan_results(self, output_path: Path, include_similarity: bool = True) -> None:
        """スキャン結果をYAMLで出力"""
        results_data: dict[str, Any] = {
            "metadata": {
                "project_root": str(self.project_root),
                "total_apis": len(self.existing_apis),
                "function_type_distribution": self._get_type_distribution(),
            },
            "existing_apis": [
                {
                    "file_path": str(api.file_path.relative_to(self.project_root)),
                    "function_name": api.function_name,
                    "class_name": api.class_name,
                    "function_type": api.function_type.value,
                    "parameters": api.parameters,
                    "return_type": api.return_type,
                    "docstring": api.docstring,
                    "line_number": api.line_number,
                    "complexity_score": api.complexity_score,
                }
                for api in self.existing_apis
            ],
        }
        with output_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(results_data, f, allow_unicode=True, sort_keys=False)

    def _get_type_distribution(self) -> dict[str, int]:
        """機能タイプの分布を取得"""
        distribution = {}
        for api in self.existing_apis:
            type_name = api.function_type.value
            distribution[type_name] = distribution.get(type_name, 0) + 1
        return distribution

    def interactive_search(self) -> None:
        """対話式API検索"""
        self.console_service.print("🔍 既存API検索ツール")
        self.console_service.print("実装予定の機能について教えてください:")
        function_name = input("関数名: ").strip()
        if not function_name:
            self.console_service.print("❌ 関数名は必須です")
            return
        description = input("機能説明（オプション）: ").strip() or None
        self.console_service.print("パラメータをカンマ区切りで入力（例: episode_id, quality_level）:")
        param_input = input("パラメータ: ").strip()
        parameters = [p.strip() for p in param_input.split(",") if p.strip()] if param_input else []
        matches = self.find_similar_apis(function_name, parameters, description)
        if not matches:
            self.console_service.print("✅ 類似する既存APIは見つかりませんでした")
            return
        self.console_service.print(f"\n🎯 {len(matches)}件の類似APIを発見:")
        for i, match in enumerate(matches[:5], 1):
            api = match.existing_api
            self.console_service.print(f"\n{i}. {api.function_name} (類似度: {match.similarity_score:.1%})")
            self.console_service.print(f"   📁 {api.file_path.relative_to(self.project_root)}:{api.line_number}")
            if api.class_name:
                self.console_service.print(f"   🏷️  クラス: {api.class_name}")
            self.console_service.print(f"   📋 パラメータ: {', '.join(api.parameters) or '(なし)'}")
            if api.docstring:
                self.console_service.print(f"   📝 説明: {api.docstring[:100]}...")
            self.console_service.print(f"   🔗 類似理由: {', '.join(match.similarity_reasons)}")
        nih_warnings = self.detect_nih_patterns(
            {"name": function_name, "parameters": parameters, "description": description}
        )
        if nih_warnings:
            self.console_service.print("\n⚠️ NIH症候群の可能性:")
            for warning in nih_warnings:
                self.console_service.print(f"   {warning}")


def main() -> None:
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="既存API発見・重複チェックツール")
    parser.add_argument("--project-root", type=Path, default=Path(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--output", type=Path, help="結果出力ファイルパス（YAML形式）")
    parser.add_argument("--interactive", action="store_true", help="対話式検索モード")
    parser.add_argument("--function", type=str, help="検索対象の関数名")
    parser.add_argument("--description", type=str, help="機能の説明")
    args = parser.parse_args()
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    scanner = APIDiscoveryScanner(args.project_root)
    console.print("🔍 既存APIをスキャン中...")
    apis = scanner.scan_existing_apis()
    console.print(f"📊 {len(apis)}個のAPIを発見")
    if args.output:
        scanner.export_scan_results(args.output)
        console.print(f"📄 結果を出力: {args.output}")
    if args.interactive:
        scanner.interactive_search()
    elif args.function:
        matches = scanner.find_similar_apis(args.function, description=args.description)
        if matches:
            console.print(f"\n🎯 '{args.function}'に類似するAPI:")
            for match in matches[:3]:
                api = match.existing_api
                console.print(f"  - {api.function_name} ({match.similarity_score:.1%})")
                console.print(f"    {api.file_path.relative_to(args.project_root)}:{api.line_number}")
        else:
            console.print(f"✅ '{args.function}'に類似するAPIは見つかりませんでした")


if __name__ == "__main__":
    main()
