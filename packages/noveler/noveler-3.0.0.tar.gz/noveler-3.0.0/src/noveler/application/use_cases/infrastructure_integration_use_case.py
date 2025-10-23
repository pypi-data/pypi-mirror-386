#!/usr/bin/env python3

"""Application.use_cases.infrastructure_integration_use_case
Where: Application use case managing infrastructure integration tasks.
What: Calls domain and infrastructure services to configure adapters, run checks, and persist reports.
Why: Provides a unified entry point for infrastructure integration operations without ad-hoc scripts.
"""

from __future__ import annotations



import uuid
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

# データクラスは新しいサービスファイルに移動済み


class InfrastructureIntegrationUseCase:
    """インフラ統合ユースケース

    レガシーアダプターの統合管理を行うアプリケーション層の実装。
    DDD準拠のアプリケーション層実装。
    """

    def __init__(
        self,
        coordination_service: InfrastructureCoordinationService,
        default_config: InfrastructureConfiguration | None,
    ) -> None:
        self.coordination_service = coordination_service
        self.default_config = default_config

        # 新しいドメインサービスの初期化
        self._registration_service = InfrastructureServiceRegistrationService(coordination_service)
        self._execution_service = InfrastructureServiceExecutionService()
        self._health_check_service = InfrastructureHealthCheckService()
        self._batch_execution_service = InfrastructureBatchExecutionService()
        self._statistics_service = InfrastructureStatisticsService()
        self._configuration_service = InfrastructureConfigurationService(default_config)
        self._aggregate_management_service = InfrastructureAggregateManagementService(
            self._configuration_service.default_config
        )

    def register_service(self, request: RegisterServiceRequest) -> RegisterServiceResponse:
        """サービスを登録(新しいサービス使用)

        DDD準拠のビジネスフロー:
        1. アグリゲート取得/作成
        2. サービス登録処理
        3. 結果返却
        """
        try:
            # ステップ1: アグリゲート取得/作成(新しいサービス使用)
            aggregate = self._aggregate_management_service.get_or_create_aggregate(request.project_id)

            # ステップ2: サービス登録処理(新しいサービス使用)
            registration_result = self._registration_service.register_service(aggregate, request)

            if not registration_result["success"]:
                return RegisterServiceResponse(
                    success=False,
                    validation_errors=registration_result.get("validation_errors"),
                    error_message=registration_result.get("error"),
                )

            # ステップ3: 成功レスポンス返却
            return RegisterServiceResponse(
                success=True,
                service_id=registration_result["service_id"],
                service_name=registration_result["service_name"],
            )

        except Exception as e:
            return RegisterServiceResponse(
                success=False,
                error_message=f"サービス登録エラー: {e!s}",
            )

    def execute_service(self, request: ExecuteServiceRequest) -> ExecuteServiceResponse:
        """サービスを実行(新しいサービス使用)

        DDD準拠のビジネスフロー:
        1. アグリゲート取得
        2. サービス実行処理
        3. 結果返却
        """
        try:
            # ステップ1: アグリゲート取得(新しいサービス使用)
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return ExecuteServiceResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            # ステップ2: サービス実行処理(新しいサービス使用)
            execution_result = self._execution_service.execute_service(aggregate, request)

            if not execution_result["success"]:
                return ExecuteServiceResponse(success=False, error_message=execution_result["error"])

            # ステップ3: 成功レスポンス返却
            return ExecuteServiceResponse(
                success=True,
                execution_result=execution_result["execution_result"],
            )

        except Exception as e:
            return ExecuteServiceResponse(
                success=False,
                error_message=f"サービス実行エラー: {e!s}",
            )

    def check_health(self, request: HealthCheckRequest) -> HealthCheckResponse:
        """サービスの健康状態をチェック(新しいサービス使用)

        DDD準拠のビジネスフロー:
        1. アグリゲート取得
        2. ヘルスチェック処理
        3. 結果返却
        """
        try:
            # ステップ1: アグリゲート取得(新しいサービス使用)
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return HealthCheckResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            # ステップ2: ヘルスチェック処理(新しいサービス使用)
            health_result = self._health_check_service.check_health(aggregate, request)

            if not health_result["success"]:
                return HealthCheckResponse(success=False, error_message=health_result["error"])

            # ステップ3: 成功レスポンス返却
            return HealthCheckResponse(
                success=True,
                health_statuses=health_result["health_statuses"],
                overall_health=health_result["overall_health"],
            )

        except Exception as e:
            return HealthCheckResponse(
                success=False,
                error_message=f"ヘルスチェックエラー: {e!s}",
            )

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResponse:
        """バッチジョブを実行(新しいサービス使用)

        DDD準拠のビジネスフロー:
        1. アグリゲート取得
        2. バッチ実行処理
        3. 結果返却
        """
        try:
            # ステップ1: アグリゲート取得(新しいサービス使用)
            aggregate = self._aggregate_management_service.get_aggregate(request.project_id)
            if not aggregate:
                return BatchExecutionResponse(
                    success=False,
                    error_message=f"プロジェクト '{request.project_id}' が見つかりません",
                )

            # ステップ2: バッチ実行処理(新しいサービス使用)
            batch_result = self._batch_execution_service.execute_batch(aggregate, request)

            if not batch_result["success"]:
                return BatchExecutionResponse(
                    success=False,
                    error_message=batch_result.get("error"),
                    validation_errors=batch_result.get("validation_errors"),
                )

            # ステップ3: 成功レスポンス返却
            return BatchExecutionResponse(
                success=True,
                batch_result=batch_result["batch_result"],
            )

        except Exception as e:
            return BatchExecutionResponse(
                success=False,
                error_message=f"バッチ実行エラー: {e!s}",
            )

    def get_service_statistics(self, project_id: str, service_name: str) -> dict[str, Any]:
        """サービスの統計情報を取得"""
        aggregate = self._get_aggregate(project_id)
        if not aggregate:
            return {}

        return aggregate.get_service_statistics(service_name)

    def get_configuration(self, project_id: str) -> dict[str, Any]:
        """プロジェクトの設定を取得"""
        aggregate = self._get_aggregate(project_id)
        if not aggregate:
            return {}

        return aggregate.get_effective_configuration()

    def _get_or_create_aggregate(self, project_id: str) -> InfrastructureIntegrationAggregate:
        """プロジェクトのアグリゲートを取得または作成"""
        if project_id not in self._aggregates:
            aggregate_id = str(uuid.uuid4())

            # デフォルト設定を適用
            global_config: dict[str, Any] = self.default_config.performance.__dict__
            cache_config: dict[str, Any] = self.default_config.cache.__dict__

            aggregate = InfrastructureIntegrationAggregate(
                aggregate_id=aggregate_id,
                project_id=project_id,
                global_config=global_config,
                cache_config=cache_config,
            )

            self._aggregates[project_id] = aggregate

        return self._aggregates[project_id]

    def _get_aggregate(self, project_id: str) -> InfrastructureIntegrationAggregate | None:
        """プロジェクトのアグリゲートを取得"""
        return self._aggregates.get(project_id)

    def _create_default_config(self) -> InfrastructureConfiguration:
        """デフォルト設定を作成"""
        performance = PerformanceConfiguration(
            max_concurrent_services=5,
            default_timeout=30,
            cache_enabled=True,
            memory_limit_mb=512,
            cpu_usage_threshold=80.0,
        )

        cache = CacheConfiguration(
            enabled=True,
            ttl_seconds=3600,
            max_size=1000,
            storage_type="memory",
        )

        return InfrastructureConfiguration(
            performance=performance,
            cache=cache,
        )

    def _evaluate_overall_health(self, health_statuses: list[ServiceHealthStatus]) -> str:
        """全体的な健康状態を評価"""
        if not health_statuses:
            return "unknown"

        error_count = sum(1 for status in health_statuses if status.status.value == "error")
        inactive_count = sum(1 for status in health_statuses if status.status.value == "inactive")
        total_count = len(health_statuses)

        error_rate = error_count / total_count
        inactive_rate = inactive_count / total_count

        if error_rate > 0.5:
            return "critical"
        if error_rate > 0.2 or inactive_rate > 0.3:
            return "degraded"
        return "healthy"

    def _validate_batch_jobs(self, batch_jobs: list[dict[str, Any]], aggregate: dict[str, Any]) -> list[str]:
        """バッチジョブの検証"""
        errors: list[Any] = []

        for i, job in enumerate(batch_jobs):
            if "service" not in job:
                errors.append(f"ジョブ {i}: サービスが指定されていません")
                continue

            service_name = job["service"]
            if not aggregate.is_service_registered(service_name):
                errors.append(f"ジョブ {i}: サービス '{service_name}' が登録されていません")

            if "data" not in job:
                errors.append(f"ジョブ {i}: データが指定されていません")

        return errors
