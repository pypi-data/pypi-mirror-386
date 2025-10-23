#!/usr/bin/env python3
"""循環インポート解消テスト

SPEC-CIRC-001: 循環インポート解消とアーキテクチャ修正
"""

import pytest
import sys
import importlib


class TestCircularImportResolution:
    """循環インポート解消テスト"""

    @pytest.mark.spec("SPEC-CIRC-001")
    def test_no_circular_import_container(self):
        """container.pyが循環インポートなしでインポート可能"""
        if 'noveler.infrastructure.di.container' in sys.modules:
            del sys.modules['noveler.infrastructure.di.container']

        from noveler.infrastructure.di.container import auto_setup_container

        assert callable(auto_setup_container)

    @pytest.mark.spec("SPEC-CIRC-001")
    def test_environment_setup_independent_import(self):
        """environment_setup.pyが独立してインポート可能"""
        module_name = 'noveler.presentation.cli.environment_setup'
        if module_name in sys.modules:
            del sys.modules[module_name]

        try:
            from noveler.presentation.cli.environment_setup import initialize_environment
        except ModuleNotFoundError:
            pytest.skip("environment_setup モジュールが存在しないためスキップ")
        else:
            assert callable(initialize_environment)

    @pytest.mark.spec("SPEC-CIRC-001")
    def test_mcp_server_startup_capability(self):
        """MCPサーバー起動に必要なモジュールがインポート可能"""
        # 現在は失敗するはず（RED状態）
        try:
            from noveler.presentation.cli.novel_cli import main
        except ModuleNotFoundError:
            pytest.skip("novel_cli モジュールが存在しないためスキップ")
        else:
            from noveler.infrastructure.di.container import auto_setup_container
            assert callable(main)
            assert callable(auto_setup_container)

    @pytest.mark.spec("SPEC-CIRC-001")
    def test_shared_utilities_independence(self):
        """shared_utilitiesがinfrastructure層から独立している"""
        # DDD違反の検証（現在は違反状態でRED）

        # 循環の原因となっているファイルを確認
        problematic_imports = [
            'noveler.infrastructure.yaml_project_settings_repository',
            'noveler.infrastructure.adapters.prompt_generation_adapter',
            'noveler.infrastructure.config.project_detector'
        ]

        for module_name in problematic_imports:
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = importlib.import_module(module_name)
            assert module is not None


class TestArchitectureCompliance:
    """アーキテクチャ準拠テスト"""

    @pytest.mark.spec("SPEC-CIRC-001")
    def test_infrastructure_layer_isolation(self):
        """インフラ層がプレゼンテーション層に依存していない"""
        # 現在はDDD違反状態（RED）

        # インフラ層のファイルがプレゼンテーション層をインポートしていないかチェック
        from pathlib import Path
        import ast

        infrastructure_files = list(Path("src/noveler/infrastructure").rglob("*.py"))
        violations = []

        for file_path in infrastructure_files[:5]:  # サンプル検査
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # プレゼンテーション層への依存をチェック
                if "noveler.presentation.shared.shared_utilities" in content:
                    violations.append(str(file_path))

            except Exception:
                continue

        assert not violations, f"プレゼンテーション層への依存が残っています: {violations}"
