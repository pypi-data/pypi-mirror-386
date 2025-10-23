#!/usr/bin/env python3
"""
File: scripts/hooks/check_anemic_domain.py
Purpose: Detect Anemic Domain Model anti-patterns in committed code
Context: Pre-commit hook to enforce rich domain models with business logic
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class AnemicDomainConfig:
    """Configuration loader for .anemic-domain.yaml"""

    DEFAULT_CONFIG = {
        "domain_properties": [
            "episode_number", "status", "state", "title", "content",
            "version", "priority", "type", "category"
        ],
        "excluded_suffixes": ["Protocol", "Request", "Response", "DTO"],
        "excluded_prefixes": ["I"],
        "target_paths": [
            "src/noveler/domain/entities",
            "src/noveler/domain/value_objects"
        ],
        "excluded_paths": ["tests/fixtures/domain"],
        "validation_keywords": ["validate", "check", "verify", "__post_init__"],
        "config_version": "1.0.0"
    }

    def __init__(self, config_path: Path | None = None):
        """Load configuration from .anemic-domain.yaml or use defaults

        Args:
            config_path: Path to .anemic-domain.yaml. If None, searches in repository root.
        """
        self.config: Dict = self.DEFAULT_CONFIG.copy()

        if config_path is None:
            # Search for .anemic-domain.yaml in repository root
            config_path = self._find_config_file()

        if config_path and config_path.exists():
            self._load_config(config_path)

    def _find_config_file(self) -> Path | None:
        """Find .anemic-domain.yaml in repository root"""
        # Start from current directory and walk up to find repository root
        current = Path.cwd()
        for _ in range(10):  # Limit search depth
            config_file = current / ".anemic-domain.yaml"
            if config_file.exists():
                return config_file
            git_dir = current / ".git"
            if git_dir.exists():
                # Found repository root, check for config file
                config_file = current / ".anemic-domain.yaml"
                if config_file.exists():
                    return config_file
                return None
            parent = current.parent
            if parent == current:
                # Reached filesystem root
                break
            current = parent
        return None

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file"""
        if yaml is None:
            # PyYAML not available, use defaults
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Merge user config with defaults
                    self.config.update(user_config)
        except (IOError, yaml.YAMLError):
            # Failed to load config, use defaults
            pass

    def get_domain_properties(self) -> List[str]:
        """Get list of domain properties to check"""
        return self.config["domain_properties"]

    def get_excluded_suffixes(self) -> List[str]:
        """Get list of excluded class suffixes"""
        return self.config["excluded_suffixes"]

    def get_excluded_prefixes(self) -> List[str]:
        """Get list of excluded class prefixes"""
        return self.config["excluded_prefixes"]

    def get_target_paths(self) -> List[str]:
        """Get list of target directory paths"""
        return self.config["target_paths"]

    def get_excluded_paths(self) -> List[str]:
        """Get list of excluded directory paths"""
        return self.config["excluded_paths"]

    def get_validation_keywords(self) -> List[str]:
        """Get list of validation method keywords"""
        return self.config["validation_keywords"]

    def is_excluded_path(self, file_path: str) -> bool:
        """Check if file path is in excluded paths

        Args:
            file_path: File path (normalized with forward slashes)

        Returns:
            True if file should be excluded
        """
        for excluded in self.get_excluded_paths():
            if excluded.replace("\\", "/") in file_path:
                return True
        return False

    def is_target_path(self, file_path: str) -> bool:
        """Check if file path is in target paths

        Args:
            file_path: File path (normalized with forward slashes)

        Returns:
            True if file is in target directory
        """
        for target in self.get_target_paths():
            if target.replace("\\", "/") in file_path:
                return True
        return False


