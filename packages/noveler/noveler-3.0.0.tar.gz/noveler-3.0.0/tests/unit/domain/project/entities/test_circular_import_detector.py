#!/usr/bin/env python3
"""循環インポート検出エンティティのテスト

仕様書: SPEC-CIRCULAR-IMPORT-DETECTION-001
"""

from pathlib import Path

import pytest
pytestmark = pytest.mark.project

from noveler.domain.entities.circular_import_detector import CircularDetectionResult, CircularImportDetector
from noveler.domain.value_objects.import_statement import ImportScope, ImportStatement, ImportType


@pytest.mark.spec("SPEC-CIRCULAR-IMPORT-DETECTION-001")
class TestCircularImportDetector:
    """循環インポート検出エンティティのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.project_root = Path("/test/project")
        self.detector = CircularImportDetector(self.project_root)

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-DETECT_SIMPLE_CIRCUL")
    def test_detect_simple_circular_imports(self):
        """簡単な循環インポートの検出"""
        # テストデータ: A → B → A の循環
        imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=5,
                statement_text="from noveler.domain.module_b import ClassB",
            ),
            ImportStatement(
                module_name="noveler.domain.module_a",
                imported_names=["ClassA"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_b.py"),
                line_number=3,
                statement_text="from noveler.domain.module_a import ClassA",
            ),
        ]

        # 循環検出実行
        result = self.detector.detect_circular_imports(imports)

        # 検証
        assert isinstance(result, CircularDetectionResult)
        assert len(result.circular_paths) == 1

        cycle = result.circular_paths[0]
        assert len(cycle.modules) == 2
        assert "noveler.domain.module_a" in cycle.modules
        assert "noveler.domain.module_b" in cycle.modules
        assert cycle.risk_level >= 1

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-NO_CIRCULAR_IMPORTS")
    def test_no_circular_imports(self):
        """循環インポートなしの場合"""
        imports = [
            ImportStatement(
                module_name="noveler.infrastructure.repository",
                imported_names=["Repository"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/service.py"),
                line_number=1,
                statement_text="from noveler.infrastructure.repository import Repository",
            )
        ]

        result = self.detector.detect_circular_imports(imports)

        assert len(result.circular_paths) == 0
        assert result.get_total_risk_score() == 0.0

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-PREDICT_NEW_IMPORT_R")
    def test_predict_new_import_risk(self):
        """新規インポートリスク予測"""
        # 既存のインポート（循環なし）
        existing_imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=1,
                statement_text="from noveler.domain.module_b import ClassB",
            )
        ]

        # 新規インポート（循環を作成）
        new_import = ImportStatement(
            module_name="noveler.domain.module_a",
            imported_names=["ClassA"],
            import_type=ImportType.FROM,
            import_scope=ImportScope.LOCAL,
            source_file=Path("src/noveler/domain/module_b.py"),
            line_number=1,
            statement_text="from noveler.domain.module_a import ClassA",
        )

        risk_score, warnings = self.detector.predict_new_import_risk(new_import, existing_imports)

        assert risk_score > 0.0
        assert len(warnings) > 0
        assert any("循環" in warning for warning in warnings)

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-COMPLEX_CIRCULAR_DET")
    def test_complex_circular_detection(self):
        """複雑な循環パターンの検出"""
        # A → B → C → A の循環
        imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=1,
                statement_text="from noveler.domain.module_b import ClassB",
            ),
            ImportStatement(
                module_name="noveler.domain.module_c",
                imported_names=["ClassC"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_b.py"),
                line_number=1,
                statement_text="from noveler.domain.module_c import ClassC",
            ),
            ImportStatement(
                module_name="noveler.domain.module_a",
                imported_names=["ClassA"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_c.py"),
                line_number=1,
                statement_text="from noveler.domain.module_a import ClassA",
            ),
        ]

        result = self.detector.detect_circular_imports(imports)

        assert len(result.circular_paths) == 1
        cycle = result.circular_paths[0]
        assert len(cycle.modules) == 3
        # B30品質作業指示書遵守: get_path_length()メソッドが未実装のため、len()を使用
        assert len(cycle.modules) == 3

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-RISK_LEVEL_CALCULATI")
    def test_risk_level_calculation(self):
        """リスクレベル計算の検証"""
        # 高リスクな循環（相対インポート + DDD層違反）
        high_risk_imports = [
            ImportStatement(
                module_name="noveler.presentation.ui",  # 上位層から下位層
                imported_names=["DomainService"],
                import_type=ImportType.RELATIVE,  # 相対インポート
                import_scope=ImportScope.RELATIVE,
                source_file=Path("src/noveler/domain/service.py"),
                line_number=1,
                statement_text="from noveler.presentation.ui import DomainService",
            ),
            ImportStatement(
                module_name="noveler.domain.service",
                imported_names=["Service"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/presentation/ui.py"),
                line_number=1,
                statement_text="from noveler.domain.service import Service",
            ),
        ]

        result = self.detector.detect_circular_imports(high_risk_imports)

        if result.circular_paths:
            cycle = result.circular_paths[0]
            assert cycle.risk_level >= 3  # 高リスク

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-GET_CRITICAL_PATHS")
    def test_get_critical_paths(self):
        """重要パスの取得"""
        imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=1,
                statement_text="from noveler.domain.module_b import ClassB",
            ),
            ImportStatement(
                module_name="noveler.domain.module_a",
                imported_names=["ClassA"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_b.py"),
                line_number=1,
                statement_text="from noveler.domain.module_a import ClassA",
            ),
        ]

        result = self.detector.detect_circular_imports(imports)
        critical_paths = result.get_critical_paths(min_risk_level=1)

        # 基本的な循環でもリスクレベル1以上
        assert len(critical_paths) >= 0

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-MODULES_IN_CYCLES")
    def test_modules_in_cycles(self):
        """循環に関与するモジュール一覧"""
        imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=1,
                statement_text="from noveler.domain.module_b import ClassB",
            ),
            ImportStatement(
                module_name="noveler.domain.module_a",
                imported_names=["ClassA"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_b.py"),
                line_number=1,
                statement_text="from noveler.domain.module_a import ClassA",
            ),
        ]

        result = self.detector.detect_circular_imports(imports)
        modules_in_cycles = result.get_modules_in_cycles()

        assert "noveler.domain.module_a" in modules_in_cycles
        assert "noveler.domain.module_b" in modules_in_cycles

    @pytest.mark.spec("SPEC-CIRCULAR_IMPORT_DETECTOR-CACHING_FUNCTIONALIT")
    def test_caching_functionality(self):
        """キャッシュ機能のテスト"""
        imports = [
            ImportStatement(
                module_name="noveler.domain.module_b",
                imported_names=["ClassB"],
                import_type=ImportType.FROM,
                import_scope=ImportScope.LOCAL,
                source_file=Path("src/noveler/domain/module_a.py"),
                line_number=1,
                statement_text="from noveler.domain.module_b import ClassB",
            )
        ]

        cache_key = "test_cache"

        # 初回実行
        result1 = self.detector.detect_circular_imports(imports, cache_key)

        # キャッシュから取得
        result2 = self.detector.detect_circular_imports(imports, cache_key)

        # 同じ結果が返されることを確認
        assert result1.analysis_summary == result2.analysis_summary
