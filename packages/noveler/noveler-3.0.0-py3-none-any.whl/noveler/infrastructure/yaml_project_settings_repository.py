"""プロジェクト設定リポジトリ - インフラストラクチャ層

プロジェクト設定.yamlから設定情報を取得する
"""

from pathlib import Path

import yaml

from noveler.infrastructure.di.container import resolve_service
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager


class YamlProjectSettingsRepository:
    """YAML形式のプロジェクト設定を扱うリポジトリ"""

    def get_genre(self, project_root: str | Path) -> str:
        """プロジェクトのジャンルを取得

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            ジャンル文字列
        """
        try:
            path_service = resolve_service("IPathService")
            settings_file = path_service.get_project_config_file()
        except (ValueError, KeyError):
            # DIコンテナが設定されていない場合のフォールバック
            settings_file = self._resolve_project_config_path(project_root)

        if not settings_file.exists():
            # 企画書から取得を試みる
            return self._get_genre_from_proposal(project_root)

        try:
            with Path(settings_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # ジャンル情報の取得(複数の可能性を考慮)
            genre = data.get("genre") or data.get("ジャンル") or data.get("category")

            if genre:
                return str(genre)
            # 企画書から取得を試みる
            return self._get_genre_from_proposal(project_root)

        except Exception:
            return "その他"

    def _get_genre_from_proposal(self, project_root: str | Path) -> str:
        """企画書.yamlからジャンルを取得"""
        try:
            path_service = resolve_service("IPathService")
            proposal_file = path_service.get_proposal_file()
        except (ValueError, KeyError):
            # DIコンテナが設定されていない場合のフォールバック
            proposal_file = Path(project_root) / "企画書.yaml"

        if not proposal_file.exists():
            return "その他"

        try:
            with Path(proposal_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # 基本情報セクションから取得
            basic_info = data.get("基本情報", {})
            genre = basic_info.get("ジャンル") or basic_info.get("genre")

            if genre:
                return str(genre)

            # トップレベルからも探す
            genre = data.get("genre") or data.get("ジャンル")

            return str(genre) if genre else "その他"

        except Exception:
            return "その他"

    def _resolve_project_config_path(self, project_root: str | Path) -> Path:
        """Resolve the project config file path using templates with safe fallback."""
        filename = "プロジェクト設定.yaml"
        base = Path(project_root)

        # プロジェクト直下の .novelerrc.* を優先
        for rc_name in (".novelerrc.yaml", ".novelerrc.yml"):
            rc_path = base / rc_name
            if rc_path.exists():
                try:
                    from noveler.infrastructure.repositories.yaml_file_template_repository import (
                        YamlFileTemplateRepository,
                    )

                    repository = YamlFileTemplateRepository(config_path=rc_path)
                    candidate = repository.get_template("project_config")
                    if isinstance(candidate, str) and candidate.strip():
                        return base / candidate.strip()
                except Exception:
                    continue

        # グローバル設定（ConfigurationManager）を参照
        try:
            manager = get_configuration_manager()
            candidate = manager.get_file_template("project_config")
            if isinstance(candidate, str) and candidate.strip():
                filename = candidate.strip()
        except Exception:
            pass

        return base / filename

    def get_title(self, project_root: str | Path) -> str:
        """プロジェクトのタイトルを取得"""
        try:
            path_service = resolve_service("IPathService")
            settings_file = path_service.get_project_config_file()
        except (ValueError, KeyError):
            # DIコンテナが設定されていない場合のフォールバック
            settings_file = self._resolve_project_config_path(project_root)

        if not settings_file.exists():
            return Path(project_root).name  # ディレクトリ名を返す

        try:
            with Path(settings_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            title = data.get("title") or data.get("タイトル") or data.get("作品名")
            return str(title) if title else Path(project_root).name

        except Exception:
            return Path(project_root).name

    def get_target_readers(self, project_root: str | Path) -> str:
        """ターゲット読者層を取得"""
        # 読者分析.yamlから取得
        try:
            path_service = resolve_service("IPathService")
            reader_analysis_file = path_service.get_reader_analysis_file()
        except (ValueError, KeyError):
            # DIコンテナが設定されていない場合のフォールバック
            reader_analysis_file = Path(project_root) / "読者分析.yaml"

        if reader_analysis_file.exists():
            try:
                with Path(reader_analysis_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                target = data.get("ターゲット読者層", {})
                if isinstance(target, dict):
                    age = target.get("年齢層", "")
                    gender = target.get("性別", "")
                    return f"{age} {gender}".strip()
                if isinstance(target, str):
                    return target

            except Exception as e:

                self.logger_service.warning("読者分析ファイル読み込みエラー: %s, エラー: %s", reader_analysis_file, e)

        # プロジェクト設定から取得
        try:
            path_service = resolve_service("IPathService")
            settings_file = path_service.get_project_config_file()
        except (ValueError, KeyError):
            settings_file = self._resolve_project_config_path(project_root)

        if settings_file.exists():
            try:
                with Path(settings_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                target = data.get("target_readers") or data.get("ターゲット読者")
                return str(target) if target else "一般"

            except Exception as e:

                self.logger_service.warning("プロジェクト設定ファイル読み込みエラー: %s, エラー: %s", settings_file, e)

        return "一般"