class AnemicDomainDetector(ast.NodeVisitor):
    """ASTを使ってドメインモデル貧血症のパターンを検知"""

    def __init__(self, file_path: str, config: AnemicDomainConfig | None = None):
        # Windows環境でのパス区切り文字を正規化
        self.file_path = file_path.replace("\\", "/")
        self.config = config or AnemicDomainConfig()
        self.issues: List[Tuple[int, str, str]] = []
        self.current_class: str = ""
        self.current_class_node: ast.ClassDef | None = None  # noqa チェック用
        self.class_methods: List[str] = []
        self.class_has_dataclass = False
        self.class_has_validation = False
        self.dataclass_generates_eq = False
        self.dataclass_is_frozen = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """クラス定義を解析"""
        # 前のクラスの結果を評価
        if self.current_class:
            self._evaluate_class(self.current_class_node)

        # 新しいクラスの解析開始
        self.current_class = node.name
        self.current_class_node = node  # noqa チェック用に保持
        self.class_methods = []
        self.class_has_dataclass = False
        self.class_has_validation = False
        self.dataclass_generates_eq = False
        self.dataclass_is_frozen = False

        # Enum継承をチェック（除外対象）
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Enum":
                # Enumクラスは検知対象外
                self.current_class = ""
                return

        # デコレータをチェック
        for decorator in node.decorator_list:
            # @dataclass または @dataclass(...) のパターン
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                self.class_has_dataclass = True
                self.dataclass_generates_eq = True  # デフォルトでeq=True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "dataclass":
                    self.class_has_dataclass = True
                    # 引数を解析
                    self._parse_dataclass_arguments(decorator)

        # Domain層のEntityまたはValue Objectか判定（設定から取得）
        in_domain_layer = self.config.is_target_path(self.file_path)

        if in_domain_layer:
            # メソッドを収集
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.class_methods.append(item.name)
                    # バリデーション関連メソッドをチェック（設定から取得）
                    # ただしプライベートメソッド（単一アンダースコア始まり）は除外
                    is_private = item.name.startswith("_") and not item.name.startswith("__")
                    validation_keywords = self.config.get_validation_keywords()
                    if not is_private and any(keyword in item.name for keyword in validation_keywords):
                        self.class_has_validation = True

        self.generic_visit(node)

    def _parse_dataclass_arguments(self, decorator: ast.Call) -> None:
        """@dataclass(...)の引数を解析して自動生成メソッドを判定"""
        # デフォルト値
        eq = True
        frozen = False

        # キーワード引数を解析
        for keyword in decorator.keywords:
            if keyword.arg == "eq":
                if isinstance(keyword.value, ast.Constant):
                    eq = keyword.value.value
            elif keyword.arg == "frozen":
                if isinstance(keyword.value, ast.Constant):
                    frozen = keyword.value.value

        self.dataclass_generates_eq = eq
        self.dataclass_is_frozen = frozen

    def _has_noqa_comment(self, node: ast.ClassDef) -> bool:
        """Check if class has # noqa: anemic-domain comment

        Args:
            node: Class definition AST node

        Returns:
            True if noqa comment is present
        """
        # Check for inline comment on class definition line
        # AST doesn't preserve comments, so we need to read the source
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if node.lineno <= len(lines):
                class_line = lines[node.lineno - 1]
                if "# noqa: anemic-domain" in class_line or "# noqa:anemic-domain" in class_line:
                    return True

                # Check decorator lines
                if node.decorator_list:
                    first_decorator_line = node.decorator_list[0].lineno
                    for line_num in range(first_decorator_line - 1, node.lineno):
                        if line_num < len(lines):
                            line = lines[line_num]
                            if "# noqa: anemic-domain" in line or "# noqa:anemic-domain" in line:
                                return True
        except (IOError, IndexError):
            pass

        return False

    def _evaluate_class(self, node: ast.ClassDef | None = None) -> None:
        """現在のクラスが貧血症かどうか評価

        Args:
            node: Class definition AST node (for noqa comment check)
        """
        # Domain層のEntityまたはValue Objectか判定（設定から取得）
        in_domain_layer = self.config.is_target_path(self.file_path)

        if not in_domain_layer:
            return

        # noqa comment check (if node is provided)
        if node and self._has_noqa_comment(node):
            return

        # ビジネスロジックメソッドのリスト
        # __post_init__ はバリデーションとしてカウント
        # パブリックメソッド（_なし）もビジネスロジックとしてカウント
        business_methods = [
            m for m in self.class_methods
            if not m.startswith("_") or m in ["__post_init__", "__eq__", "__hash__"]
        ]

        # 例外: プロトコル定義、抽象クラス、インターフェース、DTOは除外（設定から取得）
        excluded_suffixes = self.config.get_excluded_suffixes()
        excluded_prefixes = self.config.get_excluded_prefixes()

        if any(self.current_class.endswith(suffix) for suffix in excluded_suffixes):
            return
        if any(self.current_class.startswith(prefix) for prefix in excluded_prefixes):
            return

        # パターン1: @dataclass + ビジネスロジックなし
        # ただし __post_init__ があれば許容（バリデーションの可能性）
        if self.class_has_dataclass and len(business_methods) == 0 and not self.class_has_validation:
            self.issues.append((
                0,
                "ANEMIC_DATACLASS",
                f"Class '{self.current_class}' is a dataclass with no business logic methods. "
                "Consider adding validation or domain behavior methods."
            ))

        # パターン2: Value Object + バリデーションなし
        if "/value_objects/" in self.file_path and not self.class_has_validation:
            # __post_init__ も __eq__ もない場合のみエラー
            # ただし @dataclass が自動生成する __eq__ は許容
            has_eq = "__eq__" in self.class_methods or self.dataclass_generates_eq

            if "__post_init__" not in self.class_methods and not has_eq:
                self.issues.append((
                    0,
                    "NO_VALIDATION",
                    f"Value Object '{self.current_class}' has no validation logic (__post_init__) "
                    "and no equality check (__eq__). This may indicate an anemic model."
                ))

    def finalize(self) -> None:
        """最後のクラスを評価"""
        if self.current_class:
            self._evaluate_class(self.current_class_node)


