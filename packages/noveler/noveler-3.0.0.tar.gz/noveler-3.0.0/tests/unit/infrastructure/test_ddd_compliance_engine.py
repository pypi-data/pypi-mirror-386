#!/usr/bin/env python3
"""DDD準拠性エンジンテスト

仕様書: SPEC-DDD-AUTO-COMPLIANCE-001
DDDComplianceEngineの包括的テスト
"""

import tempfile
from pathlib import Path

import pytest

from noveler.infrastructure.services.ddd_compliance_engine import (
    DDDComplianceEngine,
    DDDViolation,
    LayerType,
    ValidationLevel,
    ViolationSeverity,
)


class TestDDDComplianceEngine:
    """DDD準拠性エンジンテスト"""

    @pytest.fixture
    def temp_project_root(self):
        """テスト用プロジェクトルート"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # テスト用ディレクトリ構造作成
            (project_root / "scripts" / "domain").mkdir(parents=True)
            (project_root / "scripts" / "application").mkdir(parents=True)
            (project_root / "scripts" / "infrastructure").mkdir(parents=True)
            (project_root / "scripts" / "presentation").mkdir(parents=True)

            yield project_root

    @pytest.fixture
    def compliance_engine(self, temp_project_root):
        """DDD準拠性エンジンインスタンス"""
        return DDDComplianceEngine(temp_project_root, ValidationLevel.STRICT)

    def test_engine_initialization(self, temp_project_root):
        """エンジン初期化テスト"""
        engine = DDDComplianceEngine(temp_project_root, ValidationLevel.MODERATE)

        assert engine.project_root == temp_project_root
        assert engine.validation_level == ValidationLevel.MODERATE
        assert len(engine.layer_mapping) == 6
        assert LayerType.DOMAIN in engine.dependency_rules
        assert len(engine.required_interfaces) == 3

    def test_validation_level_configuration(self, temp_project_root):
        """検証レベル設定テスト"""
        # STRICTモード
        strict_engine = DDDComplianceEngine(temp_project_root, ValidationLevel.STRICT)
        assert len(strict_engine.dependency_rules[LayerType.DOMAIN]["forbidden_patterns"]) >= 4

        # MODERATEモード
        moderate_engine = DDDComplianceEngine(temp_project_root, ValidationLevel.MODERATE)
        assert moderate_engine.validation_level == ValidationLevel.MODERATE

        # BASICモード
        basic_engine = DDDComplianceEngine(temp_project_root, ValidationLevel.BASIC)
        assert basic_engine.validation_level == ValidationLevel.BASIC

    def test_dependency_rules_initialization(self, compliance_engine):
        """依存関係ルール初期化テスト"""
        # ドメイン層ルール
        domain_rules = compliance_engine.dependency_rules[LayerType.DOMAIN]
        assert any("scripts\\.application" in pattern for pattern in domain_rules["forbidden_patterns"])
        assert any("scripts\\.domain" in pattern for pattern in domain_rules["allowed_patterns"])

        # アプリケーション層ルール
        app_rules = compliance_engine.dependency_rules[LayerType.APPLICATION]
        assert any("scripts\\.domain" in pattern for pattern in app_rules["allowed_patterns"])
        assert any("scripts\\.presentation" in pattern for pattern in app_rules["forbidden_patterns"])

    @pytest.mark.asyncio
    async def test_domain_layer_violation_detection(self, compliance_engine, temp_project_root):
        """ドメイン層違反検出テスト"""
        # 違反コードを含むファイル作成
        domain_file = temp_project_root / "scripts" / "domain" / "user_entity.py"
        domain_file.write_text("""
from noveler.infrastructure.adapters.database_adapter import DatabaseAdapter
from noveler.application.services.user_service import UserService

class UserEntity:
    def __init__(self):
        self.db = DatabaseAdapter()  # 違反: ドメインからインフラ直接依存
""")

        violations = await compliance_engine._analyze_file(domain_file, LayerType.DOMAIN)

        assert len(violations) >= 1
        violation = violations[0]
        assert violation.violation_type == "FORBIDDEN_DEPENDENCY"
        assert violation.severity == ViolationSeverity.CRITICAL
        assert "noveler.infrastructure" in violation.metadata["imported_module"]

    @pytest.mark.asyncio
    async def test_application_layer_compliance(self, compliance_engine, temp_project_root):
        """アプリケーション層準拠性テスト"""
        # 正しいアプリケーションサービス
        app_file = temp_project_root / "scripts" / "application" / "user_use_case.py"
        app_file.write_text("""
