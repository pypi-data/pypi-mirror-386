"""YAML設定ファイルからファイル名テンプレートを読み込むリポジトリ"""
import yaml
from typing import Dict, Optional
from pathlib import Path

from noveler.domain.services.file_template_service import FileTemplateRepository


class YamlFileTemplateRepository(FileTemplateRepository):
    """YAML設定ファイルからファイル名テンプレートを読み込む"""

    def __init__(self, config_path: Optional[Path] = None):
        """初期化

        Args:
            config_path: 設定ファイルパス（デフォルト: .novelerrc.yaml）
        """
        self.config_path = config_path or Path(".novelerrc.yaml")
        self._templates_cache: Optional[Dict[str, str]] = None

    def get_template(self, template_key: str) -> Optional[str]:
        """テンプレートキーからファイル名を取得"""
        templates = self._load_templates()
        return templates.get(template_key)

    def get_all_templates(self) -> Dict[str, str]:
        """全テンプレートを取得"""
        return self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """設定ファイルからテンプレートを読み込み"""
        if self._templates_cache is not None:
            return self._templates_cache

        try:
            if not self.config_path.exists():
                self._templates_cache = {}
                return self._templates_cache

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            file_templates = config.get("file_templates", {})
            self._templates_cache = file_templates
            return self._templates_cache

        except Exception:
            # 読み込みエラー時は空辞書を返す
            self._templates_cache = {}
            return self._templates_cache
