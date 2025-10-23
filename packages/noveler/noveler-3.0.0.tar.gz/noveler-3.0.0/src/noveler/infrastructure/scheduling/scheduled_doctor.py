"""Infrastructure.scheduling.scheduled_doctor
Where: Infrastructure module implementing scheduled health checks.
What: Defines jobs that monitor system health and produce diagnostics.
Why: Ensures automated monitoring tasks run reliably over time.
"""

from noveler.presentation.shared.shared_utilities import console

"定期診断実行スクリプト\ncronジョブから呼び出されて、システムの健全性を定期的にチェック\n"
import argparse
import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

sys.path.insert(0, str(Path(__file__).parent))
from noveler.application.use_cases.system_doctor_use_case import SystemDoctorUseCase as SystemDoctor
from noveler.application.use_cases.system_repair_use_case import SystemRepairUseCase as SystemRepairer
from noveler.infrastructure.adapters.error_handler_adapter import handle_error, setup_logger
from noveler.infrastructure.adapters.hierarchical_config_adapter import HierarchicalConfig

logger = setup_logger(__name__, "scheduled_doctor.log")
JST = ProjectTimezone.jst().timezone


class ScheduledDoctor:
    """定期診断クラス"""

    def __init__(self, auto_repair: bool) -> None:
        self.auto_repair = auto_repair
        self.doctor = SystemDoctor()
        self.config = HierarchicalConfig()
        self.report_dir = Path.home() / ".novel" / "diagnostic_reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.email_config = self.config.get("notification.email", {})

    def run_scheduled_check(self) -> dict:
        """定期診断を実行"""
        self.logger_service.info("定期診断を開始します")
        diagnosis = self.doctor.run_all_checks()
        report_path = self._save_report(diagnosis)
        if diagnosis["summary"]["overall_status"] != "OK":
            self.logger_service.warning(
                f"問題を検出: エラー{diagnosis['summary']['total_errors']}件、警告{diagnosis['summary']['total_warnings']}件"
            )
            if self.auto_repair:
                self.logger_service.info("自動修復を開始します")
                repairer = SystemRepairer(dry_run=False)
                repair_result = repairer.diagnose_and_repair()
                self._save_repair_report(repair_result)
                self._send_notification(diagnosis, repair_result)
            else:
                self._send_notification(diagnosis)
        else:
            self.logger_service.info("システムは正常です")
        self._cleanup_old_reports(30)
        return {
            "diagnosis": diagnosis,
            "report_path": str(report_path),
            "timestamp": project_now().datetime.isoformat(),
        }

    def _save_report(self, diagnosis: dict) -> Path:
        """診断レポートを保存"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"diagnosis_{timestamp}.json"
        with Path(report_path).open("w", encoding="utf-8") as f:
            json.dump(diagnosis, f, ensure_ascii=False, indent=2)
        self.logger_service.info("診断レポートを保存: %s", report_path)
        return report_path

    def _save_repair_report(self, repair_result: dict) -> Path:
        """修復レポートを保存"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"repair_{timestamp}.json"
        with Path(report_path).open("w", encoding="utf-8") as f:
            json.dump(repair_result, f, ensure_ascii=False, indent=2, default=str)
        self.logger_service.info("修復レポートを保存: %s", report_path)
        return report_path

    def _cleanup_old_reports(self, keep_days: int = 30) -> None:
        """古いレポートを削除"""
        cutoff_date = project_now().datetime.timestamp() - keep_days * 24 * 60 * 60
        for report_file in self.report_dir.glob("*.json"):
            if report_file.stat().st_mtime < cutoff_date:
                report_file.unlink()
                self.logger_service.info("古いレポートを削除: %s", report_file)

    def _send_notification(self, diagnosis: dict, repair_result: dict | None = None) -> None:
        """問題が見つかった場合に通知を送信"""
        notifications = self.config.get("notifications", {})
        if not notifications.get("enabled", False):
            return
        subject = f"[小説執筆支援システム] 診断結果: {diagnosis['summary']['overall_status']}"
        body = self._create_notification_body(diagnosis, repair_result)
        if notifications.get("email", {}).get("enabled", False):
            self._send_email_notification(subject, body, notifications["email"])
        if notifications.get("webhook", {}).get("enabled", False):
            self._send_webhook_notification(subject, body, notifications["webhook"])

    def _create_notification_body(self, diagnosis: dict, repair_result: dict | None = None) -> str:
        """通知本文を作成"""
        summary = diagnosis["summary"]
        body = f"小説執筆支援システム定期診断結果\n\n実行日時: {diagnosis['timestamp']}\n総合評価: {summary['overall_status']}\n\n【サマリー】\n- エラー: {summary['total_errors']}件\n- 警告: {summary['total_warnings']}件\n- 情報: {summary['total_info']}件\n\n【詳細】\n"
        if diagnosis["errors"]:
            body += "\n■ エラー:\n"
            for error in diagnosis["errors"][:5]:
                body += f"  • {error}\n"
            if len(diagnosis["errors"]) > 5:
                body += f"  (他{len(diagnosis['errors']) - 5}件)\n"
        if diagnosis["warnings"]:
            body += "\n■ 警告:\n"
            for warning in diagnosis["warnings"][:5]:
                body += f"  • {warning}\n"
            if len(diagnosis["warnings"]) > 5:
                body += f"  (他{len(diagnosis['warnings']) - 5}件)\n"
        if repair_result:
            body += "\n【自動修復結果】\n"
            if repair_result["repairs_made"]:
                body += f"✅ 成功: {len(repair_result['repairs_made'])}件\n"
                for repair in repair_result["repairs_made"][:3]:
                    body += f"  • {repair['action']}\n"
            if repair_result["repairs_failed"]:
                body += f"❌ 失敗: {len(repair_result['repairs_failed'])}件\n"
                for repair in repair_result["repairs_failed"][:3]:
                    body += f"  • {repair['action']}\n"
        return body

    def _send_email_notification(self, subject: str, body: str, email_config: dict) -> None:
        """メール通知を送信"""
        try:
            to_address = email_config.get("address")
            if not to_address:
                self.logger_service.warning("メールアドレスが設定されていません")
                return
            smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
            smtp_port = email_config.get("smtp_port", 587)
            smtp_user = email_config.get("smtp_user")
            smtp_password = email_config.get("smtp_password")
            if not smtp_user or not smtp_password:
                self.logger_service.warning("SMTP認証情報が設定されていません")
                return
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_address
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            self.logger_service.info("メール通知を送信しました: %s", to_address)
        except Exception:
            logger.exception("メール送信エラー")

    def _send_webhook_notification(self, subject: str, body: str, webhook_config: dict) -> None:
        """Webhook通知を送信(Discord/Slack)"""
        try:
            webhook_url = webhook_config.get("url")
            if not webhook_url:
                self.logger_service.warning("Webhook URLが設定されていません")
                return
            if "discord.com" in webhook_url:
                payload = {"content": f"**{subject}**\n```\n{body[:1900]}\n```"}
            else:
                payload = {"text": f"*{subject}*\n```{body}```"}
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            self.logger_service.info("Webhook通知を送信しました")
        except Exception:
            logger.exception("Webhook送信エラー")


