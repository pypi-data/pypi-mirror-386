#!/usr/bin/env python3

"""Application.infrastructure_services.infrastructure_integration_services
Where: Application service layer helpers for infrastructure orchestration.
What: Provides request/response DTOs plus focused services for registration, execution, health, and configuration.
Why: Keeps the main use cases slim while encapsulating reusable infrastructure coordination logic.
"""

from __future__ import annotations

"""インフラ統合関連ドメインサービス集

InfrastructureIntegrationUseCaseから分離された専門ロジックを格納
"""


from dataclasses import dataclass
from typing import Any

from noveler.application.infrastructure_services.infrastructure_configuration import (
    CacheConfiguration,
    InfrastructureConfiguration,
    PerformanceConfiguration,
    ServiceConfiguration,
)
from noveler.application.infrastructure_services.infrastructure_coordination_service import (
    InfrastructureCoordinationService,
)
from noveler.application.infrastructure_services.infrastructure_integration_aggregate import (
    BatchExecutionResult,
    InfrastructureIntegrationAggregate,
    ServiceExecutionResult,
    ServiceHealthStatus,
)


@dataclass(frozen=True)
class RegisterServiceRequest:
    """サービス登録要求"""

    project_id: str
    service_config: ServiceConfiguration
    override_existing: bool = False


@dataclass
class RegisterServiceResponse:
    """サービス登録応答"""

    success: bool
    service_id: str | None = None
    service_name: str | None = None
    validation_errors: list[str] = None
    error_message: str | None = None


@dataclass(frozen=True)
class ExecuteServiceRequest:
    """サービス実行要求"""

    project_id: str
    service_name: str
    execution_context: dict[str, Any]
    use_fallback: bool = True
    cache_enabled: bool = True


@dataclass
class ExecuteServiceResponse:
    """サービス実行応答"""

    success: bool
    execution_result: ServiceExecutionResult | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class HealthCheckRequest:
    """健康状態チェック要求"""

    project_id: str
    service_names: list[str] | None = None  # None の場合は全サービス


@dataclass
class HealthCheckResponse:
    """健康状態チェック応答"""

    success: bool
    health_statuses: list[ServiceHealthStatus] = None
    overall_health: str = "unknown"  # "healthy", "degraded", "critical"
    error_message: str | None = None


@dataclass(frozen=True)
class BatchExecutionRequest:
    """バッチ実行要求"""

    project_id: str
    batch_jobs: list[dict[str, Any]]
    parallel_execution: bool = True
    max_concurrency: int = 5


@dataclass
class BatchExecutionResponse:
    """バッチ実行応答"""

    success: bool
    batch_result: BatchExecutionResult | None = None
    error_message: str | None = None


class InfrastructureServiceRegistrationService:
    """インフラサービス登録専用サービス"""

    def __init__(self, coordination_service: InfrastructureCoordinationService) -> None:
        self.coordination_service = coordination_service

    def register_service(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        request: RegisterServiceRequest,
    ) -> dict[str, Any]:
        """サービスを登録"""
        try:
            # サービス設定の検証
            existing_configs = [service.configuration for service in aggregate.service_registry.get_all_services()]
            validation_errors = self.coordination_service.validate_service_configuration(
                request.service_config,
                [ServiceConfiguration(**config) for config in existing_configs],
            )

            if validation_errors:
                return {"success": False, "validation_errors": validation_errors}

            # 既存サービスとの重複チェック
            if not request.override_existing:
                if aggregate.is_service_registered(request.service_config.name):
                    return {
                        "success": False,
                        "error": f"サービス '{request.service_config.name}' は既に登録されています",
                    }

            # サービスの登録
            service_config_dict = {
                "service_type": request.service_config.service_type.value,
                "name": request.service_config.name,
                "adapter_class": request.service_config.adapter_class,
                "enabled": request.service_config.enabled,
                "priority": request.service_config.priority,
                "timeout": request.service_config.timeout,
                "retry_count": request.service_config.retry_count,
                "fallback_service": request.service_config.fallback_service,
                "dependencies": request.service_config.dependencies,
                "cache_enabled": request.service_config.cache_enabled,
                "cache_key_template": request.service_config.cache_key_template,
                "batch_size": request.service_config.batch_size,
                "health_check_interval": request.service_config.health_check_interval,
            }

            service = aggregate.register_service(service_config_dict)

            return {
                "success": True,
                "service": service,
                "service_id": service.service_id,
                "service_name": service.name,
            }

        except Exception as e:
            return {"success": False, "error": f"サービス登録エラー: {e!s}"}


class InfrastructureServiceExecutionService:
    """インフラサービス実行専用サービス"""

    def execute_service(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        request: ExecuteServiceRequest,
    ) -> dict[str, Any]:
        """サービスを実行"""
        try:
            # サービスの存在確認
            if not aggregate.is_service_registered(request.service_name):
                return {
                    "success": False,
                    "error": f"サービス '{request.service_name}' が見つかりません",
                }

            # 実行コンテキストの準備
            execution_context = request.execution_context.copy()
            execution_context["project_id"] = request.project_id
            execution_context["cache_enabled"] = request.cache_enabled

            # サービス実行(フォールバック考慮)
            if request.use_fallback:
                execution_result = aggregate.execute_service_with_fallback(
                    request.service_name,
                    execution_context,
                )

            else:
                execution_result = aggregate.execute_service(
                    request.service_name,
                    execution_context,
                )

            return {"success": True, "execution_result": execution_result}

        except Exception as e:
            return {"success": False, "error": f"サービス実行エラー: {e!s}"}


