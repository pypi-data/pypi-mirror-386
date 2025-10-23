#!/usr/bin/env python3

"""Domain.entities.infrastructure_integration_aggregate
Where: Domain aggregate coordinating infrastructure integration data.
What: Manages registered services, metrics, and configuration hierarchies.
Why: Bridges domain and infrastructure concerns for integration workflows.
"""

from __future__ import annotations

"""インフラ統合アグリゲート(DDD実装)

レガシーインフラアダプターをDDDアーキテクチャに統合する。
技術的関心事を適切に分離し、ビジネスロジックとインフラを協調させる。
"""


import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

# キャッシュデータの型変数
CacheData = TypeVar("CacheData")

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class InfrastructureServiceType(Enum):
    """インフラサービス種別"""

    QUALITY_CHECKER = "quality_checker"
    EPISODE_MANAGER = "episode_manager"
    CONFIG_LOADER = "config_loader"
    CACHE_MANAGER = "cache_manager"
    FILE_SYSTEM = "file_system"
    BACKUP_MANAGER = "backup_manager"


class ServiceStatus(Enum):
    """サービス状態"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceMetrics:
    """サービスメトリクス(値オブジェクト)"""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    peak_memory_usage: int = 0
    last_execution_time: datetime | None = None
    error_rate: float = 0.0

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100.0


@dataclass
class ServiceExecutionResult:
    """サービス実行結果(値オブジェクト)"""

    success: bool
    service_name: str
    execution_time: float
    data: dict[str, Any]
    cache_hit: bool = False
    used_fallback: bool = False
    fallback_service: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass
class ServiceHealthStatus:
    """サービス健康状態(値オブジェクト)"""

    service_name: str
    status: ServiceStatus
    last_check_time: datetime
    metrics: ServiceMetrics
    error_details: str | None = None
    uptime: float = 0.0


@dataclass
class BatchExecutionResult:
    """バッチ実行結果(値オブジェクト)"""

    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    execution_time: float
    batch_groups: list[dict[str, Any]]
    detailed_results: list[ServiceExecutionResult] = field(default_factory=list)


class InfrastructureService:
    """インフラサービス(エンティティ)

    個別のインフラサービス(レガシーアダプター)を管理する。
    """

    def __init__(self, service_id: str, service_type: str, name: str, adapter_class: type) -> None:
        self.service_id = service_id
        self.service_type = service_type
        self.name = name
        self.adapter_class = adapter_class
        self.status = ServiceStatus.INACTIVE
        self.created_at = project_now().datetime
        self.last_execution = None
        self.metrics = ServiceMetrics()
        self.configuration = {}
        self._adapter_instance = None

    def activate(self) -> None:
        """サービスを有効化"""
        self.status = ServiceStatus.ACTIVE

    def deactivate(self) -> None:
        """サービスを無効化"""
        self.status = ServiceStatus.INACTIVE

    def mark_error(self, _error_message: str) -> None:
        """エラー状態にマーク"""
        self.status = ServiceStatus.ERROR
        self.metrics.failed_executions += 1

    def record_execution(self, execution_time: float, success: bool) -> None:
        """実行記録を更新"""
        self.metrics.total_executions += 1
        self.last_execution = project_now().datetime

        if success:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1

        # 平均実行時間を更新
        total_time = self.metrics.average_execution_time * (self.metrics.total_executions - 1) + execution_time
        self.metrics.average_execution_time = total_time / self.metrics.total_executions

        # エラー率を更新
        self.metrics.error_rate = (self.metrics.failed_executions / self.metrics.total_executions) * 100.0

    def is_healthy(self) -> bool:
        """サービスが健全かチェック"""
        return (
            self.status == ServiceStatus.ACTIVE and self.metrics.error_rate < 10.0  # エラー率10%未満
        )


class ServiceRegistry:
    """サービスレジストリ(値オブジェクト)

    登録されたサービスの管理とルックアップを提供。
    """

    def __init__(self) -> None:
        self._services: dict[str, InfrastructureService] = {}
        self._service_types: dict[InfrastructureServiceType, list[str]] = {}

    def register(self, service: InfrastructureService) -> None:
        """サービスを登録"""
        self._services[service.name] = service

        # サービス種別別の管理
        if service.service_type not in self._service_types:
            self._service_types[service.service_type] = []
        self._service_types[service.service_type].append(service.name)

    def get_service(self, name: str) -> InfrastructureService | None:
        """名前でサービスを取得"""
        return self._services.get(name)

    def get_services_by_type(self, service_type: InfrastructureServiceType) -> list[InfrastructureService]:
        """種別でサービスを取得"""
        service_names = self._service_types.get(service_type, [])
        return [self._services[name] for name in service_names]

    def get_all_services(self) -> list[InfrastructureService]:
        """全サービスを取得"""
        return list(self._services.values())

    def is_registered(self, name: str) -> bool:
        """サービスが登録されているかチェック"""
        return name in self._services


class InfrastructureIntegrationAggregate:
    """インフラ統合アグリゲート(ルートエンティティ)

    レガシーアダプターの統合管理を行う。
    ビジネスロジック:
    1. サービスの登録・管理・実行
    2. 設定の階層化とオーバーライド
    3. エラー処理とフォールバック
    4. パフォーマンスの監視と最適化
    5. キャッシュの統合管理
    """

    def __init__(
        self,
        aggregate_id: str,
        project_id: str,
        global_config: dict | None = None,
        project_config: dict | None = None,
        cache_config: dict | None = None,
    ) -> None:
        self.aggregate_id = aggregate_id
        self.project_id = project_id
        self.service_registry = ServiceRegistry()
        self.created_at = project_now().datetime
        self.last_activity = project_now().datetime

        # 設定の階層化
        self.global_config = global_config or {}
        self.project_config = project_config or {}
        self.cache_config = cache_config or {}
        self._effective_config = None

        # キャッシュ管理
        self._cache: dict[str, Any] = {}
        self._cache_timestamps: dict[str, datetime] = {}

        # 統計情報
        self.total_executions = 0
        self.successful_executions = 0

    @property
    def active_services(self) -> list[InfrastructureService]:
        """アクティブなサービス一覧"""
        return [
            service for service in self.service_registry.get_all_services() if service.status == ServiceStatus.ACTIVE
        ]

    def register_service(self, service_config: dict[str, Any]) -> InfrastructureService:
        """サービスを登録

        ビジネスルール:
        - 同名サービスの重複登録は禁止
        - 優先度に基づく実行順序の管理
        - 設定の検証と適用
        """
        service_name = service_config["name"]

        if self.service_registry.is_registered(service_name):
            msg = f"サービス '{service_name}' は既に登録されています"
            raise ValueError(msg)

        service_id = str(uuid.uuid4())
        service = InfrastructureService(
            service_id=service_id,
            service_type=InfrastructureServiceType(service_config["service_type"]),
            name=service_name,
            adapter_class=service_config.get("adapter_class"),
        )

        # 設定を適用
        service.configuration = service_config

        # 有効化設定に従って状態を設定
        if service_config.get("enabled", True):
            service.activate()

        self.service_registry.register(service)
        self.last_activity = project_now().datetime

        return service

    def is_service_registered(self, name: str) -> bool:
        """サービスが登録されているかチェック"""
        return self.service_registry.is_registered(name)

    def get_services_by_priority(self) -> list[InfrastructureService]:
        """優先度順でサービスを取得"""
        services = self.service_registry.get_all_services()
        return sorted(
            services,
            key=lambda s: s.configuration.get("priority", 0),
            reverse=True,  # 高優先度が先
        )

    def execute_service(self, service_name: str, execution_context: dict) -> ServiceExecutionResult:
        """サービスを実行

        ビジネスルール:
        - サービスの健康状態チェック
        - キャッシュの確認と利用
        - 実行時間とメトリクスの記録
        - エラー処理
        """
        service = self.service_registry.get_service(service_name)
        if not service:
            return ServiceExecutionResult(
                success=False,
                service_name=service_name,
                execution_time=0.0,
                data={},
                error_message=f"サービス '{service_name}' が見つかりません",
            )

        if not service.is_healthy():
            return ServiceExecutionResult(
                success=False,
                service_name=service_name,
                execution_time=0.0,
                data={},
                error_message=f"サービス '{service_name}' は利用できません",
            )

        start_time = project_now().datetime

        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(service_name, execution_context)
            cached_result = self._get_from_cache(cache_key)

            if cached_result is not None:
                execution_time = (project_now().datetime - start_time).total_seconds()
                return ServiceExecutionResult(
                    success=True,
                    service_name=service_name,
                    execution_time=execution_time,
                    data=cached_result,
                    cache_hit=True,
                )

            # 実際のサービス実行(モック実装)
            result_data: dict[str, Any] = self._execute_service_logic(service, execution_context)
            execution_time = (project_now().datetime - start_time).total_seconds()

            # キャッシュに保存
            if service.configuration.get("cache_enabled", False):
                self._save_to_cache(cache_key, result_data)

            # メトリクス更新
            service.record_execution(execution_time, True)
            self.successful_executions += 1

            return ServiceExecutionResult(
                success=True,
                service_name=service_name,
                execution_time=execution_time,
                data=result_data,
                cache_hit=False,
            )

        except Exception as e:
            execution_time = (project_now().datetime - start_time).total_seconds()
            service.record_execution(execution_time, False)
            service.mark_error(str(e))

            return ServiceExecutionResult(
                success=False,
                service_name=service_name,
                execution_time=execution_time,
                data={},
                error_message=str(e),
            )

        finally:
            self.total_executions += 1
            self.last_activity = project_now().datetime

    def execute_service_with_fallback(
        self, service_name: str, execution_context: dict, simulate_error: bool = False
    ) -> ServiceExecutionResult:
        """フォールバック付きでサービスを実行"""
        # メインサービスの実行
        if not simulate_error:
            result = self.execute_service(service_name, execution_context)
            if result.success:
                return result

        # フォールバック処理
        service = self.service_registry.get_service(service_name)
        fallback_name = service.configuration.get("fallback_service")

        if fallback_name and self.service_registry.is_registered(fallback_name):
            fallback_result = self.execute_service(fallback_name, execution_context)
            fallback_result.used_fallback = True
            fallback_result.fallback_service = fallback_name
            fallback_result.metadata["fallback_reason"] = "メインサービスエラー"
            return fallback_result

        return ServiceExecutionResult(
            success=False,
            service_name=service_name,
            execution_time=0.0,
            data={},
            error_message="メインサービスとフォールバックサービスの両方が利用できません",
        )

    def check_service_health(self, service_name: str) -> ServiceHealthStatus:
        """サービスの健康状態をチェック"""
        service = self.service_registry.get_service(service_name)
        if not service:
            return ServiceHealthStatus(
                service_name=service_name,
                status=ServiceStatus.ERROR,
                last_check_time=project_now().datetime,
                metrics=ServiceMetrics(),
                error_details="サービスが見つかりません",
            )

        return ServiceHealthStatus(
            service_name=service_name,
            status=service.status,
            last_check_time=project_now().datetime,
            metrics=service.metrics,
            uptime=(project_now().datetime - service.created_at).total_seconds(),
        )

    def get_effective_configuration(self) -> dict[str, Any]:
        """有効な設定を取得(階層化とオーバーライド適用)"""
        if self._effective_config is None:
            self._effective_config = {}
            self._effective_config.update(self.global_config)
            self._effective_config.update(self.project_config)

        return self._effective_config.copy()

    def get_service_statistics(self, service_name: str) -> ServiceMetrics:
        """サービスの統計情報を取得"""
        service = self.service_registry.get_service(service_name)
        if not service:
            return ServiceMetrics()

        # 最新の統計情報を計算
        return service.metrics

    def execute_batch_jobs(self, batch_jobs: list[dict[str, Any]]) -> BatchExecutionResult:
        """バッチジョブを実行"""
        start_time = project_now().datetime
        successful_jobs = 0
        failed_jobs = 0
        detailed_results = []

        # サービス別にジョブをグループ化
        service_groups = {}
        for job in batch_jobs:
            service_name = job["service"]
            if service_name not in service_groups:
                service_groups[service_name] = []
            service_groups[service_name].append(job)

        # 各グループを実行
        for service_name, jobs in service_groups.items():
            for job in jobs:
                result = self.execute_service(service_name, job["data"])
                detailed_results.append(result)

                if result.success:
                    successful_jobs += 1
                else:
                    failed_jobs += 1

        execution_time = (project_now().datetime - start_time).total_seconds()

        return BatchExecutionResult(
            total_jobs=len(batch_jobs),
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            execution_time=execution_time,
            batch_groups=list(service_groups.keys()),
            detailed_results=detailed_results,
        )

    def _execute_service_logic(self, service: InfrastructureService, context: dict) -> dict[str, Any]:
        """サービスロジックの実行(モック実装)"""
        # 実際の実装では、service.adapter_classを使用してアダプターを実行
        return {
            "output": f"Service {service.name} executed successfully",
            "context": context,
            "timestamp": project_now().datetime.isoformat(),
        }

    def _generate_cache_key(self, service_name: str, context: dict) -> str:
        """キャッシュキーを生成"""

        context_str = str(sorted(context.items()))
        cache_data: dict[str, Any] = f"{service_name}:{context_str}"
        return hashlib.sha256(cache_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> CacheData | None:
        """キャッシュから取得"""
        if not self.cache_config.get("enabled", False):
            return None

        if cache_key not in self._cache:
            return None

        # TTLチェック
        ttl = self.cache_config.get("ttl_seconds", 3600)
        cache_time = self._cache_timestamps.get(cache_key)
        if cache_time and (project_now().datetime - cache_time).total_seconds() > ttl:
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            return None

        return self._cache[cache_key]

    def _save_to_cache(self, cache_key: str, data: dict) -> None:
        """キャッシュに保存"""
        if not self.cache_config.get("enabled", False):
            return

        max_size = self.cache_config.get("max_size", 1000)
        if len(self._cache) >= max_size:
            # LRU的な削除(簡易実装)
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            self._cache.pop(oldest_key, None)
            self._cache_timestamps.pop(oldest_key, None)

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = project_now().datetime
