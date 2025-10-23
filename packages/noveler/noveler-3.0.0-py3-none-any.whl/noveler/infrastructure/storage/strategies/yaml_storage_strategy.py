"""YAMLファイル保存ストラテジー

設定ファイル・構成データの保存を担当
人間が読み書きしやすい形式でのデータ保存に最適
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.i_file_storage_strategy import IFileStorageStrategy


class YamlStorageStrategy(IFileStorageStrategy):
    """YAMLファイル保存ストラテジー"""

    def save(self, file_path: Path, content: Any, metadata: dict | None = None) -> bool:
        """YAMLファイルを保存

        Args:
            file_path: 保存先パス
            content: YAML化可能なデータ
            metadata: 追加メタデータ（contentに統合される）

        Returns:
            保存成功時True
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # メタデータを統合
            save_data = content
            if isinstance(content, dict) and metadata:
                # メタデータは"_meta"キーで分離して保存
                save_data = {**content, "_meta": metadata}

            # YAMLとして保存
            with file_path.open("w", encoding="utf-8") as f:
                yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

            return True

        except Exception:
            return False

    def load(self, file_path: Path) -> Any | None:
        """YAMLファイルを読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            YAMLデータ（メタデータ除去済み）
        """
        try:
            if not file_path.exists():
                return None

            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # メタデータキーを除去してcontentのみ返す
            if isinstance(data, dict) and "_meta" in data:
                return {k: v for k, v in data.items() if k != "_meta"}
            return data

        except Exception:
            return None

    def load_with_metadata(self, file_path: Path) -> tuple[Any | None, dict | None]:
        """YAMLファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (YAMLデータ, メタデータ)のタプル
        """
        try:
            if not file_path.exists():
                return None, None

            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if isinstance(data, dict) and "_meta" in data:
                # メタデータを分離
                metadata = data["_meta"]
                content = {k: v for k, v in data.items() if k != "_meta"}
                return content, metadata
            # メタデータがない場合
            return data, {}

        except Exception:
            return None, None

    def get_supported_extensions(self) -> list[str]:
        """サポートする拡張子を取得"""
        return [".yaml", ".yml"]

    def can_handle(self, file_path: Path, content_type: str) -> bool:
        """処理可能かチェック"""
        # 拡張子チェック
        if file_path.suffix.lower() in self.get_supported_extensions():
            return True

        # 内容タイプチェック
        if content_type in ["config", "configuration", "settings", "metadata"]:
            return True

        # dictやlistのような構造化データもYAMLで処理
        return False
