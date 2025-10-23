"""
A38準拠パスサービス使用例

A38_執筆プロンプトガイド.md準拠のパス取得・ファイル操作例を示す。
既存の散在するパス生成コードをこのパターンに統一することで、
A38仕様への完全準拠とメンテナンス性向上を実現する。
"""

from noveler.presentation.shared.shared_utilities import get_a38_path_service


def example_basic_usage():
    """基本的な使用例"""
    print("=== A38準拠パスサービス基本使用例 ===")

    # サービス取得（シングルトンパターン）
    path_service = get_a38_path_service()

    # A38準拠ディレクトリパス取得
    print(f"プロットディレクトリ: {path_service.get_plots_dir()}")
    print(f"話別プロットディレクトリ: {path_service.get_episode_plots_dir()}")
    print(f"設定ディレクトリ: {path_service.get_settings_dir()}")
    print(f"原稿ディレクトリ: {path_service.get_manuscripts_dir()}")
    print(f"作業ファイルディレクトリ: {path_service.get_work_files_dir()}")


def example_episode_paths():
    """エピソード固有パス例"""
    print("\n=== エピソード固有パス例 ===")

    path_service = get_a38_path_service()
    episode_number = 5

    # A38準拠ファイルパス生成
    episode_plot_path = path_service.get_episode_plot_path(episode_number)
    print(f"話別プロット: {episode_plot_path}")
    # 出力例: PROJECT_ROOT/20_プロット/話別プロット/episode005.yaml

    manuscript_path = path_service.get_manuscript_path(episode_number, "異世界転移")
    print(f"原稿: {manuscript_path}")
    # 出力例: PROJECT_ROOT/40_原稿/第005話_異世界転移.md

    # A38準拠作業ファイル（各STEP用）
    for step in [0, 1, 5, 12]:
        work_file_path = path_service.get_work_file_path(episode_number, step)
        print(f"STEP {step:02d}: {work_file_path}")
        # 例: PROJECT_ROOT/60_作業ファイル/EP005_step00.yaml


def example_settings_paths():
    """設定ファイルパス例"""
    print("\n=== A38準拠設定ファイルパス例 ===")

    path_service = get_a38_path_service()

    # A38準拠設定ファイル
    character_settings = path_service.get_character_settings_path()
    print(f"キャラクター設定: {character_settings}")
    # PROJECT_ROOT/30_設定集/キャラクター.yaml

    character_growth = path_service.get_character_growth_history_path()
    print(f"キャラクター成長履歴: {character_growth}")
    # PROJECT_ROOT/30_設定集/キャラクター成長履歴.yaml

    worldview_settings = path_service.get_worldview_settings_path()
    print(f"世界観設定: {worldview_settings}")
    # PROJECT_ROOT/30_設定集/世界観.yaml


def example_directory_setup():
    """ディレクトリセットアップ例"""
    print("\n=== ディレクトリセットアップ例 ===")

    path_service = get_a38_path_service()

    # A38準拠ディレクトリ構造作成
    path_service.ensure_directories_exist()
    print("A38準拠ディレクトリ構造を作成しました")

    # 特定エピソード用ディレクトリ確保
    episode_number = 1
    path_service.ensure_episode_directories_exist(episode_number)
    print(f"エピソード{episode_number}用ディレクトリを確保しました")


def example_file_operations():
    """ファイル操作例"""
    print("\n=== A38準拠ファイル操作例 ===")

    path_service = get_a38_path_service()
    episode_number = 1

    # ディレクトリ作成
    path_service.ensure_episode_directories_exist(episode_number)

    # A38準拠エピソードプロット作成例
    episode_plot_path = path_service.get_episode_plot_path(episode_number)
    plot_content = """# EP001.yaml - A38準拠プロット
episode_number: 1
title: "最初の出会い"
genre: "異世界ファンタジー"
target_length: 8000

# A38準拠データ構造
scope_definition:
  theme: "新世界への第一歩"
  conflicts: ["環境適応", "言語の壁"]

structure:
  phases: 3
  beats_per_phase: 4
"""

    try:
        episode_plot_path.write_text(plot_content, encoding="utf-8")
        print(f"エピソードプロットを作成: {episode_plot_path}")
    except Exception as e:
        print(f"ファイル作成エラー: {e}")

    # A38準拠作業ファイル作成例
    work_file_path = path_service.get_work_file_path(episode_number, 0)  # STEP 0
    scope_content = """# EP001_step00.yaml - A38準拠スコープ定義
episode: 1
step: 0
title: "スコープ定義"

scope_definition:
  target_length: 8000
  narrative_focus: "主人公の異世界適応"
  emotional_arc: "困惑 → 受容 → 決意"
"""

    try:
        work_file_path.write_text(scope_content, encoding="utf-8")
        print(f"作業ファイルを作成: {work_file_path}")
    except Exception as e:
        print(f"ファイル作成エラー: {e}")


