#!/usr/bin/env python3
"""設定管理サービスファクトリー

Protocol基盤統合による循環依存解決とレガシー互換性確保
B20開発作業指示書準拠のFactoryパターン実装
依存関係注入による統合設定管理システムの構築
"""
import asyncio
import concurrent.futures
import traceback
from pathlib import Path
from typing import Any, Optional

from noveler.application.use_cases.load_configuration_use_case import LoadConfigurationRequest, LoadConfigurationUseCase
from noveler.domain.entities.novel_configuration import NovelConfiguration
from noveler.domain.interfaces.configuration_service_protocol import get_configuration_service_manager
from noveler.infrastructure.repositories.yaml_configuration_repository import YamlConfigurationRepository
from noveler.presentation.shared.shared_utilities import console


class ConfigurationServiceFactory:
    """設定管理サービスのファクトリークラス

    Protocol基盤統合による循環依存解決とレガシー互換性確保
    B20開発作業指示書のFactoryパターンに準拠した
    統合設定管理システムの依存関係構築を提供
    """

    @staticmethod
    def create_configuration_service() -> LoadConfigurationUseCase:
        """本番環境用設定サービス作成（レガシー互換）

        Returns:
            設定読み込みユースケース
        """
        repository = YamlConfigurationRepository()
        return LoadConfigurationUseCase(repository)

    @staticmethod
    def create_test_configuration_service() -> LoadConfigurationUseCase:
        """テスト環境用設定サービス作成（レガシー互換）

        Returns:
            テスト用設定読み込みユースケース
        """
        repository = YamlConfigurationRepository()
        return LoadConfigurationUseCase(repository)

    @staticmethod
    def load_configuration(config_path: Path | None = None) -> NovelConfiguration | None:
        """統合設定を読み込む便利メソッド（Protocol基盤統合版）

        Args:
            config_path: 設定ファイルパス（None時はデフォルト設定使用）

        Returns:
            設定エンティティまたはNone
        """
        try:
            # Protocol基盤を使用した新しい実装
            manager = get_configuration_service_manager()
            return asyncio.run(manager.load_configuration(config_path))
        except Exception:
            # フォールバック: レガシー実装
            return _legacy_load_configuration(config_path)

    @staticmethod
    def create_protocol_based_service():
        """Protocol基盤の設定サービス取得

        Returns:
            Protocol基盤設定サービス
        """
        manager = get_configuration_service_manager()
        return manager.get_configuration_service()

    @staticmethod
    def create_protocol_based_test_service():
        """Protocol基盤のテスト設定サービス取得

        Returns:
            Protocol基盤テスト設定サービス
        """
        manager = get_configuration_service_manager()
        return manager.get_configuration_service(for_test=True)


def _legacy_load_configuration(config_path: Path | None = None) -> NovelConfiguration | None:
    """レガシー設定読み込み実装（フォールバック用）"""
    if config_path is None:
        try:
            current_file = Path(__file__)
            guide_root = current_file.parent.parent.parent.parent
            primary_config_path = guide_root / "config" / "novel_config.yaml"
            if primary_config_path.exists():
                config_path = primary_config_path
            else:
                fallback1 = Path("config/novel_config.yaml")
                config_path = fallback1 if fallback1.exists() else guide_root / "config" / "novel_config.yaml"
        except Exception:
            current_file = Path(__file__)
            guide_root = current_file.parent.parent.parent.parent
            config_path = guide_root / "config" / "novel_config.yaml"
    try:
        repository = YamlConfigurationRepository()
        use_case = LoadConfigurationUseCase(repository)
        request = LoadConfigurationRequest(config_file_path=config_path)
        response = asyncio.run(use_case.execute(request))
        if response and response.success:
            return response.configuration
        if response:
            console.print(f"設定読み込みエラー: {response.error_message}")
        return None
    except Exception as e:
        console.print(f"設定ファクトリーエラー: {e}")
        return None


