"""
Git hook管理ユースケース

TDD GREEN フェーズ: テストを通すための最小限の実装
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase


class HookType(Enum):
    """Git hookタイプ"""

    PRE_COMMIT = "pre-commit"
    POST_COMMIT = "post-commit"
    PRE_PUSH = "pre-push"


class HookStatus(Enum):
    """Git hook状態"""

    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


@dataclass
class HookInfo:
    """Git hook情報"""

    hook_type: HookType
    status: HookStatus
    path: Path | None = None
    is_executable: bool = False


@dataclass
class GitHookInstallRequest:
    """Git hookインストールリクエスト"""

    git_root: str
    guide_root: str
    hook_type: HookType
    force: bool = False


@dataclass
class GitHookInstallResponse:
    """Git hookインストールレスポンス"""

    success: bool
    hook_type: HookType
    message: str = ""
    forced: bool = False


@dataclass
class GitHookStatusRequest:
    """Git hook状態確認リクエスト"""

    git_root: str


@dataclass
class GitHookStatusResponse:
    """Git hook状態確認レスポンス"""

    success: bool
    is_git_repository: bool
    hooks: list[HookInfo] = field(default_factory=list)
    message: str = ""


@dataclass
class GitHookTestRequest:
    """Git hookテストリクエスト"""

    git_root: str
    guide_root: str
    hook_type: HookType
    dry_run: bool = False


@dataclass
class GitHookTestResponse:
    """Git hookテストレスポンス"""

    success: bool
    hook_type: HookType
    test_output: str = ""
    error_message: str | None = None


class GitHookManagementUseCase(AbstractUseCase[dict, dict]):
    """Git hook管理ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        git_hook_repository = None,
        **kwargs) -> None:
        """初期化

        Args:
            git_hook_repository: Git Hookリポジトリ
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        self.git_hook_repository = git_hook_repository or self.repository_factory.create_git_hook_repository()

    async def execute(self, request: dict) -> dict:
        """ユースケースを実行"""
        action = request.get("action")
        if action == "install":
            return self.install_hook(request)
        if action == "uninstall":
            return self.uninstall_hook(request)
        if action == "list":
            return self.list_hooks(request)
        return {"success": False, "error": f"Unknown action: {action}"}

    def install_hook(self, request: GitHookInstallRequest) -> GitHookInstallResponse:
        """Git hookをインストール"""
        try:
            # Gitリポジトリかどうかチェック
            if not self.git_hook_repository.is_git_repository(request.git_root):
                return GitHookInstallResponse(
                    success=False,
                    hook_type=request.hook_type,
                    message="指定されたディレクトリはGitリポジトリではありません",
                )

            # インストール実行
            success, message = self.git_hook_repository.install_hook(
                request.git_root, request.hook_type, force=request.force
            )

            return GitHookInstallResponse(
                success=success,
                hook_type=request.hook_type,
                message=message,
                forced=request.force if success else False,
            )

        except Exception as e:
            return GitHookInstallResponse(
                success=False, hook_type=request.hook_type, message=f"インストールエラー: {e}"
            )

    def check_status(self, request: GitHookStatusRequest) -> GitHookStatusResponse:
        """Git hookの状態を確認"""
        try:
            # Gitリポジトリかどうかチェック
            is_git_repo = self.git_hook_repository.is_git_repository(request.git_root)

            if not is_git_repo:
                return GitHookStatusResponse(
                    success=False,
                    is_git_repository=False,
                    message="指定されたディレクトリはGitリポジトリではありません",
                )

            # 各hookの状態を確認
            hooks = self.git_hook_repository.get_all_hooks_info(request.git_root)

            return GitHookStatusResponse(
                success=True, is_git_repository=True, hooks=hooks, message="Git hookの状態を確認しました"
            )

        except Exception as e:
            return GitHookStatusResponse(success=False, is_git_repository=False, message=f"状態確認エラー: {e}")

    def test_hook(self, request: GitHookTestRequest) -> GitHookTestResponse:
        """Git hookのテストを実行"""
        try:
            # Gitリポジトリかどうかチェック
            if not self.git_hook_repository.is_git_repository(request.git_root):
                return GitHookTestResponse(
                    success=False,
                    hook_type=request.hook_type,
                    error_message="指定されたディレクトリはGitリポジトリではありません",
                )

            # テスト実行
            success, stdout, stderr = self.git_hook_repository.test_hook(
                request.git_root, request.hook_type, dry_run=request.dry_run
            )

            if success:
                return GitHookTestResponse(success=True, hook_type=request.hook_type, test_output=stdout)
            return GitHookTestResponse(
                success=False, hook_type=request.hook_type, test_output=stdout, error_message=stderr
            )

        except Exception as e:
            return GitHookTestResponse(
                success=False, hook_type=request.hook_type, error_message=f"テスト実行エラー: {e}"
            )
