#!/usr/bin/env python3
"""システム自動修復ユースケース

DDD準拠のシステム自動修復機能実装
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.application.use_cases.system_doctor_use_case import SystemDoctorRequest, SystemDoctorUseCase
from noveler.domain.repositories.project_repository import ProjectRepository
from noveler.domain.services.configuration_repair_service import ConfigurationRepairService
from noveler.domain.services.dependency_repair_service import DependencyRepairService
from noveler.domain.services.repair_report_service import RepairReportService
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class RepairAction:
    """修復アクション"""

    action_type: str  # "environment", "directory", "dependency", "configuration", "permission", "template"
    action: str
    path: str | None = None
    package: str | None = None
    error: str | None = None


@dataclass
class SystemRepairRequest:
    """システム修復リクエスト"""

    dry_run: bool = False
    output_file: str | None = None
    quiet: bool = False


@dataclass
class SystemRepairResponse:
    """システム修復レスポンス"""

    success: bool
    repairs_made: list[RepairAction] = None
    repairs_failed: list[RepairAction] = None
    diagnosis_result: dict[str, Any] = None
    summary_report: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.repairs_made is None:
            self.repairs_made = []
        if self.repairs_failed is None:
            self.repairs_failed = []

    @classmethod
    def success_response(
        cls, repairs_made: list, repairs_failed: list, diagnosis_result: dict, summary_report: str | None = None
    ) -> "SystemRepairResponse":
        """成功レスポンス作成"""
        return cls(
            success=True,
            repairs_made=repairs_made,
            repairs_failed=repairs_failed,
            diagnosis_result=diagnosis_result,
            summary_report=summary_report,
        )

    @classmethod
    def error_response(cls, error_message: str) -> "SystemRepairResponse":
        """エラーレスポンス作成"""
        return cls(success=False, error_message=error_message)


class SystemRepairUseCase:
    """システム自動修復ユースケース"""

    def __init__(self, project_repository: ProjectRepository | None = None) -> None:
        """初期化

        Args:
            project_repository: プロジェクトリポジトリ(オプション)
        """
        self.project_repository = project_repository
        self.guide_root = Path(__file__).parent.parent.parent

        # 修復サービスの初期化
        self._dependency_service = DependencyRepairService()
        self._config_service = ConfigurationRepairService()
        self._report_service = RepairReportService()

    def execute(self, request: SystemRepairRequest) -> SystemRepairResponse:
        """システム自動修復を実行

        Args:
            request: 修復リクエスト

        Returns:
            SystemRepairResponse: 修復結果
        """
        try:
            repairs_made = []
            repairs_failed = []

            if not request.quiet:
                # B20準拠: print文削除
                if hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print("[cyan]🔍 システム診断を実行中...[/cyan]\n")
                elif hasattr(self, "_logger_service") and self._logger_service:
                    self._logger_service.info("🔍 システム診断を実行中...")

            # まず診断を実行
            doctor_use_case = SystemDoctorUseCase(self.project_repository)
            doctor_request = SystemDoctorRequest(output_format="text", quiet=True)
            diagnosis_response = doctor_use_case.execute(doctor_request)

            if not diagnosis_response.success:
                return SystemRepairResponse.error_response(f"診断に失敗しました: {diagnosis_response.error_message}")

            diagnosis_result = {
                "overall_status": diagnosis_response.overall_status,
                "checks": diagnosis_response.checks,
                "errors": diagnosis_response.errors,
                "warnings": diagnosis_response.warnings,
                "info": diagnosis_response.info,
            }

            if diagnosis_response.overall_status == "OK":
                if not request.quiet:
                    # B20準拠: print文削除
                    if hasattr(self, "_get_console"):
                        console = self._get_console()
                        console.print("[green]✅ システムは正常です。修復の必要はありません。[/green]")
                    elif hasattr(self, "_logger_service") and self._logger_service:
                        self._logger_service.info("✅ システムは正常です。修復の必要はありません。")
                return SystemRepairResponse.success_response(
                    repairs_made=[],
                    repairs_failed=[],
                    diagnosis_result=diagnosis_result,
                )

            if not request.quiet:
                # B20準拠: print文削除
                if hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print("\n[yellow]🔧 問題が見つかりました。修復を開始します...[/yellow]")
                    if request.dry_run:
                        console.print("  [dim](ドライランモード:実際の修復は行われません)[/dim]")
                elif hasattr(self, "_logger_service") and self._logger_service:
                    self._logger_service.warning("🔧 問題が見つかりました。修復を開始します...")
                    if request.dry_run:
                        self._logger_service.info("(ドライランモード:実際の修復は行われません)")

            # 各チェック結果に基づいて修復(新サービス使用)
            # 依存関係修復
            deps_result = self._dependency_service.repair_dependencies(
                diagnosis_response.checks.get("dependencies", {}), request.dry_run, request.quiet
            )

            repairs_made.extend(deps_result["repairs_made"])
            repairs_failed.extend(deps_result["repairs_failed"])

            # 設定修復
            config_result = self._config_service.repair_configurations(
                diagnosis_response.checks.get("configurations", {}), request.dry_run, request.quiet
            )

            repairs_made.extend(config_result["repairs_made"])
            repairs_failed.extend(config_result["repairs_failed"])

            # 従来の手法で残りの修復を実行
            self._repair_environment(
                diagnosis_response.checks.get("environment", {}), request, repairs_made, repairs_failed
            )
            self._repair_project_structure(
                diagnosis_response.checks.get("project_structure", {}), request, repairs_made, repairs_failed
            )
            self._repair_permissions(
                diagnosis_response.checks.get("permissions", {}), request, repairs_made, repairs_failed
            )
            self._repair_templates(
                diagnosis_response.checks.get("templates", {}), request, repairs_made, repairs_failed
            )

            # サマリーレポートを生成(新サービス使用)
            summary_report = self._report_service.generate_summary_report(repairs_made, repairs_failed, request.dry_run)

            # ファイル出力処理
            if request.output_file:
                self._save_repair_results(request, repairs_made, repairs_failed, diagnosis_result)

            return SystemRepairResponse.success_response(
                repairs_made=repairs_made,
                repairs_failed=repairs_failed,
                diagnosis_result=diagnosis_result,
                summary_report=summary_report,
            )

        except Exception as e:
            return SystemRepairResponse.error_response(f"システム修復中にエラーが発生しました: {e}")

    def _repair_environment(
        self, env_check: dict, request: SystemRepairRequest, repairs_made: list, repairs_failed: list
    ) -> None:
        """環境変数の修復"""
        if env_check.get("status") != "OK":
            details: Any = env_check.get("details", {})
            env_vars = details.get("environment_variables", {})

            # 環境変数設定スクリプトの作成または更新
            if not env_vars.get("PROJECT_ROOT") or not env_vars.get("GUIDE_ROOT"):
                try:
                    self._create_env_setup_script(request)
                    repairs_made.append(
                        RepairAction(
                            action_type="environment",
                            action="環境変数設定スクリプトを作成",
                            path=str(self.guide_root / "setup_env_auto.sh"),
                        )
                    )
                    if not request.quiet:
                        # B20準拠: print文削除
                        if hasattr(self, "_logger_service") and self._logger_service:
                            self._logger_service.info("  ✅ 環境変数設定スクリプトを作成しました")
                except Exception as e:
                    repairs_failed.append(
                        RepairAction(
                            action_type="environment",
                            action="環境変数設定スクリプトの作成",
                            error=str(e),
                        )
                    )

    def _repair_project_structure(
        self, structure_check: dict, request: SystemRepairRequest, repairs_made: list, repairs_failed: list
    ) -> None:
        """プロジェクト構造の修復"""
        if structure_check.get("status") != "OK":
            details: Any = structure_check.get("details", {})
            missing_dirs = details.get("missing_directories", [])

            if missing_dirs and details.get("project_root"):
                project_root = Path(details["project_root"])
                if not request.quiet:
                    # B20準拠: print文削除
                    if hasattr(self, "_logger_service") and self._logger_service:
                        self._logger_service.info("📁 不足しているディレクトリを作成...")

                for dir_name in missing_dirs:
                    dir_path = project_root / dir_name
                    try:
                        if not request.dry_run:
                            dir_path.mkdir(parents=True, exist_ok=True)

                        repairs_made.append(
                            RepairAction(
                                action_type="directory",
                                action=f"ディレクトリを作成: {dir_name}",
                                path=str(dir_path),
                            )
                        )

                        if not request.quiet:
                            # B20準拠: print文削除
                            if hasattr(self, "_logger_service") and self._logger_service:
                                self._logger_service.info(f"  ✅ 作成: {dir_name}")
                    except Exception as e:
                        repairs_failed.append(
                            RepairAction(
                                action_type="directory",
                                action=f"ディレクトリの作成: {dir_name}",
                                path=str(dir_path),
                                error=str(e),
                            )
                        )

    def _repair_permissions(
        self, perms_check: dict, request: SystemRepairRequest, repairs_made: list, repairs_failed: list
    ) -> None:
        """ファイル権限の修復"""
        if perms_check.get("status") != "OK":
            details: Any = perms_check.get("details", {})

            if not request.quiet:
                # B20準拠: print文削除
                if hasattr(self, "_logger_service") and self._logger_service:
                    self._logger_service.info("🔐 ファイル権限を修正...")

            for file_path, status in details.items():
                if status == "Not executable":
                    full_path = self.guide_root / file_path
                    if full_path.exists():
                        try:
                            if not request.dry_run:
                                Path(full_path).chmod(0o755)

                            repairs_made.append(
                                RepairAction(
                                    action_type="permission",
                                    action=f"実行権限を付与: {file_path}",
                                    path=str(full_path),
                                )
                            )

                            if not request.quiet:
                                # B20準拠: print文削除
                                if hasattr(self, "_logger_service") and self._logger_service:
                                    self._logger_service.info(f"  ✅ 実行権限を付与: {file_path}")
                        except Exception as e:
                            repairs_failed.append(
                                RepairAction(
                                    action_type="permission",
                                    action=f"実行権限の付与: {file_path}",
                                    path=str(full_path),
                                    error=str(e),
                                )
                            )

    def _repair_templates(
        self, templates_check: dict, request: SystemRepairRequest, repairs_made: list, repairs_failed: list
    ) -> None:
        """テンプレートファイルの修復"""
        if templates_check.get("status") != "OK":
            details: Any = templates_check.get("details", {})
            templates_dir = self.guide_root / "templates"

            if not request.quiet:
                # B20準拠: print文削除
                if hasattr(self, "_logger_service") and self._logger_service:
                    self._logger_service.info("📄 テンプレートファイルを修復...")

            for template, status in details.items():
                if status == "Not found":
                    template_path = templates_dir / template
                    try:
                        if template.endswith(".yaml"):
                            self._create_basic_template(template_path, template, request)
                            repairs_made.append(
                                RepairAction(
                                    action_type="template",
                                    action=f"テンプレートを作成: {template}",
                                    path=str(template_path),
                                )
                            )
                            if not request.quiet:
                                # B20準拠: print文削除
                                if hasattr(self, "_logger_service") and self._logger_service:
                                    self._logger_service.info(f"  ✅ テンプレートを作成: {template}")
                    except Exception as e:
                        repairs_failed.append(
                            RepairAction(
                                action_type="template",
                                action=f"テンプレートの作成: {template}",
                                path=str(template_path),
                                error=str(e),
                            )
                        )

    def _create_env_setup_script(self, request: SystemRepairRequest) -> None:
        """環境変数設定スクリプトを作成"""
        setup_script = self.guide_root / "setup_env_auto.sh"

        content = f"""#!/bin/bash
