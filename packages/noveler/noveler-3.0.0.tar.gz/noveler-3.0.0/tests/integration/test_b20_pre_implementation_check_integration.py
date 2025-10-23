#!/usr/bin/env python3
"""B20実装着手前チェック統合テスト

仕様書: B20開発作業指示書準拠
"""

import shutil

import tempfile
from pathlib import Path

import pytest

from noveler.application.use_cases.b20_pre_implementation_check_use_case import (
    B20PreImplementationCheckRequest,
    B20PreImplementationCheckUseCase,
)
from noveler.domain.services.b20_pre_implementation_check_service import B20PreImplementationCheckService
from noveler.domain.services.three_commit_cycle_service import ThreeCommitCycleService


class TestB20PreImplementationCheckIntegration:
    """B20実装着手前チェック統合テスト"""

    @pytest.fixture
    def temp_project_root(self):
        """一時プロジェクトルートディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())

        # プロジェクト構造の作成
        directories = [
            "specs",
            "noveler/domain/entities",
            "noveler/domain/value_objects",
            "noveler/domain/services",
            "noveler/application/use_cases",
            "noveler/infrastructure/adapters",
            "noveler/infrastructure/repositories",
            "noveler/presentation/cli",
            "noveler/tests/unit",
            "noveler/tests/integration",
        ]

        for dir_path in directories:
            (temp_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # 基本的なCODEMAP作成
        codemap_content = """project_structure:
  name: test_novel_system
  architecture: DDD + Clean Architecture
  version: 1.0.0
  last_updated: '2025-08-09'
layers:
  - name: Domain Layer
    path: scripts/domain/
    role: Business logic and entities
    depends_on: []
"""

        (temp_dir / "CODEMAP.yaml").write_text(codemap_content)

        yield temp_dir

        # クリーンアップ
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def integration_setup(self, temp_project_root):
        """統合テスト用セットアップ"""
        from src.noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter

        check_service = B20PreImplementationCheckService(temp_project_root)
        cycle_service = ThreeCommitCycleService(temp_project_root)

        # PathServiceAdapterを作成してテスト環境に適用
        path_service = PathServiceAdapter(temp_project_root)

        # 正しいコンストラクタ引数でUseCaseを初期化
        use_case = B20PreImplementationCheckUseCase(
            logger_service=None,
            unit_of_work=None,
            console_service=None,
            path_service=path_service,  # 適切なpath_serviceを提供
            check_service=check_service,
            codemap_update_use_case=None
        )

        return {
            "project_root": temp_project_root,
            "check_service": check_service,
            "cycle_service": cycle_service,
            "use_case": use_case,
            "path_service": path_service,
        }

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-FULL_WORKFLOW_SPECIF")
    def test_full_workflow_specification_to_implementation(self, integration_setup):
        """完全ワークフロー: 仕様書作成から実装許可まで"""
        setup = integration_setup
        use_case = setup["use_case"]
        temp_root = setup["project_root"]

        feature_name = "user_authentication"

        # Step 1: 仕様書なしでのチェック（エラーが期待される）
        request = B20PreImplementationCheckRequest(feature_name=feature_name, target_layer="domain")

        response = use_case.execute(request)

        assert not response.implementation_allowed
        assert response.current_stage == "specification_required"
        assert len(response.errors) > 0

        # Step 2: 仕様書作成
        spec_content = """# ユーザー認証機能仕様書

## 概要
ユーザー認証機能の実装

## 要件
- ユーザーログイン機能
- パスワード検証機能
- セッション管理機能

## 設計方針
- DDD準拠
- Clean Architecture準拠

## 実装方針
- Domain層にUser Entityを配置
- Application層にAuthenticationServiceを配置

## テスト方針
- 単体テスト必須
- 統合テスト必須

## 受け入れ基準
- 認証成功時にセッションが作成される
- 無効な認証情報で認証が拒否される
"""

        spec_file = temp_root / "specs" / f"SPEC-{feature_name.upper()}-001.md"
        spec_file.write_text(spec_content)

        # Step 3: 仕様書ありでのチェック
        response = use_case.execute(request)

        assert response.success
        assert response.current_stage in ["codemap_check_required", "implementation_allowed"]
        assert response.completion_percentage > 0

        # Step 4: テストファイル作成（実装許可のため）
        test_file = temp_root / f"noveler/tests/unit/test_{feature_name}.py"
        test_content = """#!/usr/bin/env python3