def check_file(file_path: Path, config: AnemicDomainConfig | None = None) -> List[Tuple[int, str, str]]:
    """単一ファイルを解析

    Args:
        file_path: 解析対象ファイルパス
        config: 設定オブジェクト（省略時は自動検索またはデフォルト使用）

    Returns:
        検知された問題のリスト [(line, code, message), ...]
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        detector = AnemicDomainDetector(str(file_path), config)
        detector.visit(tree)
        detector.finalize()

        return detector.issues
    except SyntaxError as e:
        # Syntax error: skip this file (likely invalid Python)
        return []
    except UnicodeDecodeError as e:
        # Unicode decode error: file may have incompatible encoding
        error_msg = (
            f"Failed to decode file (encoding issue). "
            f"Expected UTF-8, but got decoding error at byte {e.start}: {e.reason}"
        )
        print(f"[WARNING] {file_path}: {error_msg}", file=sys.stderr)
        return []
    except IOError as e:
        # IO error: file may be inaccessible
        error_msg = f"Failed to read file: {e.strerror}"
        print(f"[WARNING] {file_path}: {error_msg}", file=sys.stderr)
        return []
    except Exception as e:
        # Unexpected error: report but continue
        error_msg = f"Unexpected error during analysis: {type(e).__name__}: {e}"
        print(f"[WARNING] {file_path}: {error_msg}", file=sys.stderr)
        return []


def main() -> int:
    """Main entry point"""
    # 設定ファイルをロード
    config = AnemicDomainConfig()

    # Git staged filesを取得
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    staged_files = result.stdout.strip().split("\n")

    # 設定に基づいて対象ファイルをフィルタリング
    domain_files = []
    for f in staged_files:
        if not f.endswith(".py"):
            continue

        normalized_path = f.replace("\\", "/")

        # 除外パスチェック（設定から取得）
        if config.is_excluded_path(normalized_path):
            continue

        # 対象パスチェック（設定から取得）
        if config.is_target_path(normalized_path):
            domain_files.append(Path(f))

    if not domain_files:
        return 0

    all_issues = []
    for file_path in domain_files:
        if not file_path.exists():
            continue

        issues = check_file(file_path, config)
        if issues:
            all_issues.append((file_path, issues))

    if all_issues:
        print("[ERROR] Anemic Domain Model detected:")
        print()
        for file_path, issues in all_issues:
            print(f"File: {file_path}")
            for line, code, message in issues:
                print(f"  [{code}] {message}")
            print()

        print("Hints:")
        print("  - Add business logic methods to Entity classes")
        print("  - Add validation in __post_init__ for Value Objects")
        print("  - Move logic from Service layer to Domain layer")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
