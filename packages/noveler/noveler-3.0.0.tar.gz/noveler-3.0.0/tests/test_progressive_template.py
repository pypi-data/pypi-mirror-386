#!/usr/bin/env python3
"""
ProgressiveTaskManagerのテンプレート読み込み機能テスト（修正版）
"""

import sys
import os
from pathlib import Path

import pytest

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
# noveler パッケージを確実に解決できるよう `src` を追加
sys.path.insert(0, str(project_root / "src"))

from noveler.domain.services.progressive_task_manager import ProgressiveTaskManager


def _run_template_loading_validation():
    """テンプレート読み込み評価を実行し結果を返す"""

    print("=" * 60)
    print("ProgressiveTaskManager テンプレート読み込みテスト（修正版）")
    print("=" * 60)

    try:
        # 1. 基本設定確認
        print("\n1. 基本設定確認")
        print(f"   プロジェクトルート: {project_root}")

        template_file = project_root / "templates" / "step00_scope_definition.yaml"
        print(f"   テンプレートファイル: {template_file}")
        print(f"   存在確認: {template_file.exists()}")

        # 2. ProgressiveTaskManager初期化
        print("\n2. ProgressiveTaskManager初期化")
        episode_number = 1
        task_manager = ProgressiveTaskManager(
            project_root=str(project_root),
            episode_number=episode_number
        )
        print("   ✓ 初期化成功")

        # 3. テンプレート読み込みテスト
        print("\n3. テンプレート読み込みテスト")
        try:
            response = task_manager.get_writing_tasks()
            print("   ✓ get_writing_tasks()実行成功")

            # 4. レスポンス構造確認
            print("\n4. レスポンス構造確認")
            print(f"   レスポンスタイプ: {type(response)}")

            if not isinstance(response, dict):
                print("   ✗ レスポンスが辞書形式ではありません")
                return False, "レスポンスが dict ではありません"

            print(f"   キー一覧: {list(response.keys())}")

            current_task = response.get('current_task')
            llm_instruction = response.get('llm_instruction', '')
            episode_num = response.get('episode_number')

            print(f"   エピソード番号: {episode_num}")
            print(f"   現在のタスク: {current_task is not None}")
            print(f"   LLM指示の長さ: {len(llm_instruction)}")

            # 5. LLM指示内容確認（外部テンプレート読み込み確認）
            print("\n5. LLM指示内容確認")
            if not llm_instruction:
                print("   ✗ LLM指示が空です")
                return False, "LLM指示が生成されませんでした"

            print("   LLM指示内容の一部:")
            lines = llm_instruction.split('\n')[:15]  # 最初の15行
            for line in lines:
                print(f"     {line}")
            if len(llm_instruction.split('\n')) > 15:
                print("     ...")

            # 6. 段階実行制御メッセージ確認
            print("\n6. 段階実行制御メッセージ確認")
            single_step_msg = "このステップのみを実行してください" in llm_instruction
            batch_blocked_msg = "複数ステップを一括で実行しないでください" in llm_instruction
            completion_msg = "完了を確認してから進んでください" in llm_instruction
            next_step_msg = "次のステップは別途指示があるまで実行しないでください" in llm_instruction

            print(f"   単一ステップメッセージ: {'✓' if single_step_msg else '✗'}")
            print(f"   バッチ実行禁止メッセージ: {'✓' if batch_blocked_msg else '✗'}")
            print(f"   完了確認メッセージ: {'✓' if completion_msg else '✗'}")
            print(f"   次ステップ制御メッセージ: {'✓' if next_step_msg else '✗'}")

            # 7. 外部テンプレート由来内容確認
            print("\n7. 外部テンプレート由来内容確認")
            scope_definition_msg = "スコープ定義" in llm_instruction
            episode_purpose_msg = "エピソード" in llm_instruction and "目標" in llm_instruction
            character_count_msg = "文字数" in llm_instruction

            print(f"   スコープ定義メッセージ: {'✓' if scope_definition_msg else '✗'}")
            print(f"   エピソード目標メッセージ: {'✓' if episode_purpose_msg else '✗'}")
            print(f"   文字数設定メッセージ: {'✓' if character_count_msg else '✗'}")

            # 結果サマリー
            print("\n" + "=" * 60)
            print("テスト結果サマリー")
            print("=" * 60)

            checks = [
                ("テンプレートファイル存在", template_file.exists()),
                ("ProgressiveTaskManager初期化", True),
                ("get_writing_tasks実行", True),
                ("LLM指示生成", len(llm_instruction) > 0),
                ("単一ステップ制御", single_step_msg),
                ("バッチ実行禁止", batch_blocked_msg),
                ("外部テンプレート読み込み", scope_definition_msg and episode_purpose_msg)
            ]

            for check_name, result in checks:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"   {check_name}: {status}")

            all_passed = all(result for _, result in checks)

            print("\n" + "=" * 60)
            final_status = "外部テンプレート読み込みが正常に動作しています" if all_passed else "一部の機能で問題があります"
            print(f"最終結果: {final_status}")
            print("=" * 60)

            if not all_passed:
                return False, "テンプレート検証の一部チェックが失敗しました"

            return True, ""

        except Exception as e:
            print(f"   ✗ テンプレート読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
            return False, f"テンプレート読み込みエラー: {e}"

    except Exception as e:
        print(f"✗ 初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        return False, f"初期化エラー: {e}"


def test_template_loading():
    """テンプレート読み込み機能をテストする"""
    template_file = project_root / "templates" / "step00_scope_definition.yaml"
    if not template_file.exists():
        pytest.skip("テンプレートファイルが存在しないためスキップ")

    success, message = _run_template_loading_validation()
    assert success, message


if __name__ == "__main__":
    ok, msg = _run_template_loading_validation()
    sys.exit(0 if ok else 1)
