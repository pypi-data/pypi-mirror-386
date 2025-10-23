"""Infrastructure.repositories.yaml_infrastructure_repository
Where: Infrastructure repository storing infrastructure configuration via YAML.
What: Loads and saves infrastructure configuration files for integration workflows.
Why: Keeps infrastructure configuration data manageable and versionable.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""YAMLインフラリポジトリ(インフラ層実装)

インフラ統合設定をYAMLファイルで永続化するリポジトリ実装。
DDD原則に基づき、ドメインロジックとデータ永続化を分離。
"""


from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.application.infrastructure_services.infrastructure_configuration import (
    CacheConfiguration,
    InfrastructureConfiguration,
    PerformanceConfiguration,
)
from noveler.application.infrastructure_services.infrastructure_integration_aggregate import (
    InfrastructureIntegrationAggregate,
    ServiceStatus,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YamlInfrastructureRepository:
    """YAMLインフラリポジトリ

    インフラ統合設定とアグリゲートの永続化を担当。
    ドメインロジックから技術的関心事を分離。
    """

    def __init__(self, base_path: Path | str | None = None) -> None:
        """
        Args:
            base_path: YAML設定ファイルの基底パス(デフォルト: 現在ディレクトリ)
        """
        self.base_path = Path(base_path) if isinstance(base_path, str) else (base_path or Path())
        self.config_dir = self.base_path / "infrastructure_configs"
        self.config_dir.mkdir(exist_ok=True)

    def save_infrastructure_configuration(self, project_id: str, config: InfrastructureConfiguration) -> None:
        """インフラ設定を保存

        Args:
            project_id: プロジェクトID
            config: インフラ設定
        """
        config_file = self.config_dir / f"{project_id}_infrastructure.yaml"

        # ドメインオブジェクトをYAML形式に変換
        yaml_data: dict[str, Any] = {
            "metadata": {
                "project_id": project_id,
                "saved_at": project_now().datetime.isoformat(),
                "version": "1.0",
            },
            "configuration": config.to_dict(),
        }

        with Path(config_file).open("w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    def load_infrastructure_configuration(
        self,
        project_id: str,
    ) -> InfrastructureConfiguration | None:
        """インフラ設定を読み込み

        Args:
            project_id: プロジェクトID

        Returns:
            インフラ設定(存在しない場合はNone)
        """
        config_file = self.config_dir / f"{project_id}_infrastructure.yaml"

        if not config_file.exists():
            return None

        try:
            with Path(config_file).open(encoding="utf-8") as f:
                yaml_data: dict[str, Any] = yaml.safe_load(f)

            config_data: dict[str, Any] = yaml_data.get("configuration", {})
            return InfrastructureConfiguration.from_dict(config_data)

        except Exception as e:
            msg = f"インフラ設定読み込みエラー: {e!s}"
            raise Exception(msg) from e

    def save_service_configuration(self, project_id: str, service_config: dict[str, Any]) -> None:
        """サービス設定を保存

        個別のサービス設定を追加または更新する。
        """
        # 既存設定を読み込み
        infrastructure_config: dict[str, Any] = self.load_infrastructure_configuration(project_id)

        if infrastructure_config is None:
            # 新規設定作成
            infrastructure_config: dict[str, Any] = InfrastructureConfiguration(
                performance=PerformanceConfiguration(),
                cache=CacheConfiguration(),
                services=[service_config],
            )

        else:
            # 既存設定にサービス追加
            infrastructure_config: dict[str, Any] = infrastructure_config.add_service_config(service_config)

        # 更新された設定を保存
        self.save_infrastructure_configuration(project_id, infrastructure_config)

    def remove_service_configuration(self, project_id: str, service_name: str) -> None:
        """サービス設定を削除"""
        infrastructure_config: dict[str, Any] = self.load_infrastructure_configuration(project_id)

        if infrastructure_config is None:
            return

        # サービス設定を削除
        updated_config: dict[str, Any] = infrastructure_config.remove_service_config(service_name)

        # 更新された設定を保存
        self.save_infrastructure_configuration(project_id, updated_config)

    def save_aggregate_state(
        self,
        aggregate: InfrastructureIntegrationAggregate,
    ) -> None:
        """アグリゲート状態を保存

        Args:
            aggregate: インフラ統合アグリゲート
        """
        state_file = self.config_dir / f"{aggregate.project_id}_aggregate_state.yaml"

        # アグリゲート状態をYAML形式に変換
        services_data: dict[str, Any] = []
        for service in aggregate.service_registry.get_all_services():
            service_data: dict[str, Any] = {
                "service_id": service.service_id,
                "service_type": service.service_type.value,
                "name": service.name,
                "adapter_class": service.adapter_class,
                "status": service.status.value,
                "created_at": service.created_at.isoformat(),
                "last_execution": service.last_execution.isoformat() if service.last_execution else None,
                "metrics": {
                    "total_executions": service.metrics.total_executions,
                    "successful_executions": service.metrics.successful_executions,
                    "failed_executions": service.metrics.failed_executions,
                    "average_execution_time": service.metrics.average_execution_time,
                    "peak_memory_usage": service.metrics.peak_memory_usage,
                    "error_rate": service.metrics.error_rate,
                    "last_execution_time": service.metrics.last_execution_time.isoformat()
                    if service.metrics.last_execution_time
                    else None,
                },
                "configuration": service.configuration,
            }
            services_data.append(service_data)

        yaml_data: dict[str, Any] = {
            "metadata": {
                "aggregate_id": aggregate.aggregate_id,
                "project_id": aggregate.project_id,
                "saved_at": project_now().datetime.isoformat(),
                "version": "1.0",
            },
            "aggregate_state": {
                "created_at": aggregate.created_at.isoformat(),
                "last_activity": aggregate.last_activity.isoformat(),
                "total_executions": aggregate.total_executions,
                "successful_executions": aggregate.successful_executions,
                "global_config": aggregate.global_config,
                "project_config": aggregate.project_config,
                "cache_config": aggregate.cache_config,
            },
            "services": services_data,
        }

        with Path(state_file).open("w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    def load_aggregate_state(
        self,
        project_id: str,
    ) -> dict[str, Any] | None:
        """アグリゲート状態を読み込み

        Args:
            project_id: プロジェクトID

        Returns:
            アグリゲート状態データ(存在しない場合はNone)
        """
        state_file = self.config_dir / f"{project_id}_aggregate_state.yaml"

        if not state_file.exists():
            return None

        try:
            with Path(state_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f)

        except Exception as e:
            msg = f"アグリゲート状態読み込みエラー: {e!s}"
            raise Exception(msg) from e

    def restore_aggregate(
        self,
        project_id: str,
    ) -> InfrastructureIntegrationAggregate | None:
        """アグリゲートを復元

        保存された状態からアグリゲートを復元する。

        Args:
            project_id: プロジェクトID

        Returns:
            復元されたアグリゲート(存在しない場合はNone)
        """
        state_data: dict[str, Any] = self.load_aggregate_state(project_id)

        if state_data is None:
            return None

        try:
            metadata = state_data["metadata"]
            aggregate_state = state_data["aggregate_state"]
            services_data: dict[str, Any] = state_data.get("services", [])

            # アグリゲートを作成
            aggregate = InfrastructureIntegrationAggregate(
                aggregate_id=metadata["aggregate_id"],
                project_id=metadata["project_id"],
                global_config=aggregate_state["global_config"],
                project_config=aggregate_state["project_config"],
                cache_config=aggregate_state["cache_config"],
            )

            # 統計情報を復元
            aggregate.total_executions = aggregate_state["total_executions"]
            aggregate.successful_executions = aggregate_state["successful_executions"]

            # サービスを復元
            for service_data in services_data:
                service_config: dict[str, Any] = service_data["configuration"]
                service = aggregate.register_service(service_config)

                # サービス状態を復元
                service.service_id = service_data["service_id"]
                service.status = ServiceStatus(service_data["status"])
                service.created_at = datetime.fromisoformat(service_data["created_at"])

                if service_data["last_execution"]:
                    service.last_execution = datetime.fromisoformat(service_data["last_execution"])

                # メトリクスを復元
                metrics_data: dict[str, Any] = service_data["metrics"]
                service.metrics.total_executions = metrics_data["total_executions"]
                service.metrics.successful_executions = metrics_data["successful_executions"]
                service.metrics.failed_executions = metrics_data["failed_executions"]
                service.metrics.average_execution_time = metrics_data["average_execution_time"]
                service.metrics.peak_memory_usage = metrics_data["peak_memory_usage"]
                service.metrics.error_rate = metrics_data["error_rate"]

                if metrics_data["last_execution_time"]:
                    service.metrics.last_execution_time = datetime.fromisoformat(metrics_data["last_execution_time"])

            return aggregate

        except Exception as e:
            msg = f"アグリゲート復元エラー: {e!s}"
            raise Exception(msg) from e

    def list_project_configurations(self) -> list[str]:
        """プロジェクト設定一覧を取得

        Returns:
            プロジェクトIDのリスト
        """
        project_ids = []

        for config_file in self.config_dir.glob("*_infrastructure.yaml"):
            project_id = config_file.stem.replace("_infrastructure", "")
            project_ids.append(project_id)

        return sorted(project_ids)

    def delete_project_configuration(self, project_id: str) -> None:
        """プロジェクト設定を削除

        Args:
            project_id: プロジェクトID
        """
        config_file = self.config_dir / f"{project_id}_infrastructure.yaml"
        state_file = self.config_dir / f"{project_id}_aggregate_state.yaml"

        if config_file.exists():
            config_file.unlink()

        if state_file.exists():
            state_file.unlink()

    def backup_configurations(self, backup_dir: Path | str | None = None) -> Path:
        """設定ファイルをバックアップ

        Args:
            backup_dir: バックアップ先ディレクトリ(デフォルト: タイムスタンプ付きディレクトリ)

        Returns:
            バックアップディレクトリのパス
        """
        if backup_dir is None:
            timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
            backup_dir = self.base_path / f"infrastructure_backup_{timestamp}"

        backup_dir.mkdir(exist_ok=True)

        # 全ての設定ファイルをコピー
        for config_file in self.config_dir.glob("*.yaml"):
            backup_file = backup_dir / config_file.name
            backup_file.write_text(config_file.read_text(encoding="utf-8"), encoding="utf-8")

        return backup_dir

    def restore_from_backup(self, backup_dir: Path | str) -> None:
        """バックアップから設定を復元

        Args:
            backup_dir: バックアップディレクトリのパス
        """
        backup_path = Path(backup_dir) if isinstance(backup_dir, str) else backup_dir
        if not backup_path.exists():
            msg = f"バックアップディレクトリが見つかりません: {backup_path}"
            raise FileNotFoundError(msg)

        # バックアップファイルを設定ディレクトリにコピー
        for backup_file in backup_path.glob("*.yaml"):
            config_file = self.config_dir / backup_file.name
            config_file.write_text(backup_file.read_text(encoding="utf-8"), encoding="utf-8")

    def get_repository_statistics(self) -> dict[str, Any]:
        """リポジトリ統計情報を取得

        Returns:
            統計情報
        """
        config_files = list(self.config_dir.glob("*_infrastructure.yaml"))
        state_files = list(self.config_dir.glob("*_aggregate_state.yaml"))

        total_size = sum(f.stat().st_size for f in config_files + state_files)

        return {
            "total_projects": len(config_files),
            "total_aggregates": len(state_files),
            "total_files": len(config_files) + len(state_files),
            "total_size_bytes": total_size,
            "config_directory": str(self.config_dir),
            "last_modified": max((f.stat().st_mtime for f in config_files + state_files), default=0),
        }


class InfrastructureRepositoryFactory:
    """インフラリポジトリファクトリー

    環境に応じて適切なリポジトリ実装を生成する。
    """

    @staticmethod
    def create_yaml_repository(
        base_path: Path | str | None = None, create_directories: bool = True
    ) -> YamlInfrastructureRepository:
        """YAMLリポジトリを作成

        Args:
            base_path: 基底パス
            create_directories: ディレクトリを自動作成するか

        Returns:
            YAMLインフラリポジトリ
        """
        repo = YamlInfrastructureRepository(base_path)

        if create_directories:
            repo.config_dir.mkdir(parents=True, exist_ok=True)

        return repo

    @staticmethod
    def create_memory_repository() -> MemoryInfrastructureRepository:
        """メモリリポジトリを作成(テスト用)

        Returns:
            メモリインフラリポジトリ
        """
        return MemoryInfrastructureRepository()


class MemoryInfrastructureRepository:
    """メモリインフラリポジトリ(テスト用)

    メモリ上でインフラ設定を管理するテスト用実装。
    """

    def __init__(self) -> None:
        self._configurations: dict[str, InfrastructureConfiguration] = {}
        self._aggregate_states: dict[str, dict[str, Any]] = {}

    def save_infrastructure_configuration(self, project_id: str, config: InfrastructureConfiguration) -> None:
        """インフラ設定を保存"""
        self._configurations[project_id] = config

    def load_infrastructure_configuration(
        self,
        project_id: str,
    ) -> InfrastructureConfiguration | None:
        """インフラ設定を読み込み"""
        return self._configurations.get(project_id)

    def save_aggregate_state(
        self,
        aggregate: InfrastructureIntegrationAggregate,
    ) -> None:
        """アグリゲート状態を保存"""
        # 簡易実装(実際の状態保存は省略)
        self._aggregate_states[aggregate.project_id] = {
            "aggregate_id": aggregate.aggregate_id,
            "saved_at": project_now().datetime.isoformat(),
        }

    def restore_aggregate(
        self,
        project_id: str,
    ) -> InfrastructureIntegrationAggregate | None:
        """アグリゲートを復元"""
        if project_id not in self._aggregate_states:
            return None

        # 簡易実装(新しいアグリゲートを作成)
        return InfrastructureIntegrationAggregate(
            aggregate_id="memory_aggregate",
            project_id=project_id,
        )

    def list_project_configurations(self) -> list[str]:
        """プロジェクト設定一覧を取得"""
        return list(self._configurations.keys())

    def clear(self) -> None:
        """全データを削除(テスト用)"""
        self._configurations.clear()
        self._aggregate_states.clear()
