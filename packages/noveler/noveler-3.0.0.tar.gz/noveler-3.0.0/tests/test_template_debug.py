#!/usr/bin/env python3
"""
ProgressiveTaskManagerの外部テンプレート読み込みデバッグテスト
"""

import sys
from pathlib import Path

import pytest

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
# noveler パッケージを確実に解決できるよう `src` を追加
sys.path.insert(0, str(project_root / "src"))

from noveler.domain.services.progressive_task_manager import ProgressiveTaskManager

# ログレベルを設定してデバッグ情報を表示


def _run_external_template_debug():
    """外部テンプレート読み込み検証ロジック"""

    print("=" * 70)
    print("ProgressiveTaskManager 外部テンプレート読み込み詳細デバッグ")
    print("=" * 70)

    try:
        # 1. タスク状態ファイルをクリア
        print("\n1. タスク状態のクリア")
        episode_number = 1
        state_file = project_root / "temp" / "task_states" / f"episode_{episode_number:03d}_state.json"
        print(f"   状態ファイル: {state_file}")

        if state_file.exists():
            state_file.unlink()
            print("   ✓ 既存の状態ファイルを削除")
        else:
            print("   ✓ 状態ファイルは存在しません（初期状態）")

        # 2. ProgressiveTaskManager初期化
        print("\n2. ProgressiveTaskManager初期化")
        task_manager = ProgressiveTaskManager(
            project_root=str(project_root),
            episode_number=episode_number
        )
        print("   ✓ 初期化成功")

        # 3. 現在の状態確認
        print("\n3. 現在のタスク状態確認")
        current_state = task_manager.current_state
        print(f"   現在のステップ: {current_state.get('current_step')}")
        print(f"   完了ステップ: {current_state.get('completed_steps', [])}")

        # 4. テンプレートディレクトリ確認
        print("\n4. テンプレートディレクトリ設定確認")
        templates_dir = task_manager.prompt_templates_dir
        print(f"   テンプレートディレクトリ: {templates_dir}")
        print(f"   存在確認: {templates_dir.exists()}")

        # 5. Step 0のテンプレートファイル確認
        print("\n5. Step 0テンプレートファイル確認")
        step_id = 0
        step_slug = task_manager._get_step_slug(step_id)
        if float(step_id).is_integer():
            step_token = f"write_step{int(step_id):02d}"
        else:
            step_token = f"write_step{str(step_id).replace('.', '_')}"
        template_filename = f"{step_token}_{step_slug}.yaml"
        template_path = templates_dir / "writing" / template_filename

        print(f"   ステップID: {step_id}")
        print(f"   ステップスラッグ: {step_slug}")
        print(f"   テンプレートファイル名: {template_filename}")
        print(f"   テンプレートパス: {template_path}")
        print(f"   ファイル存在: {template_path.exists()}")

        # 6. 直接テンプレート読み込みテスト
        print("\n6. 直接テンプレート読み込みテスト")
        template_data = task_manager._load_prompt_template(step_id)

        if not template_data:
            print("   ✗ テンプレート読み込み失敗")
            return False, "テンプレートをロードできませんでした"

        print("   ✓ テンプレート読み込み成功")
        print("   テンプレートメタデータ:")
        metadata = template_data.get('metadata', {})
        for key, value in metadata.items():
            print(f"     {key}: {value}")

        # プロンプト内容確認
        prompt_section = template_data.get('prompt', {})
        main_instruction = prompt_section.get('main_instruction', '')
        if main_instruction:
            print(f"   プロンプト長: {len(main_instruction)}")
            print("   プロンプト内容の一部:")
            lines = main_instruction.split('\n')[:10]
            for line in lines:
                print(f"     {line}")
            if len(main_instruction.split('\n')) > 10:
                print("     ...")

        # 制御設定確認
        control_settings = template_data.get('control_settings', {})
        print(f"   制御設定: {control_settings}")

        # 7. テンプレート変数置換テスト
        print("\n7. テンプレート変数置換テスト")
        current_task = task_manager._get_task_by_id(task_manager.tasks_config["tasks"], step_id)
        variables = task_manager._prepare_template_variables(step_id, current_task)
        print(f"   準備された変数: {variables}")

        if main_instruction:
            enhanced_instruction = task_manager._replace_variables(main_instruction, variables)

            print("   変数置換後のプロンプト内容:")
            lines = enhanced_instruction.split('\n')[:15]
            for line in lines:
                print(f"     {line}")
            if len(enhanced_instruction.split('\n')) > 15:
                print("     ...")

            # 外部テンプレート特有のメッセージ確認
            print("\n   外部テンプレート由来メッセージ確認:")
            scope_msg = "スコープ定義" in enhanced_instruction or "scope" in enhanced_instruction
            episode_msg = "エピソード" in enhanced_instruction
            structure_msg = "inputs・constraints・tasks" in enhanced_instruction

            print(f"     スコープ定義: {'✓' if scope_msg else '✗'}")
            print(f"     エピソード: {'✓' if episode_msg else '✗'}")
            print(f"     構造指示: {'✓' if structure_msg else '✗'}")

        # 8. get_writing_tasks()での外部テンプレート利用確認
        print("\n8. get_writing_tasks()での外部テンプレート利用確認")
        response = task_manager.get_writing_tasks()
        llm_instruction = response.get('llm_instruction', '')

        print(f"   LLM指示の長さ: {len(llm_instruction)}")
        print("   LLM指示内容:")
        lines = llm_instruction.split('\n')[:10]
        for line in lines:
            print(f"     {line}")
        if len(llm_instruction.split('\n')) > 10:
            print("     ...")

        # 外部テンプレート使用判定
        external_template_used = "inputs・constraints・tasks" in llm_instruction or "エピソード" in llm_instruction

        print(f"\n   外部テンプレート使用: {'✓ YES' if external_template_used else '✗ NO'}")

        # 結果サマリー
        print("\n" + "=" * 70)
        print("デバッグテスト結果サマリー")
        print("=" * 70)

        checks = [
            ("状態ファイルクリア", True),
            ("ProgressiveTaskManager初期化", True),
            ("テンプレートディレクトリ設定", templates_dir.exists()),
            ("テンプレートファイル存在", template_path.exists()),
            ("直接テンプレート読み込み", template_data is not None),
            ("外部テンプレート利用", external_template_used)
        ]

        for check_name, result in checks:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"   {check_name}: {status}")

        all_passed = all(result for _, result in checks)

        print("\n" + "=" * 70)
        if all_passed:
            print("最終結果: 外部テンプレート読み込み機能が正常に動作しています！")
            print("=" * 70)
            return True, ""

        print("最終結果: 外部テンプレート読み込みで問題が発生しています")
        print("=" * 70)
        return False, "外部テンプレート利用チェックが失敗しました"

    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False, f"テスト実行エラー: {e}"


def test_external_template_loading():
    """外部テンプレート読み込み機能の詳細テスト"""
    template_path = project_root / "templates" / "step00_scope_definition.yaml"
    if not template_path.exists():
        pytest.skip("テンプレートファイルが存在しないためスキップ")

    success, message = _run_external_template_debug()
    assert success, message


if __name__ == "__main__":
    ok, msg = _run_external_template_debug()
    if ok:
        sys.exit(0)
    print(f"✗ {msg}")
    sys.exit(1)