\"\"\"ユーザー認証機能のテスト\"\"\"

import pytest

class TestUserAuthentication:
    \"\"\"ユーザー認証テスト\"\"\"

    @pytest.mark.spec('SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-VALID_CREDENTIALS')
    def test_valid_credentials(self):
        \"\"\"有効な認証情報のテスト\"\"\"
        assert True

    @pytest.mark.spec('SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-INVALID_CREDENTIALS')
    def test_invalid_credentials(self):
        \"\"\"無効な認証情報のテスト\"\"\"
        assert True
"""

        test_file.write_text(test_content)

        # Step 5: テスト作成後のチェック
        response = use_case.execute(request)

        # 実装許可状態になることを確認（条件によっては）
        assert response.success
        assert response.completion_percentage >= 16.7  # 最低1つの要件が完了

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-AUTO_FIX_FUNCTIONALI")
    def test_auto_fix_functionality(self, integration_setup):
        """自動修正機能のテスト"""
        setup = integration_setup
        use_case = setup["use_case"]
        temp_root = setup["project_root"]

        feature_name = "auto_fix_test"

        # 仕様書なしで自動修正オプション付きで実行
        request = B20PreImplementationCheckRequest(
            feature_name=feature_name, target_layer="application", auto_fix_issues=True, create_missing_spec=True
        )

        response = use_case.execute(request)

        assert response.success

        # 自動修正結果があることを確認
        if response.auto_fix_results:
            assert "spec_creation" in response.auto_fix_results
            assert response.auto_fix_results["spec_creation"]["success"] is True

        # 自動作成された仕様書の存在確認
        specs_dir = temp_root / "specs"
        expected_pattern = f"*{feature_name.upper().replace('_', '-')}*.md"
        created_specs = list(specs_dir.glob(expected_pattern))
        assert len(created_specs) > 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-GUIDANCE_ONLY_FUNCTI")
    def test_guidance_only_functionality(self, integration_setup):
        """ガイダンス機能のテスト"""
        setup = integration_setup
        use_case = setup["use_case"]

        feature_name = "guidance_test"

        guidance = use_case.get_development_stage_guidance(feature_name)

        assert "current_stage" in guidance
        assert "stage_description" in guidance
        assert "completion_percentage" in guidance
        assert "next_actions" in guidance
        assert "estimated_time" in guidance

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-THREE_COMMIT_CYCLE_I")
    def test_three_commit_cycle_integration(self, integration_setup):
        """3コミットサイクルとの統合テスト"""
        setup = integration_setup
        cycle_service = setup["cycle_service"]
        setup["project_root"]

        feature_name = "cycle_integration_test"

        # 3コミットサイクル開始
        cycle = cycle_service.start_new_cycle(feature_name)

        assert cycle.feature_name == feature_name
        assert not cycle.can_commit_now()

        # サイクル状態の確認
        status = cycle_service.get_cycle_status(feature_name)

        assert status.cycle_exists
        assert status.current_cycle is not None
        assert not status.can_proceed_to_next_stage
        assert len(status.next_stage_requirements) > 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-CLI_INTEGRATION_SIMU")
    def test_cli_integration_simulation(self, integration_setup):
        """CLI統合のシミュレーションテスト"""
        setup = integration_setup
        use_case = setup["use_case"]
        setup["project_root"]

        # CLIコマンド相当の処理をシミュレーション
        feature_name = "cli_integration_test"

        # 1. プレチェック（-s フラグ相当）
        request = B20PreImplementationCheckRequest(
            feature_name=feature_name, target_layer="domain", create_missing_spec=True
        )

        response = use_case.execute(request)

        assert response.success

        # 2. ガイダンス表示（-g フラグ相当）
        guidance = use_case.get_development_stage_guidance(feature_name)

        assert guidance["current_stage"] in ["specification_required", "codemap_check_required"]
        assert len(guidance["next_actions"]) > 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-ERROR_HANDLING_INTEG")
    def test_error_handling_integration(self, integration_setup):
        """エラーハンドリング統合テスト"""
        setup = integration_setup
        use_case = setup["use_case"]

        # 無効な層名でのテスト
        request = B20PreImplementationCheckRequest(feature_name="error_test", target_layer="invalid_layer")

        response = use_case.execute(request)

        # エラーが適切に処理されることを確認
        assert not response.implementation_allowed
        assert len(response.errors) > 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-PERFORMANCE_INTEGRAT")
    def test_performance_integration(self, integration_setup):
        """パフォーマンス統合テスト"""
        setup = integration_setup
        use_case = setup["use_case"]
        temp_root = setup["project_root"]

        # 大量のファイルを作成（ディレクトリも含めて）
        scripts_domain_dir = temp_root / "scripts" / "domain"
        scripts_domain_dir.mkdir(parents=True, exist_ok=True)
        for i in range(50):
            (scripts_domain_dir / f"entity_{i}.py").write_text(f"# Entity {i}")
        feature_name = "performance_test"

        import time

        start_time = time.time()

        request = B20PreImplementationCheckRequest(feature_name=feature_name, target_layer="domain")

        response = use_case.execute(request)

        execution_time = time.time() - start_time

        # 実行時間が合理的な範囲内であることを確認
        assert execution_time < 3.0  # 3秒以内
        assert response.success
        assert response.execution_time_ms < 3000

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-CONCURRENT_ACCESS_SI")
    def test_concurrent_access_simulation(self, integration_setup):
        """並行アクセス シミュレーションテスト"""
        setup = integration_setup
        use_case = setup["use_case"]

        # 複数の機能名で並行してチェック実行をシミュレーション
        feature_names = ["feature_a", "feature_b", "feature_c"]

        responses = []
        for feature_name in feature_names:
            request = B20PreImplementationCheckRequest(feature_name=feature_name, target_layer="domain")

            response = use_case.execute(request)
            responses.append(response)

        # 全てのレスポンスが適切に処理されることを確認
        for response in responses:
            assert response.success
            assert response.execution_time_ms > 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-REAL_WORLD_SCENARIO_")
    def test_real_world_scenario_complete_feature_development(self, integration_setup):
        """実世界シナリオ: 完全な機能開発フロー"""
        setup = integration_setup
        use_case = setup["use_case"]
        cycle_service = setup["cycle_service"]
        temp_root = setup["project_root"]

        feature_name = "complete_feature"

        # Phase 1: 初期チェック（仕様書なし）
        request = B20PreImplementationCheckRequest(
            feature_name=feature_name, target_layer="domain", create_missing_spec=True, auto_fix_issues=True
        )

        response = use_case.execute(request)
        # 最初の実行では実装許可されない可能性があるが、自動修正により改善される

        # Phase 2: 仕様書作成後のチェック
        spec_file = temp_root / "specs" / f"SPEC-{feature_name.upper()}-001.md"
        if spec_file.exists():  # 自動作成された場合:
            # 内容を充実化
            enhanced_spec = """# Complete Feature Specification