def example_migration_from_old_paths():
    """旧パスシステムからの移行例"""
    print("\n=== 旧パスシステムからの移行例 ===")

    # 🚫 旧方式（非推奨・A38非準拠）
    print("【旧方式 - 使用禁止】")
    # old_plot_path = Path("20_プロット") / f"第{episode:03d}話_タイトル.md"
    # old_work_path = Path("temp") / f"episode{episode:03d}_step{step:02d}.yaml"
    print("❌ ハードコードパス: Path('20_プロット') / f'第{episode:03d}話_タイトル.md'")
    print("❌ 非A38形式: Path('temp') / f'episode{episode:03d}_step{step:02d}.yaml'")

    # ✅ 新方式（A38準拠）
    print("\n【新方式 - A38準拠】")
    path_service = get_a38_path_service()
    episode_number = 1

    # A38準拠パス取得
    new_plot_path = path_service.get_episode_plot_path(episode_number)
    new_work_path = path_service.get_work_file_path(episode_number, 0)

    print(f"✅ A38準拠プロット: {new_plot_path}")
    print(f"✅ A38準拠作業ファイル: {new_work_path}")

    print("\n移行の利点:")
    print("- A38_執筆プロンプトガイド.md完全準拠")
    print("- 統一されたパス管理")
    print("- ハードコーディング解消")
    print("- テスト環境対応")
    print("- 後方互換性維持")


def example_test_environment():
    """テスト環境対応例"""
    print("\n=== テスト環境対応例 ===")

    import os

    # テスト環境設定
    os.environ["NOVELER_ENV"] = "test"

    path_service = get_a38_path_service()

    print("テスト環境でのパス:")
    print(f"プロット: {path_service.get_plots_dir()}")
    print(f"作業ファイル: {path_service.get_work_files_dir()}")
    print(f"原稿: {path_service.get_manuscripts_dir()}")

    # 環境をリセット
    del os.environ["NOVELER_ENV"]


def example_real_world_usage():
    """実際の使用シナリオ例"""
    print("\n=== 実際の使用シナリオ例 ===")

    # シナリオ: A38プロンプト実行準備
    path_service = get_a38_path_service()
    episode_number = 3

    print(f"エピソード{episode_number}のA38プロンプト実行準備:")

    # 1. 必要なディレクトリ確保
    path_service.ensure_episode_directories_exist(episode_number)
    print("✓ ディレクトリ構造確保完了")

    # 2. 入力ファイル存在チェック
    required_files = [
        path_service.get_episode_plot_path(episode_number),
        path_service.get_character_settings_path(),
        path_service.get_worldview_settings_path()
    ]

    for file_path in required_files:
        exists = "✓" if file_path.exists() else "✗"
        print(f"{exists} {file_path}")

    # 3. 出力ファイルパス準備
    output_paths = []
    for step in range(16):  # STEP 0-15
        work_file_path = path_service.get_work_file_path(episode_number, step)
        output_paths.append(work_file_path)

    print(f"✓ 出力パス準備完了 ({len(output_paths)}ファイル)")

    # 4. 最終原稿パス
    final_manuscript = path_service.get_work_file_path(episode_number, 12, "md")
    print(f"✓ 最終原稿: {final_manuscript}")


if __name__ == "__main__":
    """実行例"""
    print("A38準拠パスサービス使用例実行\n")

    # 各例を実行
    example_basic_usage()
    example_episode_paths()
    example_settings_paths()
    example_directory_setup()
    example_file_operations()
    example_migration_from_old_paths()
    example_test_environment()
    example_real_world_usage()

    print("\n=== まとめ ===")
    print("このA38準拠パスサービスにより:")
    print("• A38_執筆プロンプトガイド.md完全準拠")
    print("• 統一されたパス管理システム")
    print("• ハードコーディング完全解消")
    print("• テスト環境での干渉防止")
    print("• 後方互換性による段階的移行")
    print("• 品質の高いファイル操作")
    print("\n既存コードは scripts/tools/a38_path_migration_tool.py で移行支援")