# 自動生成された環境変数設定スクリプト
# 生成日時: {project_now().datetime.strftime("%Y-%m-%d %H:%M:%S")}

# ガイドルートの設定
export GUIDE_ROOT="{self.guide_root}"

# プロジェクトルートの自動検出
CURRENT_DIR="$(pwd)"
while [ "$CURRENT_DIR" != "/" ]; do
    if [ -f "$CURRENT_DIR/プロジェクト設定.yaml" ]; then:
        export PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

if [ -z "$PROJECT_ROOT" ]; then:
    echo "⚠️  プロジェクトが見つかりません。プロジェクトディレクトリで実行してください。"
else
    echo "✅ 環境変数を設定しました:"
    echo "  PROJECT_ROOT: $PROJECT_ROOT"
    echo "  GUIDE_ROOT: $GUIDE_ROOT"
fi
"""

        if not request.dry_run:
            with setup_script.Path("w").open(encoding="utf-8") as f:
                f.write(content)
            setup_script.chmod(0o755)

    def _create_default_global_config(self, config_path: Path) -> None:
        """デフォルトのグローバル設定を作成"""
        content = f"""# グローバル設定ファイル
# 作成日時: {project_now().datetime.strftime("%Y-%m-%d %H:%M:%S")}

default_author:
  pen_name: "あなたのペンネーム"
  email: ""

