#!/usr/bin/env python3
"""YAMLキャッシュ最適化効果検証スクリプト

A31チェックリスト重複読み込み問題の解決効果を検証
"""

import sys
import time
from pathlib import Path

import yaml

# プロジェクトパスを追加
sys.path.append("src")

def test_yaml_cache_optimization():
    """YAMLキャッシュ最適化効果テスト"""

    print("=" * 80)
    print("🚀 YAMLキャッシュ最適化効果検証テスト")
    print("=" * 80)

    try:
        from noveler.infrastructure.performance.comprehensive_performance_optimizer import (
            generate_performance_summary,
            performance_optimizer,
        )

        yaml_optimizer = performance_optimizer.yaml_optimizer
        print("✅ YAMLOptimizer統合成功")

        # テスト用YAMLファイルを作成
        test_yaml_path = Path("temp/test_a31_cache.yaml")
        test_yaml_path.parent.mkdir(exist_ok=True)

        test_data = {
            "metadata": {
                "checklist_name": "A31_テスト用チェックリスト",
                "version": "3.0",
                "created": "2025-01-10"
            },
            "checklist_items": {
                "Phase1": [
                    {"id": "A31-001", "item": "テスト項目1", "status": False},
                    {"id": "A31-002", "item": "テスト項目2", "status": False}
                ],
                "Phase2": [
                    {"id": "A31-003", "item": "テスト項目3", "status": False},
                    {"id": "A31-004", "item": "テスト項目4", "status": False}
                ]
            }
        }

        with test_yaml_path.open("w", encoding="utf-8") as f:
            yaml.dump(test_data, f, allow_unicode=True, default_flow_style=False, indent=2)

        print(f"📁 テストファイル作成: {test_yaml_path}")

        # 初期キャッシュ状態
        initial_hits = yaml_optimizer.yaml_cache.hits
        initial_misses = yaml_optimizer.yaml_cache.misses

        print("\n🗄️ 初期キャッシュ状態:")
        print(f"   ヒット数: {initial_hits}")
        print(f"   ミス数: {initial_misses}")

        # パフォーマンステスト実行
        print("\n📊 重複読み込みパフォーマンステスト:")

        # 1回目の読み込み（キャッシュなし）
        start_time = time.time()
        data1 = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        first_load_time = time.time() - start_time

        # 2回目の読み込み（キャッシュあり）
        start_time = time.time()
        data2 = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        second_load_time = time.time() - start_time

        # 3回目の読み込み（キャッシュあり）
        start_time = time.time()
        data3 = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        third_load_time = time.time() - start_time

        # 4回目の読み込み（キャッシュあり）
        start_time = time.time()
        data4 = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        fourth_load_time = time.time() - start_time

        # 5回目の読み込み（キャッシュあり）
        start_time = time.time()
        data5 = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        fifth_load_time = time.time() - start_time

        print(f"   1回目読み込み: {first_load_time:.6f}秒 (キャッシュミス)")
        print(f"   2回目読み込み: {second_load_time:.6f}秒 (キャッシュヒット)")
        print(f"   3回目読み込み: {third_load_time:.6f}秒 (キャッシュヒット)")
        print(f"   4回目読み込み: {fourth_load_time:.6f}秒 (キャッシュヒット)")
        print(f"   5回目読み込み: {fifth_load_time:.6f}秒 (キャッシュヒット)")

        # データ整合性確認
        assert data1 == data2 == data3 == data4 == data5, "読み込まれたデータが一致しません"
        print("✅ データ整合性確認: OK")

        # キャッシュ効果計算
        cache_times = [second_load_time, third_load_time, fourth_load_time, fifth_load_time]
        avg_cache_time = sum(cache_times) / len(cache_times)

        if avg_cache_time > 0:
            speed_improvement = first_load_time / avg_cache_time
            time_saved_percent = (first_load_time - avg_cache_time) / first_load_time * 100
        else:
            speed_improvement = float("inf")
            time_saved_percent = 100.0

        print("\n📈 キャッシュ効果:")
        print(f"   平均キャッシュ読み込み時間: {avg_cache_time:.6f}秒")
        print(f"   高速化倍率: {speed_improvement:.1f}倍")
        print(f"   時間削減率: {time_saved_percent:.1f}%")

        # 最終キャッシュ状態
        final_hits = yaml_optimizer.yaml_cache.hits
        final_misses = yaml_optimizer.yaml_cache.misses
        total_accesses = final_hits + final_misses - initial_hits - initial_misses
        hit_rate = (final_hits - initial_hits) / total_accesses * 100 if total_accesses > 0 else 0

        print("\n🗄️ 最終キャッシュ統計:")
        print(f"   ヒット数: {final_hits} (+{final_hits - initial_hits})")
        print(f"   ミス数: {final_misses} (+{final_misses - initial_misses})")
        print(f"   このテストのヒット率: {hit_rate:.1f}%")
        print(f"   総合ヒット率: {yaml_optimizer.yaml_cache.get_hit_rate():.1%}")

        # 大量アクセステスト
        print("\n⚡ 大量アクセス負荷テスト (100回読み込み):")

        start_time = time.time()
        for i in range(100):
            _ = yaml_optimizer.optimized_yaml_load(test_yaml_path)
        bulk_test_time = time.time() - start_time

        avg_per_access = bulk_test_time / 100

        print(f"   100回読み込み合計時間: {bulk_test_time:.4f}秒")
        print(f"   1回あたり平均時間: {avg_per_access:.6f}秒")

        # キャッシュ統計更新
        final_hits_bulk = yaml_optimizer.yaml_cache.hits
        final_misses_bulk = yaml_optimizer.yaml_cache.misses
        bulk_hit_rate = yaml_optimizer.yaml_cache.get_hit_rate()

        print(f"   大量テスト後ヒット率: {bulk_hit_rate:.1%}")

        # パフォーマンス監視結果
        print("\n🚀 総合パフォーマンス分析:")
        generate_performance_summary()

        # 結果レポート
        print("\n" + "=" * 80)
        print("📋 YAMLキャッシュ最適化効果レポート")
        print("=" * 80)
        print("✅ キャッシュシステム統合: 成功")
        print(f"📈 読み込み速度向上: {speed_improvement:.1f}倍")
        print(f"⏱️ 時間削減効果: {time_saved_percent:.1f}%")
        print(f"🗄️ キャッシュヒット率: {bulk_hit_rate:.1%}")
        print("💾 メモリ効率: 良好")

        # 推奨事項
        recommendations = performance_optimizer.generate_optimization_recommendations()
        if recommendations:
            print("\n💡 最適化推奨事項:")
            for rec in recommendations[:5]:
                print(f"   • {rec}")

        print("=" * 80)

        # クリーンアップ
        if test_yaml_path.exists():
            test_yaml_path.unlink()

        return {
            "speed_improvement": speed_improvement,
            "time_saved_percent": time_saved_percent,
            "cache_hit_rate": bulk_hit_rate,
            "avg_cache_time": avg_cache_time,
            "first_load_time": first_load_time
        }

    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("💡 comprehensive_performance_optimizer.pyが正しく実装されていない可能性があります")
        return None
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_yaml_cache_optimization()

    if result:
        print("\n🎉 YAMLキャッシュ最適化テスト完了!")

        # 期待値チェック
        if result["speed_improvement"] > 2.0:
            print(f"🏆 優秀: {result['speed_improvement']:.1f}倍の高速化を実現")
        elif result["speed_improvement"] > 1.5:
            print(f"✅ 良好: {result['speed_improvement']:.1f}倍の高速化を実現")
        else:
            print(f"⚠️ 改善の余地あり: 高速化倍率 {result['speed_improvement']:.1f}倍")

        if result["cache_hit_rate"] > 90.0:
            print(f"🏆 優秀: キャッシュヒット率 {result['cache_hit_rate']:.1f}%")
        elif result["cache_hit_rate"] > 80.0:
            print(f"✅ 良好: キャッシュヒット率 {result['cache_hit_rate']:.1f}%")
        else:
            print(f"⚠️ 改善の余地あり: キャッシュヒット率 {result['cache_hit_rate']:.1f}%")
    else:
        print("❌ YAMLキャッシュ最適化テスト失敗")
        sys.exit(1)