def main() -> None:
    parser = argparse.ArgumentParser(description="定期診断実行スクリプト")
    parser.add_argument("--auto-repair", action="store_true", help="問題を自動修復")
    parser.add_argument("--notify", action="store_true", help="通知を強制的に送信(テスト用)")
    parser.add_argument("--config", help="設定ファイルのパス")
    args = parser.parse_args()
    from noveler.infrastructure.di.container import resolve_service

    try:
        resolve_service("IConsoleService")
    except ValueError:
        from noveler.domain.value_objects.project_time import project_now
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

        ConsoleServiceAdapter()
    try:
        scheduled = ScheduledDoctor(auto_repair=args.auto_repair)
        if args.notify:
            test_diagnosis = {
                "timestamp": project_now().datetime.isoformat(),
                "summary": {"overall_status": "WARNING", "total_errors": 1, "total_warnings": 2, "total_info": 1},
                "errors": ["テストエラー: これはテスト通知です"],
                "warnings": ["テスト警告1", "テスト警告2"],
            }
            scheduled._send_notification(test_diagnosis)
            console.print("テスト通知を送信しました")
        else:
            result = scheduled.run_scheduled_check()
            console.print(f"定期診断完了: {result['success']}")
            console.print(f"レポート: {result.get('report_path', 'N/A')}")
            console.print(f"結果: {result.get('summary', 'N/A')}")
    except Exception as e:
        logger.exception("定期診断エラー")
        handle_error(e, "定期診断中にエラーが発生しました")


if __name__ == "__main__":
    main()
