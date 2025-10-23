"""JSONファイル保存ストラテジー

API応答・キャッシュデータ・パフォーマンス重視データの保存を担当
機械処理向けのデータ保存に最適
"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_file_storage_strategy import IFileStorageStrategy


class JsonStorageStrategy(IFileStorageStrategy):
    """JSONファイル保存ストラテジー"""

    def save(self, file_path: Path, content: Any, metadata: dict | None = None) -> bool:
        """JSONファイルを保存

        Args:
            file_path: 保存先パス
            content: JSON化可能なデータ
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

            # JSONとして保存
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(
                    save_data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str,  # datetime等の変換対応
                )

            return True

        except Exception:
            return False

    def load(self, file_path: Path) -> Any | None:
        """JSONファイルを読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            JSONデータ（メタデータ除去済み）
        """
        try:
            if not file_path.exists():
                return None

            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # メタデータキーを除去してcontentのみ返す
            if isinstance(data, dict) and "_meta" in data:
                return {k: v for k, v in data.items() if k != "_meta"}
            return data

        except Exception:
            return None

    def load_with_metadata(self, file_path: Path) -> tuple[Any | None, dict | None]:
        """JSONファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (JSONデータ, メタデータ)のタプル
        """
        try:
            if not file_path.exists():
                return None, None

            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

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
        return [".json"]

    def can_handle(self, file_path: Path, content_type: str) -> bool:
        """処理可能かチェック"""
        # 拡張子チェック
        if file_path.suffix.lower() in self.get_supported_extensions():
            return True

        # 内容タイプチェック
        return content_type in ["api_response", "cache", "data", "result"]
