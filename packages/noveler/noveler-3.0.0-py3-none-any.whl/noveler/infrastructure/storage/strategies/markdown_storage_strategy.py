"""Markdownファイル保存ストラテジー

YAML frontmatter付きMarkdown形式での保存を担当
原稿・ドキュメント等の人間が読み書きする文書に最適
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.i_file_storage_strategy import IFileStorageStrategy


class MarkdownStorageStrategy(IFileStorageStrategy):
    """Markdownファイル保存ストラテジー（YAML frontmatter対応）"""

    def save(self, file_path: Path, content: Any, metadata: dict | None = None) -> bool:
        """Markdownファイルを保存

        Args:
            file_path: 保存先パス
            content: Markdown内容（文字列）
            metadata: YAML frontmatterとして保存するメタデータ

        Returns:
            保存成功時True
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # メタデータのデフォルト値設定
            if metadata is None:
                metadata = {}

            # 自動メタデータの追加
            if "created" not in metadata:
                metadata["created"] = datetime.now(timezone.utc).isoformat()
            if "format" not in metadata:
                metadata["format"] = "markdown"

            # YAML frontmatter + Markdown内容の結合
            full_content = self._create_frontmatter_content(str(content), metadata)

            file_path.write_text(full_content, encoding="utf-8")
            return True

        except Exception:
            return False

    def load(self, file_path: Path) -> Any | None:
        """Markdownファイルを読み込み（内容のみ）

        Args:
            file_path: 読み込みファイルパス

        Returns:
            Markdown内容（frontmatter除去済み）
        """
        try:
            if not file_path.exists():
                return None

            content = file_path.read_text(encoding="utf-8")
            return self._extract_content_from_frontmatter(content)

        except Exception:
            return None

    def load_with_metadata(self, file_path: Path) -> tuple[Any | None, dict | None]:
        """Markdownファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (Markdown内容, frontmatterメタデータ)のタプル
        """
        try:
            if not file_path.exists():
                return None, None

            content = file_path.read_text(encoding="utf-8")
            markdown_content = self._extract_content_from_frontmatter(content)
            metadata = self._extract_metadata_from_frontmatter(content)

            return markdown_content, metadata

        except Exception:
            return None, None

    def get_supported_extensions(self) -> list[str]:
        """サポートする拡張子を取得"""
        return [".md", ".markdown"]

    def can_handle(self, file_path: Path, content_type: str) -> bool:
        """処理可能かチェック"""
        # 拡張子チェック
        if file_path.suffix.lower() in self.get_supported_extensions():
            return True

        # 内容タイプチェック
        return content_type in ["manuscript", "document", "text"]

    def _create_frontmatter_content(self, content: str, metadata: dict) -> str:
        """YAML frontmatter付きMarkdownコンテンツを作成

        Args:
            content: Markdown内容
            metadata: frontmatterメタデータ

        Returns:
            frontmatter付きコンテンツ
        """
        if not metadata:
            return content

        try:
            # YAMLとして安全にダンプ
            yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True, sort_keys=False)

            return f"""---
{yaml_content.rstrip()}
---

{content}"""
        except Exception:
            # YAML生成失敗時はメタデータなしで保存
            return content

    def _extract_content_from_frontmatter(self, full_content: str) -> str:
        """frontmatterからMarkdown内容を抽出

        Args:
            full_content: frontmatter付き全内容

        Returns:
            Markdown内容のみ
        """
        if not full_content.startswith("---"):
            return full_content

        # frontmatterパターンのマッチング
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            return match.group(2).strip()
        return full_content

    def _extract_metadata_from_frontmatter(self, full_content: str) -> dict:
        """frontmatterからメタデータを抽出

        Args:
            full_content: frontmatter付き全内容

        Returns:
            メタデータ辞書
        """
        if not full_content.startswith("---"):
            return {}

        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            try:
                yaml_content = match.group(1)
                return yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                return {}
        else:
            return {}