class InfrastructureHealthCheckService:
    """インフラヘルスチェック専用サービス"""

    def check_health(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        request: HealthCheckRequest,
    ) -> dict[str, Any]:
        """サービスの健康状態をチェック"""
        try:
            # 対象サービスの特定
            if request.service_names:
                target_services = request.service_names
            else:
                # 全サービスを対象
                target_services = [service.name for service in aggregate.service_registry.get_all_services()]

            # 各サービスの健康状態チェック
            health_statuses = []
            for service_name in target_services:
                if aggregate.is_service_registered(service_name):
                    status = aggregate.check_service_health(service_name)
                    health_statuses.append(status)

            # 全体的な健康状態の評価
            overall_health = self._evaluate_overall_health(health_statuses)

            return {
                "success": True,
                "health_statuses": health_statuses,
                "overall_health": overall_health,
            }

        except Exception as e:
            return {"success": False, "error": f"ヘルスチェックエラー: {e!s}"}

    def _evaluate_overall_health(self, health_statuses: list[ServiceHealthStatus]) -> str:
        """全体的な健康状態を評価"""
        if not health_statuses:
            return "unknown"

        critical_count = sum(1 for status in health_statuses if not status.is_healthy)
        degraded_count = sum(1 for status in health_statuses if status.is_healthy and status.response_time > 5000)

        total_services = len(health_statuses)
        critical_ratio = critical_count / total_services
        degraded_ratio = degraded_count / total_services

        if critical_ratio > 0.5:
            return "critical"
        if critical_ratio > 0.1 or degraded_ratio > 0.3:
            return "degraded"
        return "healthy"


class InfrastructureBatchExecutionService:
    """インフラバッチ実行専用サービス"""

    def execute_batch(
        self,
        aggregate: InfrastructureIntegrationAggregate,
        request: BatchExecutionRequest,
    ) -> dict[str, Any]:
        """バッチ実行"""
        try:
            # バッチジョブの検証
            validation_errors = self._validate_batch_jobs(request.batch_jobs)
            if validation_errors:
                return {"success": False, "validation_errors": validation_errors}

            # バッチ実行
            batch_result = aggregate.execute_batch(
                request.batch_jobs,
                parallel=request.parallel_execution,
                max_concurrency=request.max_concurrency,
            )

            return {"success": True, "batch_result": batch_result}

        except Exception as e:
            return {"success": False, "error": f"バッチ実行エラー: {e!s}"}

    def _validate_batch_jobs(self, batch_jobs: list[dict[str, Any]]) -> list[str]:
        """バッチジョブを検証"""
        errors: list[Any] = []
        for i, job in enumerate(batch_jobs):
            if "service_name" not in job:
                errors.append(f"ジョブ {i}: service_name が必要です")
            if "context" not in job:
                errors.append(f"ジョブ {i}: context が必要です")
            if not isinstance(job.get("context"), dict):
                errors.append(f"ジョブ {i}: context は辞書である必要があります")
        return errors


class InfrastructureStatisticsService:
    """インフラ統計情報専用サービス"""

    def get_service_statistics(self, aggregate: InfrastructureIntegrationAggregate) -> dict[str, Any]:
        """サービス統計情報を取得"""
        try:
            statistics = aggregate.get_service_statistics()
            return {"success": True, "statistics": statistics}
        except Exception as e:
            return {"success": False, "error": f"統計情報取得エラー: {e!s}"}


class InfrastructureConfigurationService:
    """インフラ設定管理専用サービス"""

    def __init__(self, default_config: InfrastructureConfiguration | None = None) -> None:
        self.default_config = default_config or self._create_default_config()

    def get_configuration(self, aggregate: InfrastructureIntegrationAggregate) -> dict[str, Any]:
        """設定情報を取得"""
        try:
            config = aggregate.get_configuration()
            return {"success": True, "configuration": config}
        except Exception as e:
            return {"success": False, "error": f"設定取得エラー: {e!s}"}

    def _create_default_config(self) -> InfrastructureConfiguration:
        """デフォルト設定を作成"""
        cache_config: dict[str, Any] = CacheConfiguration(
            enabled=True,
            max_size=1000,
            ttl_seconds=3600,
            key_prefix="infra_",
        )

        performance_config: dict[str, Any] = PerformanceConfiguration(
            max_concurrent_executions=10,
            default_timeout=30,
            health_check_interval=60,
            retry_backoff_factor=2.0,
        )

        return InfrastructureConfiguration(
            cache_configuration=cache_config,
            performance_configuration=performance_config,
            enable_metrics=True,
            enable_logging=True,
        )


class InfrastructureAggregateManagementService:
    """インフラアグリゲート管理専用サービス"""

    def __init__(self, default_config: InfrastructureConfiguration) -> None:
        self.default_config = default_config
        self._aggregates: dict[str, InfrastructureIntegrationAggregate] = {}

    def get_or_create_aggregate(self, project_id: str) -> InfrastructureIntegrationAggregate:
        """アグリゲートを取得または作成"""
        if project_id not in self._aggregates:
            self._aggregates[project_id] = InfrastructureIntegrationAggregate(
                project_id=project_id,
                configuration=self.default_config,
            )

        return self._aggregates[project_id]

    def get_aggregate(self, project_id: str) -> InfrastructureIntegrationAggregate | None:
        """アグリゲートを取得"""
        return self._aggregates.get(project_id)
