#!/usr/bin/env python3
"""テスト用ヘルパー関数

ハードコーディング排除のための統一テストユーティリティ


仕様書: SPEC-UNIT-TEST
"""

from pathlib import Path

from noveler.presentation.shared.shared_utilities import get_common_path_service


def create_test_project_structure(project_root: Path) -> None:
    """テスト用プロジェクト構造を作成

    ハードコーディングを排除し、CommonPathServiceを使用してディレクトリ構造を作成

    Args:
        project_root: プロジェクトルートディレクトリ
    """
    path_service = get_common_path_service(project_root)

    # 必要なディレクトリをすべて作成
    directories = [
        path_service.get_plots_dir(),
        path_service.get_plots_dir(),
        path_service.get_plots_dir() / "章別プロット",
        path_service.get_plots_dir() / "話別プロット",
        path_service.get_management_dir(),
        path_service.get_manuscript_dir(),
        path_service.get_management_dir(),
        path_service.get_management_dir() / "A31_チェックリスト",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_test_manuscript_path(project_root: Path, episode_number: int = 1, title: str = "テスト") -> Path:
    """テスト用原稿ファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        episode_number: エピソード番号
        title: エピソードタイトル

    Returns:
        Path: 原稿ファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    manuscript_dir = path_service.get_manuscript_dir()

    filename = f"第{episode_number:03d}話_{title}.md"
    return manuscript_dir / filename


def get_test_plot_path(project_root: Path, episode_number: int = 1) -> Path:
    """テスト用プロットファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        episode_number: エピソード番号

    Returns:
        Path: プロットファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    plot_dir = path_service.get_plots_dir()

    filename = f"第{episode_number:03d}話_プロット.yaml"
    return plot_dir / filename


def create_test_episode_file(
    project_root: Path, episode_number: int = 1, title: str = "テスト", content: str | None = None
) -> Path:
    """テスト用エピソードファイルを作成

    Args:
        project_root: プロジェクトルートディレクトリ
        episode_number: エピソード番号
        title: エピソードタイトル
        content: ファイル内容（指定されない場合はデフォルト内容）

    Returns:
        Path: 作成されたファイルパス
    """
    episode_path = get_test_manuscript_path(project_root, episode_number, title)

    if content is None:
        content = f"""# 第{episode_number:03d}話 {title}

## シーン1: 物語の始まり

テスト用の原稿コンテンツです。

## シーン2: 展開

エピソード{episode_number}のテスト内容が続きます。
"""

    episode_path.parent.mkdir(parents=True, exist_ok=True)
    episode_path.write_text(content, encoding="utf-8")

    return episode_path


def cleanup_test_project(project_root: Path) -> None:
    """テストプロジェクトをクリーンアップ

    Args:
        project_root: クリーンアップ対象のプロジェクトルート
    """
    import shutil  # noqa: PLC0415

    if project_root.exists():
        shutil.rmtree(project_root)


def get_test_management_path(project_root: Path, filename: str = "話数管理.yaml") -> Path:
    """テスト用管理ファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        filename: 管理ファイル名

    Returns:
        Path: 管理ファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    management_dir = path_service.get_management_dir()
    return management_dir / filename


def get_test_settings_path(project_root: Path, filename: str = "キャラクター.yaml") -> Path:
    """テスト用設定ファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        filename: 設定ファイル名

    Returns:
        Path: 設定ファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    settings_dir = path_service.get_management_dir()
    return settings_dir / filename


def get_test_planning_path(project_root: Path, filename: str = "企画書.yaml") -> Path:
    """テスト用企画ファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        filename: 企画ファイル名

    Returns:
        Path: 企画ファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    planning_dir = path_service.get_plots_dir()
    return planning_dir / filename


def get_test_chapter_plot_path(project_root: Path, chapter_number: int = 1) -> Path:
    """テスト用章別プロットファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ
        chapter_number: 章番号

    Returns:
        Path: 章別プロットファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    plot_dir = path_service.get_plots_dir()
    return plot_dir / "章別プロット" / f"第{chapter_number}章.yaml"


def get_test_master_plot_path(project_root: Path) -> Path:
    """テスト用全体構成ファイルパスを取得

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        Path: 全体構成ファイルパス
    """
    path_service = get_common_path_service(project_root)
    path_service = get_common_path_service()
    plot_dir = path_service.get_plots_dir()
    return plot_dir / "全体構成.yaml"
