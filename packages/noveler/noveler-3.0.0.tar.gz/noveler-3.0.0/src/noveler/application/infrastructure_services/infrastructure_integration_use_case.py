# File: src/noveler/application/infrastructure_services/infrastructure_integration_use_case.py
# Purpose: Coordinate infrastructure service registration/execution with refactored domain aggregates.
# Context: Bridges legacy aggregate flows with new orchestration, configuration snapshots, and metrics sinks.

"""Infrastructure integration application use case."""

from __future__ import annotations

from typing import Any

from noveler.application.infrastructure_services.infrastructure_configuration import (
    CacheConfiguration,
    InfrastructureConfiguration,
    PerformanceConfiguration,
)
from noveler.application.infrastructure_services.infrastructure_coordination_service import (
    InfrastructureCoordinationService,
)
from noveler.application.infrastructure_services.infrastructure_integration_aggregate import (
    InfrastructureIntegrationAggregate,
    ServiceHealthStatus,
)
from noveler.application.infrastructure_services.infrastructure_integration_services import (
    BatchExecutionRequest,
    BatchExecutionResponse,
    ExecuteServiceRequest,
    ExecuteServiceResponse,
    HealthCheckRequest,
    HealthCheckResponse,
    InfrastructureAggregateManagementService,
    InfrastructureBatchExecutionService,
    InfrastructureConfigurationService,
    InfrastructureHealthCheckService,
    InfrastructureServiceExecutionService,
    InfrastructureServiceRegistrationService,
    InfrastructureStatisticsService,
    RegisterServiceRequest,
    RegisterServiceResponse,
)
from noveler.application.infrastructure_services.service_execution_orchestrator import ServiceExecutionOrchestrator
from noveler.application.services.infrastructure_integration_mapper import InfrastructureIntegrationMapper
from noveler.application.simple_message_bus import MessageBus
from noveler.domain.interfaces.configuration_service import IConfigurationService
from noveler.domain.interfaces.configuration_source_port import ConfigurationSourcePort
from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort
from noveler.infrastructure.adapters.configuration_source_adapter import ConfigurationSourceAdapter
from noveler.infrastructure.adapters.infrastructure_cache_provider import InMemoryCacheProvider
from noveler.infrastructure.adapters.infrastructure_fallback_strategy import AggregateFallbackStrategy
from noveler.infrastructure.adapters.infrastructure_metrics_sink import LoggingMetricsSink
from noveler.infrastructure.adapters.infrastructure_service_gateway import AggregateServiceGateway
from noveler.infrastructure.adapters.message_bus_metrics_sink import MessageBusMetricsSink
from noveler.infrastructure.adapters.metrics_sink_composite import CompositeMetricsSink
from noveler.infrastructure.adapters.outbox_metrics_sink import OutboxMetricsSink


