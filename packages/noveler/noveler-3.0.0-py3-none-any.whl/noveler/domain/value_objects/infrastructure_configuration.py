"""Domain.value_objects.infrastructure_configuration
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""インフラ設定関連の値オブジェクト

DDD原則に基づく不変な設定値オブジェクト群。
"""


from dataclasses import dataclass
from typing import Any

from noveler.domain.entities.infrastructure_integration_aggregate import InfrastructureServiceType


@dataclass(frozen=True)
class ServiceConfiguration:
    """サービス設定(値オブジェクト)

    個別のインフラサービスの設定を表現。
    """

    service_type: InfrastructureServiceType
    name: str
    adapter_class: str | None = None
    enabled: bool = True
    priority: int = 0
    timeout: int = None  # ConfigManagerから取得
    retry_count: int = 3
    fallback_service: str | None = None
    dependencies: list[str] = None
    cache_enabled: bool = False
    cache_key_template: str | None = None
    batch_size: int = 1
    health_check_interval: int = 60

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.name:
            msg = "サービス名は必須です"
            raise ValueError(msg)
        if self.priority < 0:
            msg = "優先度は0以上である必要があります"
            raise ValueError(msg)
        if self.timeout <= 0:
            msg = "タイムアウトは1以上である必要があります"
            raise ValueError(msg)
        if self.retry_count < 0:
            msg = "リトライ回数は0以上である必要があります"
            raise ValueError(msg)
        if self.batch_size <= 0:
            msg = "バッチサイズは1以上である必要があります"
            raise ValueError(msg)

        # dependencies のデフォルト値設定
        if self.dependencies is None:
            object.__setattr__(self, "dependencies", [])

    def with_enabled(self, enabled: bool) -> ServiceConfiguration:
        """有効/無効を変更した新しいインスタンスを作成"""
        return ServiceConfiguration(
            service_type=self.service_type,
            name=self.name,
            adapter_class=self.adapter_class,
            enabled=enabled,
            priority=self.priority,
            timeout=self.timeout,
            retry_count=self.retry_count,
            fallback_service=self.fallback_service,
            dependencies=self.dependencies,
            cache_enabled=self.cache_enabled,
            cache_key_template=self.cache_key_template,
            batch_size=self.batch_size,
            health_check_interval=self.health_check_interval,
        )

    def with_priority(self, priority: int) -> ServiceConfiguration:
        """優先度を変更した新しいインスタンスを作成"""
        return ServiceConfiguration(
            service_type=self.service_type,
            name=self.name,
            adapter_class=self.adapter_class,
            enabled=self.enabled,
            priority=priority,
            timeout=self.timeout,
            retry_count=self.retry_count,
            fallback_service=self.fallback_service,
            dependencies=self.dependencies,
            cache_enabled=self.cache_enabled,
            cache_key_template=self.cache_key_template,
            batch_size=self.batch_size,
            health_check_interval=self.health_check_interval,
        )


@dataclass(frozen=True)
class PerformanceConfiguration:
    """パフォーマンス設定(値オブジェクト)

    システム全体のパフォーマンス関連設定。
    """

    max_concurrent_services: int = 5
    default_timeout: int = None  # ConfigManagerから取得
    cache_enabled: bool = True
    memory_limit_mb: int = 512
    cpu_usage_threshold: float = 80.0
    auto_scaling_enabled: bool = False

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.max_concurrent_services <= 0:
            msg = "最大同時実行サービス数は1以上である必要があります"
            raise ValueError(msg)
        if self.default_timeout <= 0:
            msg = "デフォルトタイムアウトは1以上である必要があります"
            raise ValueError(msg)
        if self.memory_limit_mb <= 0:
            msg = "メモリ制限は1以上である必要があります"
            raise ValueError(msg)
        if not (0.0 <= self.cpu_usage_threshold <= 100.0):
            msg = "CPU使用率閾値は0-100の範囲である必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class CacheConfiguration:
    """キャッシュ設定(値オブジェクト)

    システム全体のキャッシュ関連設定。
    """

    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 1000
    storage_type: str = "memory"
    compression_enabled: bool = False
    eviction_policy: str = "lru"

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.ttl_seconds <= 0:
            msg = "TTLは1以上である必要があります"
            raise ValueError(msg)
        if self.max_size <= 0:
            msg = "最大サイズは1以上である必要があります"
            raise ValueError(msg)
        if self.storage_type not in ["memory", "redis", "file"]:
            msg = "ストレージタイプは memory, redis, file のいずれかである必要があります"
            raise ValueError(msg)
        if self.eviction_policy not in ["lru", "lfu", "fifo"]:
            msg = "退避ポリシーは lru, lfu, fifo のいずれかである必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class SecurityConfiguration:
    """セキュリティ設定(値オブジェクト)

    セキュリティ関連の設定。
    """

    encryption_enabled: bool = False
    access_control_enabled: bool = True
    allowed_operations: list[str] = None
    restricted_paths: list[str] = None
    audit_logging_enabled: bool = True

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.allowed_operations is None:
            object.__setattr__(self, "allowed_operations", [])
        if self.restricted_paths is None:
            object.__setattr__(self, "restricted_paths", [])


