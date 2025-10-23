#!/usr/bin/env python3
"""依存関係分析ツールのユニットテスト

TDD原則に従い、実装前にテストを作成


仕様書: SPEC-UNIT-TEST
"""

# まだ実装されていないモジュールをインポート(RED段階)
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from noveler.infrastructure.monitoring.dependency_analyzer import (
    CircularDependency,
    DependencyAnalyzer,
    DependencyGraph,
    DependencyMetrics,
    LayerViolation,
    ViolationType,
)


class TestDependencyAnalyzer:
    """DependencyAnalyzerのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.analyzer = DependencyAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""

        shutil.rmtree(self.temp_dir)

    def test_initialization_default_settings(self) -> None:
        """アナライザーが正しく初期化されることを確認"""
        assert self.analyzer is not None
        assert self.analyzer.layer_hierarchy == ["domain", "application", "infrastructure", "presentation"]
        assert self.analyzer.violations == []

    def test_simple_dependency_detection(self) -> None:
        """基本的なインポートから依存関係を検出できることを確認"""
        # テスト用ファイルを作成
        domain_file = self.project_root / "domain" / "entities" / "user.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text("""
class User:
    def __init__(self, name: str) -> None:
        self.name = name
""")

        app_file = self.project_root / "application" / "use_cases" / "create_user.py"
        app_file.parent.mkdir(parents=True)
        app_file.write_text("""
from noveler.domain.entities.user import User

class CreateUserUseCase:
    def execute(self, name: str) -> User:
        return User(name)
""")

        # 依存関係を分析
        graph = self.analyzer.analyze_project(self.project_root)

        # 依存関係が正しく検出されることを確認
        assert graph is not None
        assert "application.use_cases.create_user" in graph.nodes
        assert "domain.entities.user" in graph.nodes
        assert graph.has_dependency("application.use_cases.create_user", "domain.entities.user")

    def test_layer_violation_detection(self) -> None:
        """不適切なレイヤー間依存を検出できることを確認"""
        # インフラストラクチャのDatabaseクラスを作成
        infra_file = self.project_root / "infrastructure" / "database.py"
        infra_file.parent.mkdir(parents=True)
        infra_file.write_text("""
class Database:
    def __init__(self) -> None:
        pass
""")

        # ドメイン層がインフラ層に依存(違反)
        domain_file = self.project_root / "domain" / "services" / "user_service.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text("""
from noveler.infrastructure.database import Database

class UserService:
    def __init__(self) -> None:
        self.db = Database()  # 違反:ドメインがインフラに依存
""")

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)

        # レイヤー違反が検出されることを確認
        layer_violations = [v for v in violations if isinstance(v, LayerViolation)]
        assert len(layer_violations) > 0
        assert any("domain" in v.source_module and "infrastructure" in v.target_module for v in layer_violations)

    def test_circular_dependency_detection(self) -> None:
        """循環依存を検出できることを確認"""
        # モジュールA
        module_a = self.project_root / "application" / "module_a.py"
        module_a.parent.mkdir(parents=True)
        module_a.write_text("""
from noveler.application.module_b import ClassB

class ClassA:
    def __init__(self) -> None:
        self.b = ClassB()
""")

        # モジュールB(循環依存)
        module_b = self.project_root / "application" / "module_b.py"
        module_b.write_text("""
from noveler.application.module_a import ClassA

class ClassB:
    def __init__(self) -> None:
        self.a = ClassA()
""")

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)

        # 循環依存が検出されることを確認
        circular_deps = [v for v in violations if isinstance(v, CircularDependency)]
        assert len(circular_deps) > 0
        # cycleのパスが完全名で含まれることを確認
        assert any(
            "application.module_a" in str(v.cycle) and "application.module_b" in str(v.cycle) for v in circular_deps
        )

    def test_external_package_dependency_analysis(self) -> None:
        """外部パッケージへの依存を層別に分析できることを確認"""
        # ドメイン層での外部依存(潜在的な問題)
        domain_file = self.project_root / "domain" / "value_objects" / "email.py"
        domain_file.parent.mkdir(parents=True)
        domain_file.write_text("""
import requests  # 外部パッケージ(ドメイン層では避けるべき)
import re  # 標準ライブラリ(OK)

class Email:
    def __init__(self, value: str) -> None:
        self.value = value
""")

        # インフラ層での外部依存(OK)
        infra_file = self.project_root / "infrastructure" / "api_client.py"
        infra_file.parent.mkdir(parents=True)
        infra_file.write_text("""
import requests  # 外部パッケージ(インフラ層ではOK)

class ApiClient:
    def get(self, url: str):
        return requests.get(url)
