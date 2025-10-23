"""CLIエピソード引数パーサー
仕様: specs/cli_episode_number_integration.spec.md
"""

from pathlib import Path

from noveler.domain.services.episode_number_resolver import EpisodeNumberResolver


def parse_episode_argument(arg: str, project_root: Path) -> Path:
    """話数またはファイル名を解析してファイルパスを返す

    Args:
        arg: コマンドライン引数(話数またはファイル名)
        project_root: プロジェクトのルートディレクトリ

    Returns:
        Path: 解決されたファイルパス

    Raises:
        EpisodeNotFoundError: 話数が見つからない場合
        ManagementFileNotFoundError: 話数管理.yamlが存在しない場合
        FileNotFoundError: ファイルが存在しない場合
    """
    try:
        # 数値として解析を試みる
        episode_number = int(arg)
        if episode_number <= 0:
            # 0以下は無効な話数なので文字列として扱う
            return Path(arg)

        # EpisodeNumberResolverで話数を解決
        resolver = EpisodeNumberResolver(project_root)
        info = resolver.resolve_episode_number(episode_number)

        # ファイルの存在確認
        if not info.exists:
            msg = f"話数{episode_number}のファイルが存在しません: {info.file_path}"
            raise FileNotFoundError(msg)

        return info.file_path

    except ValueError:
        # 数値でない場合はファイル名として処理
        return Path(arg)
