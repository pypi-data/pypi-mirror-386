#!/usr/bin/env python3
"""YAMLCODEMAPリポジトリの単体テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from noveler.domain.entities.codemap_entity import (
    ArchitectureLayer,
    B20Compliance,
    CircularImportIssue,
    CodeMapEntity,
    CodeMapMetadata,
    QualityPreventionIntegration,
)
from noveler.infrastructure.repositories.yaml_codemap_repository import YamlCodeMapRepository


class TestYamlCodeMapRepository:
    """YAMLCODEMAPリポジトリのテストクラス"""

    @pytest.fixture
    def temp_dir(self):
        """テンポラリディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def codemap_path(self, temp_dir):
        """CODEMAPファイルパス"""
        return temp_dir / "CODEMAP.yaml"

    @pytest.fixture
    def repository(self, codemap_path):
        """テスト対象のリポジトリ"""
        return YamlCodeMapRepository(codemap_path)

    @pytest.fixture
    def sample_codemap_entity(self):
        """サンプルCODEMAPエンティティ"""
        metadata = CodeMapMetadata(
            name="Test Project",
            architecture="DDD + Clean Architecture",
            version="1.0.0",
            last_updated=datetime(2025, 1, 15, 10, 30, 0),
            commit="abc1234",
        )

        architecture_layers = [
            ArchitectureLayer(
                name="Domain Layer",
                path="noveler/domain/",
                role="Business logic and entities",
                depends_on=[],
                key_modules=["entities", "value_objects", "services"],
                entry_point="entities/__init__.py",
            ),
            ArchitectureLayer(
                name="Application Layer",
                path="noveler/application/",
                role="Use cases and orchestration",
                depends_on=["Domain Layer"],
                key_modules=["use_cases"],
                entry_point="use_cases/__init__.py",
            ),
        ]

        circular_import_issues = [
            CircularImportIssue(
                location="noveler/domain/entities/scene_entity.py",
                issue="循環インポート: novel_cli.py ← scene_entity.py",
                solution="バレルモジュールパターン適用",
                status="完了",
                commit="fix5678",
            )
        ]

        b20_compliance = B20Compliance(
            ddd_layer_separation={"status": "準拠", "dependency_direction": "Domain←Application←Infrastructure"},
            import_management={"scripts_prefix": "統一済み", "relative_imports": "禁止済み"},
            shared_components={"console_usage": "統一済み", "path_service": "統一済み"},
        )

        quality_prevention = QualityPreventionIntegration(
            architecture_linter={"status": "active"},
            hardcoding_detector={"status": "active"},
            automated_prevention={"status": "enabled"},
        )

        return CodeMapEntity(
            metadata=metadata,
            architecture_layers=architecture_layers,
            circular_import_issues=circular_import_issues,
            b20_compliance=b20_compliance,
            quality_prevention=quality_prevention,
        )

    @pytest.fixture
    def sample_yaml_data(self):
        """サンプルYAMLデータ"""
        return {
            "project_structure": {
                "name": "Test Project",
                "architecture": "DDD + Clean Architecture",
                "version": "1.0.0",
                "last_updated": "2025-01-15T10:30:00",
                "commit": "abc1234",
                "layers": [
                    {
                        "name": "Domain Layer",
                        "path": "noveler/domain/",
                        "role": "Business logic and entities",
                        "depends_on": [],
                        "key_modules": ["entities", "value_objects"],
                        "entry_point": "entities/__init__.py",
                    }
                ],
            },
            "circular_import_solutions": {
                "resolved_issues": [
                    {
                        "location": "noveler/domain/entities/scene_entity.py",
                        "issue": "循環インポート問題",
                        "solution": "バレルモジュール適用",
                        "status": "完了",
                        "commit": "fix1234",
                    }
                ]
            },
            "b20_compliance": {
                "ddd_layer_separation": {"status": "準拠"},
                "import_management": {"scripts_prefix": "統一済み"},
                "shared_components": {},
            },
            "quality_prevention_integration": {
                "architecture_linter": {"status": "active"},
                "hardcoding_detector": {"status": "active"},
                "automated_prevention": {"status": "enabled"},
            },
        }

    def test_init_creates_backup_directory(self, temp_dir):
        """初期化時にバックアップディレクトリが作成されるテスト"""
        # Arrange
        codemap_path = temp_dir / "CODEMAP.yaml"

        # Act
        repository = YamlCodeMapRepository(codemap_path)

        # Assert
        assert repository.backup_dir.exists()
        assert repository.backup_dir.name == ".codemap_backups"

    def test_load_codemap_success(self, repository, codemap_path, sample_yaml_data):
        """CODEMAP正常読み込みテスト"""
        # Arrange
        with open(codemap_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_yaml_data, f)

        # Act
        codemap = repository.load_codemap()

        # Assert
        assert codemap is not None
        assert codemap.metadata.name == "Test Project"
        assert codemap.metadata.architecture == "DDD + Clean Architecture"
        assert codemap.metadata.commit == "abc1234"
        assert len(codemap.architecture_layers) == 1
        assert len(codemap.circular_import_issues) == 1

    def test_load_codemap_file_not_exists(self, repository, codemap_path):
        """ファイル不存在時のテスト"""
        # Act
        codemap = repository.load_codemap()

        # Assert
        assert codemap is None

    def test_load_codemap_yaml_error(self, repository, codemap_path):
        """YAML解析エラーのテスト"""
        # Arrange - 不正なYAML
        codemap_path.write_text("invalid: yaml: content: [", encoding="utf-8")

        # Act
        codemap = repository.load_codemap()

        # Assert
        assert codemap is None

    def test_load_codemap_general_error(self, repository):
        """一般的なエラーのテスト"""
        # Arrange - ファイルアクセス権限エラーをシミュレート
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            # Act
            codemap = repository.load_codemap()

            # Assert
            assert codemap is None

    def test_save_codemap_success(self, repository, codemap_path, sample_codemap_entity):
        """CODEMAP正常保存テスト"""
        # Act
        result = repository.save_codemap(sample_codemap_entity)

        # Assert
        assert result is True
        assert codemap_path.exists()

        # 保存されたファイルの内容確認
        with open(codemap_path, encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["project_structure"]["name"] == "Test Project"
        assert saved_data["project_structure"]["commit"] == "abc1234"

    def test_save_codemap_error(self, repository, sample_codemap_entity):
        """CODEMAP保存エラーのテスト"""
        # Arrange - 書き込みエラーをシミュレート
        with patch("builtins.open", side_effect=PermissionError("Write denied")):
            # Act
            result = repository.save_codemap(sample_codemap_entity)

            # Assert
            assert result is False

    def test_create_backup_success(self, repository, codemap_path):
        """バックアップ作成成功テスト"""
        # Arrange
        codemap_path.write_text("test: content", encoding="utf-8")

        # Act
        backup_id = repository.create_backup()

        # Assert
        assert backup_id is not None
        assert backup_id.startswith("codemap_backup_")

        # バックアップファイルが存在することを確認
        backup_file = repository.backup_dir / f"{backup_id}.yaml"
        assert backup_file.exists()
        assert backup_file.read_text(encoding="utf-8") == "test: content"

    def test_create_backup_no_file(self, repository):
        """バックアップ対象ファイルが存在しない場合のテスト"""
        # Act
        backup_id = repository.create_backup()

        # Assert
        assert backup_id is None

    def test_create_backup_error(self, repository, codemap_path):
        """バックアップ作成エラーのテスト"""
        # Arrange
        codemap_path.write_text("test: content", encoding="utf-8")

        with patch("shutil.copy2", side_effect=PermissionError("Backup failed")):
            # Act
            backup_id = repository.create_backup()

            # Assert
            assert backup_id is None

    def test_restore_from_backup_success(self, repository, codemap_path):
        """バックアップ復元成功テスト"""
        # Arrange - バックアップファイルを作成
        backup_content = "restored: content"
        backup_id = "test_backup_20250115_103000"
        backup_file = repository.backup_dir / f"{backup_id}.yaml"
        backup_file.write_text(backup_content, encoding="utf-8")

        # 現在のファイルを作成
        codemap_path.write_text("current: content", encoding="utf-8")

        # Act
        result = repository.restore_from_backup(backup_id)

        # Assert
        assert result is True
        assert codemap_path.read_text(encoding="utf-8") == backup_content

    def test_restore_from_backup_not_found(self, repository):
        """存在しないバックアップからの復元テスト"""
        # Act
        result = repository.restore_from_backup("nonexistent_backup")

        # Assert
        assert result is False

    def test_restore_from_backup_error(self, repository, codemap_path):
        """バックアップ復元エラーのテスト"""
        # Arrange
        backup_id = "test_backup"
        backup_file = repository.backup_dir / f"{backup_id}.yaml"
        backup_file.write_text("backup: content", encoding="utf-8")

        with patch("shutil.copy2", side_effect=PermissionError("Restore failed")):
            # Act
            result = repository.restore_from_backup(backup_id)

            # Assert
            assert result is False

    def test_list_backups_success(self, repository):
        """バックアップ一覧取得成功テスト"""
        # Arrange - バックアップファイルを複数作成
        backup_files = [
            "codemap_backup_20250115_100000.yaml",
            "codemap_backup_20250115_110000.yaml",
            "codemap_backup_20250115_120000.yaml",
        ]

        for filename in backup_files:
            backup_file = repository.backup_dir / filename
            backup_file.write_text(f"backup: {filename}", encoding="utf-8")

        # Act
        backups = repository.list_backups()

        # Assert
        assert len(backups) == 3
        # 新しい順でソートされることを確認
        assert backups[0] == "codemap_backup_20250115_120000"
        assert backups[1] == "codemap_backup_20250115_110000"
        assert backups[2] == "codemap_backup_20250115_100000"

    def test_list_backups_empty(self, repository):
        """バックアップが存在しない場合のテスト"""
        # Act
        backups = repository.list_backups()

        # Assert
        assert backups == []

    def test_list_backups_error(self, repository):
        """バックアップ一覧取得エラーのテスト"""
        # Arrange
        with patch.object(repository.backup_dir, "glob", side_effect=PermissionError("Access denied")):
            # Act
            backups = repository.list_backups()

            # Assert
            assert backups == []

    def test_cleanup_old_backups_success(self, repository):
        """古いバックアップクリーンアップ成功テスト"""
        # Arrange - 5個のバックアップファイルを作成
        backup_files = [f"codemap_backup_2025011{i}_100000.yaml" for i in range(5, 10)]

        for filename in backup_files:
            backup_file = repository.backup_dir / filename
            backup_file.write_text(f"backup: {filename}", encoding="utf-8")

        # Act - 3個だけ保持
        deleted_count = repository.cleanup_old_backups(keep_count=3)

        # Assert
        assert deleted_count == 2
        remaining_backups = repository.list_backups()
        assert len(remaining_backups) == 3

    def test_cleanup_old_backups_sufficient(self, repository):
        """クリーンアップが不要な場合のテスト"""
        # Arrange - 2個のバックアップファイルを作成
        for i in range(2):
            backup_file = repository.backup_dir / f"codemap_backup_2025011{i}_100000.yaml"
            backup_file.write_text(f"backup: {i}", encoding="utf-8")

        # Act - 5個保持設定で実行
        deleted_count = repository.cleanup_old_backups(keep_count=5)

        # Assert
        assert deleted_count == 0

    def test_cleanup_old_backups_error(self, repository):
        """バックアップクリーンアップエラーのテスト"""
        # Arrange
        backup_file = repository.backup_dir / "codemap_backup_20250115_100000.yaml"
        backup_file.write_text("backup: content", encoding="utf-8")

        with patch.object(repository, "list_backups", side_effect=PermissionError("Access denied")):
            # Act
            deleted_count = repository.cleanup_old_backups(keep_count=0)

            # Assert
            assert deleted_count == 0

    def test_validate_yaml_structure_valid(self, repository, codemap_path, sample_yaml_data):
        """YAML構造検証成功テスト"""
        # Arrange
        with open(codemap_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_yaml_data, f)

        # Act
        errors = repository.validate_yaml_structure()

        # Assert
        assert errors == []

    def test_validate_yaml_structure_file_not_exists(self, repository):
        """ファイル不存在時の検証テスト"""
        # Act
        errors = repository.validate_yaml_structure()

        # Assert
        assert "CODEMAP file does not exist" in errors

    def test_validate_yaml_structure_not_dict(self, repository, codemap_path):
        """ルート要素が辞書でない場合のテスト"""
        # Arrange
        with open(codemap_path, "w", encoding="utf-8") as f:
            yaml.dump(["not", "a", "dict"], f)

        # Act
        errors = repository.validate_yaml_structure()

        # Assert
        assert "Root element must be a dictionary" in errors

    def test_validate_yaml_structure_missing_sections(self, repository, codemap_path):
        """必須セクションが不足している場合のテスト"""
        # Arrange - 不完全なYAML
        incomplete_data = {
            "project_structure": {
                "name": "Test Project"
                # 他の必須フィールドが不足
            }
            # 他の必須セクションが不足
        }

        with open(codemap_path, "w", encoding="utf-8") as f:
            yaml.dump(incomplete_data, f)

        # Act
        errors = repository.validate_yaml_structure()

        # Assert
        assert any("Missing field in project_structure" in error for error in errors)
        assert any("Missing 'circular_import_solutions' section" in error for error in errors)
        assert any("Missing 'b20_compliance' section" in error for error in errors)

    def test_validate_yaml_structure_yaml_error(self, repository, codemap_path):
        """YAML構文エラーの検証テスト"""
        # Arrange
        codemap_path.write_text("invalid: yaml: [", encoding="utf-8")

        # Act
        errors = repository.validate_yaml_structure()

        # Assert
        assert any("YAML syntax error" in error for error in errors)

    def test_parse_yaml_to_entity_comprehensive(self, repository, sample_yaml_data):
        """YAML→エンティティ変換の包括テスト"""
        # Act
        entity = repository._parse_yaml_to_entity(sample_yaml_data)

        # Assert
        # メタデータ
        assert entity.metadata.name == "Test Project"
        assert entity.metadata.architecture == "DDD + Clean Architecture"
        assert entity.metadata.version == "1.0.0"
        assert entity.metadata.commit == "abc1234"

        # アーキテクチャレイヤー
        assert len(entity.architecture_layers) == 1
        assert entity.architecture_layers[0].name == "Domain Layer"
        assert entity.architecture_layers[0].path == "noveler/domain/"

        # 循環インポート問題
        assert len(entity.circular_import_issues) == 1
        assert entity.circular_import_issues[0].location == "noveler/domain/entities/scene_entity.py"
        assert entity.circular_import_issues[0].status == "完了"

        # B20準拠性
        assert entity.b20_compliance is not None
        assert entity.b20_compliance.ddd_layer_separation["status"] == "準拠"

        # 品質予防統合
        assert entity.quality_prevention is not None
        assert entity.quality_prevention.architecture_linter["status"] == "active"

    @pytest.mark.parametrize(
        ("date_format", "expected_success"),
        [
            ("2025-01-15T10:30:00", True),
            ("2025-01-15T10:30:00Z", True),
            ("2025-01-15", True),
            ("invalid-date", False),
            (12345, False),
        ],
    )
    def test_parse_yaml_date_formats(self, repository, sample_yaml_data, date_format, expected_success):
        """日付フォーマット解析のパラメータ化テスト"""
        # Arrange
        sample_yaml_data["project_structure"]["last_updated"] = date_format

        # Act
        entity = repository._parse_yaml_to_entity(sample_yaml_data)

        # Assert
        if expected_success:
            assert entity.metadata.last_updated is not None
        else:
            # 無効な日付の場合、現在時刻が使用される
            assert entity.metadata.last_updated is not None
            assert abs((entity.metadata.last_updated - datetime.now(timezone.utc)).total_seconds()) < 60