class ConfigurationManager:
    """設定管理マネージャー

    シングルトン的な設定アクセスを提供し、
    パフォーマンスとメモリ効率を最適化する
    """

    _instance: Optional["ConfigurationManager"] = None
    _configuration: NovelConfiguration | None = None
    _load_error_shown: bool = False
    _project_configs: dict[Path, dict[str, Any]] = {}
    _project_load_errors: set[Path] = set()

    def __new__(cls) -> "ConfigurationManager":
        """シングルトンインスタンス作成"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_configuration(self, force_reload: bool = False) -> NovelConfiguration | None:
        """設定を取得（キャッシュ付き）

        Args:
            force_reload: 強制再読み込みフラグ

        Returns:
            設定エンティティまたはNone
        """
        if self._configuration is None or force_reload:
            try:
                from noveler.application.use_cases.load_configuration_use_case import (
                    LoadConfigurationRequest,
                    LoadConfigurationUseCase,
                )
                from noveler.infrastructure.repositories.yaml_configuration_repository import (
                    YamlConfigurationRepository,
                )

                yaml_repository = YamlConfigurationRepository()
                use_case = LoadConfigurationUseCase(yaml_repository)
                current_file = Path(__file__)
                guide_root = current_file.parent.parent.parent.parent
                primary_config_path = guide_root / "config" / "novel_config.yaml"
                if primary_config_path.exists():
                    config_path = primary_config_path
                else:
                    fallback1 = Path("config/novel_config.yaml")
                    config_path = fallback1 if fallback1.exists() else guide_root / "config" / "novel_config.yaml"
                request = LoadConfigurationRequest(config_file_path=config_path)
                try:
                    asyncio.get_running_loop()
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, use_case.execute(request))
                        response = future.result()
                except RuntimeError:
                    response = asyncio.run(use_case.execute(request))
                if response and response.success:
                    self._configuration = response.configuration
                else:
                    if not ConfigurationManager._load_error_shown:
                        if response:
                            console.print(f"設定読み込みエラー: {response.error_message}")
                        ConfigurationManager._load_error_shown = True
                    self._configuration = None
            except Exception as e:
                if not ConfigurationManager._load_error_shown:
                    console.print(f"設定ファクトリーエラー: {e}")
                    console.print("スタックトレース:")
                    traceback.print_exc()
                    ConfigurationManager._load_error_shown = True
                self._configuration = None
        return self._configuration

    def get_system_setting(self, key: str, default: str | None = None) -> str:
        """システム設定を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        config = self.get_configuration()
        if config:
            return config.get_system_setting(key, default)
        return default

    def get_path_setting(self, category: str, key: str, default: str | None = None) -> str:
        """パス設定を取得

        Args:
            category: パスカテゴリ
            key: パスキー
            default: デフォルト値

        Returns:
            パス文字列またはデフォルト値
        """
        config = self.get_configuration()
        if config:
            return config.get_path_setting(category, key, default)
        return default

    def get_default_setting(self, category: str, key: str, default: str | None = None) -> str:
        """デフォルト設定を取得

        Args:
            category: 設定カテゴリ
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値またはデフォルト値
        """
        config = self.get_configuration()
        if config:
            return config.get_default_setting(category, key, default)
        return default

    def is_feature_enabled(self, category: str, feature: str) -> bool:
        """機能フラグの有効性確認

        Args:
            category: 機能カテゴリ
            feature: 機能名

        Returns:
            機能有効性
        """
        config = self.get_configuration()
        if config:
            return config.is_feature_enabled(category, feature)
        return False

    def get_project_configuration(self, project_root: Path, force_reload: bool = False) -> dict[str, Any] | None:
        """プロジェクト設定を取得（キャッシュ付き）

        Args:
            project_root: プロジェクトルートパス
            force_reload: 強制再読み込みフラグ

        Returns:
            プロジェクト設定辞書またはNone
        """
        if not force_reload and project_root in self._project_configs:
            return self._project_configs[project_root]
        try:
            from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import (
                YamlProjectConfigRepository,
            )

            repository = YamlProjectConfigRepository(project_root)
            config_data = repository.load_config(project_root)
            self._project_configs[project_root] = config_data
            self._project_load_errors.discard(project_root)
            return config_data
        except Exception as e:
            if project_root not in self._project_load_errors:
                console.print(f"プロジェクト設定読み込みエラー ({project_root}): {e}")
                self._project_load_errors.add(project_root)
            return None

    def get_merged_configuration(self, project_root: Path) -> dict[str, Any]:
        """統合設定を取得（プロジェクト設定優先）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            統合された設定辞書
        """
        system_config = self.get_configuration()
        system_dict = system_config.to_dict() if system_config else {}
        project_config = self.get_project_configuration(project_root)
        project_dict = project_config or {}
        return {**system_dict, **project_dict}

    def clear_project_cache(self, project_root: Path | None = None) -> None:
        """プロジェクト設定キャッシュをクリア

        Args:
            project_root: クリア対象のプロジェクトルート（Noneの場合は全てクリア）
        """
        if project_root is None:
            self._project_configs.clear()
            self._project_load_errors.clear()
        else:
            self._project_configs.pop(project_root, None)
            self._project_load_errors.discard(project_root)

    def get_file_template(self, template_key: str) -> str:
        """ファイル名テンプレート取得

        Args:
            template_key: テンプレートキー

        Returns:
            ファイル名（設定またはデフォルト値）
        """
        from noveler.domain.services.file_template_service import FileTemplateService
        from noveler.infrastructure.repositories.yaml_file_template_repository import YamlFileTemplateRepository

        try:
            repository = YamlFileTemplateRepository()
            service = FileTemplateService(repository)
            return service.get_filename(template_key)
        except Exception:
            # エラー時はFileTemplateServiceのデフォルト値を使用
            service = FileTemplateService(None)
            return service.get_filename(template_key)

    def get_project_config_filename(self) -> str:
        """プロジェクト設定ファイル名取得"""
        return self.get_file_template("project_config")


_config_manager = ConfigurationManager()


def get_configuration_manager() -> ConfigurationManager:
    """設定管理マネージャーを取得

    Returns:
        ConfigurationManager インスタンス
    """
    return _config_manager