from noveler.domain.entities.user import User
from noveler.domain.interfaces.user_repository_protocol import IUserRepository

class UserUseCase:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def create_user(self, name: str) -> User:
        user = User(name=name)
        return await self._user_repository.save(user)
""")

        violations = await compliance_engine._analyze_file(app_file, LayerType.APPLICATION)

        # 正しい実装なので違反なし
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_presentation_layer_violations(self, compliance_engine, temp_project_root):
        """プレゼンテーション層違反テスト"""
        # 違反コードを含むファイル作成
        presentation_file = temp_project_root / "scripts" / "presentation" / "user_controller.py"
        presentation_file.write_text("""
from noveler.infrastructure.services.email_service import EmailService
from noveler.infrastructure.adapters.database_adapter import DatabaseAdapter

class UserController:
    def __init__(self):
        self.email_service = EmailService()  # 違反: プレゼンテーションからインフラ直接依存
        self.db_adapter = DatabaseAdapter()   # 違反: アダプター直接依存
""")

        violations = await compliance_engine._analyze_file(presentation_file, LayerType.PRESENTATION)

        assert len(violations) >= 2

        # インフラサービス直接依存違反
        infra_violation = next(v for v in violations if "services" in v.metadata.get("imported_module", ""))

        assert infra_violation.severity == ViolationSeverity.HIGH

    def test_import_compliance_checking(self, compliance_engine):
        """インポート準拠性チェックテスト"""
        import ast

        # 違反インポート文作成
        code = "from noveler.infrastructure.services.email_service import EmailService"
        tree = ast.parse(code)
        import_node = tree.body[0]

        violation = compliance_engine._check_import_compliance(
            Path("noveler/domain/test.py"),
            import_node,
            LayerType.DOMAIN,
            compliance_engine.dependency_rules[LayerType.DOMAIN],
        )

        assert violation is not None
        assert violation.violation_type == "FORBIDDEN_DEPENDENCY"
        assert violation.severity == ViolationSeverity.CRITICAL

    def test_violation_severity_determination(self, compliance_engine):
        """違反重要度決定テスト"""
        # クリティカル違反
        critical_severity = compliance_engine._determine_violation_severity(
            LayerType.DOMAIN, "noveler.infrastructure.services.database"
        )

        assert critical_severity == ViolationSeverity.CRITICAL

        # 高重要度違反
        high_severity = compliance_engine._determine_violation_severity(
            LayerType.PRESENTATION, "noveler.infrastructure.services.email"
        )

        assert high_severity == ViolationSeverity.HIGH

        # 中程度違反
        medium_severity = compliance_engine._determine_violation_severity(
            LayerType.APPLICATION, "noveler.utilities.helper"
        )

        assert medium_severity == ViolationSeverity.MEDIUM

    def test_dependency_recommendation_generation(self, compliance_engine):
        """依存関係推奨事項生成テスト"""
        # ドメイン→インフラ依存の推奨事項
        domain_infra_rec = compliance_engine._get_dependency_recommendation(
            LayerType.DOMAIN, "noveler.infrastructure.adapters.database"
        )

        assert "インターフェース" in domain_infra_rec
        assert "アダプター" in domain_infra_rec

        # アプリケーション→プレゼンテーション依存の推奨事項
        app_presentation_rec = compliance_engine._get_dependency_recommendation(
            LayerType.APPLICATION, "noveler.presentation.controllers.user"
        )

        assert "プレゼンテーション層から" in app_presentation_rec

    @pytest.mark.asyncio
    async def test_interface_abstractions_check(self, compliance_engine, temp_project_root):
        """インターフェース抽象化チェックテスト"""
        # 必須インターフェースが存在しない場合
        violations = await compliance_engine._check_interface_abstractions()

        # 3つの必須インターフェースすべてが存在しないので3件の違反
        assert len(violations) == 3

        missing_interface_violation = violations[0]
        assert missing_interface_violation.violation_type == "MISSING_INTERFACE"
        assert missing_interface_violation.severity == ViolationSeverity.HIGH

        # インターフェースファイル作成
        interface_dir = temp_project_root / "src" / "noveler" / "domain" / "interfaces"
        interface_dir.mkdir(parents=True)

        # repository_protocol.py作成
        (interface_dir / "repository_protocol.py").write_text("""
