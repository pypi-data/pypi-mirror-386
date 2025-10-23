#!/usr/bin/env python3
"""プロジェクト名自動取得ユーティリティ

DDD準拠: Infrastructure層の独立実装
PROJECT_ROOT環境変数とproject.yamlファイルからプロジェクト名を自動検出する。
"""

import os
from pathlib import Path
from typing import Any

import yaml


def get_project_name_from_env() -> str | None:
    """環境変数とproject.yamlからプロジェクト名を取得

    Returns:
        Optional[str]: プロジェクト名(見つからない場合はNone)
    """
    # 1. PROJECT_ROOT環境変数の確認
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        return None

    project_root_path = Path(project_root)
    if not project_root_path.exists():
        return None

    # 2. project.yaml ファイルの確認
    project_yaml_path = project_root_path / "project.yaml"
    if not project_yaml_path.exists():
        # プロジェクト設定.yaml も試行
        project_yaml_path = project_root_path / "プロジェクト設定.yaml"
        if not project_yaml_path.exists():
            # PROJECT_ROOT環境変数が設定されている場合は、そのディレクトリ名を確実に使用
            return project_root_path.name

    # 3. YAML ファイルからプロジェクト名を読み取り
    try:
        f_content = project_yaml_path.read_text(encoding="utf-8")
        project_data: dict[str, Any] = yaml.safe_load(f_content) or {}

        # 複数の可能なキーを試行(優先順位付き)
        project_name_keys = [
            "title",  # プロジェクト設定.yaml の標準フィールド
            "project.name",  # ネストされた project.name
            "project_name",  # 直接的な project_name
            "name",  # 汎用的な name
            "project.project_name",  # 深くネストされた形式
        ]

        for key in project_name_keys:
            if "." in key:
                # ネストされたキー(例: project.name)
                keys = key.split(".")
                value = project_data
                try:
                    for k in keys:
                        value = value[k]
                    if value and str(value).strip():
                        # titleの場合、角括弧を除去して正規化
                        title = str(value).strip()
                        if key == "title":
                            # "[DEBUG]" などの特殊記号を除去
                            title = title.replace("[DEBUG]", "DEBUG").replace("[DEBUG]", "DEBUG")
                            title = title.replace("Ｆランク", "Fランク")  # 全角から半角へ
                        return title
                except (KeyError, TypeError):
                    continue
            else:
                # 単純なキー
                value = project_data.get(key)
                if value and str(value).strip():
                    title = str(value).strip()
                    if key == "title":
                        # "[DEBUG]" などの特殊記号を除去
                        title = title.replace("[DEBUG]", "DEBUG").replace("[DEBUG]", "DEBUG")
                        title = title.replace("Ｆランク", "Fランク")  # 全角から半角へ
                    return title

        # プロジェクト名が見つからない場合はPROJECT_ROOTディレクトリ名をフォールバック
        return project_root_path.name

    except Exception:
        # YAML読み取りエラーの場合はPROJECT_ROOTディレクトリ名をフォールバック
        return project_root_path.name


def detect_project_root() -> Path | None:
    """現在のディレクトリからプロジェクトルートを検出

    Returns:
        Optional[Path]: プロジェクトルートパス(見つからない場合はNone)
    """
    current = Path.cwd()
    project_indicators = [
        "project.yaml",
        "プロジェクト設定.yaml",
        "pyproject.toml",
        ".git",
        "CLAUDE.md",
        "40_原稿",  # 小説プロジェクト特有のディレクトリ
    ]

    while current != current.parent:
        if any((current / indicator).exists() for indicator in project_indicators):
            return current
        current = current.parent
    return None


def _get_project_name_from_path(project_root: Path) -> str | None:
    """パスから直接プロジェクト名を取得（DDD準拠・副作用なし）

    Args:
        project_root: プロジェクトルートパス

    Returns:
        Optional[str]: プロジェクト名(見つからない場合はNone)
    """
    if not project_root or not project_root.exists():
        return None

    # 1. プロジェクト設定ファイルからの読み取りを試行
    config_files = [project_root / "project.yaml", project_root / "プロジェクト設定.yaml"]

    for config_file in config_files:
        if config_file.exists():
            try:
                f_content = config_file.read_text(encoding="utf-8")
                project_data: dict[str, Any] = yaml.safe_load(f_content) or {}

                # 複数の可能なキーを試行(優先順位付き)
                project_name_keys = [
                    "title",  # プロジェクト設定.yaml の標準フィールド
                    "project.name",  # ネストされた project.name
                    "project_name",  # 直接的な project_name
                    "name",  # 汎用的な name
                    "project.project_name",  # 深くネストされた形式
                ]

                for key in project_name_keys:
                    if "." in key:
                        # ネストされたキー(例: project.name)
                        keys = key.split(".")
                        value = project_data
                        try:
                            for k in keys:
                                value = value[k]
                            if value and str(value).strip():
                                # titleの場合、角括弧を除去して正規化
                                title = str(value).strip()
                                if key == "title":
                                    # "[DEBUG]" などの特殊記号を除去
                                    title = title.replace("[DEBUG]", "DEBUG").replace("[DEBUG]", "DEBUG")
                                    title = title.replace("Ｆランク", "Fランク")  # 全角から半角へ
                                return title
                        except (KeyError, TypeError):
                            continue
                    else:
                        # 単純なキー
                        value = project_data.get(key)
                        if value and str(value).strip():
                            title = str(value).strip()
                            if key == "title":
                                # "[DEBUG]" などの特殊記号を除去
                                title = title.replace("[DEBUG]", "DEBUG").replace("[DEBUG]", "DEBUG")
                                title = title.replace("Ｆランク", "Fランク")  # 全角から半角へ
                            return title
            except Exception:
                continue

    # 2. フォールバック: ディレクトリ名から取得
    return project_root.name


