"""
Episode Title Retrieval Domain Service

SPEC-PROMPT-GENERATE-AUTO-TITLE: Automatic title retrieval for prompt generation
SDD+DDD+TDD準拠実装
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from noveler.domain.interfaces.path_service import IPathService

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class EpisodeTitleSource(Enum):
    """エピソードタイトル取得元"""

    FILE_SYSTEM = "file_system"
    REPOSITORY_DATA = "repository_data"
    DEFAULT_FALLBACK = "default_fallback"


@dataclass
class EpisodeTitleResult:
    """エピソードタイトル取得結果"""

    title: str
    source: EpisodeTitleSource
    confidence: float
    is_default: bool

    def is_high_confidence(self) -> bool:
        """高信頼度判定"""
        return self.confidence >= 0.8


class EpisodeTitleRetrievalService:
    """エピソードタイトル取得ドメインサービス

    責務:
    - 既存プロジェクトデータからのタイトル自動取得
    - ファイルシステム・リポジトリデータの統合検索
    - フォールバック戦略による堅牢性確保

    DDD準拠設計:
    - Pure Domain Logic（インフラ依存なし）
    - 共通基盤統合（CommonPathService活用）
    - エラーハンドリング統合
    """

    def __init__(self, path_service: IPathService) -> None:
        """サービス初期化"""
        self._path_service = path_service
    def retrieve_episode_title(
        self, project_root: Path, episode_number: int, project_name: str | None = None
    ) -> EpisodeTitleResult:
        """エピソードタイトル自動取得

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
            project_name: プロジェクト名（オプション）

        Returns:
            EpisodeTitleResult: タイトル取得結果
        """
        # 1st Priority: PathServiceの統一ロジックで取得
        try:
            title = self._path_service.get_episode_title(episode_number)
            if title:
                return EpisodeTitleResult(
                    title=title, source=EpisodeTitleSource.FILE_SYSTEM, confidence=0.95, is_default=False
                )
        except Exception:
            pass

        # 2nd Priority: ファイルシステムから直接取得（互換フォールバック）
        file_system_result = self._extract_from_file_system(project_root, episode_number)
        if file_system_result and file_system_result.is_high_confidence():
            return file_system_result

        # 3rd Priority: リポジトリデータから取得
        if project_name:
            repository_result = self._extract_from_repository_data(project_name, episode_number)
            if repository_result and repository_result.is_high_confidence():
                return repository_result

        # Fallback: デフォルトタイトル生成
        return self._generate_default_title(episode_number)

    def _extract_from_file_system(self, project_root: Path, episode_number: int) -> EpisodeTitleResult | None:
        """ファイルシステムからタイトル抽出

        Args:
            project_root: プロジェクトルート
            episode_number: エピソード番号

        Returns:
            Optional[EpisodeTitleResult]: 抽出結果
        """
        try:
            # B20準拠: Path ServiceはDI注入されたものを使用
            # path_service = self._path_service
            manuscript_dir = self._path_service.get_manuscript_dir()

            if not manuscript_dir.exists():
                return None

            # パターン検索: 第{number:03d}話_*.md
            import glob

            pattern = f"第{episode_number:03d}話_*.md"
            search_path = str(manuscript_dir / pattern)

            matching_files = glob.glob(search_path)
            if matching_files:
                file_path = Path(matching_files[0])  # TODO: IPathServiceを使用するように修正
                title = self._parse_title_from_filename(file_path.stem)

                if title and len(title) >= 2:  # 意味のあるタイトル判定:
                    return EpisodeTitleResult(
                        title=title, source=EpisodeTitleSource.FILE_SYSTEM, confidence=0.95, is_default=False
                    )

            return None

        except Exception:
            return None

    def _parse_title_from_filename(self, filename: str) -> str | None:
        """ファイル名からタイトル解析

        Args:
            filename: ファイル名（拡張子なし）

        Returns:
            Optional[str]: 解析されたタイトル
        """
        if "_" in filename:
            parts = filename.split("_", 1)
            if len(parts) > 1:
                return parts[1]
        return None

    def _extract_from_repository_data(self, project_name: str, episode_number: int) -> EpisodeTitleResult | None:
        """リポジトリデータからタイトル取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            Optional[EpisodeTitleResult]: 取得結果
        """
        try:
            # リポジトリデータ取得（将来の拡張用プレースホルダー）
            # 現在は実装なしでNoneを返す
            return None

        except Exception:
            return None

    def _generate_default_title(self, episode_number: int) -> EpisodeTitleResult:
        """デフォルトタイトル生成

        Args:
            episode_number: エピソード番号

        Returns:
            EpisodeTitleResult: デフォルトタイトル結果
        """
        default_title = f"第{episode_number:03d}話"

        return EpisodeTitleResult(
            title=default_title, source=EpisodeTitleSource.DEFAULT_FALLBACK, confidence=0.5, is_default=True
        )
