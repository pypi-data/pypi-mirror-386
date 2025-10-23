#!/usr/bin/env python3
"""YAML形式CODEMAPリポジトリ

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.codemap_entity import (
    ArchitectureLayer,
    B20Compliance,
    CircularImportIssue,
    CodeMapEntity,
    CodeMapMetadata,
    QualityPreventionIntegration,
)

# DDD準拠: Infrastructure→Presentation違反を遅延初期化で回避


class _BackupDirectory:
    """Path ラッパー: テストでのメソッド差し替えを容易にする"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.mkdir(exist_ok=True)

    def __truediv__(self, other: object) -> Path:
        return self._path / other

    def __getattr__(self, name: str) -> Any:
        return getattr(self._path, name)

    def glob(self, pattern: str):
        return self._path.glob(pattern)


class YamlCodeMapRepository:
    """YAML形式CODEMAPリポジトリ

    REQ-2.1: YAML読み書き機能
    REQ-2.2: バックアップ・リカバリ機能
    """

    def __init__(self, codemap_path: Path, console_service: Any = None, logger_service: Any = None) -> None:
        """初期化

        Args:
            codemap_path: CODEMAP.yamlファイルパス
            console_service: コンソールサービス（DI注入）
            logger_service: ロガーサービス（DI注入）
        """
        self.codemap_path = codemap_path
        self.backup_dir = _BackupDirectory(codemap_path.parent / ".codemap_backups")
        self._console_service = console_service

        self.logger_service = logger_service
        self.console_service = console_service
    def _get_console(self) -> Any:
        """コンソールサービス取得（DI注入またはフォールバック）"""
        if self._console_service:
            return self._console_service

        # フォールバック: 共通コンソールインスタンス使用
        if not hasattr(self, "_fallback_console"):
            from noveler.presentation.shared.shared_utilities import console

            self._fallback_console = console
        return self._fallback_console

    def load_codemap(self) -> CodeMapEntity | None:
        """CODEMAPを読み込み

        Returns:
            Optional[CodeMapEntity]: CODEMAPエンティティ、失敗時はNone
        """
        try:
            if not self.codemap_path.exists():
                self._get_console().print(f"[yellow]CODEMAP not found: {self.codemap_path}[/yellow]")
                return None

            with self.codemap_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return self._parse_yaml_to_entity(data)

        except yaml.YAMLError as e:
            self._get_console().print(f"[red]YAML parsing error: {e}[/red]")
            return None
        except Exception as e:
            self._get_console().print(f"[red]Failed to load CODEMAP: {e}[/red]")
            return None

    def save_codemap(self, codemap: CodeMapEntity) -> bool:
        """CODEMAPを保存

        Args:
            codemap: CODEMAPエンティティ

        Returns:
            bool: 保存成功時True
        """
        try:
            # エンティティを辞書に変換
            data = codemap.to_dict()

            # YAML形式で保存
            with open(self.codemap_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

            self._get_console().print(f"[green]✅ CODEMAP updated: {self.codemap_path}[/green]")
            return True

        except Exception as e:
            self._get_console().print(f"[red]❌ Failed to save CODEMAP: {e}[/red]")
            return False

    def create_backup(self) -> str | None:
        """バックアップ作成

        Returns:
            Optional[str]: バックアップID、失敗時はNone
        """
        try:
            if not self.codemap_path.exists():
                return None

            # マイクロ秒まで含めて連続呼び出しでも重複しないようにする
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            backup_id = f"codemap_backup_{timestamp}"
            backup_path = self.backup_dir / f"{backup_id}.yaml"

            shutil.copy2(self.codemap_path, backup_path)

            self._get_console().print(f"[dim]📄 Backup created: {backup_id}[/dim]")
            return backup_id

        except Exception as e:
            self._get_console().print(f"[yellow]⚠️ Failed to create backup: {e}[/yellow]")
            return None

    def restore_from_backup(self, backup_id: str) -> bool:
        """バックアップから復元

        Args:
            backup_id: バックアップID

        Returns:
            bool: 復元成功時True
        """
        try:
            backup_path = self.backup_dir / f"{backup_id}.yaml"

            if not backup_path.exists():
                self._get_console().print(f"[red]Backup not found: {backup_id}[/red]")
                return False

            shutil.copy2(backup_path, self.codemap_path)

            self._get_console().print(f"[yellow]🔄 Restored from backup: {backup_id}[/yellow]")
            return True

        except Exception as e:
            self._get_console().print(f"[red]❌ Failed to restore backup: {e}[/red]")
            return False

    def list_backups(self) -> list[str]:
        """バックアップ一覧取得

        Returns:
            list[str]: バックアップID一覧
        """
        try:
            backups = []
            for backup_file in self.backup_dir.glob("codemap_backup_*.yaml"):
                backup_id = backup_file.stem
                backups.append(backup_id)

            return sorted(backups, reverse=True)  # 新しい順

        except Exception as e:
            self._get_console().print(f"[yellow]⚠️ Failed to list backups: {e}[/yellow]")
            return []

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """古いバックアップのクリーンアップ

        Args:
            keep_count: 保持するバックアップ数

        Returns:
            int: 削除したバックアップ数
        """
        try:
            backups = self.list_backups()

            if len(backups) <= keep_count:
                return 0

            deleted_count = 0
            for backup_id in backups[keep_count:]:
                backup_path = self.backup_dir / f"{backup_id}.yaml"
                if backup_path.exists():
                    backup_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                self._get_console().print(f"[dim]🗑️ Cleaned up {deleted_count} old backups[/dim]")

            return deleted_count

        except Exception as e:
            self._get_console().print(f"[yellow]⚠️ Failed to cleanup backups: {e}[/yellow]")
            return 0

    def validate_yaml_structure(self) -> list[str]:
        """YAML構造の検証

        Returns:
            list[str]: 検証エラー一覧
        """
        errors: list[Any] = []

        try:
            if not self.codemap_path.exists():
                errors.append("CODEMAP file does not exist")
                return errors

            with self.codemap_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 必須フィールドチェック
            if not isinstance(data, dict):
                errors.append("Root element must be a dictionary")
                return errors

            # project_structureセクション
            if "project_structure" not in data:
                errors.append("Missing 'project_structure' section")
            else:
                ps = data["project_structure"]
                required_fields = ["name", "architecture", "version", "last_updated"]
                for field in required_fields:
                    if field not in ps:
                        errors.append(f"Missing field in project_structure: {field}")

            # circular_import_solutionsセクション
            if "circular_import_solutions" not in data:
                errors.append("Missing 'circular_import_solutions' section")

            # b20_complianceセクション
            if "b20_compliance" not in data:
                errors.append("Missing 'b20_compliance' section")

        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def _parse_yaml_to_entity(self, data: dict[str, Any]) -> CodeMapEntity:
        """YAML データからエンティティに変換

        Args:
            data: YAML解析結果

        Returns:
            CodeMapEntity: CODEMAPエンティティ
        """
        # project_structure解析
        ps_data: dict[str, Any] = data.get("project_structure", {})

        # last_updatedの解析
        last_updated = ps_data.get("last_updated", "")
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            except ValueError:
                try:
                    last_updated = datetime.strptime(last_updated, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    from noveler.domain.value_objects.project_time import project_now
                    last_updated = project_now().datetime
        elif not isinstance(last_updated, datetime):
            from noveler.domain.value_objects.project_time import project_now
            last_updated = project_now().datetime

        metadata = CodeMapMetadata(
            name=ps_data.get("name", "Unknown Project"),
            architecture=ps_data.get("architecture", "Unknown"),
            version=ps_data.get("version", "1.0.0"),
            last_updated=last_updated,
            commit=ps_data.get("commit"),
        )

        # architecture layers解析
        layers_data: dict[str, Any] = ps_data.get("layers", [])
        architecture_layers = []
        for layer_data in layers_data:
            layer = ArchitectureLayer(
                name=layer_data.get("name", ""),
                path=layer_data.get("path", ""),
                role=layer_data.get("role", ""),
                depends_on=layer_data.get("depends_on", []),
                key_modules=layer_data.get("key_modules", []),
                entry_point=layer_data.get("entry_point"),
            )

            architecture_layers.append(layer)

        # circular_import_solutions解析
        cis_data: dict[str, Any] = data.get("circular_import_solutions", {})
        resolved_issues_data: dict[str, Any] = cis_data.get("resolved_issues", [])
        circular_import_issues = []
        for issue_data in resolved_issues_data:
            issue = CircularImportIssue(
                location=issue_data.get("location", ""),
                issue=issue_data.get("issue", ""),
                solution=issue_data.get("solution", ""),
                status=issue_data.get("status", ""),
                commit=issue_data.get("commit"),
            )

            circular_import_issues.append(issue)

        # b20_compliance解析
        compliance_data: dict[str, Any] = data.get("b20_compliance", {})
        b20_compliance = B20Compliance(
            ddd_layer_separation=compliance_data.get("ddd_layer_separation", {}),
            import_management=compliance_data.get("import_management", {}),
            shared_components=compliance_data.get("shared_components", {}),
        )

        # quality_prevention_integration解析
        quality_data: dict[str, Any] = data.get("quality_prevention_integration", {})
        quality_prevention = QualityPreventionIntegration(
            architecture_linter=quality_data.get("architecture_linter", {}),
            hardcoding_detector=quality_data.get("hardcoding_detector", {}),
            automated_prevention=quality_data.get("automated_prevention", {}),
        )

        return CodeMapEntity(
            metadata=metadata,
            architecture_layers=architecture_layers,
            circular_import_issues=circular_import_issues,
            b20_compliance=b20_compliance,
            quality_prevention=quality_prevention,
        )