## 概要
完全な機能開発のテスト

## 要件
- 要件A
- 要件B
- 要件C

## 設計
- DDD準拠設計
- Clean Architecture準拠

## 実装計画
1. Domain Entity作成
2. Use Case実装
3. Infrastructure実装
4. Presentation実装

## テスト計画
- 単体テスト
- 統合テスト
- E2Eテスト

## 受け入れ基準
- 全テスト成功
- パフォーマンス要件満足
"""
            spec_file.write_text(enhanced_spec)

        # Phase 3: テスト作成
        test_file = temp_root / f"noveler/tests/unit/test_{feature_name}.py"
        test_file.write_text("""#!/usr/bin/env python3
import pytest

class TestCompleteFeature:
    @pytest.mark.spec('SPEC-B20_PRE_IMPLEMENTATION_CHECK_INTEGRATION-BASIC_FUNCTIONALITY')
    def test_basic_functionality(self):
        assert True
""")

        # Phase 4: 再チェック
        response = use_case.execute(request)

        # 改善されていることを確認
        assert response.completion_percentage > 30.0  # 大幅な改善

        # Phase 5: 3コミットサイクルとの統合確認
        cycle_service.start_new_cycle(feature_name)

        # 自動検出された要件があることを確認
        detected_requirements = cycle_service.auto_detect_completed_requirements(feature_name)
        assert len(detected_requirements) > 0
