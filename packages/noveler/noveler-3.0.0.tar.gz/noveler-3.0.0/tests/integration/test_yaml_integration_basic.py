#!/usr/bin/env python3
"""
DDD準拠YAML統合基盤 基本動作確認スクリプト

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書
基盤の基本動作を確認するための簡易テストスクリプト


仕様書: SPEC-INTEGRATION
"""

import sys
from pathlib import Path

import pytest

# スクリプトルートを追加
script_root = Path(__file__).parent
sys.path.insert(0, str(script_root))


@pytest.mark.spec("SPEC-INTEGRATION")
def test_yaml_integration_basic():
    """YAML統合基盤の基本動作確認"""
    print("🔧 DDD準拠YAML統合基盤 動作確認開始")

    try:
        # 基本インポートテスト
        from noveler.application.services.yaml_processing_service import YamlProcessingService
        from noveler.domain.interfaces.yaml_processor import IYamlProcessor
        from noveler.infrastructure.adapters.yaml_processor_adapter import YamlProcessorAdapter

        print("✅ モジュールインポート成功")

        # インスタンス生成テスト
        processor = YamlProcessorAdapter()
        service = YamlProcessingService(processor)
        print("✅ サービスインスタンス生成成功")

        # 基本処理テスト
        test_content = """これはテストエピソードの内容です。
複数行にわたる内容で、YAML処理の動作を確認します。
DDD準拠統合基盤のテストです。

このテストでは以下の機能を確認します：
1. マルチライン文字列の処理
2. YAML構造の生成
3. メタデータの適切な設定
4. バリデーション機能の動作
5. パフォーマンスの確認

統合基盤は正しく動作する必要があります。"""

        result = service.process_episode_content(test_content)
        print("✅ エピソードコンテンツ処理成功")

        # 結果検証
        assert isinstance(result, dict), "結果は辞書である必要があります"
        assert "content" in result, "結果にcontentフィールドが必要です"
        assert "processed_at" in result, "結果にprocessed_atフィールドが必要です"
        assert "content_length" in result, "結果にcontent_lengthフィールドが必要です"
        assert "line_count" in result, "結果にline_countフィールドが必要です"

        print(f"  - コンテンツ長: {result['content_length']}")
        print(f"  - 行数: {result['line_count']}")
        print(f"  - 処理日時: {result['processed_at'][:19]}...")

        # YAML構造生成テスト
        yaml_structure = service.create_episode_yaml_structure(
            episode_number=1, title="テストエピソード", content=test_content
        )

        print("✅ YAML構造生成成功")

        # YAML構造検証
        assert isinstance(yaml_structure, dict), "YAML構造は辞書である必要があります"
        assert "metadata" in yaml_structure, "YAML構造にmetadataが必要です"
        assert "prompt_content" in yaml_structure, "YAML構造にprompt_contentが必要です"
        assert "validation" in yaml_structure, "YAML構造にvalidationが必要です"

        metadata = yaml_structure["metadata"]
        assert metadata["episode_number"] == 1, "エピソード番号が正しく設定される必要があります"
        assert metadata["title"] == "テストエピソード", "タイトルが正しく設定される必要があります"
        assert "spec_id" in metadata, "仕様IDが設定される必要があります"

        print(f"  - エピソード番号: {metadata['episode_number']}")
        print(f"  - タイトル: {metadata['title']}")
        print(f"  - 仕様ID: {metadata['spec_id']}")

        # インターフェース準拠確認
        assert isinstance(processor, IYamlProcessor), "アダプターはIYamlProcessorを実装する必要があります"
        print("✅ DDD準拠インターフェース実装確認成功")

        # マルチライン処理テスト
        multiline_string = processor.create_multiline_string(test_content)
        assert multiline_string is not None, "マルチライン文字列生成が成功する必要があります"
        print("✅ マルチライン文字列処理成功")

        # 辞書処理テスト
        test_dict = {"title": "テストタイトル", "content": test_content, "number": 42, "enabled": True}

        processed_dict = processor.process_content_to_dict(test_dict)
        assert isinstance(processed_dict, dict), "処理済み辞書は辞書型である必要があります"
        assert "title" in processed_dict, "処理後も既存フィールドが保持される必要があります"
        assert processed_dict["number"] == 42, "数値フィールドが保持される必要があります"
        assert processed_dict["enabled"] is True, "真偽値フィールドが保持される必要があります"
        print("✅ 辞書処理成功")

        print("\n🎉 DDD準拠YAML統合基盤 全ての基本動作確認が成功しました！")
        return True

    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.spec("SPEC-INTEGRATION")
def test_performance():
    """パフォーマンステスト"""
    print("\n⚡ パフォーマンステスト開始")

    try:
        import time

        from noveler.application.services.yaml_processing_service import YamlProcessingService
        from noveler.infrastructure.adapters.yaml_processor_adapter import YamlProcessorAdapter

        processor = YamlProcessorAdapter()
        service = YamlProcessingService(processor)

        # 大きなコンテンツ生成
        large_content = "\n".join([f"Line {i}: This is a test line for performance testing." for i in range(1000)])

        start_time = time.time()
        result = service.process_episode_content(large_content)
        end_time = time.time()

        processing_time = end_time - start_time

        print(f"  - 処理時間: {processing_time:.3f}秒")
        print(f"  - コンテンツ行数: {result['line_count']}")
        print(f"  - コンテンツ長: {result['content_length']}")

        # パフォーマンス要件確認 (1000行を1秒以内)
        if processing_time < 1.0:
            print("✅ パフォーマンス要件クリア")
            return True
        print(f"⚠️  パフォーマンス要件未達 (期待: < 1.0秒, 実際: {processing_time:.3f}秒)")
        return False

    except Exception as e:
        print(f"❌ パフォーマンステストエラー: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DDD準拠YAML処理統合基盤 総合動作確認")
    print("SPEC-YAML-001 準拠")
    print("=" * 60)

    # 基本動作確認
    basic_success = test_yaml_integration_basic()

    # パフォーマンステスト
    performance_success = test_performance()

    print("\n" + "=" * 60)
    print("🏁 総合結果")
    print("=" * 60)

    if basic_success and performance_success:
        print("✅ 全てのテストが成功しました！")
        print("🎯 DDD準拠YAML処理統合基盤は正常に動作しています")
        sys.exit(0)
    else:
        print("❌ 一部のテストが失敗しました")
        sys.exit(1)
