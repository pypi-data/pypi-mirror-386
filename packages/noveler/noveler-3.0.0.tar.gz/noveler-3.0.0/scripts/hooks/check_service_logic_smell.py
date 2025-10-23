#!/usr/bin/env python3
"""
File: scripts/hooks/check_service_logic_smell.py
Purpose: Detect domain logic leaking into Service/UseCase layers
Context: Enforce "Tell, Don't Ask" principle and prevent anemic domain models
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class ServiceLogicSmellDetector(ast.NodeVisitor):
    """Service層にドメインロジックが漏れているパターンを検知"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[Tuple[int, str, str]] = []
        self.current_class: str = ""
        self.current_method: str = ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """クラス定義を解析"""
        self.current_class = node.name
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """メソッド定義を解析"""
        self.current_method = node.name

        # Service/UseCase層でのドメインロジックパターンを検知
        in_service_layer = (
            "/application/use_cases/" in self.file_path or
            "/domain/services/" in self.file_path
        )

        if in_service_layer:
            self._check_domain_logic_patterns(node)

        self.generic_visit(node)

    def _check_domain_logic_patterns(self, node: ast.FunctionDef) -> None:
        """ドメインロジックが漏れているパターンをチェック"""

        # パターン1: if文でEntity/VOのプロパティを直接チェック
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                # episode.episode_number < 1 のようなパターン
                if self._is_domain_property_check(child.test):
                    self.issues.append((
                        child.lineno,
                        "DOMAIN_LOGIC_IN_SERVICE",
                        f"Method '{self.current_method}' checks domain property directly. "
                        "Consider moving this logic to the domain entity."
                    ))

            # パターン2: Entity/VOのプロパティに直接代入
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Attribute):
                        # entity.status = "completed" のようなパターン
                        if self._looks_like_entity_mutation(target):
                            self.issues.append((
                                child.lineno,
                                "DIRECT_ENTITY_MUTATION",
                                f"Method '{self.current_method}' mutates entity directly. "
                                "Use domain methods instead (e.g., entity.complete())."
                            ))

    def _is_domain_property_check(self, node: ast.AST) -> bool:
        """ドメインプロパティの直接チェックかどうか判定"""
        if isinstance(node, ast.Compare):
            # left側がAttribute（obj.property）かチェック
            if isinstance(node.left, ast.Attribute):
                attr_name = node.left.attr
                # episode_number, status, state など典型的なドメインプロパティ
                domain_properties = [
                    "episode_number", "status", "state", "title", "content",
                    "version", "priority", "type", "category"
                ]
                if attr_name in domain_properties:
                    return True
        return False

    def _looks_like_entity_mutation(self, node: ast.Attribute) -> bool:
        """Entityの直接変更かどうか判定（ヒューリスティック）"""
        # entity.status のようなパターン
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            # 変数名が entity, vo, model などで終わる場合
            if any(var_name.endswith(suffix) for suffix in ["entity", "vo", "model", "obj"]):
                return True
            # または episode, character などドメインオブジェクト名
            domain_names = ["episode", "character", "plot", "theme", "scene"]
            if any(name in var_name.lower() for name in domain_names):
                return True
        return False


def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """単一ファイルを解析"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        detector = ServiceLogicSmellDetector(str(file_path))
        detector.visit(tree)

        return detector.issues
    except SyntaxError:
        return []


def main() -> int:
    """Main entry point"""
    # Git staged filesを取得
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    staged_files = result.stdout.strip().split("\n")

    # Service/UseCase層のPythonファイルのみ対象（Windows対応: パス正規化）
    service_files = [
        Path(f) for f in staged_files
        if f.endswith(".py") and (
            "/application/use_cases/" in f.replace("\\", "/") or
            "/domain/services/" in f.replace("\\", "/")
        )
    ]

    if not service_files:
        return 0

    all_issues = []
    for file_path in service_files:
        if not file_path.exists():
            continue

        issues = check_file(file_path)
        if issues:
            all_issues.append((file_path, issues))

    if all_issues:
        print("[WARNING] Domain logic may be leaking into Service layer:")
        print()
        for file_path, issues in all_issues:
            print(f"File: {file_path}")
            for line, code, message in issues:
                print(f"  Line {line}: [{code}] {message}")
            print()

        print("Hints:")
        print("  - Use 'Tell, Don't Ask' principle")
        print("  - Move validation/business logic to Entity/VO methods")
        print("  - Example: Instead of 'if episode.episode_number < 1', use 'episode.validate()'")
        print()
        # WARNING扱い（失敗させない）
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