""")

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        external_deps = self.analyzer.analyze_external_dependencies(graph)

        # ドメイン層の外部依存が警告されることを確認
        assert "domain" in external_deps
        assert "requests" in external_deps["domain"]

        # 標準ライブラリは外部依存として扱わない
        assert "re" not in external_deps.get("domain", [])

    def test_dependency_metrics_calculation(self) -> None:
        """依存関係の各種メトリクスを計算できることを確認"""
        # テスト用の依存関係を構築
        self._create_test_project_structure()

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        metrics = self.analyzer.calculate_metrics(graph)

        # メトリクスが正しく計算されることを確認
        assert isinstance(metrics, DependencyMetrics)
        assert metrics.coupling >= 0
        assert metrics.cohesion >= 0
        assert metrics.cohesion <= 1
        assert metrics.max_depth >= 0
        assert all(module in metrics.fan_in for module in graph.nodes)
        assert all(module in metrics.fan_out for module in graph.nodes)

    def test_dependency_graph_visualization(self) -> None:
        """依存関係グラフを可視化形式で出力できることを確認"""
        # 簡単な依存関係を作成
        self._create_simple_dependency()

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)

        # Mermaid形式での出力
        mermaid_output = self.analyzer.export_to_mermaid(graph)
        assert "graph TD" in mermaid_output
        assert "domain" in mermaid_output
        assert "application" in mermaid_output
        assert "-->" in mermaid_output

        # Graphviz形式での出力
        dot_output = self.analyzer.export_to_graphviz(graph)
        assert "digraph" in dot_output
        assert "->" in dot_output

    def test_fix_suggestion_generation(self) -> None:
        """違反に対する修正提案を生成できることを確認"""
        # レイヤー違反を含むコードを作成
        self._create_layer_violation()

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)

        # 修正提案を生成
        suggestions = self.analyzer.generate_fix_suggestions(violations)

        # 提案が生成されることを確認
        assert len(suggestions) > 0
        assert any(
            "dependency injection" in s.description.lower() or "interface" in s.description.lower() for s in suggestions
        )

    def test_config_file_exclusion_patterns(self) -> None:
        """特定のパターンを除外できることを確認"""
        # 除外設定
        self.analyzer.add_exclusion_pattern("test_*")
        self.analyzer.add_exclusion_pattern("*_test.py")

        # テストファイルを作成
        test_file = self.project_root / "application" / "test_something.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
from noveler.infrastructure.database import Database  # テストでは許可
""")

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)

        # テストファイルの違反は除外されることを確認
        assert not any("test_something" in str(v) for v in violations)

    def test_custom_rule_addition(self) -> None:
        """カスタム検証ルールを追加できることを確認"""

        # カスタムルール:特定の命名規則違反を検出
        def custom_naming_rule(module_path: str, _dependencies: list[str]) -> list:
            violations = []
            if "create_user" in module_path and not module_path.endswith("_use_case"):
                violations.append(f"Use case module {module_path} should end with '_use_case'")
            return violations

        # ルールを追加
        self.analyzer.add_custom_rule("naming_convention", custom_naming_rule)

        # 違反するファイルを作成
        bad_file = self.project_root / "application" / "create_user.py"
        bad_file.parent.mkdir(parents=True)
        bad_file.write_text("""
class CreateUserUseCase:
    pass
""")

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)

        # カスタムルール違反が検出されることを確認
        custom_violations = [v for v in violations if v.violation_type == ViolationType.CUSTOM]
        assert len(custom_violations) > 0

    def test_ci_pipeline_integration(self) -> None:
        """CI/CDパイプラインで使用できる形式で結果を出力"""
        # 違反を含むプロジェクトを作成
        self._create_violations()

        # 分析実行
        graph = self.analyzer.analyze_project(self.project_root)
        violations = self.analyzer.detect_violations(graph)
        metrics = self.analyzer.calculate_metrics(graph)

        # JUnit XML形式での出力
        junit_xml = self.analyzer.export_to_junit_xml(violations)
        assert '<?xml version="1.0"' in junit_xml
        assert "<testsuites" in junit_xml
        assert "<failure" in junit_xml if violations else True

        # JSON形式での出力
        json_output = self.analyzer.export_to_json(graph, violations, metrics)

        data = json.loads(json_output)
        assert "violations" in data
        assert "metrics" in data
        assert "dependencies" in data

    # ヘルパーメソッド

    def _create_test_project_structure(self) -> None:
        """テスト用のプロジェクト構造を作成"""
        # ドメイン層
        (self.project_root / "domain" / "entities").mkdir(parents=True)
        (self.project_root / "domain" / "entities" / "user.py").write_text("class User: pass")

        # アプリケーション層
        (self.project_root / "application" / "use_cases").mkdir(parents=True)
        (self.project_root / "application" / "use_cases" / "create_user.py").write_text(
            "from noveler.domain.entities.user import User\nclass CreateUser: pass"
        )

        # インフラ層
        (self.project_root / "infrastructure" / "repositories").mkdir(parents=True)
        (self.project_root / "infrastructure" / "repositories" / "user_repository.py").write_text(
            "from noveler.domain.entities.user import User\nclass UserRepository: pass"
        )

    def _create_simple_dependency(self) -> None:
        """シンプルな依存関係を作成"""
        (self.project_root / "domain").mkdir(parents=True)
        (self.project_root / "domain" / "model.py").write_text("class Model: pass")

        (self.project_root / "application").mkdir(parents=True)
        (self.project_root / "application" / "service.py").write_text("from noveler.domain.model import Model")

    def _create_layer_violation(self) -> None:
        """レイヤー違反を作成"""
        # インフラストラクチャ層のファイルを作成
        infra_file = self.project_root / "infrastructure" / "database.py"
        infra_file.parent.mkdir(parents=True)
        infra_file.write_text("""
class Database:
    def __init__(self) -> None:
        pass
""")

        # ドメイン層がインフラ層に依存(違反)
        (self.project_root / "domain" / "services").mkdir(parents=True)
        (self.project_root / "domain" / "services" / "user_service.py").write_text("""
from noveler.infrastructure.database import Database


class UserService:
    def __init__(self) -> None:
        self.db = Database()
""")

    def _create_violations(self) -> None:
        """複数の違反を含むプロジェクトを作成"""
        self._create_layer_violation()

        # 循環依存も追加
        (self.project_root / "application").mkdir(parents=True, exist_ok=True)
        (self.project_root / "application" / "a.py").write_text("from noveler.application.b import B")
        (self.project_root / "application" / "b.py").write_text("from noveler.application.a import A")


