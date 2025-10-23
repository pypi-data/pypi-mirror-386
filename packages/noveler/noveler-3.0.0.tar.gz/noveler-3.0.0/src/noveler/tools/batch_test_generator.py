"""Tools.batch_test_generator
Where: Tool generating tests in batch from specifications.
What: Creates test cases based on spec inputs to expand coverage quickly.
Why: Accelerates test creation and reduces manual work.
"""

from noveler.presentation.shared.shared_utilities import console

"一括テスト生成ツール\n\n未テストモジュールに対してSPEC準拠テストファイルを一括生成\nDDD準拠・開発者体験最適化対応\n"
import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now

try:
    from noveler.infrastructure.logging.unified_logger import get_logger
except ImportError:  # pragma: no cover - fallback for lightweight environments
    from noveler.domain.interfaces.logger_interface import NullLogger

    def get_logger(_: str) -> NullLogger:
        """Return a NullLogger when unified logging infrastructure is unavailable."""
        return NullLogger()


logger = get_logger(__name__)


@dataclass
class TestGenerationConfig:
    """テスト生成設定"""

    project_root: Path
    source_patterns: list[str]
    test_patterns: list[str]
    template_style: str = "ddd_compliant"
    spec_prefix: str = "SPEC"
    max_tests_per_class: int = 15
    include_async_tests: bool = True
    include_performance_tests: bool = True
    mock_external_dependencies: bool = True


@dataclass
class ClassInfo:
    """クラス情報"""

    name: str
    file_path: Path
    methods: list[str]
    dependencies: list[str]
    is_async: bool
    docstring: str | None
    complexity_score: int


@dataclass
class TestGenerationResult:
    """テスト生成結果"""

    generated_files: list[str]
    skipped_files: list[str]
    errors: list[str]
    total_test_cases: int
    execution_time_seconds: float
    quality_metrics: dict[str, Any]


