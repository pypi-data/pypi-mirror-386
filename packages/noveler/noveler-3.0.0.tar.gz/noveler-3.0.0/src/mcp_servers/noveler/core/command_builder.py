"""Command builder utilities used by the MCP integration layer.

The helpers in this module focus solely on preparing command line arguments
and environment state, leaving I/O and subprocess execution to higher layers.
"""

from pathlib import Path
from typing import Any


class CommandBuilder:
    """Build command line invocations for the ``noveler`` CLI.

    The class contains pure helpers so tests can exercise command composition
    without spawning subprocesses.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialise the builder.

        Args:
            base_dir (Path | None): Optional base directory used to resolve the
                CLI entry points. When omitted the project root inferred from
                the source tree is used.
        """
        self._base_dir = base_dir or Path(__file__).parent.parent.parent.parent

    def build_novel_command(
        self,
        command: str,
        options: dict[str, Any],
        project_root: str | None = None
    ) -> tuple[list[str], Path]:
        """Create a raw ``noveler`` command invocation.

        Args:
            command (str): CLI command such as ``"write 1"``.
            options (dict[str, Any]): Additional CLI options expressed as a
                dictionary.
            project_root (str | None): Optional project root used to compute
                the working directory.

        Returns:
            tuple[list[str], Path]: Command arguments suitable for
            ``subprocess`` together with the working directory.
        """
        # novelerコマンドパスの決定
        noveler_cmd = self._get_noveler_command_path()

        # コマンド配列を構築
        cmd_parts = [str(noveler_cmd), *command.split()]

        # オプションの追加
        for key, value in options.items():
            if isinstance(value, bool):
                if value:  # Trueの場合のみフラグを追加
                    cmd_parts.append(f"--{key}")
                # Falseの場合は何もしない
            elif value is not None:
                cmd_parts.extend([f"--{key}", str(value)])

        # 作業ディレクトリの決定
        working_dir = Path(project_root).absolute() if project_root else Path.cwd()

        return cmd_parts, working_dir

    def build_status_command(self, project_root: str | None = None) -> tuple[list[str], Path]:
        """Compose the ``status`` command.

        Args:
            project_root (str | None): Optional project root to override the
                working directory.

        Returns:
            tuple[list[str], Path]: Prepared command arguments and working
            directory.
        """
        noveler_cmd = self._get_noveler_command_path()
        cmd_parts = [str(noveler_cmd), "status"]
        working_dir = Path(project_root).absolute() if project_root else Path.cwd()

        return cmd_parts, working_dir

    def build_check_command(
        self,
        check_type: str,
        file_path: str | None = None,
        options: dict[str, Any] | None = None
    ) -> tuple[list[str], Path]:
        """Build a ``noveler check`` command.

        Args:
            check_type (str): Quality check variant such as ``"readability"``
                or ``"grammar"``.
            file_path (str | None): Optional target file passed to the CLI.
            options (dict[str, Any] | None): Additional CLI flags expressed as
                a dictionary.

        Returns:
            tuple[list[str], Path]: Command arguments and working directory.
        """
        noveler_cmd = self._get_noveler_command_path()
        cmd_parts = [str(noveler_cmd), "check", check_type]

        if file_path:
            cmd_parts.append(file_path)

        # オプションの追加
        options = options or {}
        for key, value in options.items():
            if isinstance(value, bool):
                if value:  # Trueの場合のみフラグを追加
                    cmd_parts.append(f"--{key}")
                # Falseの場合は何もしない
            elif value is not None:
                cmd_parts.extend([f"--{key}", str(value)])

        working_dir = Path.cwd()
        return cmd_parts, working_dir

    def _get_noveler_command_path(self) -> Path:
        """Resolve the path to the ``noveler`` executable.

        Returns:
            Path: Path to the production or development CLI entry point.
        """
        # dist版が存在するかチェック
        if (self._base_dir / "dist").exists():
            return self._base_dir / "bin" / "noveler"
        return self._base_dir / "bin" / "noveler-dev"

    def validate_command(self, command: str) -> bool:
        """Confirm that a command string matches the supported pattern.

        Args:
            command (str): Raw command string.

        Returns:
            bool: ``True`` when the command name is part of the allow list.
        """
        if not command.strip():
            return False

        # 基本的なコマンド形式のチェック
        parts = command.split()
        if not parts:
            return False

        # 許可されたコマンドパターンの検証
        valid_commands = {
            "write", "check", "status", "plot", "analyze", "backup"
        }

        return parts[0] in valid_commands

    def build_environment_vars(
        self,
        project_root: str | None = None
    ) -> dict[str, str]:
        """Assemble process environment overrides.

        Args:
            project_root (str | None): Optional project root used to populate
                ``PROJECTS_ROOT``/``PROJECT_ROOT``.

        Returns:
            dict[str, str]: Environment variable mapping.
        """
        env_vars = {}

        if project_root:
            working_dir = Path(project_root).absolute()
            env_vars["PROJECTS_ROOT"] = str(working_dir)
            env_vars["PROJECT_ROOT"] = str(working_dir)

        return env_vars
