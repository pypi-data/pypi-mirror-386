#!/usr/bin/env python3
"""システム診断ユースケース

DDD準拠のシステム診断機能実装
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.services.environment_diagnostic_service import EnvironmentDiagnosticService
from noveler.domain.services.project_structure_diagnostic_service import ProjectStructureDiagnosticService
from noveler.domain.services.system_diagnostic_services import (
    ConfigurationDiagnosticService,
    DependencyDiagnosticService,
    DiagnosticReportService,
    GitDiagnosticService,
    PermissionDiagnosticService,
    ScriptDiagnosticService,
    TemplateDiagnosticService,
)
from noveler.domain.value_objects.project_time import project_now


@dataclass
class SystemDoctorRequest:
    """システム診断リクエスト"""

    output_format: str = "text"  # "text", "json", "yaml"
    output_file: str | None = None
    quiet: bool = False


@dataclass
class SystemDoctorResponse:
    """システム診断レスポンス"""

    success: bool
    overall_status: str  # "OK", "WARNING", "ERROR"
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    checks: dict[str, Any] = None
    errors: list[str] = None
    warnings: list[str] = None
    info: list[str] = None
    report_content: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.checks is None:
            self.checks = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info is None:
            self.info = []

    @classmethod
    def success_response(
        cls,
        overall_status: str,
        checks: dict,
        errors: list,
        warnings: list,
        info: list,
        report_content: str | None = None,
    ) -> "SystemDoctorResponse":
        """成功レスポンス作成"""
        return cls(
            success=True,
            overall_status=overall_status,
            total_errors=len(errors),
            total_warnings=len(warnings),
            total_info=len(info),
            checks=checks,
            errors=errors,
            warnings=warnings,
            info=info,
            report_content=report_content,
        )

    @classmethod
    def error_response(cls, error_message: str) -> "SystemDoctorResponse":
        """エラーレスポンス作成"""
        return cls(success=False, overall_status="ERROR", error_message=error_message)


class SystemDoctorUseCase(AbstractUseCase[SystemDoctorRequest, SystemDoctorResponse]):
    """システム診断ユースケース - B20準拠DI実装"""

    def __init__(
        self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        **kwargs: object,
    ) -> None:
        """初期化 - B20準拠

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        self.guide_root = Path(__file__).parent.parent.parent
        self.project_root = self._detect_current_project_root()

        # 診断サービスの初期化 - B20準拠: Unit of Work経由でリポジトリアクセス
        self._env_service = EnvironmentDiagnosticService()
        self._structure_service = ProjectStructureDiagnosticService(
            self._unit_of_work.project_repository, self.guide_root
        )

        # 新しい診断サービスの初期化
        self._dependency_service = DependencyDiagnosticService()
        self._config_service = ConfigurationDiagnosticService(self.guide_root, self.project_root)
        self._script_service = ScriptDiagnosticService(self.guide_root)
        self._template_service = TemplateDiagnosticService(self.guide_root)
        self._permission_service = PermissionDiagnosticService(self.guide_root)
        self._git_service = GitDiagnosticService(self.guide_root)
        self._report_service = DiagnosticReportService()

    async def execute(self, request: SystemDoctorRequest) -> SystemDoctorResponse:
        """システム診断を実行 - B20準拠Unit of Work適用

        Args:
            request: 診断リクエスト

        Returns:
            SystemDoctorResponse: 診断結果
        """
        self._logger_service.info(f"システム診断開始: 出力形式={request.output_format}")

        try:
            # B20準拠: Unit of Work トランザクション管理（読み取り専用）
            with self._unit_of_work.transaction():
                # 診断結果を格納する辞書
                results: dict[str, Any] = {
                    "timestamp": project_now().datetime.isoformat(),
                    "checks": {},
                    "errors": [],
                    "warnings": [],
                    "info": [],
                }

                if not request.quiet:
                    if hasattr(self, "_get_console"):
                        console = self._get_console()
                        console.print("[cyan]🔍 小説執筆支援システム診断を開始します...[/cyan]\n")
                    elif self._logger_service:
                        self._logger_service.info("🔍 小説執筆支援システム診断を開始します...")

                # 環境チェック(新サービス使用)
                env_result = self._env_service.check_environment(request.quiet)
                results["checks"]["environment"] = env_result["check_result"]
                results["errors"].extend(env_result["errors"])
                results["warnings"].extend(env_result["warnings"])
                self._process_log_entries(results, env_result.get("log_messages", []), request.quiet)

                # プロジェクト構造チェック(新サービス使用)
                structure_result = self._structure_service.check_project_structure(request.quiet)
                results["checks"]["structure"] = structure_result["check_result"]
                results["errors"].extend(structure_result["errors"])
                results["warnings"].extend(structure_result["warnings"])
                self._process_log_entries(results, structure_result.get("log_messages", []), request.quiet)

                # 新しいドメインサービスを使用してチェックを実行
                self._dependency_service.check_dependencies(results, request.quiet)
                self._config_service.check_configurations(results, request.quiet)
                self._script_service.check_scripts(results, request.quiet)
                self._template_service.check_templates(results, request.quiet)
                self._permission_service.check_permissions(results, request.quiet)
                self._git_service.check_git_status(results, request.quiet)

                # 全体ステータスを決定
                overall_status = self._determine_overall_status(results)

                # レポート内容を生成(新しいサービス使用)
                report_content = None
                if request.output_format == "text" or not request.quiet:
                    report_content = self._report_service.generate_text_report(results, overall_status)

                # ファイル出力処理(新しいサービス使用)
                if request.output_file:
                    output_file = Path(request.output_file)
                    self._report_service.save_results_to_file(
                        output_file, results, overall_status, request.output_format
                    )

                return SystemDoctorResponse.success_response(
                    overall_status=overall_status,
                    checks=results["checks"],
                    errors=results["errors"],
                    warnings=results["warnings"],
                    info=results["info"],
                    report_content=report_content,
                )

        except Exception as e:
            self._logger_service.error(f"システム診断実行エラー: {e}")
            return SystemDoctorResponse.error_response(f"システム診断中にエラーが発生しました: {e}")

    def _check_package_availability(self, import_name: str) -> bool:
        """パッケージが利用可能かチェック"""
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def _determine_overall_status(self, results: dict) -> str:
        """全体のステータスを決定"""
        total_errors = len(results["errors"])
        total_warnings = len(results["warnings"])

        if total_errors > 0:
            return "ERROR"
        if total_warnings > 0:
            return "WARNING"
        return "OK"

    def _find_project_config(self, start_path: Path | None = None) -> Path | None:
        """プロジェクト設定.yamlを検索(フォールバック実装)"""
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()
        while current != current.parent:
            config_path = current / "プロジェクト設定.yaml"
            if config_path.exists():
                return config_path
            current = current.parent
        return None

    def _detect_current_project_root(self) -> Path | None:
        """現在のディレクトリからプロジェクトルートを検出"""
        current = Path.cwd()
        project_indicators = ["pyproject.toml", "setup.py", ".git", "CLAUDE.md"]

        while current != current.parent:
            if any((current / indicator).exists() for indicator in project_indicators):
                return current
            current = current.parent
        return None

    def _process_log_entries(
        self,
        results: dict[str, Any],
        log_entries: list[dict[str, str]],
        quiet: bool,
    ) -> None:
        """Merge domain log entries into aggregated results and forward them to outputs."""
        if not log_entries:
            return

        for entry in log_entries:
            message = entry.get("message")
            if not message:
                continue
            level = entry.get("level", "info")
            if level == "error":
                results["errors"].append(message)
            elif level == "warning":
                results["warnings"].append(message)
            else:
                results["info"].append(message)
            self._publish_log(level, message, quiet)

    def _publish_log(self, level: str, message: str, quiet: bool) -> None:
        """Forward diagnostic messages to the configured logger or shared console."""
        logger = self._logger_service
        if logger is not None:
            log_method = getattr(logger, level, None)
            if callable(log_method):
                log_method(message)
            elif hasattr(logger, "info"):
                logger.info(message)

        if quiet:
            return

        if hasattr(self, "_get_console"):
            console = self._get_console()
            color_map = {"warning": "[yellow]", "error": "[red]"}
            prefix = color_map.get(level, "[cyan]")
            console.print(f"{prefix}{message}[/]")
