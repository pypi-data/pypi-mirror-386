"""統一ファイル保存サービス実装

用途に応じてファイル形式を自動判定し、適切な保存を行うサービス
複数のストラテジーを組み合わせて最適化された保存処理を提供
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_file_storage_strategy import IFileStorageStrategy
from noveler.domain.interfaces.i_unified_file_storage import FileContentType, IUnifiedFileStorage
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.storage.format_detector import FileFormatDetector
from noveler.infrastructure.storage.strategies import JsonStorageStrategy, MarkdownStorageStrategy, YamlStorageStrategy


class UnifiedFileStorageService(IUnifiedFileStorage):
    """統一ファイル保存サービス実装"""

    def __init__(self, project_root: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root or Path.cwd()
        self.format_detector = FileFormatDetector()

        # ストラテジーの初期化
        self._strategies: dict[str, IFileStorageStrategy] = {
            ".md": MarkdownStorageStrategy(),
            ".markdown": MarkdownStorageStrategy(),
            ".yaml": YamlStorageStrategy(),
            ".yml": YamlStorageStrategy(),
            ".json": JsonStorageStrategy(),
        }

    def save(
        self,
        file_path: Path | str,
        content: str | dict | list,
        content_type: FileContentType = FileContentType.AUTO,
        metadata: dict | None = None,
        encoding: str = "utf-8",
    ) -> bool:
        """ファイルを保存（形式自動選択）

        Args:
            file_path: 保存先パス
            content: 保存内容
            content_type: 内容タイプ（AUTO時は自動判定）
            metadata: メタデータ
            encoding: エンコーディング

        Returns:
            保存成功時True
        """
        try:
            # パス正規化
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            # 内容タイプの自動判定
            if content_type == FileContentType.AUTO:
                content_type = self.format_detector.detect_content_type(path, content)

            # 最適な拡張子の取得と適用
            # ただし、明示的に拡張子が指定されている場合は尊重する
            if not path.suffix:
                optimal_ext = self.format_detector.get_optimal_extension(content_type, path)
                path = path.with_suffix(optimal_ext)
            # 既存拡張子がある場合、互換性をチェックして必要時のみ変更
            elif content_type != FileContentType.AUTO:
                current_ext = path.suffix.lower()
                # 明示的に指定された拡張子が互換性がない場合のみ変更
                if not self.format_detector._is_compatible_extension(content_type, current_ext):
                    optimal_ext = self.format_detector.get_optimal_extension(content_type, path)
                    path = path.with_suffix(optimal_ext)

            # メタデータの自動追加
            if metadata is None:
                metadata = {}
            metadata.update(
                {
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "content_type": content_type.value,
                    "encoding": encoding,
                    "service": "UnifiedFileStorageService",
                }
            )

            # 適切なストラテジーで保存
            strategy = self._get_strategy(path)
            return strategy.save(path, content, metadata)

        except Exception:
            return False

    def load(self, file_path: Path | str) -> str | dict | list | None:
        """ファイルを読み込み（形式自動判定）

        Args:
            file_path: 読み込みファイルパス

        Returns:
            ファイル内容、失敗時はNone
        """
        try:
            # パス正規化
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            if not path.exists():
                return None

            # 適切なストラテジーで読み込み
            strategy = self._get_strategy(path)
            return strategy.load(path)

        except Exception:
            return None

    def load_with_metadata(self, file_path: Path | str) -> tuple[Any | None, dict | None]:
        """ファイルをメタデータと共に読み込み

        Args:
            file_path: 読み込みファイルパス

        Returns:
            (ファイル内容, メタデータ)のタプル、失敗時は(None, None)
        """
        try:
            # パス正規化
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            if not path.exists():
                return None, None

            # 適切なストラテジーで読み込み
            strategy = self._get_strategy(path)
            return strategy.load_with_metadata(path)

        except Exception:
            return None, None

    def save_manuscript(
        self, episode: int | str, content: str, metadata: dict | None = None
    ) -> bool:
        """原稿専用の保存メソッド

        Args:
            episode: エピソード番号
            content: 原稿内容
            project_root: プロジェクトルート
            metadata: メタデータ

        Returns:
            保存成功時True
        """
        try:
            # B20準拠: パス管理はPathServiceを使用
            path_service = create_path_service()
            manuscript_dir = path_service.get_manuscript_dir()

            # エピソード番号の正規化
            episode_num = int(episode) if isinstance(episode, str) else episode

            # ファイル名の決定
            filename = self.format_detector.suggest_filename(FileContentType.MANUSCRIPT, "", episode_num)
            file_path = manuscript_dir / filename

            # 原稿専用メタデータの設定
            manuscript_metadata = {
                "title": f"第{episode_num:03d}話",
                "episode": episode_num,
                "status": "completed",
                **(metadata or {}),
            }

            return self.save(file_path, content, FileContentType.MANUSCRIPT, manuscript_metadata)

        except Exception:
            return False

    def get_optimal_format(self, content_type: FileContentType, file_path: Path | None = None) -> str:
        """最適なファイル形式を取得

        Args:
            content_type: 内容タイプ
            file_path: ファイルパス（拡張子判定用）

        Returns:
            推奨される拡張子
        """
        return self.format_detector.get_optimal_extension(content_type, file_path)

    def _get_strategy(self, file_path: Path) -> IFileStorageStrategy:
        """ファイルパスに応じた適切なストラテジーを取得

        Args:
            file_path: ファイルパス

        Returns:
            対応するストラテジー

        Raises:
            ValueError: サポートされていない形式の場合
        """
        extension = file_path.suffix.lower()

        if extension in self._strategies:
            return self._strategies[extension]
        # デフォルトはYAML
        return self._strategies[".yaml"]

    def get_supported_formats(self) -> list[str]:
        """サポートされているファイル形式の一覧を取得

        Returns:
            サポート形式のリスト
        """
        return list(self._strategies.keys())

    def add_strategy(self, extension: str, strategy: IFileStorageStrategy) -> None:
        """新しいストラテジーを追加

        Args:
            extension: 拡張子
            strategy: ストラテジー実装
        """
        self._strategies[extension.lower()] = strategy
