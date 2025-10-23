# 統合インフラストラクチャアダプター仕様書

## 概要
統合インフラストラクチャアダプターは、システム全体のインフラストラクチャ層コンポーネントを統合・管理するアダプターです。各種アダプター、サービス、リポジトリを統一的に初期化・設定・監視し、アプリケーション層に対して一貫したインフラストラクチャインターフェースを提供します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import threading

T = TypeVar('T')

class ComponentType(Enum):
    """コンポーネントタイプ"""
    REPOSITORY = "repository"
    ADAPTER = "adapter"
    SERVICE = "service"
    CLIENT = "client"
    PROVIDER = "provider"
    HANDLER = "handler"

class ComponentStatus(Enum):
    """コンポーネント状態"""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

class HealthStatus(Enum):
    """健全性状態"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
class ComponentInfo:
    """コンポーネント情報"""
    name: str
    component_type: ComponentType
    class_name: str
    status: ComponentStatus
    health_status: HealthStatus
    last_health_check: datetime
    initialization_time: Optional[datetime]
    dependencies: List[str]
    configuration: Dict[str, Any]
    metrics: Dict[str, Any]

@dataclass
class InfrastructureConfig:
    """インフラストラクチャ設定"""
    component_configs: Dict[str, Dict[str, Any]]
    dependency_graph: Dict[str, List[str]]
    health_check_interval: int
    startup_timeout: int
    shutdown_timeout: int
    monitoring_enabled: bool
    retry_config: Dict[str, Any]

class IInfrastructureComponent(ABC):
    """インフラストラクチャコンポーネントインターフェース"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """コンポーネントを初期化"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """コンポーネントをシャットダウン"""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健全性をチェック"""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        pass

class UnifiedInfrastructureAdapter:
    """統合インフラストラクチャアダプター"""

    def __init__(
        self,
        config: InfrastructureConfig,
        component_registry: IComponentRegistry,
        dependency_resolver: IDependencyResolver,
        health_monitor: IHealthMonitor,
        configuration_manager: IConfigurationManager
    ):
        self._config = config
        self._registry = component_registry
        self._resolver = dependency_resolver
        self._monitor = health_monitor
        self._config_manager = configuration_manager
        self._components: Dict[str, IInfrastructureComponent] = {}
        self._component_info: Dict[str, ComponentInfo] = {}
        self._initialization_lock = threading.RLock()
```

## データ構造

### インターフェース定義

```python
class IComponentRegistry(ABC):
    """コンポーネントレジストリインターフェース"""

    @abstractmethod
    def register(self, name: str, component_class: Type[IInfrastructureComponent]) -> None:
        """コンポーネントクラスを登録"""
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[Type[IInfrastructureComponent]]:
        """コンポーネントクラスを取得"""
        pass

    @abstractmethod
    def list_components(self) -> Dict[str, Type[IInfrastructureComponent]]:
        """全コンポーネントを一覧取得"""
        pass