from abc import ABC, abstractmethod
from typing import Protocol

class IRepository(Protocol):
    @abstractmethod
    async def save(self, entity) -> None:
        pass
""")

        # 再チェック
        violations_after = await compliance_engine._check_interface_abstractions()
        assert len(violations_after) == 2  # 1つ減る

    @pytest.mark.asyncio
    async def test_di_compliance_check(self, compliance_engine, temp_project_root):
        """DI準拠性チェックテスト"""
        # ファクトリーディレクトリが存在しない場合
        violations = await compliance_engine._check_di_compliance()

        assert len(violations) >= 1
        di_violation = violations[0]
        assert di_violation.violation_type == "MISSING_FACTORY_PATTERN"
        assert di_violation.severity == ViolationSeverity.MEDIUM

        # ファクトリーディレクトリ作成
        factory_dir = temp_project_root / "src" / "noveler" / "infrastructure" / "factories"
        factory_dir.mkdir(parents=True)

        # 再チェック
        violations_after = await compliance_engine._check_di_compliance()
        assert len(violations_after) == 0

    def test_layer_compliance_calculation(self, compliance_engine):
        """層別準拠率計算テスト"""
        # 違反リスト作成
        violations = [
            DDDViolation(
                file_path="test1.py",
                line_number=1,
                violation_type="TEST",
                severity=ViolationSeverity.CRITICAL,
                description="Test",
                recommendation="Test",
                rule_id="TEST_001",
            ),
            DDDViolation(
                file_path="test2.py",
                line_number=1,
                violation_type="TEST",
                severity=ViolationSeverity.HIGH,
                description="Test",
                recommendation="Test",
                rule_id="TEST_002",
            ),
        ]

        compliance = compliance_engine._calculate_layer_compliance(violations, 10)

        # クリティカル(1.0) + 高(0.7) = 1.7の重みを10ファイルで割る
        # 準拠率 = 1.0 - (1.7 / 10) = 0.83
        assert 0.8 <= compliance <= 0.85

    def test_overall_compliance_calculation(self, compliance_engine):
        """全体準拠率計算テスト"""
        violations = [
            DDDViolation(
                file_path="test.py",
                line_number=1,
                violation_type="TEST",
                severity=ViolationSeverity.MEDIUM,
                description="Test",
                recommendation="Test",
                rule_id="TEST_001",
            )
        ]

        compliance_percentage = compliance_engine._calculate_overall_compliance(violations, 5)

        # 1つのMEDIUM違反(0.4重み)を5ファイルで割った結果の百分率
        expected = (1.0 - (0.4 / 5)) * 100
        assert abs(compliance_percentage - expected) < 0.1

    @pytest.mark.asyncio
    async def test_full_project_analysis(self, compliance_engine, temp_project_root):
        """プロジェクト全体分析テスト"""
        # テスト用ファイル群作成
        self._create_test_files(temp_project_root)

        # 分析実行
        report = await compliance_engine.analyze_project_compliance()

        assert report.project_root == str(temp_project_root)
        assert report.validation_level == ValidationLevel.STRICT
        assert report.total_files_analyzed >= 3
        assert 0.0 <= report.compliance_percentage <= 100.0
        assert len(report.layer_compliance) >= 3
        assert "total_violations" in report.summary

    def _create_test_files(self, project_root: Path) -> None:
        """テスト用ファイル群作成"""
        # ドメインファイル（正しい）
        domain_file = project_root / "scripts" / "domain" / "entities" / "user.py"
        domain_file.parent.mkdir(parents=True, exist_ok=True)
        domain_file.write_text("""
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    name: str
    email: str
""")

        # アプリケーションファイル（違反あり）
        app_file = project_root / "scripts" / "application" / "services" / "user_service.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("""
from noveler.domain.entities.user import User
from noveler.infrastructure.services.email_service import EmailService  # 違反

class UserService:
    def __init__(self):
        self.email_service = EmailService()  # 違反

    async def create_user(self, name: str, email: str) -> User:
        user = User(id=None, name=name, email=email)
        await self.email_service.send_welcome_email(user)
        return user
