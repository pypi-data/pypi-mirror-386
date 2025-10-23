"""原稿生成サービスファクトリー

ゴールデンサンプルのbootstrapパターンに基づいた依存性注入実装。
"""


from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.domain.interfaces.path_service_protocol import IPathService
from noveler.domain.services.writing_steps.manuscript_generator_service import (
    ManuscriptGeneratorService,
)
from noveler.infrastructure.factories.configuration_service_factory import (
    ConfigurationManager,
    get_configuration_manager,
)
from noveler.infrastructure.factories.logger_service_factory import get_logger_service
from noveler.infrastructure.factories.path_service_factory import get_path_service


def create_manuscript_generator(
    logger_service: ILoggerService | None = None,
    path_service: IPathService | None = None,
    config_manager: ConfigurationManager | None = None,
    **overrides
) -> ManuscriptGeneratorService:
    """原稿生成サービスのファクトリー関数

    ゴールデンサンプルのbootstrapパターンに基づき、
    依存性を解決してサービスインスタンスを生成する。

    Args:
        logger_service: ロガーサービス（Noneの場合はデフォルトを使用）
        path_service: パスサービス（Noneの場合はデフォルトを使用）
        config_manager: 設定管理サービス（Noneの場合はデフォルトを使用）
        **overrides: その他のオーバーライド設定

    Returns:
        設定済みのManuscriptGeneratorServiceインスタンス

    Example:
        # デフォルト設定で生成
        service = create_manuscript_generator()

        # カスタム依存性で生成
        custom_logger = MyCustomLogger()
        service = create_manuscript_generator(logger_service=custom_logger)

        # テスト用のモック注入
        mock_config = MockConfigurationManager()
        service = create_manuscript_generator(config_manager=mock_config)
    """
    # デフォルト依存性の解決
    if logger_service is None:
        logger_service = get_logger_service("manuscript_generator")

    if path_service is None:
        path_service = get_path_service()

    if config_manager is None:
        config_manager = get_configuration_manager()

    # サービスインスタンスの生成
    return ManuscriptGeneratorService(
        logger_service=logger_service,
        path_service=path_service,
        config_manager=config_manager,
        **overrides
    )


def create_test_manuscript_generator(**overrides) -> ManuscriptGeneratorService:
    """テスト用の原稿生成サービスを作成

    テスト環境用の設定で原稿生成サービスを生成する。

    Args:
        **overrides: オーバーライド設定

    Returns:
        テスト用に設定されたManuscriptGeneratorServiceインスタンス

    Example:
        # テスト用サービスの生成
        service = create_test_manuscript_generator()

        # カスタム設定でテスト
        service = create_test_manuscript_generator(
            target_word_count=1000,
            dry_run=True
        )
    """
    # テスト用のモックまたは軽量実装を使用
    # 実際のファイルI/OやAPI呼び出しを避ける

    # 必要に応じてテスト用の依存性を設定
    test_logger = get_logger_service("test_manuscript_generator")
    test_path = get_path_service()

    # テスト用の設定マネージャー（キャッシュやファイルアクセスを最小限に）
    test_config = get_configuration_manager()

    return create_manuscript_generator(
        logger_service=test_logger,
        path_service=test_path,
        config_manager=test_config,
        **overrides
    )