class IDependencyResolver(ABC):
    """依存関係解決インターフェース"""

    @abstractmethod
    def resolve_initialization_order(
        self,
        components: List[str],
        dependencies: Dict[str, List[str]]
    ) -> List[str]:
        """初期化順序を解決"""
        pass

    @abstractmethod
    def check_circular_dependencies(
        self,
        dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """循環依存をチェック"""
        pass

class IHealthMonitor(ABC):
    """健全性監視インターフェース"""

    @abstractmethod
    def start_monitoring(self, components: Dict[str, IInfrastructureComponent]) -> None:
        """監視を開始"""
        pass

    @abstractmethod
    def stop_monitoring(self) -> None:
        """監視を停止"""
        pass

    @abstractmethod
    def get_health_status(self, component_name: str) -> HealthStatus:
        """健全性状態を取得"""
        pass

    @abstractmethod
    def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """全コンポーネントの健全性状態を取得"""
        pass

class IConfigurationManager(ABC):
    """設定管理インターフェース"""

    @abstractmethod
    def load_configuration(self, path: str) -> Dict[str, Any]:
        """設定をロード"""
        pass

    @abstractmethod
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """コンポーネント設定を取得"""
        pass

    @abstractmethod
    def reload_configuration(self) -> None:
        """設定を再ロード"""
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """設定を検証"""
        pass
```

### アダプター実装

```python
@dataclass
class InitializationResult:
    """初期化結果"""
    component_name: str
    success: bool
    duration: float
    error_message: Optional[str]
    dependencies_resolved: List[str]

@dataclass
class ShutdownResult:
    """シャットダウン結果"""
    component_name: str
    success: bool
    duration: float
    error_message: Optional[str]

@dataclass
class SystemHealthReport:
    """システム健全性レポート"""
    overall_status: HealthStatus
    component_statuses: Dict[str, HealthStatus]
    unhealthy_components: List[str]
    degraded_components: List[str]
    timestamp: datetime
    recommendations: List[str]

class DefaultComponentRegistry(IComponentRegistry):
    """デフォルトコンポーネントレジストリ"""

    def __init__(self):
        self._registry: Dict[str, Type[IInfrastructureComponent]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        component_class: Type[IInfrastructureComponent],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self._registry[name] = component_class
        self._metadata[name] = metadata or {}

    def get(self, name: str) -> Optional[Type[IInfrastructureComponent]]:
        return self._registry.get(name)

    def list_components(self) -> Dict[str, Type[IInfrastructureComponent]]:
        return self._registry.copy()

    def get_metadata(self, name: str) -> Dict[str, Any]:
        return self._metadata.get(name, {})

class TopologicalDependencyResolver(IDependencyResolver):
    """トポロジカル依存関係解決器"""

    def resolve_initialization_order(
        self,
        components: List[str],
        dependencies: Dict[str, List[str]]
    ) -> List[str]:
        # トポロジカルソートによる初期化順序決定
        in_degree = {comp: 0 for comp in components}

        # 入次数計算
        for comp in components:
            for dep in dependencies.get(comp, []):
                if dep in in_degree:
                    in_degree[comp] += 1

        # 初期化順序決定
        queue = [comp for comp, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 依存先の入次数を減算
            for comp in components:
                if current in dependencies.get(comp, []):
                    in_degree[comp] -= 1
                    if in_degree[comp] == 0:
                        queue.append(comp)

        if len(result) != len(components):
            remaining = set(components) - set(result)
            raise ValueError(f"循環依存が検出されました: {remaining}")

        return result

    def check_circular_dependencies(
        self,
        dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """循環依存の検出"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # 循環検出
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in dependencies.get(node, []):
                dfs(dep, path[:])

            rec_stack.remove(node)

        for component in dependencies.keys():
            if component not in visited:
                dfs(component, [])

        return cycles
```

## パブリックメソッド

### UnifiedInfrastructureAdapter

```python
def initialize_infrastructure(self) -> Dict[str, InitializationResult]:
    """
    インフラストラクチャを初期化

    Returns:
        Dict[str, InitializationResult]: コンポーネント別初期化結果
    """
    with self._initialization_lock:
        results = {}

        try:
            # 設定検証
            validation_errors = self._config_manager.validate_configuration(
                self._config.component_configs
            )
            if validation_errors:
                raise ValueError(f"設定検証エラー: {validation_errors}")

            # 循環依存チェック
            cycles = self._resolver.check_circular_dependencies(
                self._config.dependency_graph
            )
            if cycles:
                raise ValueError(f"循環依存が検出されました: {cycles}")

            # 初期化順序決定
            components = list(self._config.component_configs.keys())
            initialization_order = self._resolver.resolve_initialization_order(
                components,
                self._config.dependency_graph
            )

            # 各コンポーネントの初期化
            for component_name in initialization_order:
                result = self._initialize_component(component_name)
                results[component_name] = result

                if not result.success:
                    # 初期化失敗時は後続をスキップ
                    break

            # 健全性監視開始
            if self._config.monitoring_enabled:
                self._monitor.start_monitoring(self._components)

            return results

        except Exception as e:
            # 初期化失敗時のクリーンアップ
            self._cleanup_failed_initialization()
            raise RuntimeError(f"インフラストラクチャ初期化失敗: {e}")

def shutdown_infrastructure(self) -> Dict[str, ShutdownResult]:
    """
    インフラストラクチャをシャットダウン

    Returns:
        Dict[str, ShutdownResult]: コンポーネント別シャットダウン結果
    """
    results = {}

    try:
        # 健全性監視停止
        self._monitor.stop_monitoring()

        # シャットダウン順序（初期化の逆順）
        shutdown_order = list(reversed(list(self._components.keys())))

        for component_name in shutdown_order:
            result = self._shutdown_component(component_name)
            results[component_name] = result

        # 全コンポーネント状態をシャットダウンに更新
        for name in self._component_info.keys():
            self._update_component_status(name, ComponentStatus.SHUTDOWN)

        return results

    except Exception as e:
        logger.error(f"シャットダウン処理エラー: {e}")
        return results

def get_component(self, component_name: str) -> Optional[IInfrastructureComponent]:
    """
    コンポーネントを取得

    Args:
        component_name: コンポーネント名

    Returns:
        Optional[IInfrastructureComponent]: コンポーネントインスタンス
    """
    return self._components.get(component_name)

def register_component(
    self,
    name: str,
    component_class: Type[IInfrastructureComponent],
    config: Dict[str, Any],
    dependencies: Optional[List[str]] = None
) -> None:
    """
    コンポーネントを動的登録

    Args:
        name: コンポーネント名
        component_class: コンポーネントクラス
        config: 設定
        dependencies: 依存関係
    """
    # レジストリに登録
    self._registry.register(name, component_class)

    # 設定更新
    self._config.component_configs[name] = config
    if dependencies:
        self._config.dependency_graph[name] = dependencies

    # 既に初期化済みの場合は即座に初期化
    if self._components:
        self._initialize_component(name)

def get_system_health(self) -> SystemHealthReport:
    """
    システム全体の健全性を取得

    Returns:
        SystemHealthReport: システム健全性レポート
    """
    component_statuses = self._monitor.get_all_health_status()

    # 全体状態の判定
    unhealthy_components = [
        name for name, status in component_statuses.items()
        if status == HealthStatus.UNHEALTHY
    ]
    degraded_components = [
        name for name, status in component_statuses.items()
        if status == HealthStatus.DEGRADED
    ]

    if unhealthy_components:
        overall_status = HealthStatus.UNHEALTHY
    elif degraded_components:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    # 推奨事項生成
    recommendations = self._generate_health_recommendations(
        unhealthy_components,
        degraded_components
    )

    return SystemHealthReport(
        overall_status=overall_status,
        component_statuses=component_statuses,
        unhealthy_components=unhealthy_components,
        degraded_components=degraded_components,
        timestamp=datetime.now(),
        recommendations=recommendations
    )

def reload_configuration(self, component_name: Optional[str] = None) -> None:
    """
    設定を再ロード

    Args:
        component_name: 特定コンポーネントの設定のみ再ロード（Noneの場合は全体）
    """
    try:
        self._config_manager.reload_configuration()

        if component_name:
            # 特定コンポーネントの設定再ロード
            if component_name in self._components:
                new_config = self._config_manager.get_component_config(component_name)
                self._reconfigure_component(component_name, new_config)
        else:
            # 全コンポーネントの設定再ロード
            for name in self._components.keys():
                new_config = self._config_manager.get_component_config(name)
                self._reconfigure_component(name, new_config)

    except Exception as e:
        raise RuntimeError(f"設定再ロードエラー: {e}")

def get_component_metrics(
    self,
    component_name: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    コンポーネントメトリクスを取得

    Args:
        component_name: 特定コンポーネント名（Noneの場合は全体）

    Returns:
        Dict[str, Dict[str, Any]]: コンポーネント別メトリクス
    """
    if component_name:
        component = self._components.get(component_name)
        if component:
            return {component_name: component.get_metrics()}
        return {}

    metrics = {}
    for name, component in self._components.items():
        try:
            metrics[name] = component.get_metrics()
        except Exception as e:
            logger.error(f"メトリクス取得エラー {name}: {e}")
            metrics[name] = {"error": str(e)}

    return metrics
```

## プライベートメソッド

```python
def _initialize_component(self, component_name: str) -> InitializationResult:
    """コンポーネントを初期化"""
    start_time = datetime.now()

    try:
        # コンポーネントクラス取得
        component_class = self._registry.get(component_name)
        if not component_class:
            raise ValueError(f"コンポーネント {component_name} が見つかりません")

        # インスタンス作成
        component_instance = component_class()

        # 設定取得
        config = self._config_manager.get_component_config(component_name)

        # 依存関係解決
        dependencies = self._config.dependency_graph.get(component_name, [])
        resolved_deps = self._resolve_component_dependencies(dependencies)

        # 設定に依存関係を注入
        if resolved_deps:
            config['dependencies'] = resolved_deps

        # 初期化実行
        self._update_component_status(component_name, ComponentStatus.INITIALIZING)
        component_instance.initialize(config)

        # 登録
        self._components[component_name] = component_instance
        self._update_component_status(component_name, ComponentStatus.READY)
        self._component_info[component_name].initialization_time = datetime.now()

        duration = (datetime.now() - start_time).total_seconds()

        return InitializationResult(
            component_name=component_name,
            success=True,
            duration=duration,
            error_message=None,
            dependencies_resolved=dependencies
        )

    except Exception as e:
        self._update_component_status(component_name, ComponentStatus.ERROR)
        duration = (datetime.now() - start_time).total_seconds()

        return InitializationResult(
            component_name=component_name,
            success=False,
            duration=duration,
            error_message=str(e),
            dependencies_resolved=[]
        )

def _shutdown_component(self, component_name: str) -> ShutdownResult:
    """コンポーネントをシャットダウン"""
    start_time = datetime.now()

    try:
        component = self._components.get(component_name)
        if not component:
            return ShutdownResult(
                component_name=component_name,
                success=True,  # 既にシャットダウン済み
                duration=0.0,
                error_message=None
            )

        # シャットダウン実行
        self._update_component_status(component_name, ComponentStatus.SHUTTING_DOWN)
        component.shutdown()

        # 除去
        del self._components[component_name]
        self._update_component_status(component_name, ComponentStatus.SHUTDOWN)

        duration = (datetime.now() - start_time).total_seconds()

        return ShutdownResult(
            component_name=component_name,
            success=True,
            duration=duration,
            error_message=None
        )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()

        return ShutdownResult(
            component_name=component_name,
            success=False,
            duration=duration,
            error_message=str(e)
        )

def _resolve_component_dependencies(
    self,
    dependencies: List[str]
) -> Dict[str, IInfrastructureComponent]:
    """コンポーネント依存関係を解決"""
    resolved = {}

    for dep_name in dependencies:
        if dep_name in self._components:
            resolved[dep_name] = self._components[dep_name]
        else:
            raise ValueError(f"依存関係 {dep_name} が解決できません")

    return resolved

def _update_component_status(
    self,
    component_name: str,
    status: ComponentStatus
) -> None:
    """コンポーネント状態を更新"""
    if component_name not in self._component_info:
        # 初回作成
        component_class = self._registry.get(component_name)
        component_type = self._determine_component_type(component_class)

        self._component_info[component_name] = ComponentInfo(
            name=component_name,
            component_type=component_type,
            class_name=component_class.__name__ if component_class else "Unknown",
            status=status,
            health_status=HealthStatus.UNKNOWN,
            last_health_check=datetime.now(),
            initialization_time=None,
            dependencies=self._config.dependency_graph.get(component_name, []),
            configuration=self._config.component_configs.get(component_name, {}),
            metrics={}
        )
    else:
        # 状態更新
        self._component_info[component_name].status = status

def _determine_component_type(
    self,
    component_class: Type[IInfrastructureComponent]
) -> ComponentType:
    """コンポーネントタイプを判定"""
    class_name = component_class.__name__.lower()

    if "repository" in class_name:
        return ComponentType.REPOSITORY
    elif "adapter" in class_name:
        return ComponentType.ADAPTER
    elif "service" in class_name:
        return ComponentType.SERVICE
    elif "client" in class_name:
        return ComponentType.CLIENT
    elif "provider" in class_name:
        return ComponentType.PROVIDER
    elif "handler" in class_name:
        return ComponentType.HANDLER
    else:
        return ComponentType.SERVICE  # デフォルト

def _reconfigure_component(
    self,
    component_name: str,
    new_config: Dict[str, Any]
) -> None:
    """コンポーネント設定を再構成"""
    component = self._components.get(component_name)
    if not component:
        return

    try:
        # 既存コンポーネントをシャットダウン
        self._shutdown_component(component_name)

        # 新しい設定で再初期化
        self._config.component_configs[component_name] = new_config
        self._initialize_component(component_name)

    except Exception as e:
        logger.error(f"コンポーネント {component_name} の再設定エラー: {e}")
        self._update_component_status(component_name, ComponentStatus.ERROR)

def _generate_health_recommendations(
    self,
    unhealthy_components: List[str],
    degraded_components: List[str]
) -> List[str]:
    """健全性に基づく推奨事項を生成"""
    recommendations = []

    if unhealthy_components:
        recommendations.append(
            f"不健全なコンポーネント {unhealthy_components} の状態確認が必要です"
        )
        recommendations.append("ログとメトリクスを確認してください")
        recommendations.append("必要に応じてコンポーネントを再起動してください")

    if degraded_components:
        recommendations.append(
            f"性能低下コンポーネント {degraded_components} の監視を強化してください"
        )
        recommendations.append("リソース使用状況を確認してください")

    if len(unhealthy_components) + len(degraded_components) > len(self._components) * 0.3:
        recommendations.append("システム全体の再起動を検討してください")

    return recommendations

def _cleanup_failed_initialization(self) -> None:
    """失敗した初期化のクリーンアップ"""
    for component_name in list(self._components.keys()):
        try:
            self._shutdown_component(component_name)
        except Exception as e:
            logger.error(f"クリーンアップエラー {component_name}: {e}")

    self._components.clear()
```

## アダプターパターン実装

### 具体的インフラストラクチャコンポーネント

```python
class YamlRepositoryAdapter(IInfrastructureComponent):
    """YAMLリポジトリアダプター"""

    def __init__(self):
        self._repositories = {}
        self._config = {}

    def initialize(self, config: Dict[str, Any]) -> None:
        self._config = config

        # 各YAMLリポジトリを初期化
        for repo_name, repo_config in config.get('repositories', {}).items():
            repo_class = self._get_repository_class(repo_config['type'])
            repo_instance = repo_class()
            repo_instance.initialize(repo_config)
            self._repositories[repo_name] = repo_instance

    def shutdown(self) -> None:
        for repo in self._repositories.values():
            repo.shutdown()
        self._repositories.clear()

    def health_check(self) -> Dict[str, Any]:
        status = {"healthy": True, "repositories": {}}

        for name, repo in self._repositories.items():
            repo_health = repo.health_check()
            status["repositories"][name] = repo_health
            if not repo_health.get("healthy", False):
                status["healthy"] = False

        return status

    def get_metrics(self) -> Dict[str, Any]:
        metrics = {"repository_count": len(self._repositories)}

        for name, repo in self._repositories.items():
            metrics[f"{name}_metrics"] = repo.get_metrics()

        return metrics

class MessageServiceAdapter(IInfrastructureComponent):
    """メッセージサービスアダプター"""

    def __init__(self):
        self._channels = {}
        self._config = {}

    def initialize(self, config: Dict[str, Any]) -> None:
        self._config = config

        # 各通知チャネルを初期化
        for channel_name, channel_config in config.get('channels', {}).items():
            channel_class = self._get_channel_class(channel_config['type'])
            channel_instance = channel_class()
            channel_instance.initialize(channel_config)
            self._channels[channel_name] = channel_instance

    def shutdown(self) -> None:
        for channel in self._channels.values():
            channel.shutdown()
        self._channels.clear()

    def health_check(self) -> Dict[str, Any]:
        status = {"healthy": True, "channels": {}}

        for name, channel in self._channels.items():
            channel_health = channel.health_check()
            status["channels"][name] = channel_health
            if not channel_health.get("healthy", False):
                status["healthy"] = False

        return status

    def get_metrics(self) -> Dict[str, Any]:
        metrics = {"channel_count": len(self._channels)}

        for name, channel in self._channels.items():
            metrics[f"{name}_metrics"] = channel.get_metrics()

        return metrics

class QualityCheckAdapter(IInfrastructureComponent):
    """品質チェックアダプター"""

    def __init__(self):
        self._checkers = {}
        self._config = {}

    def initialize(self, config: Dict[str, Any]) -> None:
        self._config = config

        # 各品質チェッカーを初期化
        for checker_name, checker_config in config.get('checkers', {}).items():
            checker_class = self._get_checker_class(checker_config['type'])
            checker_instance = checker_class()
            checker_instance.initialize(checker_config)
            self._checkers[checker_name] = checker_instance

    def shutdown(self) -> None:
        for checker in self._checkers.values():
            checker.shutdown()
        self._checkers.clear()

    def health_check(self) -> Dict[str, Any]:
        return {"healthy": len(self._checkers) > 0, "checkers": len(self._checkers)}

    def get_metrics(self) -> Dict[str, Any]:
        return {"checker_count": len(self._checkers)}
```

## 依存関係

```python
from domain.repositories import (
    EpisodeRepository,
    ProjectRepository,
    QualityRecordRepository
)
from application.use_cases import *
from infrastructure.repositories import *
from infrastructure.adapters import *
from infrastructure.services import *
```

## 設計原則遵守

### ファサードパターン
- **複雑性の隠蔽**: インフラ層の複雑性をアプリケーション層から隠蔽
- **統一インターフェース**: 各種インフラコンポーネントへの統一アクセス
- **初期化・設定の一元化**: 全コンポーネントの初期化を統合管理

### 依存性注入
- **構成可能性**: 設定による動的なコンポーネント構成
- **テスタビリティ**: モックコンポーネントの注入が容易
- **疎結合**: コンポーネント間の依存関係を明示的に管理

## 使用例

### 基本的な使用

```python
# 設定定義
config = InfrastructureConfig(
    component_configs={
        "yaml_repository": {
            "type": "YamlRepositoryAdapter",
            "repositories": {
                "episode": {"type": "YamlEpisodeRepository", "path": "./data"},
                "project": {"type": "YamlProjectRepository", "path": "./projects"}
            }
        },
        "message_service": {
            "type": "MessageServiceAdapter",
            "channels": {
                "slack": {"type": "SlackChannel", "webhook_url": "..."},
                "email": {"type": "EmailChannel", "smtp_config": {...}}
            }
        }
    },
    dependency_graph={
        "message_service": ["yaml_repository"]
    },
    health_check_interval=30,
    startup_timeout=60,
    shutdown_timeout=30,
    monitoring_enabled=True,
    retry_config={}
)

# アダプター初期化
infrastructure = UnifiedInfrastructureAdapter(
    config=config,
    component_registry=DefaultComponentRegistry(),
    dependency_resolver=TopologicalDependencyResolver(),
    health_monitor=PeriodicHealthMonitor(),
    configuration_manager=YamlConfigurationManager()
)

# システム起動
initialization_results = infrastructure.initialize_infrastructure()
for component, result in initialization_results.items():
    if result.success:
        print(f"{component}: 初期化成功 ({result.duration:.2f}s)")
    else:
        print(f"{component}: 初期化失敗 - {result.error_message}")

# コンポーネント使用
yaml_repo = infrastructure.get_component("yaml_repository")
message_service = infrastructure.get_component("message_service")
```

### 動的コンポーネント登録

```python
# 新しいコンポーネントを動的登録
infrastructure.register_component(
    name="quality_checker",
    component_class=QualityCheckAdapter,
    config={
        "checkers": {
            "style": {"type": "StyleChecker", "rules": "strict"},
            "structure": {"type": "StructureChecker", "min_length": 1000}
        }
    },
    dependencies=["yaml_repository"]
)

# システム健全性確認
health_report = infrastructure.get_system_health()
print(f"システム状態: {health_report.overall_status}")
for component, status in health_report.component_statuses.items():
    print(f"  {component}: {status}")
```

## エラーハンドリング

```python
try:
    results = infrastructure.initialize_infrastructure()

    # 個別コンポーネントの初期化失敗を確認
    failed_components = [
        name for name, result in results.items()
        if not result.success
    ]

    if failed_components:
        print(f"初期化失敗コンポーネント: {failed_components}")

        # 部分的な運用継続の判定
        critical_components = ["yaml_repository"]
        critical_failures = [c for c in failed_components if c in critical_components]

        if critical_failures:
            # 致命的な失敗
            infrastructure.shutdown_infrastructure()
            raise RuntimeError(f"致命的コンポーネント初期化失敗: {critical_failures}")
        else:
            # 非致命的な失敗は継続
            print("非致命的な初期化失敗があります。部分的に運用を継続します。")

except Exception as e:
    logger.error(f"インフラストラクチャ初期化エラー: {e}")
    # フォールバック処理
    use_minimal_infrastructure()
```

## テスト観点

### ユニットテスト
- 依存関係解決の正確性
- コンポーネント初期化順序
- 健全性監視の動作
- 設定検証の完全性

### 統合テスト
- 実際のコンポーネント間連携
- システム全体の起動・シャットダウン
- 障害時の動作確認
- 設定再ロードの動作

### パフォーマンステスト
- 大量コンポーネントの初期化時間
- 健全性チェックの実行時間
- メモリ使用量の測定

## 品質基準

### コード品質
- 循環的複雑度: 10以下
- テストカバレッジ: 85%以上
- 型ヒント: 100%実装

### 設計品質
- 単一責任原則の徹底
- 依存関係の明確化
- 設定駆動設計の実現

### 運用品質
- 起動・シャットダウンの信頼性
- 監視・アラート機能の完備
- 設定管理の堅牢性