class TestDependencyGraph:
    """DependencyGraphのテストクラス"""

    def test_graph_basic_operations(self) -> None:
        """依存グラフの基本的な操作をテスト"""
        graph = DependencyGraph()

        # ノードの追加
        graph.add_node("module_a", layer="domain")
        graph.add_node("module_b", layer="application")

        assert "module_a" in graph.nodes
        assert graph.get_layer("module_a") == "domain"

        # エッジの追加
        graph.add_edge("module_b", "module_a")

        assert graph.has_dependency("module_b", "module_a")
        assert not graph.has_dependency("module_a", "module_b")

        # 依存関係の取得
        deps = graph.get_dependencies("module_b")
        assert "module_a" in deps

        dependents = graph.get_dependents("module_a")
        assert "module_b" in dependents

    def test_cycle_detection(self) -> None:
        """グラフ内の循環を検出できることを確認"""
        graph = DependencyGraph()

        # 循環を作成
        graph.add_node("a")
        graph.add_node("b")
        graph.add_node("c")

        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "a")

        cycles = graph.find_cycles()
        assert len(cycles) > 0
        assert {"a", "b", "c"} in [set(cycle) for cycle in cycles]

    def test_topological_sort(self) -> None:
        """依存関係の順序を正しく計算できることを確認"""
        graph = DependencyGraph()

        # 依存関係を構築
        graph.add_node("base")
        graph.add_node("middle")
        graph.add_node("top")

        graph.add_edge("top", "middle")
        graph.add_edge("middle", "base")

        # トポロジカルソート
        sorted_nodes = graph.topological_sort()

        # baseが最初、topが最後になることを確認
        assert sorted_nodes.index("base") < sorted_nodes.index("middle")
        assert sorted_nodes.index("middle") < sorted_nodes.index("top")


class TestDependencyMetrics:
    """DependencyMetricsのテストクラス"""

    def test_coupling_calculation(self) -> None:
        """結合度(カップリング)が正しく計算されることを確認"""
        metrics = DependencyMetrics()

        # テストデータ
        metrics.fan_out = {"a": 3, "b": 1, "c": 0}
        metrics.fan_in = {"a": 0, "b": 2, "c": 1}

        coupling = metrics.calculate_coupling()
        assert coupling > 0

    def test_cohesion_calculation(self) -> None:
        """凝集度(コヒージョン)が正しく計算されることを確認"""
        metrics = DependencyMetrics()

        # 同一パッケージ内の依存関係
        metrics.internal_dependencies = {"package_a": 5}
        metrics.external_dependencies = {"package_a": 2}

        cohesion = metrics.calculate_cohesion("package_a")
        assert 0 <= cohesion <= 1
        assert cohesion == 5 / (5 + 2)  # 内部依存の割合
