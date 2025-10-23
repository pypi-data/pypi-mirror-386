"""
DI (Dependency Injection) Infrastructure Package

Purpose: プロジェクト全体のTODO: DI箇所を段階的に解決

Exports:
    - DIContainer: 軽量依存性注入コンテナ
    - get_container: グローバルコンテナ取得
    - configure_dependencies: 依存関係設定
"""

from noveler.infrastructure.di.simple_di_container import DIContainer, configure_dependencies, get_container

__all__ = ["DIContainer", "configure_dependencies", "get_container"]
