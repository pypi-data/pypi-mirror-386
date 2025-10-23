"""Infrastructure.setup.project_env_setup
Where: Infrastructure module configuring project environments.
What: Sets environment variables, paths, and prerequisites for running the project.
Why: Simplifies environment setup for developers and automation.
"""

from noveler.presentation.shared.shared_utilities import console


"プロジェクト設定.yamlからパス情報を読み取り、環境変数設定用のシェルスクリプトを生成\n\n使用方法:\n    python3 setup_project_env.py [プロジェクト設定.yamlのパス]\n\n    # 生成されたスクリプトを実行\n    source project_env.sh\n"
import os
import sys
from pathlib import Path
from typing import Any

import yaml


def load_project_config(config_path) -> dict[str, Any]:
    """プロジェクト設定を読み込む"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    try:
        with Path(config_path).open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"設定ファイル読み込みエラー: {e}")
        sys.exit(1)


def generate_env_script(config: object, config_path) -> None:
    """環境変数設定スクリプトを生成"""
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    if "paths" not in config or "project_root" not in config["paths"]:
        console.print("エラー: プロジェクトルート設定が見つかりません")
        sys.exit(1)
    project_root = config["paths"]["project_root"]
    if not os.path.exists(project_root):
        console.print(f"警告: プロジェクトルート '{project_root}' が存在しません")
    config_dir = os.path.dirname(os.path.abspath(config_path))
    if os.path.abspath(config_dir) == os.path.abspath(project_root):
        guide_root = os.path.join(os.path.dirname(project_root), "00_ガイド")
    else:
        guide_root = os.path.join(os.path.dirname(config_dir), "00_ガイド")
    if "guide_root" in config["paths"]:
        guide_root = config["paths"]["guide_root"]
    project_name = config.get("project", {}).get("name", "Unknown Project")
    script_content = f"""#!/bin/bash\n# プロジェクト環境設定スクリプト\n# プロジェクト: {project_name}\n# 生成日時: $(date\n)\n# プロジェクトルートの設定\nexport PROJECT_ROOT="{project_root}"\n\n# ガイドルートの設定\nexport GUIDE_ROOT="{guide_root}"\n\n# プロジェクト名の設定(オプション)\nexport PROJECT_NAME="{project_name}"\n\n# 環境変数の確認\necho "環境変数を設定しました:"\necho "PROJECT_ROOT: $PROJECT_ROOT"\necho "GUIDE_ROOT: $GUIDE_ROOT"\necho "PROJECT_NAME: $PROJECT_NAME"\n\n# ディレクトリの存在確認\nif [ ! -d "$PROJECT_ROOT" ]; then:\n    echo "警告: プロジェクトディレクトリが存在しません: $PROJECT_ROOT"\nfi\n\nif [ ! -d "$GUIDE_ROOT" ]; then:\n    echo "警告: ガイドディレクトリが存在しません: $GUIDE_ROOT"\nfi\n\n# 便利なエイリアス\nalias cdproj="cd '$PROJECT_ROOT'"\nalias cdguide="cd '$GUIDE_ROOT'"\nalias cdscripts="cd '$GUIDE_ROOT/scripts'"\nalias cdmanuscripts="cd '\\$PROJECT_ROOT/40_原稿'"\nalias cdmanagement="cd '\\$PROJECT_ROOT/50_管理資料'"\n\necho ""\necho "便利なエイリアスも設定しました:"\necho "  cdproj       - プロジェクトルートへ移動"\necho "  cdguide      - ガイドディレクトリへ移動"\necho "  cdscripts    - スクリプトディレクトリへ移動"\necho "  cdmanuscripts - 原稿ディレクトリへ移動"\necho "  cdmanagement  - 管理資料ディレクトリへ移動"\n"""
    output_path = "project_env.sh"
    try:
        # バッチ書き込みを使用
        Path(output_path).write_text(script_content, encoding="utf-8")
        Path(output_path).chmod(493)
        console.print(f"環境設定スクリプトを生成しました: {output_path}")
        console.print(f"使用方法: source {output_path}")
    except Exception as e:
        console.print(f"スクリプト生成エラー: {e}")
        sys.exit(1)


def main() -> None:
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    if len(sys.argv) < 2:
        config_path = "プロジェクト設定.yaml"
        if not os.path.exists(config_path):
            console.print("使用方法: python project_env_setup.py <設定ファイルパス>")
            console.print("または、カレントディレクトリにプロジェクト設定.yamlを配置してください")
            sys.exit(1)
    else:
        config_path = sys.argv[1]
    if not os.path.exists(config_path):
        console.print(f"エラー: 設定ファイル '{config_path}' が見つかりません")
        sys.exit(1)
    config = load_project_config(config_path)
    generate_env_script(config, config_path)


if __name__ == "__main__":
    main()
