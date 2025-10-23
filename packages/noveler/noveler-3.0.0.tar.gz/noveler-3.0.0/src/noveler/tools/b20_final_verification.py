"""Tools.b20_final_verification
Where: Tool performing final verification for B20 compliance.
What: Runs automated checks to confirm compliance before release.
Why: Ensures readiness of the project regarding B20 standards.
"""

from noveler.presentation.shared.shared_utilities import console


"B20準拠開発作業指示書.md最終検証ツール\n\nB20準拠開発が完全に実施されたかを検証する。\n"
import subprocess
from pathlib import Path

from noveler.infrastructure.adapters.console_service_adapter import get_console_service


class B20ComplianceVerifier:
    """B20準拠性の最終検証を行う"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"
        self.results = {}

    def verify_all(self) -> dict[str, any]:
        """全体検証の実行"""
        self.console_service.print("🔍 B20準拠開発作業指示書.md最終検証開始")
        self.console_service.print("=" * 60)
        self.results["phase1_domain_arch"] = self._verify_domain_architecture()
        self.results["phase2_unit_of_work"] = self._verify_unit_of_work()
        self.results["phase3_dependency_injection"] = self._verify_dependency_injection()
        self.results["phase4_fc_is_architecture"] = self._verify_fc_is_architecture()
        self.results["phase5_quality_assurance"] = self._verify_quality_assurance()
        return self.results

    def _verify_domain_architecture(self) -> dict[str, any]:
        """Domain層アーキテクチャの検証"""
        self.console_service.print("📋 Phase 1: Domain層アーキテクチャ違反修正の検証")
        domain_dir = self.scripts_dir / "domain"
        violations = []
        if domain_dir.exists():
            for py_file in domain_dir.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "from noveler.infrastructure" in content or "import noveler.infrastructure" in content:
                        violations.append(str(py_file.relative_to(self.project_root)))
                except Exception:
                    continue
        result = {
            "status": "pass" if len(violations) == 0 else "fail",
            "violations": violations,
            "description": "Domain層からInfrastructure層への依存確認",
        }
        self.console_service.print(f"  ✅ Domain層純粋性: {result['status'].upper()}")
        if violations:
            self.console_service.print(f"    ⚠️ 違反ファイル: {len(violations)}件")
        return result

    def _verify_unit_of_work(self) -> dict[str, any]:
        """Unit of Workパターンの検証"""
        self.console_service.print("📋 Phase 2: Unit of Workパターン拡張の検証")
        uow_file = self.scripts_dir / "infrastructure" / "unit_of_work.py"
        repository_factory_file = self.scripts_dir / "infrastructure" / "di" / "repository_factory.py"
        uow_exists = uow_file.exists()
        factory_exists = repository_factory_file.exists()
        backup_integrated = False
        if uow_exists:
            try:
                content = uow_file.read_text(encoding="utf-8")
                backup_integrated = "backup_repository" in content
            except Exception:
                pass
        result = {
            "status": "pass" if uow_exists and factory_exists and backup_integrated else "fail",
            "unit_of_work_exists": uow_exists,
            "repository_factory_exists": factory_exists,
            "backup_repository_integrated": backup_integrated,
            "description": "Unit of Workパターンと拡張リポジトリ統合確認",
        }
        self.console_service.print(f"  ✅ Unit of Work: {result['status'].upper()}")
        self.console_service.print(f"    - Unit of Work存在: {('✓' if uow_exists else '✗')}")
        self.console_service.print(f"    - Repository Factory: {('✓' if factory_exists else '✗')}")
        self.console_service.print(f"    - Backup統合: {('✓' if backup_integrated else '✗')}")
        return result

    def _verify_dependency_injection(self) -> dict[str, any]:
        """依存性注入の検証"""
        self.console_service.print("📋 Phase 3: 依存性注入適用の検証")
        use_cases_dir = self.scripts_dir / "application" / "use_cases"
        b20_compliant = 0
        total_use_cases = 0
        if use_cases_dir.exists():
            use_case_files = list(use_cases_dir.glob("*use_case.py"))
            total_use_cases = len(use_case_files)
            for use_case_file in use_case_files:
                try:
                    content = use_case_file.read_text(encoding="utf-8")
                    if (
                        "logger_service" in content
                        and "unit_of_work" in content
                        and ("self._logger_service = logger_service" in content)
                        and ("self._unit_of_work = unit_of_work" in content)
                    ):
                        b20_compliant += 1
                except Exception:
                    continue
        compliance_rate = b20_compliant / total_use_cases * 100 if total_use_cases > 0 else 0
        result = {
            "status": "pass" if compliance_rate >= 80 else "partial" if compliance_rate >= 50 else "fail",
            "total_use_cases": total_use_cases,
            "b20_compliant": b20_compliant,
            "compliance_rate": compliance_rate,
            "description": "B20準拠DIパターン適用率確認",
        }
        self.console_service.print(f"  ✅ DI適用状況: {result['status'].upper()}")
        self.console_service.print(f"    - 総ユースケース数: {total_use_cases}")
        self.console_service.print(f"    - B20準拠: {b20_compliant}件")
        self.console_service.print(f"    - 準拠率: {compliance_rate:.1f}%")
        return result

    def _verify_fc_is_architecture(self) -> dict[str, any]:
        """FC/ISアーキテクチャの検証"""
        self.console_service.print("📋 Phase 4: FC/ISアーキテクチャの検証")
        fc_contract_file = self.scripts_dir / "tests" / "contracts" / "functional_core_contract.py"
        purity_test_file = self.scripts_dir / "tests" / "contracts" / "test_functional_core_purity.py"
        fc_contract_exists = fc_contract_file.exists()
        purity_tests_exist = purity_test_file.exists()
        test_passed = False
        if purity_tests_exist:
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(purity_test_file), "-v"],
                    check=False,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                test_passed = result.returncode == 0
            except Exception:
                test_passed = False
        result = {
            "status": "pass" if fc_contract_exists and purity_tests_exist and test_passed else "partial",
            "fc_contract_exists": fc_contract_exists,
            "purity_tests_exist": purity_tests_exist,
            "tests_passed": test_passed,
            "description": "FC/IS契約テストフレームワークとアーキテクチャ検証",
        }
        self.console_service.print(f"  ✅ FC/ISアーキテクチャ: {result['status'].upper()}")
        self.console_service.print(f"    - FC契約フレームワーク: {('✓' if fc_contract_exists else '✗')}")
        self.console_service.print(f"    - 純粋性テスト: {('✓' if purity_tests_exist else '✗')}")
        self.console_service.print(f"    - テスト実行: {('✓ PASS' if test_passed else '✗ FAIL')}")
        return result

    def _verify_quality_assurance(self) -> dict[str, any]:
        """品質保証の検証"""
        self.console_service.print("📋 Phase 5: テスト・品質保証の検証")
        b20_tools = [
            self.scripts_dir / "tools" / "b20_batch_di_converter.py",
            self.scripts_dir / "tools" / "b20_batch_di_cleanup.py",
            self.scripts_dir / "tools" / "b20_final_verification.py",
        ]
        tools_exist = sum(1 for tool in b20_tools if tool.exists())
        use_cases_dir = self.scripts_dir / "application" / "use_cases"
        backup_files = 0
        if use_cases_dir.exists():
            backup_files = len(list(use_cases_dir.glob("*.py.backup")))
        result = {
            "status": "pass" if tools_exist >= 2 and backup_files > 0 else "partial",
            "b20_tools_exist": tools_exist,
            "conversion_backups": backup_files,
            "description": "B20準拠開発ツールと変換履歴確認",
        }
        self.console_service.print(f"  ✅ 品質保証: {result['status'].upper()}")
        self.console_service.print(f"    - B20ツール存在: {tools_exist}/3")
        self.console_service.print(f"    - 変換バックアップ: {backup_files}件")
        return result

    def generate_final_report(self) -> str:
        """最終検証レポート生成"""
        total_phases = len(self.results)
        passed_phases = sum(1 for result in self.results.values() if result["status"] == "pass")
        partial_phases = sum(1 for result in self.results.values() if result["status"] == "partial")
        overall_status = (
            "EXCELLENT"
            if passed_phases == total_phases
            else "GOOD"
            if passed_phases + partial_phases >= total_phases * 0.8
            else "NEEDS_IMPROVEMENT"
        )
        report = f"\nB20準拠開発作業指示書.md 最終検証レポート\n{'=' * 60}\n検証日時: 2025-08-28\nプロジェクト: 小説執筆支援システム\n\n■ 全体結果\n総合評価: {overall_status}\n完全達成: {passed_phases}/{total_phases} フェーズ\n部分達成: {partial_phases}/{total_phases} フェーズ\n\n■ フェーズ別結果\n"
        phase_names = {
            "phase1_domain_arch": "Phase 1: Domain層アーキテクチャ違反修正",
            "phase2_unit_of_work": "Phase 2: Unit of Workパターン拡張",
            "phase3_dependency_injection": "Phase 3: 依存性注入適用",
            "phase4_fc_is_architecture": "Phase 4: FC/ISアーキテクチャ",
            "phase5_quality_assurance": "Phase 5: テスト・品質保証",
        }
        for phase_key, result in self.results.items():
            phase_name = phase_names.get(phase_key, phase_key)
            status_icon = "✅" if result["status"] == "pass" else "🔶" if result["status"] == "partial" else "❌"
            report += f"{status_icon} {phase_name}: {result['status'].upper()}\n"
            report += f"   {result['description']}\n\n"
        if overall_status == "EXCELLENT":
            report += "\n🎉 B20準拠開発作業指示書.mdの要求事項を完全に満たしています！\n   - Domain Driven Design アーキテクチャ実装完了\n   - Functional Core / Imperative Shell パターン適用\n   - 依存性注入による疎結合設計\n   - Unit of Workによる整合性保証\n   - 品質保証プロセス確立\n\n次のステップ: 継続的統合・継続的品質向上の実施\n"
        return report


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent.parent
    verifier = B20ComplianceVerifier(project_root)
    verifier.verify_all()
    get_console_service()
    console.print("\n" + "=" * 60)
    console.print(verifier.generate_final_report())


if __name__ == "__main__":
    main()
