"""ファイル形式自動判定サービス

用途・内容・パスに基づいて最適なファイル形式を自動判定する
"""

import re
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_unified_file_storage import FileContentType


class FileFormatDetector:
    """ファイル形式自動判定クラス"""

    # 用途別推奨形式マッピング
    CONTENT_TYPE_FORMAT_MAP = {
        FileContentType.MANUSCRIPT: ".md",  # 原稿 -> Markdown
        FileContentType.CONFIG: ".yaml",  # 設定 -> YAML
        FileContentType.METADATA: ".yaml",  # メタデータ -> YAML
        FileContentType.CACHE: ".json",  # キャッシュ -> JSON
        FileContentType.API_RESPONSE: ".json",  # API応答 -> JSON
    }

    # ディレクトリ名による判定ルール
    DIRECTORY_TYPE_MAP = {
        "40_原稿": FileContentType.MANUSCRIPT,
        "manuscripts": FileContentType.MANUSCRIPT,
        "docs": FileContentType.MANUSCRIPT,
        "config": FileContentType.CONFIG,
        "settings": FileContentType.CONFIG,
        "cache": FileContentType.CACHE,
        "temp": FileContentType.CACHE,
        "api": FileContentType.API_RESPONSE,
        "metadata": FileContentType.METADATA,
    }

    # ファイル名パターンによる判定ルール
    FILENAME_PATTERN_MAP = {
        r"第\d+話": FileContentType.MANUSCRIPT,  # 第001話.md
        r"episode_\d+": FileContentType.MANUSCRIPT,  # episode_001.md
        r"config": FileContentType.CONFIG,  # config.yaml
        r"settings": FileContentType.CONFIG,  # settings.yaml
        r"\.cache": FileContentType.CACHE,  # *.cache.json
        r"_response": FileContentType.API_RESPONSE,  # *_response.json
        r"_result": FileContentType.API_RESPONSE,  # *_result.json
    }

    def detect_content_type(
        self, file_path: Path, content: Any | None = None, hint: str | None = None
    ) -> FileContentType:
        """内容タイプを自動判定

        Args:
            file_path: ファイルパス
            content: ファイル内容（判定ヒント用）
            hint: 判定ヒント文字列

        Returns:
            判定された内容タイプ
        """
        # 1. ヒントによる判定
        if hint:
            for content_type in FileContentType:
                if content_type.value in hint.lower():
                    return content_type

        # 2. ディレクトリ名による判定
        for parent in file_path.parents:
            dir_name = parent.name.lower()
            if dir_name in self.DIRECTORY_TYPE_MAP:
                return self.DIRECTORY_TYPE_MAP[dir_name]

        # 3. ファイル名パターンによる判定
        filename = file_path.name.lower()
        for pattern, content_type in self.FILENAME_PATTERN_MAP.items():
            if re.search(pattern, filename):
                return content_type

        # 4. 拡張子による判定
        suffix = file_path.suffix.lower()
        if suffix in [".md", ".markdown"]:
            return FileContentType.MANUSCRIPT
        if suffix in [".yaml", ".yml"]:
            return FileContentType.CONFIG
        if suffix in [".json"]:
            return FileContentType.API_RESPONSE

        # 5. 内容による判定（文字列の場合）
        if content and isinstance(content, str):
            # Markdownライクな内容の検出
            if self._looks_like_markdown(content) or content.strip().startswith("---"):
                return FileContentType.MANUSCRIPT

        # 6. デフォルト（設定として処理）
        return FileContentType.CONFIG

    def get_optimal_extension(self, content_type: FileContentType, current_path: Path | None = None) -> str:
        """最適な拡張子を取得

        Args:
            content_type: 内容タイプ
            current_path: 現在のファイルパス（既存拡張子の考慮用）

        Returns:
            推奨拡張子
        """
        # 既存の拡張子が適切な場合はそれを保持
        if current_path and current_path.suffix:
            current_ext = current_path.suffix.lower()
            if self._is_compatible_extension(content_type, current_ext):
                return current_ext

        # 用途別推奨形式を返す
        return self.CONTENT_TYPE_FORMAT_MAP.get(content_type, ".yaml")

    def suggest_filename(self, content_type: FileContentType, base_name: str, episode: int | None = None) -> str:
        """最適なファイル名を提案

        Args:
            content_type: 内容タイプ
            base_name: ベースファイル名
            episode: エピソード番号（原稿の場合）

        Returns:
            推奨ファイル名
        """
        extension = self.CONTENT_TYPE_FORMAT_MAP.get(content_type, ".yaml")

        if content_type == FileContentType.MANUSCRIPT and episode:
            return f"第{episode:03d}話{extension}"
        # 拡張子がない場合は追加
        if not base_name.endswith(extension):
            return f"{base_name}{extension}"
        return base_name

    def _looks_like_markdown(self, content: str) -> bool:
        """内容がMarkdownかどうかを判定

        Args:
            content: 判定対象の内容

        Returns:
            Markdownらしい場合True
        """
        markdown_indicators = [
            r"^#+\s",  # ヘッダー
            r"^\*\s",  # リスト
            r"^-\s",  # リスト
            r"^\d+\.\s",  # 番号付きリスト
            r"\*\*.*?\*\*",  # 太字
            r"_.*?_",  # 斜体
            r"\[.*?\]\(.*?\)",  # リンク
            r"```",  # コードブロック
        ]

        return any(re.search(pattern, content, re.MULTILINE) for pattern in markdown_indicators)

    def _is_compatible_extension(self, content_type: FileContentType, extension: str) -> bool:
        """内容タイプと拡張子の互換性をチェック

        Args:
            content_type: 内容タイプ
            extension: 拡張子

        Returns:
            互換性がある場合True
        """
        compatible_extensions = {
            FileContentType.MANUSCRIPT: [".md", ".markdown"],
            FileContentType.CONFIG: [".yaml", ".yml", ".json"],  # CONFIGはJSONも許可
            FileContentType.METADATA: [".yaml", ".yml", ".json"],  # METADATAもJSONも許可
            FileContentType.CACHE: [".json"],
            FileContentType.API_RESPONSE: [".json"],
        }

        return extension in compatible_extensions.get(content_type, [])