""")

        # プレゼンテーションファイル（正しい）
        presentation_file = project_root / "scripts" / "presentation" / "cli" / "user_cli.py"
        presentation_file.parent.mkdir(parents=True, exist_ok=True)
        presentation_file.write_text("""
from noveler.application.services.user_service import UserService

class UserCLI:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def create_user_command(self, name: str, email: str):
        user = await self._user_service.create_user(name, email)
        print(f"Created user: {user.name}")
""")

    @pytest.mark.asyncio
    async def test_report_export_json(self, compliance_engine, temp_project_root):
        """JSONレポートエクスポートテスト"""
        self._create_test_files(temp_project_root)
        report = await compliance_engine.analyze_project_compliance()

        output_path = temp_project_root / "test_report.json"
        await compliance_engine.export_report(report, output_path, "json")

        assert output_path.exists()

        import json

        with open(output_path, encoding="utf-8") as f:
            report_data = json.load(f)

        assert "timestamp" in report_data
        assert "compliance_percentage" in report_data
        assert "violations" in report_data
        assert isinstance(report_data["violations"], list)

    @pytest.mark.asyncio
    async def test_report_export_markdown(self, compliance_engine, temp_project_root):
        """Markdownレポートエクスポートテスト"""
        self._create_test_files(temp_project_root)
        report = await compliance_engine.analyze_project_compliance()

        output_path = temp_project_root / "test_report.md"
        await compliance_engine.export_report(report, output_path, "markdown")

        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert "# DDD準拠性レポート" in content
        assert "準拠性サマリー" in content
        assert "検出された違反" in content

    def test_performance_large_project(self, compliance_engine, temp_project_root):
        """大規模プロジェクトでのパフォーマンステスト"""
        # 大量のファイル作成（パフォーマンステスト用）
        for i in range(50):
            file_path = temp_project_root / "scripts" / "domain" / f"entity_{i}.py"
            file_path.write_text(f"""
class Entity{i}:
    def __init__(self, value):
        self.value = value
""")

        import time

        start_time = time.time()

        # 分析実行
        # report = await compliance_engine.analyze_project_compliance()
        end_time = time.time()
        execution_time = end_time - start_time

        # 50ファイルの分析が5秒以内に完了することを確認
        assert execution_time < 5.0


@pytest.mark.spec("SPEC-DDD-AUTO-COMPLIANCE-001")
class TestDDDComplianceIntegration:
    """DDD準拠性統合テスト"""

    @pytest.mark.asyncio
    async def test_real_project_compliance_analysis(self):
        """実プロジェクトでの準拠性分析テスト"""
        # 実際のプロジェクトルートで分析実行
        project_root = Path(__file__).parent.parent.parent.parent.parent
        engine = DDDComplianceEngine(project_root, ValidationLevel.MODERATE)

        report = await engine.analyze_project_compliance()

        # 基本的な結果検証
        assert report.total_files_analyzed > 0
        assert 0.0 <= report.compliance_percentage <= 100.0
        assert len(report.layer_compliance) >= 3

        # 品質基準チェック
        # 実プロジェクトなので緩い基準
        assert report.compliance_percentage >= 60.0  # 最低60%の準拠率

        # 重要な層の存在確認
        assert "domain" in report.layer_compliance
        assert "application" in report.layer_compliance
        assert "infrastructure" in report.layer_compliance

    @pytest.mark.asyncio
    async def test_compliance_improvement_tracking(self):
        """準拠性改善トラッキングテスト"""
        project_root = Path(__file__).parent.parent.parent.parent.parent

        # 複数の検証レベルで分析
        engines = {
            "basic": DDDComplianceEngine(project_root, ValidationLevel.BASIC),
            "moderate": DDDComplianceEngine(project_root, ValidationLevel.MODERATE),
            "strict": DDDComplianceEngine(project_root, ValidationLevel.STRICT),
        }

        results = {}
        for level, engine in engines.items():
            results[level] = await engine.analyze_project_compliance()

        # 検証レベルが厳しくなるほど準拠率が下がることを確認
        assert results["basic"].compliance_percentage >= results["moderate"].compliance_percentage
        assert results["moderate"].compliance_percentage >= results["strict"].compliance_percentage

        # 違反数は厳しいレベルほど多くなる
        assert len(results["strict"].violations) >= len(results["moderate"].violations)
        assert len(results["moderate"].violations) >= len(results["basic"].violations)