class InfrastructureIntegrationUseCase:
    """Application use case coordinating infrastructure integration flows."""

    def __init__(
        self,
        coordination_service: InfrastructureCoordinationService,
        default_config: InfrastructureConfiguration | None,
        configuration_provider: IConfigurationService | None = None,
        configuration_source: ConfigurationSourcePort | None = None,
        metrics_sink: MetricsSinkPort | None = None,
        mapper: InfrastructureIntegrationMapper | None = None,
        orchestrator: ServiceExecutionOrchestrator | None = None,
        message_bus: MessageBus | None = None,
    ) -> None:
        self.coordination_service = coordination_service
        self.default_config = default_config

        self._registration_service = InfrastructureServiceRegistrationService(coordination_service)
        self._execution_service = InfrastructureServiceExecutionService()
        self._health_check_service = InfrastructureHealthCheckService()
        self._batch_execution_service = InfrastructureBatchExecutionService()
        self._statistics_service = InfrastructureStatisticsService()
        self._configuration_service = InfrastructureConfigurationService(default_config)
        self._aggregate_management_service = InfrastructureAggregateManagementService(
            self._configuration_service.default_config
        )
        self._configuration_provider = configuration_provider
        self._configuration_source = configuration_source
        if configuration_provider and not configuration_source:
            self._configuration_source = ConfigurationSourceAdapter(configuration_provider)

        logging_sink = LoggingMetricsSink()
        outbox_sink = OutboxMetricsSink()
        bus_sink = MessageBusMetricsSink(message_bus) if message_bus else None
        composite_sink = CompositeMetricsSink([metrics_sink, logging_sink, outbox_sink, bus_sink])
        cache_provider = InMemoryCacheProvider()
        mapper_instance = mapper or InfrastructureIntegrationMapper()
        self._service_execution_orchestrator = orchestrator or ServiceExecutionOrchestrator(
            execution_service=self._execution_service,
            metrics_sink=composite_sink,
            mapper=mapper_instance,
            cache_provider=cache_provider,
            gateway_factory=lambda agg: AggregateServiceGateway(agg, self._execution_service),
            fallback_factory=lambda agg: AggregateFallbackStrategy(agg, self._execution_service),
        )
        self._mapper = mapper_instance
        self._message_bus = message_bus

        self._config_tokens: dict[str, str] = {}
        self._feature_flag_cache: dict[str, dict[str, bool]] = {}

    def register_service(self, request: RegisterServiceRequest) -> RegisterServiceResponse:
        """Register infrastructure service configuration."""
        try:
            aggregate = self._aggregate_management_service.get_or_create_aggregate(request.project_id)
            registration_result = self._registration_service.register_service(aggregate, request)

            if not registration_result["success"]:
                return RegisterServiceResponse(
                    success=False,
                    validation_errors=registration_result.get("validation_errors"),
                    error_message=registration_result.get("error"),
                )

            return RegisterServiceResponse(
                success=True,
                service_id=registration_result["service_id"],
                service_name=registration_result["service_name"],
            )
        except Exception as exc:  # noqa: BLE001
            return RegisterServiceResponse(success=False, error_message=f"サービス登録エラー: {exc!s}")

    def execute_service(self, request: ExecuteServiceRequest) -> ExecuteServiceResponse:
        """Execute infrastructure service with optional refactored orchestration."""
        try:
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return ExecuteServiceResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            if self._use_refactored_flow(request.project_id):
                return self._service_execution_orchestrator.execute(aggregate, request)

            execution_result = self._execution_service.execute_service(aggregate, request)
            if not execution_result["success"]:
                return ExecuteServiceResponse(success=False, error_message=execution_result["error"])

            return ExecuteServiceResponse(success=True, execution_result=execution_result["execution_result"])
        except Exception as exc:  # noqa: BLE001
            return ExecuteServiceResponse(success=False, error_message=f"サービス実行エラー: {exc!s}")

    def check_health(self, request: HealthCheckRequest) -> HealthCheckResponse:
        """Evaluate infrastructure service health."""
        try:
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return HealthCheckResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            health_result = self._health_check_service.check_health(aggregate, request)
            if not health_result["success"]:
                return HealthCheckResponse(success=False, error_message=health_result["error"])

            return HealthCheckResponse(
                success=True,
                health_statuses=health_result["health_statuses"],
                overall_health=health_result["overall_health"],
            )
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResponse(success=False, error_message=f"ヘルスチェックエラー: {exc!s}")

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResponse:
        """Execute batch jobs for infrastructure services."""
        try:
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return BatchExecutionResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            batch_result = self._batch_execution_service.execute_batch(aggregate, request)
            if not batch_result["success"]:
                return BatchExecutionResponse(
                    success=False,
                    error_message=batch_result.get("error"),
                    batch_result=batch_result.get("batch_result"),
                )

            return BatchExecutionResponse(success=True, batch_result=batch_result["batch_result"])
        except Exception as exc:  # noqa: BLE001
            return BatchExecutionResponse(success=False, error_message=f"バッチ実行エラー: {exc!s}")

    def get_service_statistics(self, project_id: str, service_name: str) -> dict[str, Any]:
        """Return service statistics if project aggregate exists."""
        aggregate = self._aggregate_management_service.get_aggregate(project_id)
        if not aggregate:
            return {}
        return aggregate.get_service_statistics(service_name)

    def get_configuration(self, project_id: str) -> dict[str, Any]:
        """Return effective configuration for the project aggregate."""
        aggregate = self._aggregate_management_service.get_aggregate(project_id)
        if not aggregate:
            return {}
        return aggregate.get_effective_configuration()

    def _use_refactored_flow(self, project_id: str) -> bool:
        """Return whether refactored orchestration should be used."""
        if not self._configuration_provider:
            return False

        snapshot = None
        token = None
        if self._configuration_source:
            try:
                snapshot, token = self._configuration_source.snapshot(project_id)
            except Exception:  # noqa: BLE001
                snapshot = None
                token = None

        prev_token = self._config_tokens.get(project_id)
        if token and token != prev_token:
            if prev_token and self._configuration_source:
                old_config, new_config = self._configuration_source.diff_since(project_id, prev_token)
                self._feature_flag_cache[project_id] = new_config.get("features", {}) or old_config.get("features", {})
            else:
                features = snapshot.get("features", {}) if snapshot else {}
                self._feature_flag_cache[project_id] = features
            self._config_tokens[project_id] = token

        if project_id not in self._feature_flag_cache:
            try:
                self._feature_flag_cache[project_id] = self._configuration_provider.get_feature_flags()
            except Exception:  # noqa: BLE001
                self._feature_flag_cache[project_id] = {}

        features = self._feature_flag_cache.get(project_id, {})
        if not features and snapshot:
            features = snapshot.get("features", {})
            self._feature_flag_cache[project_id] = features

        if not features:
            return bool(self._configuration_provider.is_feature_enabled("infrastructure_refactor"))
        return bool(
            features.get("infrastructure_refactor")
            or self._configuration_provider.is_feature_enabled("infrastructure_refactor")
        )