@dataclass(frozen=True)
class MonitoringConfiguration:
    """監視設定(値オブジェクト)

    システム監視とアラート設定。
    """

    enabled: bool = True
    health_check_interval: int = 60
    metrics_collection_interval: int = 30
    alert_threshold_error_rate: float = 10.0
    alert_threshold_response_time: float = 5.0
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.health_check_interval <= 0:
            msg = "ヘルスチェック間隔は1以上である必要があります"
            raise ValueError(msg)
        if self.metrics_collection_interval <= 0:
            msg = "メトリクス収集間隔は1以上である必要があります"
            raise ValueError(msg)
        if not (0.0 <= self.alert_threshold_error_rate <= 100.0):
            msg = "エラー率アラート閾値は0-100の範囲である必要があります"
            raise ValueError(msg)
        if self.alert_threshold_response_time <= 0:
            msg = "レスポンス時間アラート閾値は1以上である必要があります"
            raise ValueError(msg)
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            msg = "ログレベルは DEBUG, INFO, WARNING, ERROR, CRITICAL のいずれかである必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class InfrastructureConfiguration:
    """インフラ統合設定(値オブジェクト)

    全体のインフラ設定を統合する。
    """

    performance: PerformanceConfiguration
    cache: CacheConfiguration
    security: SecurityConfiguration = None
    monitoring: MonitoringConfiguration = None
    services: list[ServiceConfiguration] = None

    def __post_init__(self) -> None:
        """デフォルト値設定"""
        if self.security is None:
            object.__setattr__(self, "security", SecurityConfiguration())
        if self.monitoring is None:
            object.__setattr__(self, "monitoring", MonitoringConfiguration())
        if self.services is None:
            object.__setattr__(self, "services", [])

    def get_service_config(self, service_name: str) -> ServiceConfiguration | None:
        """サービス設定を取得"""
        for service_config in self.services:
            if service_config.name == service_name:
                return service_config
        return None

    def add_service_config(self, service_config: ServiceConfiguration) -> InfrastructureConfiguration:
        """サービス設定を追加した新しいインスタンスを作成"""
        new_services = [*list(self.services), service_config]
        return InfrastructureConfiguration(
            performance=self.performance,
            cache=self.cache,
            security=self.security,
            monitoring=self.monitoring,
            services=new_services,
        )

    def remove_service_config(self, service_name: str) -> InfrastructureConfiguration:
        """サービス設定を削除した新しいインスタンスを作成"""
        new_services = [service for service in self.services if service.name != service_name]
        return InfrastructureConfiguration(
            performance=self.performance,
            cache=self.cache,
            security=self.security,
            monitoring=self.monitoring,
            services=new_services,
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "performance": {
                "max_concurrent_services": self.performance.max_concurrent_services,
                "default_timeout": self.performance.default_timeout,
                "cache_enabled": self.performance.cache_enabled,
                "memory_limit_mb": self.performance.memory_limit_mb,
                "cpu_usage_threshold": self.performance.cpu_usage_threshold,
                "auto_scaling_enabled": self.performance.auto_scaling_enabled,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "ttl_seconds": self.cache.ttl_seconds,
                "max_size": self.cache.max_size,
                "storage_type": self.cache.storage_type,
                "compression_enabled": self.cache.compression_enabled,
                "eviction_policy": self.cache.eviction_policy,
            },
            "security": {
                "encryption_enabled": self.security.encryption_enabled,
                "access_control_enabled": self.security.access_control_enabled,
                "allowed_operations": self.security.allowed_operations,
                "restricted_paths": self.security.restricted_paths,
                "audit_logging_enabled": self.security.audit_logging_enabled,
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "health_check_interval": self.monitoring.health_check_interval,
                "metrics_collection_interval": self.monitoring.metrics_collection_interval,
                "alert_threshold_error_rate": self.monitoring.alert_threshold_error_rate,
                "alert_threshold_response_time": self.monitoring.alert_threshold_response_time,
                "log_level": self.monitoring.log_level,
            },
            "services": [
                {
                    "service_type": service.service_type.value,
                    "name": service.name,
                    "adapter_class": service.adapter_class,
                    "enabled": service.enabled,
                    "priority": service.priority,
                    "timeout": service.timeout,
                    "retry_count": service.retry_count,
                    "fallback_service": service.fallback_service,
                    "dependencies": service.dependencies,
                    "cache_enabled": service.cache_enabled,
                    "cache_key_template": service.cache_key_template,
                    "batch_size": service.batch_size,
                    "health_check_interval": service.health_check_interval,
                }
                for service in self.services
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InfrastructureConfiguration:
        """辞書から作成"""
        performance = PerformanceConfiguration(**data.get("performance", {}))
        cache = CacheConfiguration(**data.get("cache", {}))
        security = SecurityConfiguration(**data.get("security", {}))
        monitoring = MonitoringConfiguration(**data.get("monitoring", {}))

        services = []
        for service_data in data.get("services", []):
            service_config: dict[str, Any] = ServiceConfiguration(
                service_type=InfrastructureServiceType(service_data["service_type"]),
                name=service_data["name"],
                adapter_class=service_data.get("adapter_class"),
                enabled=service_data.get("enabled", True),
                priority=service_data.get("priority", 0),
                timeout=service_data.get("timeout", 30),
                retry_count=service_data.get("retry_count", 3),
                fallback_service=service_data.get("fallback_service"),
                dependencies=service_data.get("dependencies", []),
                cache_enabled=service_data.get("cache_enabled", False),
                cache_key_template=service_data.get("cache_key_template"),
                batch_size=service_data.get("batch_size", 1),
                health_check_interval=service_data.get("health_check_interval", 60),
            )

            services.append(service_config)

        return cls(
            performance=performance,
            cache=cache,
            security=security,
            monitoring=monitoring,
            services=services,
        )