class BatchTestGenerator:
    """一括テスト生成器

    責務:
    - 未テストモジュールの自動検出
    - SPEC準拠テストファイル生成
    - DDD準拠テンプレート適用
    - 依存関係モック自動生成
    """

    def __init__(self, config: TestGenerationConfig, dry_run: bool = False) -> None:
        """初期化

        Args:
            config: テスト生成設定
            dry_run: True の場合、実際のファイル生成を行わない
        """
        self.config = config
        self.project_root = config.project_root
        self.generated_count = 0
        self.dry_run = dry_run
        self.templates = {
            "ddd_compliant": self._get_ddd_template(),
            "basic": self._get_basic_template(),
            "advanced": self._get_advanced_template(),
        }

    def generate_tests_batch(self, target_modules: list[str] | None = None) -> TestGenerationResult:
        """一括テスト生成実行

        Args:
            target_modules: 対象モジュールリスト（Noneで全対象）

        Returns:
            TestGenerationResult: 生成結果
        """
        start_time = project_now().datetime
        logger.info("一括テスト生成開始")
        try:
            if target_modules is None:
                target_classes = self._discover_untested_modules()
            else:
                target_classes = self._analyze_specified_modules(target_modules)
            logger.info(f"対象クラス数: {len(target_classes)}")
            generated_files = []
            skipped_files = []
            errors = []
            total_test_cases = 0
            for class_info in target_classes:
                try:
                    if self.dry_run:
                        test_file_path = self._get_corresponding_test_file(class_info.file_path)
                        test_count = len(class_info.methods) + 2
                        generated_files.append(str(test_file_path))
                        total_test_cases += test_count
                        logger.info(f"[DRY-RUN] 生成対象: {test_file_path} (テストケース数: {test_count})")
                    else:
                        result = self._generate_test_for_class(class_info)
                        if result["success"]:
                            generated_files.append(result["file_path"])
                            total_test_cases += result["test_count"]
                            logger.info(f"生成完了: {result['file_path']}")
                        else:
                            skipped_files.append(class_info.file_path)
                            errors.extend(result.get("errors", []))
                except Exception as e:
                    errors.append(f"{class_info.file_path}: {e!s}")
                    logger.exception("生成エラー %s", class_info.file_path)
            quality_metrics = self._calculate_quality_metrics(generated_files, total_test_cases)
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            result = TestGenerationResult(
                generated_files=generated_files,
                skipped_files=skipped_files,
                errors=errors,
                total_test_cases=total_test_cases,
                execution_time_seconds=execution_time,
                quality_metrics=quality_metrics,
            )
            logger.info("一括テスト生成完了: %sファイル、%sテストケース", len(generated_files), total_test_cases)
            return result
        except Exception:
            logger.exception("一括テスト生成エラー")
            raise

    def _discover_untested_modules(self) -> list[ClassInfo]:
        """未テストモジュール発見"""
        untested_classes = []
        for pattern in self.config.source_patterns:
            for source_file in self.project_root.rglob(pattern):
                if self._should_skip_file(source_file):
                    continue
                test_file = self._get_corresponding_test_file(source_file)
                if not test_file.exists():
                    classes = self._extract_class_info(source_file)
                    untested_classes.extend(classes)
        return untested_classes

    def _analyze_specified_modules(self, module_paths: list[str]) -> list[ClassInfo]:
        """指定モジュール解析"""
        specified_classes = []
        for module_path in module_paths:
            file_path = Path(module_path)
            if not file_path.is_absolute():
                file_path = self.project_root / file_path
            if file_path.exists() and file_path.is_file():
                if self._should_skip_file(file_path):
                    logger.info(f"スキップ: {file_path}")
                    continue
                classes = self._extract_class_info(file_path)
                specified_classes.extend(classes)
            else:
                logger.warning(f"ファイルが見つからないか、ディレクトリです: {module_path}")
        return specified_classes

    def _extract_class_info(self, file_path: Path) -> list[ClassInfo]:
        """クラス情報抽出"""
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class_node(node, file_path, content)
                    classes.append(class_info)
            return classes
        except Exception as e:
            logger.warning(f"クラス情報抽出エラー {file_path}: {e}")
            return []

    def _analyze_class_node(self, node: ast.ClassDef, file_path: Path, content: str) -> ClassInfo:
        """クラスノード解析"""
        methods = []
        dependencies = set()
        is_async = False
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                if isinstance(item, ast.AsyncFunctionDef):
                    is_async = True
            elif isinstance(item, ast.AsyncFunctionDef):
                methods.append(item.name)
                is_async = True
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    dependencies.add(alias.name)
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    dependencies.add(item.module)
        complexity_score = self._calculate_complexity_score(node)
        return ClassInfo(
            name=node.name,
            file_path=file_path,
            methods=methods,
            dependencies=list(dependencies),
            is_async=is_async,
            docstring=ast.get_docstring(node),
            complexity_score=complexity_score,
        )

    def _calculate_complexity_score(self, node: ast.ClassDef) -> int:
        """複雑度スコア計算"""
        score = 0
        methods = [item for item in node.body if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)]
        score += len(methods) * 2
        for method in methods:
            score += self._calculate_nesting_depth(method)
        for item in ast.walk(node):
            if isinstance(item, ast.If | ast.While | ast.For | ast.Try):
                score += 1
        return score

    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """ネストレベル計算"""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.With | ast.Try):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def _generate_test_for_class(self, class_info: ClassInfo) -> dict[str, Any]:
        """クラス用テスト生成"""
        try:
            test_file_path = self._get_corresponding_test_file(class_info.file_path)
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            template = self.templates[self.config.template_style]
            test_content = self._generate_test_content(class_info, template)
            with test_file_path.open("w", encoding="utf-8") as f:
                f.write(test_content)
            test_count = len(class_info.methods) + 2
            return {"success": True, "file_path": str(test_file_path), "test_count": test_count}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def _generate_test_content(self, class_info: ClassInfo, template: str) -> str:
        """テストコンテンツ生成"""
        variables = {
            "class_name": class_info.name,
            "module_path": self._get_module_path(class_info.file_path),
            "test_class_name": f"Test{class_info.name}",
            "docstring": class_info.docstring or f"{class_info.name}のテスト",
            "dependencies": self._generate_dependency_mocks(class_info.dependencies),
            "method_tests": self._generate_method_tests(class_info),
            "async_decorator": "@pytest.mark.asyncio" if class_info.is_async else "",
            "imports": self._generate_imports(class_info),
            "spec_prefix": self._generate_spec_prefix(class_info.name),
        }
        return template.format(**variables)

    def _generate_dependency_mocks(self, dependencies: list[str]) -> str:
        """依存関係モック生成"""
        if not dependencies or not self.config.mock_external_dependencies:
            return ""
        mock_fixtures = []
        for dep in dependencies[:5]:
            clean_name = re.sub("[^\\w]", "_", dep.split(".")[-1].lower())
            mock_fixtures.append(
                f'\n    @pytest.fixture\n    def mock_{clean_name}(self):\n        """${dep} のモック"""\n        return Mock()'
            )
        return "\n".join(mock_fixtures)

    def _generate_method_tests(self, class_info: ClassInfo) -> str:
        """メソッドテスト生成"""
        method_tests = []
        spec_counter = 2
        method_tests.append(
            f'\n    @mark.spec("{self._generate_spec_prefix(class_info.name)}-001")\n    def test_initialization(self):\n        """初期化テスト"""\n        # Arrange & Act & Assert パターン実装\n        assert True  # TODO: 実装する'
        )
        for method in class_info.methods[: self.config.max_tests_per_class - 1]:
            if method.startswith("_"):
                continue
            spec_id = f"{self._generate_spec_prefix(class_info.name)}-{spec_counter:03d}"
            async_decorator = "@pytest.mark.asyncio\n    " if class_info.is_async and "async" in method else ""
            method_tests.append(
                f'\n    @mark.spec("{spec_id}")\n    {async_decorator}def test_{method}(self):\n        """${method}テスト"""\n        # Arrange\n        # TODO: テストデータ準備\n\n        # Act\n        # TODO: メソッド実行\n\n        # Assert\n        # TODO: 結果検証\n        assert True  # TODO: 実装する'
            )
            spec_counter += 1
        return "\n".join(method_tests)

    def _generate_imports(self, class_info: ClassInfo) -> str:
        """インポート生成"""
        imports = [
            "import pytest",
            "from pathlib import Path",
            "from unittest.mock import Mock, patch, AsyncMock"
            if class_info.is_async
            else "from unittest.mock import Mock, patch",
            "from pytest import mark",
        ]
        module_path = self._get_module_path(class_info.file_path)
        imports.append(f"\nfrom {module_path} import {class_info.name}")
        return "\n".join(imports)

    def _generate_spec_prefix(self, class_name: str) -> str:
        """SPEC ID プレフィックス生成"""
        abbreviation = "".join([c for c in class_name if c.isupper()])[:3]
        if len(abbreviation) < 2:
            abbreviation = class_name[:3].upper()
        return f"SPEC-{abbreviation}"

    def _get_module_path(self, file_path: Path) -> str:
        """モジュールパス取得"""
        relative_path = file_path.relative_to(self.project_root)
        return str(relative_path.with_suffix("")).replace("/", ".")

    def _get_corresponding_test_file(self, source_file: Path) -> Path:
        """対応するテストファイルパス取得"""
        if source_file.is_absolute():
            try:
                relative_path = source_file.relative_to(self.project_root / "src" / "noveler")
            except ValueError:
                logger.warning(f"ファイルがプロジェクト外: {source_file}")
                return self.project_root / "tests" / "unit" / "unknown" / f"test_{source_file.name}"
        else:
            relative_path = Path(str(source_file).replace("noveler/", ""))
        test_file_name = f"test_{source_file.name}"
        return self.project_root / "tests" / "unit" / relative_path.parent / test_file_name

    def _should_skip_file(self, file_path: Path) -> bool:
        """ファイルスキップ判定"""
        skip_patterns = [
            "__pycache__",
            "__init__.py",
            "test_",
            ".pyc",
            "migrations/",
            "noveler/tools/",
            "backup/",
            "archive/",
            "temp/",
        ]
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def _calculate_quality_metrics(self, generated_files: list[str], test_count: int) -> dict[str, Any]:
        """品質メトリクス計算"""
        return {
            "files_generated": len(generated_files),
            "total_test_cases": test_count,
            "average_tests_per_file": test_count / len(generated_files) if generated_files else 0,
            "spec_compliance_rate": 1.0,
            "coverage_improvement_estimate": len(generated_files) * 15,
            "generation_efficiency": test_count / max(1, self.generated_count),
        }

    def _get_ddd_template(self) -> str:
        """DDD準拠テストテンプレート"""
        return '#!/usr/bin/env python3\n"""{docstring}\n\n{class_name}の動作を検証するユニットテスト\nDDD準拠・包括的テストカバレッジ対応版\n"""\n\n{imports}\n\n\nclass {test_class_name}:\n    """{class_name} テストクラス"""\n{dependencies}\n{method_tests}'

    def _get_basic_template(self) -> str:
        """基本テストテンプレート"""
        return '#!/usr/bin/env python3\n"""{docstring}\n\n{class_name}の基本テスト\n"""\n\n{imports}\n\n\nclass {test_class_name}:\n    """{class_name} テストクラス"""\n{method_tests}'

    def _get_advanced_template(self) -> str:
        """高度テストテンプレート"""
        return '#!/usr/bin/env python3\n"""{docstring}\n\n{class_name}の詳細テスト\nパフォーマンス・セキュリティ・エラーハンドリング含む\n"""\n\n{imports}\nimport time\nimport psutil\nfrom datetime import datetime\n\n\nclass {test_class_name}:\n    """{class_name} テストクラス"""\n{dependencies}\n{method_tests}\n\n    @mark.spec("{spec_prefix}-999")\n    def test_performance_baseline(self):\n        """パフォーマンスベースラインテスト"""\n        start_time = time.time()\n        # TODO: パフォーマンステスト実装\n        execution_time = time.time() - start_time\n        assert execution_time < 1.0  # 1秒以内の実行'

    def export_generation_report(self, result: TestGenerationResult, output_path: Path | None = None) -> None:
        """生成レポートエクスポート"""
        if output_path is None:
            output_path = self.project_root / "temp" / "test_generation_report.json"
        report_data = {
            "generation_timestamp": project_now().datetime.isoformat(),
            "configuration": asdict(self.config),
            "results": asdict(result),
            "recommendations": self._generate_recommendations(result),
        }
        if self.dry_run:
            logger.info(f"[DRY-RUN] レポート出力予定: {output_path}")
            console.print("\n=== DRY-RUN レポート内容 ===")
            report_json = json.dumps(report_data, ensure_ascii=False, indent=2, default=str)
            console.print(report_json[:1000])
            if len(report_json) > 1000:
                console.print("... (以下省略)")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"生成レポートをエクスポート: {output_path}")

    def _generate_recommendations(self, result: TestGenerationResult) -> list[str]:
        """改善推奨事項生成"""
        recommendations = []
        if result.quality_metrics["average_tests_per_file"] < 10:
            recommendations.append("テストケース数を増やして網羅性を向上")
        if len(result.errors) > 0:
            recommendations.append("生成エラーの原因調査と修正")
        if result.quality_metrics["files_generated"] > 20:
            recommendations.append("並行テスト実行でCI/CD効率化")
        recommendations.append("生成されたテストの手動レビューと調整実施")
        recommendations.append("テストデータとモックの具体的な実装")
        return recommendations


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="一括テスト生成ツール")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--pattern", action="append", default=["noveler/**/*.py"], help="対象ファイルパターン")
    parser.add_argument(
        "--template",
        choices=["ddd_compliant", "basic", "advanced"],
        default="ddd_compliant",
        help="テンプレートスタイル",
    )
    parser.add_argument("--max-tests", type=int, default=15, help="クラス当たり最大テスト数")
    parser.add_argument("--targets", nargs="*", help="対象モジュール指定")
    parser.add_argument("--output-report", type=Path, help="レポート出力先")
    parser.add_argument("--dry-run", action="store_true", help="実際のファイル生成を行わずに対象の確認のみ")
    args = parser.parse_args()
    config = TestGenerationConfig(
        project_root=args.project_root,
        source_patterns=args.pattern,
        test_patterns=["tests/**/test_*.py"],
        template_style=args.template,
        max_tests_per_class=args.max_tests,
        include_async_tests=True,
        include_performance_tests=args.template == "advanced",
        mock_external_dependencies=True,
    )
    try:
        generator = BatchTestGenerator(config, dry_run=args.dry_run)
        result = generator.generate_tests_batch(args.targets)
        if args.output_report:
            generator.export_generation_report(result, args.output_report)
        else:
            generator.export_generation_report(result)
        if args.dry_run:
            console.print("\n🔍 [DRY-RUN MODE] 一括テスト生成シミュレーション完了!")
            console.print(f"📁 生成予定ファイル数: {len(result.generated_files)}")
            console.print(f"🧪 生成予定テストケース数: {result.total_test_cases}")
            console.print(f"⏱️  分析時間: {result.execution_time_seconds:.2f}秒")
            if result.generated_files:
                console.print("\n生成予定ファイル一覧:")
                for file in result.generated_files[:10]:
                    console.print(f"  - {file}")
                if len(result.generated_files) > 10:
                    console.print(f"  ... 他 {len(result.generated_files) - 10} ファイル")
        else:
            console.print("\n🎉 一括テスト生成完了!")
            console.print(f"📁 生成ファイル数: {len(result.generated_files)}")
            console.print(f"🧪 テストケース数: {result.total_test_cases}")
            console.print(f"⏱️  実行時間: {result.execution_time_seconds:.2f}秒")
        if result.errors:
            console.print(f"⚠️  エラー数: {len(result.errors)}")
            for error in result.errors[:3]:
                console.print(f"   - {error}")
        console.print("\n📊 品質メトリクス:")
        for key, value in result.quality_metrics.items():
            console.print(f"   - {key}: {value}")
        return 0 if not result.errors else 1
    except Exception:
        logger.exception("一括テスト生成エラー")
        return 1


if __name__ == "__main__":
    sys.exit(main())
