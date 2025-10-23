#!/usr/bin/env python3
"""テストレポート生成ツール

TDD+DDD準拠のテスト結果を分析し、詳細なレポートを生成する
"""

import json
import subprocess
import sys
from pathlib import Path

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestReportGenerator:
    """テストレポート生成器"""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = project_root
        self.report_dir = project_root / "logs" / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_comprehensive_report(self) -> dict[str, object]:
        """包括的なテストレポートを生成"""

        report = {
            "timestamp": project_now().datetime.isoformat(),
            "project_root": str(self.project_root),
            "test_results": {},
            "coverage_report": {},
            "quality_metrics": {},
            "performance_metrics": {},
            "compliance_check": {},
            "summary": {},
        }

        # テスト結果の収集
        report["test_results"] = self._collect_test_results()

        # カバレッジレポートの生成
        report["coverage_report"] = self._generate_coverage_report()

        # 品質メトリクスの収集
        report["quality_metrics"] = self._collect_quality_metrics()

        # パフォーマンスメトリクスの収集
        report["performance_metrics"] = self._collect_performance_metrics()

        # TDD+DDD準拠チェック
        report["compliance_check"] = self._check_tdd_ddd_compliance()

        # サマリーの生成
        report["summary"] = self._generate_summary(report)

        # レポートファイルの保存
        self._save_report(report)

        return report

    def _collect_test_results(self) -> dict[str, object]:
        """テスト結果の収集"""
        test_results = {
            "unit_tests": {},
            "integration_tests": {},
            "e2e_tests": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "errors": [],
        }

        try:
            # ユニットテストの実行
            unit_result = self._run_tests("tests/unit", "unit")
            test_results["unit_tests"] = unit_result

            # 統合テストの実行
            integration_result = self._run_tests("tests/integration", "integration")
            test_results["integration_tests"] = integration_result

            # E2Eテストの実行
            e2e_result = self._run_tests("tests/e2e", "e2e")
            test_results["e2e_tests"] = e2e_result

            # 統計の計算
            for test_type in ["unit_tests", "integration_tests", "e2e_tests"]:
                result = test_results[test_type]
                if result:
                    test_results["total_tests"] += result.get("total", 0)
                    test_results["passed_tests"] += result.get("passed", 0)
                    test_results["failed_tests"] += result.get("failed", 0)
                    test_results["skipped_tests"] += result.get("skipped", 0)

        except Exception as e:
            test_results["errors"].append(f"テスト結果収集エラー: {e}")

        return test_results

    def _run_tests(self, test_path: str, test_type: str) -> dict[str, object]:
        """指定されたテストを実行"""
        result = {
            "test_type": test_type,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "execution_time": 0,
            "details": [],
        }

        try:
            # pytest実行
            cmd = [
                "python",
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file=logs/{test_type}_report.json",
            ]

            start_time = project_now().datetime
            process = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            end_time = project_now().datetime

            result["execution_time"] = (end_time - start_time).total_seconds()
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr

            # JSONレポートの解析
            json_report_path = self.project_root / "logs" / f"{test_type}_report.json"
            if json_report_path.exists():
                with Path(json_report_path).open(encoding="utf-8") as f:
                    json_report = json.load(f)
                    summary = json_report.get("summary", {})
                    result["total"] = summary.get("total", 0)
                    result["passed"] = summary.get("passed", 0)
                    result["failed"] = summary.get("failed", 0)
                    result["skipped"] = summary.get("skipped", 0)
                    result["details"] = json_report.get("tests", [])

        except subprocess.TimeoutExpired:
            result["error"] = "テスト実行がタイムアウトしました"
        except Exception as e:
            result["error"] = f"テスト実行エラー: {e!s}"

        return result

    def _generate_coverage_report(self) -> dict[str, object]:
        """カバレッジレポートの生成"""
        coverage_report = {
            "overall_coverage": 0,
            "domain_coverage": 0,
            "application_coverage": 0,
            "infrastructure_coverage": 0,
            "quality_coverage": 0,
            "files": [],
            "missing_lines": {},
            "branch_coverage": 0,
        }

        try:
            # カバレッジ測定の実行
            cmd = [
                "python",
                "-m",
                "pytest",
                "tests/unit",
                "--cov=domain",
                "--cov=application",
                "--cov=infrastructure",
                "--cov=quality",
                "--cov=utils",
                "--cov-report=json:logs/coverage.json",
                "--cov-report=xml:logs/coverage.xml",
                "--cov-report=html:logs/htmlcov",
                "--cov-report=term-missing",
                "--tb=no",
                "-q",
            ]

            subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            # JSONカバレッジレポートの解析
            coverage_json_path = self.project_root / "logs" / "coverage.json"
            if coverage_json_path.exists():
                with Path(coverage_json_path).open(encoding="utf-8") as f:
                    coverage_data = json.load(f)

                    # 全体カバレッジ
                    totals = coverage_data.get("totals", {})
                    coverage_report["overall_coverage"] = totals.get("percent_covered", 0)

                    # ファイル別カバレッジ
                    files = coverage_data.get("files", {})
                    for file_path, file_data in files.items():
                        file_info = {
                            "file": file_path,
                            "coverage": file_data.get("summary", {}).get("percent_covered", 0),
                            "lines_covered": file_data.get("summary", {}).get("covered_lines", 0),
                            "lines_total": file_data.get("summary", {}).get("num_statements", 0),
                            "missing_lines": file_data.get("missing_lines", []),
                        }
                        coverage_report["files"].append(file_info)

                        # 層別カバレッジの計算
                        if "domain/" in file_path:
                            coverage_report["domain_coverage"] = max(
                                coverage_report["domain_coverage"],
                                file_info["coverage"],
                            )

                        elif "application/" in file_path:
                            coverage_report["application_coverage"] = max(
                                coverage_report["application_coverage"],
                                file_info["coverage"],
                            )

                        elif "infrastructure/" in file_path:
                            coverage_report["infrastructure_coverage"] = max(
                                coverage_report["infrastructure_coverage"],
                                file_info["coverage"],
                            )

                        elif "quality/" in file_path:
                            coverage_report["quality_coverage"] = max(
                                coverage_report["quality_coverage"],
                                file_info["coverage"],
                            )

        except Exception as e:
            coverage_report["error"] = f"カバレッジレポート生成エラー: {e!s}"

        return coverage_report

    def _collect_quality_metrics(self) -> dict[str, object]:
        """品質メトリクスの収集"""
        quality_metrics = {
            "code_quality": {},
            "type_checking": {},
            "security": {},
            "documentation": {},
            "complexity": {},
        }

        try:
            # flake8による品質チェック
            quality_metrics["code_quality"] = self._run_flake8()

            # mypyによる型チェック
            quality_metrics["type_checking"] = self._run_mypy()

            # banditによるセキュリティチェック
            quality_metrics["security"] = self._run_bandit()

            # pydocstyleによるドキュメンテーションチェック
            quality_metrics["documentation"] = self._run_pydocstyle()

        except Exception as e:
            quality_metrics["error"] = f"品質メトリクス収集エラー: {e!s}"

        return quality_metrics

    def _run_flake8(self) -> dict[str, object]:
        """flake8による品質チェック"""
        try:
            cmd = ["python", "-m", "flake8", "domain", "application", "infrastructure", "quality", "--format=json"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)

            violations = []
            if result.stdout:
                try:
                    violations = json.loads(result.stdout)
                except json.JSONDecodeError:
                    violations = []

            return {
                "violations": violations,
                "total_violations": len(violations),
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)}

    def _run_mypy(self) -> dict[str, object]:
        """mypyによる型チェック"""
        try:
            cmd = ["python", "-m", "mypy", "domain", "application", "--ignore-missing-imports"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)

            errors = []
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                errors.extend(line.strip() for line in lines if "error:" in line)

            return {
                "errors": errors,
                "total_errors": len(errors),
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)}

    def _run_bandit(self) -> dict[str, object]:
        """banditによるセキュリティチェック"""
        try:
            cmd = ["python", "-m", "bandit", "-r", "domain", "application", "infrastructure", "quality", "-f", "json"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)

            security_issues = []
            if result.stdout:
                try:
                    bandit_report = json.loads(result.stdout)
                    security_issues = bandit_report.get("results", [])
                except json.JSONDecodeError:
                    security_issues = []

            return {
                "security_issues": security_issues,
                "total_issues": len(security_issues),
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)}

    def _run_pydocstyle(self) -> dict[str, object]:
        """pydocstyleによるドキュメンテーションチェック"""
        try:
            cmd = ["python", "-m", "pydocstyle", "domain", "application", "--convention=google"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)

            doc_issues = []
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                doc_issues.extend(line.strip() for line in lines if line.strip())

            return {
                "documentation_issues": doc_issues,
                "total_issues": len(doc_issues),
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)}

    def _collect_performance_metrics(self) -> dict[str, object]:
        """パフォーマンスメトリクスの収集"""
        performance_metrics = {
            "test_execution_time": {},
            "memory_usage": {},
            "benchmark_results": {},
        }

        try:
            # ベンチマークテストの実行
            cmd = [
                "python",
                "-m",
                "pytest",
                "tests/unit",
                "-k",
                "performance",
                "--benchmark-only",
                "--benchmark-json=logs/benchmark.json",
            ]

            subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            # ベンチマーク結果の解析
            benchmark_path = self.project_root / "logs" / "benchmark.json"
            if benchmark_path.exists():
                with Path(benchmark_path).open(encoding="utf-8") as f:
                    benchmark_data = json.load(f)
                    performance_metrics["benchmark_results"] = benchmark_data

        except Exception as e:
            performance_metrics["error"] = f"パフォーマンスメトリクス収集エラー: {e!s}"

        return performance_metrics

    def _check_tdd_ddd_compliance(self) -> dict[str, object]:
        """TDD+DDD準拠チェック"""
        compliance_check = {
            "tdd_compliance": {},
            "ddd_compliance": {},
            "overall_compliance": False,
        }

        try:
            # TDD+DDD準拠チェックツールの実行
            cmd = ["python", "tools/check_tdd_ddd_compliance.py"]
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            compliance_check["return_code"] = result.returncode
            compliance_check["overall_compliance"] = result.returncode == 0
            compliance_check["output"] = result.stdout
            compliance_check["errors"] = result.stderr

        except Exception as e:
            compliance_check["error"] = f"準拠チェックエラー: {e!s}"

        return compliance_check

    def _generate_summary(self, report: dict[str, object]) -> dict[str, object]:
        """サマリーの生成"""
        summary = {
            "overall_status": "PASS",
            "test_success_rate": 0,
            "coverage_percentage": 0,
            "quality_score": 0,
            "compliance_status": "FAIL",
            "recommendations": [],
        }

        try:
            # テスト成功率の計算
            test_results = report.get("test_results", {})
            total_tests = test_results.get("total_tests", 0)
            passed_tests = test_results.get("passed_tests", 0)

            if total_tests > 0:
                summary["test_success_rate"] = (passed_tests / total_tests) * 100

            # カバレッジ率の取得
            coverage_report = report.get("coverage_report", {})
            summary["coverage_percentage"] = coverage_report.get("overall_coverage", 0)

            # 品質スコアの計算
            quality_metrics = report.get("quality_metrics", {})
            quality_score = 100

            # flake8エラーによる減点
            code_quality = quality_metrics.get("code_quality", {})
            violations = code_quality.get("total_violations", 0)
            quality_score -= min(violations * 2, 30)

            # mypyエラーによる減点
            type_checking = quality_metrics.get("type_checking", {})
            type_errors = type_checking.get("total_errors", 0)
            quality_score -= min(type_errors * 3, 30)

            # セキュリティ問題による減点
            security = quality_metrics.get("security", {})
            security_issues = security.get("total_issues", 0)
            quality_score -= min(security_issues * 5, 20)

            summary["quality_score"] = max(quality_score, 0)

            # 準拠ステータスの取得
            compliance_check = report.get("compliance_check", {})
            summary["compliance_status"] = "PASS" if compliance_check.get("overall_compliance", False) else "FAIL"

            # 総合ステータスの判定
            if (
                summary["test_success_rate"] >= 90
                and summary["coverage_percentage"] >= 80
                and summary["quality_score"] >= 80
                and summary["compliance_status"] == "PASS"
            ):
                summary["overall_status"] = "PASS"
            else:
                summary["overall_status"] = "FAIL"

            # 推奨事項の生成
            recommendations = []

            if summary["test_success_rate"] < 90:
                recommendations.append("テスト成功率を90%以上に改善してください")

            if summary["coverage_percentage"] < 80:
                recommendations.append("テストカバレッジを80%以上に改善してください")

            if summary["quality_score"] < 80:
                recommendations.append("コード品質を改善してください(flake8、mypy、banditの警告を解消)")

            if summary["compliance_status"] == "FAIL":
                recommendations.append("TDD+DDD準拠チェックをパスしてください")

            summary["recommendations"] = recommendations

        except Exception as e:
            summary["error"] = f"サマリー生成エラー: {e!s}"

        return summary

    def _save_report(self, report: dict[str, object]) -> None:
        """レポートファイルの保存"""
        try:
            # JSONレポートの保存
            json_path = self.report_dir / "test_report.json"
            with Path(json_path).open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # HTMLレポートの生成
            html_path = self.report_dir / "test_report.html"
            self._generate_html_report(report, html_path)

            # Markdownレポートの生成
            md_path = self.report_dir / "test_report.md"
            self._generate_markdown_report(report, md_path)


        except Exception:
            pass

    def _generate_html_report(self, report: dict[str, object], output_path: Path | str) -> None:
        """HTMLレポートの生成"""
        summary = report.get("summary", {})

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TDD+DDD テストレポート</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .warning {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TDD+DDD テストレポート</h1>
                <p>生成日時: {report.get("timestamp", "Unknown")}</p>
                <p>総合ステータス: <span class="{"pass" if summary.get("overall_status") == "PASS" else "fail"}">{summary.get("overall_status", "Unknown")}</span></p>
            </div>

            <div class="section">
                <h2>サマリー</h2>
                <table>
                    <tr><th>項目</th><th>値</th></tr>
                    <tr><td>テスト成功率</td><td>{summary.get("test_success_rate", 0):.1f}%</td></tr>
                    <tr><td>カバレッジ率</td><td>{summary.get("coverage_percentage", 0):.1f}%</td></tr>
                    <tr><td>品質スコア</td><td>{summary.get("quality_score", 0):.1f}</td></tr>
                    <tr><td>TDD+DDD準拠</td><td>{summary.get("compliance_status", "Unknown")}</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>テスト結果</h2>
                <p>実装中...</p>
            </div>

            <div class="section">
                <h2>推奨事項</h2>
                <ul>
        """

        for recommendation in summary.get("recommendations", []):
            html_content += f"<li>{recommendation}</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_markdown_report(self, report: dict[str, object], output_path: Path | str) -> None:
        """Markdownレポートの生成"""
        summary = report.get("summary", {})

        md_content = f"""# TDD+DDD テストレポート

**生成日時**: {report.get("timestamp", "Unknown")}
**総合ステータス**: {summary.get("overall_status", "Unknown")}

## サマリー

| 項目 | 値 |
|------|-----|
| テスト成功率 | {summary.get("test_success_rate", 0):.1f}% |
| カバレッジ率 | {summary.get("coverage_percentage", 0):.1f}% |
| 品質スコア | {summary.get("quality_score", 0):.1f} |
| TDD+DDD準拠 | {summary.get("compliance_status", "Unknown")} |

## テスト結果

### ユニットテスト
- 実装中...

### 統合テスト
- 実装中...

### E2Eテスト
- 実装中...

## 推奨事項

"""

        for recommendation in summary.get("recommendations", []):
            md_content += f"- {recommendation}\n"

        md_content += """
## 詳細情報

完全な詳細情報は `test_report.json` を参照してください。
"""

        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(md_content)


def main() -> None:
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    generator = TestReportGenerator(project_root)
    report = generator.generate_comprehensive_report()

    # サマリーの表示
    summary = report.get("summary", {})

    if summary.get("recommendations"):
        for _rec in summary["recommendations"]:
            pass

    if summary.get("overall_status") == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
