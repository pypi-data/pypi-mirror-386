#!/usr/bin/env python3
"""各プロジェクトフォルダにnovelコマンドのショートカットを設置"""

import os
import shutil
import stat
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console


def setup_shortcuts() -> bool:
    """各プロジェクトにショートカットを設置"""

    # 00_ガイドディレクトリを基準に
    guide_dir = Path(__file__).parent.parent.parent
    novel_dir = guide_dir.parent
    template_path = guide_dir / "templates" / "novel_shortcut.sh"

    if not template_path.exists():
        console.print(f"エラー: テンプレートファイル '{template_path}' が見つかりません")
        return False

    console.print("プロジェクトにnovelショートカットを設置します...")
    console.print(f"対象ディレクトリ: {novel_dir}")
    console.print("")

    installed_count = 0

    # 各ディレクトリをチェック
    for project_dir in sorted(novel_dir.iterdir()):
        if not project_dir.is_dir():
            continue

        # 00_ガイドは除外
        if project_dir.name == "00_ガイド":
            continue

        # プロジェクト設定.yamlがあるか確認
        config_path = project_dir / "プロジェクト設定.yaml"
        if not config_path.exists():
            continue

        # ショートカットの配置先
        shortcut_path = project_dir / "novel"

        # 既存のファイルがある場合
        if shortcut_path.exists():
            console.print(f"⚠️  既存のファイルを発見: {shortcut_path}")
            response = input("  上書きしますか? (y/N): ")
            if response.lower() != "y":
                console.print("  スキップしました")
                continue

        # ショートカットをコピー
        try:
            shutil.copy2(template_path, shortcut_path)
            # 実行権限を追加
            st = os.stat(shortcut_path)
            os.chmod(shortcut_path, st.st_mode | stat.S_IEXEC)
            console.print(f"✅ 設置完了: {project_dir.name}")
            installed_count += 1
        except Exception as e:
            console.print(f"❌ エラー: {e}")

    console.print("")
    console.print(f"完了: {installed_count}個のプロジェクトに設置しました")

    if installed_count > 0:
        console.print("")
        console.print("使用方法:")
        console.print("  各プロジェクトフォルダで以下のように実行できます:")
        console.print("  ./novel check 1")
        console.print("  ./novel write 5")
        console.print("  ./novel analyze")

    return True


if __name__ == "__main__":
    setup_shortcuts()
