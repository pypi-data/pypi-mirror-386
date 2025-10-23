"""
エピソードプロンプトリポジトリ実装

DDD準拠: Infrastructure層のリポジトリ実装
SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

from pathlib import Path

from noveler.domain.entities.episode_prompt import EpisodePrompt
from noveler.domain.repositories.episode_prompt_repository import EpisodePromptRepository as IEpisodePromptRepository
from noveler.domain.value_objects.prompt_save_result import PromptSaveResult
from noveler.infrastructure.adapters.yaml_handler_adapter import YAMLHandlerAdapter


class EpisodePromptRepository(IEpisodePromptRepository):
    """エピソードプロンプトリポジトリ

    責務:
    - エピソードプロンプトのファイルシステム永続化
    - YAML形式での保存・読み込み
    - ファイル操作エラーハンドリング
    - YAMLハンドラーアダプター統合
    """

    def __init__(self) -> None:
        """リポジトリ初期化"""
        # 共通基盤統合: YAMLハンドラーアダプター
        self._yaml_adapter = self._create_yaml_adapter()

    def save_prompt(self, episode_prompt: EpisodePrompt, file_path: Path) -> PromptSaveResult:
        """エピソードプロンプト保存

        Args:
            episode_prompt: 保存対象エンティティ
            file_path: 保存先ファイルパス

        Returns:
            PromptSaveResult: 保存結果
        """
        try:
            # 保存先パスはアプリケーション層で決定済み
            save_path = file_path

            # 1. ディレクトリ作成
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 2. YAML内容生成（エンティティのドメイン知識活用）
            yaml_content = episode_prompt.get_yaml_content()

            # 3. YAMLハンドラーアダプターによる保存
            self._yaml_adapter.save_yaml(yaml_content, str(save_path))

            file_size = save_path.stat().st_size if save_path.exists() else 0
            return PromptSaveResult.create_success(file_path=save_path, file_size_bytes=file_size)

        except OSError as e:
            return PromptSaveResult.create_failure(error_message=f"ファイルシステムエラー: {e!s}")

        except Exception as e:
            return PromptSaveResult.create_failure(error_message=f"予期しないエラー: {e!s}")

    def load_prompt(self, file_path: Path) -> EpisodePrompt | None:
        """エピソードプロンプト読み込み

        Args:
            file_path: 読み込み元パス

        Returns:
            EpisodePrompt: 読み込まれたエンティティ（失敗時None）
        """
        try:
            if not file_path.exists():
                return None

            # YAMLハンドラーアダプターによる読み込み
            load_result = self._yaml_adapter.load_yaml_file(file_path)

            if load_result.success and load_result.data:
                # ドメインエンティティへの復元
                return EpisodePrompt.from_yaml_data(load_result.data)

            return None

        except Exception:
            # ログ出力は省略（エラーオーケストレーターに委譲）
            return None

    def exists(self, file_path: Path) -> bool:
        """プロンプトファイル存在確認

        Args:
            file_path: 確認対象パス

        Returns:
            bool: 存在する場合True
        """
        return file_path.exists() and file_path.is_file()

    def delete_prompt(self, file_path: Path) -> bool:
        """プロンプトファイル削除

        Args:
            file_path: 削除するファイルパス

        Returns:
            bool: 削除成功時True
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    def list_prompts(self, directory_path: Path) -> list[Path]:
        """指定ディレクトリ内のプロンプト一覧取得

        Args:
            directory_path: 検索対象ディレクトリ

        Returns:
            list[Path]: プロンプトファイルパス一覧
        """
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                return []

            # 第000話_*.yaml パターンでフィルタリング
            prompt_files = []
            for file_path in directory_path.iterdir():
                if (
                    file_path.is_file()
                    and file_path.suffix == ".yaml"
                    and file_path.stem.startswith("第")
                    and "話_" in file_path.stem
                ):
                    prompt_files.append(file_path)

            # エピソード番号順にソート
            return sorted(prompt_files, key=self._extract_episode_number)

        except Exception:
            return []

    def _extract_episode_number(self, file_path: Path) -> int:
        """ファイル名からエピソード番号抽出

        Args:
            file_path: ファイルパス

        Returns:
            int: エピソード番号（抽出失敗時は999999）
        """
        try:
            # 第000話_タイトル.yaml から 000 部分を抽出
            stem = file_path.stem
            if stem.startswith("第") and "話_" in stem:
                number_part = stem[1 : stem.index("話_")]
                return int(number_part)
        except (ValueError, IndexError):
            pass

        return 999999  # ソート時に最後に配置

    def _create_yaml_adapter(self) -> "YAMLHandlerAdapter":
        """YAMLハンドラーアダプター作成

        Returns:
            YAMLHandlerAdapter: 共通基盤統合アダプター
        """
        from noveler.infrastructure.adapters.yaml_handler_adapter import YAMLHandlerAdapter

        return YAMLHandlerAdapter()
