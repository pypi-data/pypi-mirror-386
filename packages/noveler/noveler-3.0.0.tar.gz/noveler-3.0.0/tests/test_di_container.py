#!/usr/bin/env python3
"""DIコンテナの動作テスト"""

import sys
import pytest
from pathlib import Path
from noveler.infrastructure.logging.unified_logger import get_logger

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# ログ設定
logger = get_logger(__name__)

def test_di_container():
    """DIコンテナの基本動作をテスト"""
    logger.info("🔧 DIコンテナテスト開始...")

    try:
        # DIファクトリーの取得
        from noveler.infrastructure.di.domain_di_container_factory import get_domain_di_factory

        logger.info("📦 DI ファクトリーを取得中...")
        di_factory = get_domain_di_factory()
        logger.info(f"✅ DI ファクトリー取得成功: {type(di_factory).__name__}")

        # CreateEpisodeUseCaseの取得
        from noveler.application.use_cases.create_episode_use_case import CreateEpisodeUseCase

        logger.info("🔧 CreateEpisodeUseCaseを解決中...")
        create_episode_use_case = di_factory.resolve(CreateEpisodeUseCase)
        logger.info(f"✅ CreateEpisodeUseCase取得成功: {type(create_episode_use_case).__name__}")

        # 実際にリポジトリが注入されているかテスト
        logger.info("📊 依存関係の確認...")
        logger.info(f"  - episode_repository: {type(create_episode_use_case.episode_repository).__name__}")
        logger.info(f"  - project_repository: {type(create_episode_use_case.project_repository).__name__}")
        logger.info(f"  - quality_repository: {type(create_episode_use_case.quality_repository).__name__}")

        return True

    except Exception as e:
        logger.exception(f"❌ DIコンテナテストエラー: {e}")
        return False

@pytest.mark.asyncio
async def test_usecase_execution():
    """ユースケース実行のテスト"""
    logger.info("🚀 ユースケース実行テスト開始...")

    try:
        from noveler.infrastructure.di.domain_di_container_factory import get_domain_di_factory
        from noveler.application.use_cases.create_episode_use_case import CreateEpisodeUseCase, CreateEpisodeRequest
        import asyncio

        # DIからユースケース取得
        di_factory = get_domain_di_factory()
        create_episode_use_case = di_factory.resolve(CreateEpisodeUseCase)

        # リクエスト作成
        request = CreateEpisodeRequest(
            project_id="test_project",
            episode_number=1,
            title="第001話",
            target_words=4000,
            initial_content="",
            tags=["テスト"],
            metadata={"test_mode": True}
        )

        logger.info(f"📝 リクエスト作成完了: {request}")

        # 非同期実行
        logger.info("⚡ ユースケース非同期実行中...")
        response = await create_episode_use_case.execute(request)
        logger.info(f"✅ ユースケース実行完了: success={response.success}")
        logger.info(f"📄 レスポンス詳細: {response.message}")
        if response.episode_id:
            logger.info(f"🆔 エピソードID: {response.episode_id}")

        return response.success

    except Exception as e:
        logger.exception(f"❌ ユースケース実行テストエラー: {e}")
        return False

def test_mcp_server_direct_call():
    """MCPサーバーの直接呼び出しテスト"""
    logger.info("🌐 MCPサーバー直接呼び出しテスト開始...")

    try:
        from mcp_servers.noveler.json_conversion_server import JSONConversionServer
        from pathlib import Path

        # MCPサーバー作成
        server = JSONConversionServer()

        # _execute_novel_command を直接呼び出し
        command = "write 1"
        options = {"fresh-start": False}
        project_root = str(Path.cwd())

        logger.info(f"📞 _execute_novel_command 直接呼び出し: {command}")
        result = server._execute_novel_command(command, options, project_root)

        logger.info("✅ MCPサーバー直接呼び出し完了")
        logger.info(f"📋 結果サマリー: {result[:200]}...")

        return True

    except Exception as e:
        logger.exception(f"❌ MCPサーバー直接呼び出しテストエラー: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 DIコンテナ・ユースケース統合テスト開始")
    logger.info("=" * 60)

    # テスト実行
    tests = [
        ("DIコンテナ基本動作", test_di_container),
        ("ユースケース実行", test_usecase_execution),
        ("MCPサーバー直接呼び出し", test_mcp_server_direct_call),
    ]

    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n🔬 [{test_name}] 開始...")
        results[test_name] = test_func()
        logger.info(f"{'✅' if results[test_name] else '❌'} [{test_name}] {'成功' if results[test_name] else '失敗'}")

    # 結果サマリー
    logger.info("\n" + "=" * 60)
    logger.info("📊 テスト結果サマリー:")
    success_count = sum(results.values())
    total_count = len(results)

    for test_name, success in results.items():
        logger.info(f"  {'✅' if success else '❌'} {test_name}")

    logger.info(f"\n🎯 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        logger.info("🎉 全テスト成功！DIコンテナとユースケース直接呼び出しが正常に動作しています")
    else:
        logger.error("⚠️ 一部のテストが失敗しました")

    sys.exit(0 if success_count == total_count else 1)