def get_current_project_name() -> str | None:
    """現在のディレクトリのプロジェクト名を取得

    以下の順序で試行:
    1. PROJECT_ROOT環境変数 + project.yaml（最優先）
    2. 現在のディレクトリからの自動検出（フォールバック）

    Returns:
        Optional[str]: プロジェクト名(見つからない場合はNone)
    """
    # 1. 環境変数からの取得を試行（最優先）
    project_name = get_project_name_from_env()
    if project_name:
        return project_name

    # 2. PROJECT_ROOT環境変数が設定されているが、YAMLファイルの読み取りに失敗した場合
    # 環境変数のパスからディレクトリ名を直接取得
    project_root_env = os.getenv("PROJECT_ROOT")
    if project_root_env:
        project_root_path = Path(project_root_env)
        if project_root_path.exists():
            return project_root_path.name

    # 3. フォールバック: 現在のディレクトリからの自動検出
    project_root = detect_project_root()
    if not project_root:
        return None

    # DDD準拠修正: 環境変数の上書きを廃止し、直接パスから名前を取得
    # 副作用のある環境変数操作を廃止
    return _get_project_name_from_path(project_root)


def validate_project_name(project_name: str) -> bool:
    """プロジェクト名の妥当性を検証

    Args:
        project_name: 検証するプロジェクト名

    Returns:
        bool: 妥当な場合True
    """
    if not project_name or not project_name.strip():
        return False

    # PROJECT_ROOT環境変数が設定されている場合、そのディレクトリ内で検証
    project_root_env = os.getenv("PROJECT_ROOT")
    if project_root_env:
        project_path = Path(project_root_env)
        if project_path.exists():
            # プロジェクト設定ファイルの存在確認
            config_files = [project_path / "project.yaml", project_path / "プロジェクト設定.yaml"]
            for config_file in config_files:
                if config_file.exists():
                    # 設定ファイルからプロジェクト名を読み取って比較
                    try:
                        f_content = config_file.read_text(encoding="utf-8")
                        project_data: dict[str, Any] = yaml.safe_load(f_content) or {}

                        # titleフィールドでの比較を優先
                        title = project_data.get("title")
                        if title and str(title).strip() == project_name:
                            return True

                        # その他のフィールドでも比較
                        project_keys = ["project.name", "project_name", "name"]
                        for key in project_keys:
                            if "." in key:
                                keys = key.split(".")
                                value = project_data
                                try:
                                    for k in keys:
                                        value = value[k]
                                    if value and str(value).strip() == project_name:
                                        return True
                                except (KeyError, TypeError):
                                    continue
                            else:
                                value = project_data.get(key)
                                if value and str(value).strip() == project_name:
                                    return True
                    except Exception:
                        pass

            # ディレクトリ名での比較もフォールバック
            if project_path.name == project_name:
                return True

    # プロジェクトルートの検出を試行
    project_root = detect_project_root()
    if project_root:
        # プロジェクト設定ファイルの存在確認
        config_files = [project_root / "project.yaml", project_root / "プロジェクト設定.yaml"]
        for config_file in config_files:
            if config_file.exists():
                try:
                    f_content = config_file.read_text(encoding="utf-8")
                    project_data: dict[str, Any] = yaml.safe_load(f_content) or {}

                    # titleフィールドでの比較を優先
                    title = project_data.get("title")
                    if title and str(title).strip() == project_name:
                        return True

                    # その他のフィールドでも比較
                    project_keys = ["project.name", "project_name", "name"]
                    for key in project_keys:
                        if "." in key:
                            keys = key.split(".")
                            value = project_data
                            try:
                                for k in keys:
                                    value = value[k]
                                if value and str(value).strip() == project_name:
                                    return True
                            except (KeyError, TypeError):
                                continue
                        else:
                            value = project_data.get(key)
                            if value and str(value).strip() == project_name:
                                return True
                except Exception:
                    pass

        # ディレクトリ名での比較もフォールバック
        if project_root.name == project_name:
            return True

    # PROJECTS_ROOT環境変数が設定されている場合の検証
    projects_root = os.getenv("PROJECTS_ROOT")
    if projects_root:
        project_path = Path(projects_root) / project_name
        if project_path.exists():
            return True

    return False