default_project:
  genre: "ファンタジー"
  min_length_per_episode: 4000

writing_environment:
  preferred_editor: "code"
  auto_save:
    enabled: true
    interval_minutes: 10

quality_management:
  default_threshold: 80
  auto_check:
    on_complete: true
"""

        with config_path.Path("w").open(encoding="utf-8") as f:
            f.write(content)

    def _create_basic_template(self, template_path: Path, template_name: str, request: SystemRepairRequest) -> None:
        """基本的なテンプレートを作成"""
        content = f"""# {template_name}
# 自動生成日時: {project_now().datetime.strftime("%Y-%m-%d %H:%M:%S")}

# このファイルは自動修復により作成されました
# 必要に応じて内容を更新してください

metadata:
  template_name: "{template_name}"
  created_at: "{project_now().datetime.isoformat()}"
  auto_generated: true
"""

        if not request.dry_run:
            template_path.parent.mkdir(parents=True, exist_ok=True)
            with template_path.Path("w").open(encoding="utf-8") as f:
                f.write(content)

    def _save_repair_results(
        self, request: SystemRepairRequest, repairs_made: list, repairs_failed: list, diagnosis_result: dict
    ) -> None:
        """修復結果をファイルに保存"""
        output_path = Path(request.output_file)

        result = {
            "timestamp": project_now().datetime.isoformat(),
            "dry_run": request.dry_run,
            "diagnosis": diagnosis_result,
            "repairs_made": [
                {
                    "type": r.action_type,
                    "action": r.action,
                    "path": r.path,
                    "package": r.package,
                }
                for r in repairs_made
            ],
            "repairs_failed": [
                {
                    "type": r.action_type,
                    "action": r.action,
                    "path": r.path,
                    "package": r.package,
                    "error": r.error,
                }
                for r in repairs_failed
            ],
        }

        with output_path.Path("w").open(encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # B20準拠: print文削除、ロガー使用
        logger = get_logger(__name__)
        logger.info(f"結果を保存しました: {output_path}")
