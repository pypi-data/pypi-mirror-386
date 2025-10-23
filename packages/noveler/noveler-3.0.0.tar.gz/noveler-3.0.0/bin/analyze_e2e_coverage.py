#!/usr/bin/env python3
"""E2Eテストカバレッジ分析ツール

E2Eテストのカバレッジ分析とレポート生成
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class E2ECoverageAnalyzer:
    """E2Eテストカバレッジ分析"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.e2e_test_dir = project_root / "tests" / "e2e"
        self.cli_dir = project_root / "scripts" / "presentation" / "cli"
        self.reports_dir = project_root / "temp" / "reports" / "e2e"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # カバレッジ分析結果
        self.coverage_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_files": [],
            "command_coverage": {},
            "scenario_coverage": {},
            "workflow_coverage": {},
            "performance_coverage": {},
            "missing_coverage": []
        }

    def analyze_test_files(self) -> list[Path]:
        """E2Eテストファイルの分析"""
        print("E2Eテストファイルの分析中...")

        test_files = list(self.e2e_test_dir.glob("test_*.py"))

        for test_file in test_files:
            file_info = {
                "file": str(test_file.relative_to(self.project_root)),
                "size": test_file.stat().st_size,
                "lines": len(test_file.read_text(encoding="utf-8").splitlines()),
                "test_methods": [],
                "covered_commands": set(),
                "test_categories": set()
            }

            content = test_file.read_text(encoding="utf-8")

            # テストメソッドの抽出
            test_methods = re.findall(r"def (test_\w+)", content)
            file_info["test_methods"] = test_methods

            # カバーされているコマンドの抽出
            command_matches = re.findall(r'"([^"]*(?:status|write|quality|backup|plot|analyze|config|health)[^"]*)"', content)
            for match in command_matches:
                # "python {self.novel_cmd} status" -> "status"
                if " " in match:
                    parts = match.split()
                    if len(parts) >= 3:
                        command = parts[-1] if not parts[-1].startswith("-") else parts[-2]
                        file_info["covered_commands"].add(command)

            # pytest マーカーの抽出
            markers = re.findall(r"@pytest\.mark\.(\w+)", content)
            file_info["test_categories"].update(markers)

            # セット型を リスト に変換（JSON対応）
            file_info["covered_commands"] = list(file_info["covered_commands"])
            file_info["test_categories"] = list(file_info["test_categories"])

            self.coverage_data["test_files"].append(file_info)

            print(f"  分析完了: {test_file.name} ({len(test_methods)} テスト)")

        print(f"総E2Eテストファイル: {len(test_files)}")
        return test_files

    def analyze_command_coverage(self) -> None:
        """コマンドカバレッジの分析"""
        print("コマンドカバレッジの分析中...")

        # 利用可能コマンドの抽出
        available_commands = self.discover_available_commands()

        # テストでカバーされているコマンドの集計
        covered_commands = set()
        for test_file in self.coverage_data["test_files"]:
            covered_commands.update(test_file["covered_commands"])

        # カバレッジ分析
        uncovered_commands = set(available_commands) - covered_commands

        self.coverage_data["command_coverage"] = {
            "total_commands": len(available_commands),
            "covered_commands": len(covered_commands),
            "coverage_percentage": len(covered_commands) / max(len(available_commands), 1) * 100,
            "covered_list": sorted(covered_commands),
            "uncovered_list": sorted(uncovered_commands),
            "all_commands": sorted(available_commands)
        }

        print(f"コマンドカバレッジ: {len(covered_commands)}/{len(available_commands)} ({len(covered_commands) / max(len(available_commands), 1) * 100:.1f}%)")

        if uncovered_commands:
            print("未カバーコマンド:")
            for cmd in sorted(uncovered_commands)[:5]:  # 最初の5個を表示
                print(f"  - {cmd}")

    def discover_available_commands(self) -> list[str]:
        """利用可能なコマンドの発見"""
        commands = set()

        # CLIファイルから基本コマンドを抽出
        cli_files = list(self.cli_dir.glob("*.py"))

        for cli_file in cli_files:
            try:
                content = cli_file.read_text(encoding="utf-8")

                # Typer のコマンド定義を検索
                typer_commands = re.findall(r'@app\.command\(["\']?(\w+)["\']?\)', content)
                commands.update(typer_commands)

                # def関数からコマンドを推測
                function_commands = re.findall(r"def (\w+)_command\(", content)
                commands.update([cmd.replace("_command", "") for cmd in function_commands])

                # "novel" で始まるコメントからコマンドを抽出
                novel_commands = re.findall(r"novel (\w+)", content)
                commands.update(novel_commands)

            except Exception as e:
                print(f"  警告: {cli_file.name} 分析エラー: {e}")

        # 既知の基本コマンドを追加
        basic_commands = [
            "status", "write", "quality", "backup", "plot", "analyze",
            "config", "health", "create", "init", "check"
        ]
        commands.update(basic_commands)

        return list(commands)

    def analyze_scenario_coverage(self) -> None:
        """シナリオカバレッジの分析"""
        print("シナリオカバレッジの分析中...")

        scenarios = {
            "complete_workflow": "完全執筆ワークフロー",
            "quality_workflow": "品質保証ワークフロー",
            "project_management": "プロジェクト管理ワークフロー",
            "error_recovery": "エラー回復ワークフロー",
            "concurrent_operations": "並行操作テスト",
            "performance_testing": "パフォーマンステスト",
            "stress_testing": "ストレステスト",
            "data_migration": "データ移行テスト",
            "backup_restore": "バックアップ・復元テスト",
            "configuration_management": "設定管理テスト"
        }

        covered_scenarios = set()

        # テストメソッドからシナリオを推定
        for test_file in self.coverage_data["test_files"]:
            for method in test_file["test_methods"]:
                for scenario_key in scenarios:
                    if any(keyword in method.lower() for keyword in scenario_key.split("_")):
                        covered_scenarios.add(scenario_key)

        uncovered_scenarios = set(scenarios.keys()) - covered_scenarios

        self.coverage_data["scenario_coverage"] = {
            "total_scenarios": len(scenarios),
            "covered_scenarios": len(covered_scenarios),
            "coverage_percentage": len(covered_scenarios) / len(scenarios) * 100,
            "covered_list": [scenarios[s] for s in sorted(covered_scenarios)],
            "uncovered_list": [scenarios[s] for s in sorted(uncovered_scenarios)],
            "scenario_details": scenarios
        }

        print(f"シナリオカバレッジ: {len(covered_scenarios)}/{len(scenarios)} ({len(covered_scenarios) / len(scenarios) * 100:.1f}%)")

    def analyze_workflow_coverage(self) -> None:
        """ワークフローカバレッジの分析"""
        print("ワークフローカバレッジの分析中...")

        workflows = {
            "new_project_creation": "新規プロジェクト作成",
            "episode_writing": "話別執筆",
            "plot_management": "プロット管理",
            "quality_checking": "品質チェック",
            "backup_operations": "バックアップ操作",
            "project_analysis": "プロジェクト分析",
            "configuration_setup": "設定管理",
            "troubleshooting": "トラブルシューティング"
        }

        covered_workflows = set()

        # テストカテゴリとメソッドからワークフローを推定
        for test_file in self.coverage_data["test_files"]:
            # カテゴリベースの判定
            categories = test_file.get("test_categories", [])
            if "workflow" in categories:
                covered_workflows.add("episode_writing")
            if "quality" in categories:
                covered_workflows.add("quality_checking")
            if "performance" in categories or "stress" in categories:
                covered_workflows.add("project_analysis")

            # メソッド名ベースの判定
            for method in test_file["test_methods"]:
                method_lower = method.lower()
                if "create" in method_lower or "new" in method_lower:
                    covered_workflows.add("new_project_creation")
                if "write" in method_lower or "episode" in method_lower:
                    covered_workflows.add("episode_writing")
                if "plot" in method_lower:
                    covered_workflows.add("plot_management")
                if "quality" in method_lower or "check" in method_lower:
                    covered_workflows.add("quality_checking")
                if "backup" in method_lower:
                    covered_workflows.add("backup_operations")
                if "analyze" in method_lower or "status" in method_lower:
                    covered_workflows.add("project_analysis")
                if "config" in method_lower:
                    covered_workflows.add("configuration_setup")
                if "error" in method_lower or "recovery" in method_lower:
                    covered_workflows.add("troubleshooting")

        uncovered_workflows = set(workflows.keys()) - covered_workflows

        self.coverage_data["workflow_coverage"] = {
            "total_workflows": len(workflows),
            "covered_workflows": len(covered_workflows),
            "coverage_percentage": len(covered_workflows) / len(workflows) * 100,
            "covered_list": [workflows[w] for w in sorted(covered_workflows)],
            "uncovered_list": [workflows[w] for w in sorted(uncovered_workflows)],
            "workflow_details": workflows
        }

        print(f"ワークフローカバレッジ: {len(covered_workflows)}/{len(workflows)} ({len(covered_workflows) / len(workflows) * 100:.1f}%)")

    def analyze_performance_coverage(self) -> None:
        """パフォーマンステストカバレッジの分析"""
        print("パフォーマンステストカバレッジの分析中...")

        performance_aspects = {
            "large_data_processing": "大容量データ処理",
            "concurrent_operations": "並行処理",
            "memory_usage": "メモリ使用量",
            "long_running_stability": "長時間実行安定性",
            "resource_limitations": "リソース制限",
            "rapid_execution": "高速連続実行",
            "stress_conditions": "ストレス条件",
            "regression_testing": "回帰テスト"
        }

        covered_aspects = set()

        for test_file in self.coverage_data["test_files"]:
            categories = test_file.get("test_categories", [])
            methods = test_file["test_methods"]

            # パフォーマンステストの特定
            if "performance" in categories or "stress" in categories:
                for method in methods:
                    method_lower = method.lower()
                    if "large" in method_lower or "big" in method_lower:
                        covered_aspects.add("large_data_processing")
                    if "concurrent" in method_lower or "parallel" in method_lower:
                        covered_aspects.add("concurrent_operations")
                    if "memory" in method_lower:
                        covered_aspects.add("memory_usage")
                    if "long" in method_lower or "stability" in method_lower:
                        covered_aspects.add("long_running_stability")
                    if "rapid" in method_lower or "fast" in method_lower:
                        covered_aspects.add("rapid_execution")
                    if "stress" in method_lower:
                        covered_aspects.add("stress_conditions")
                    if "regression" in method_lower:
                        covered_aspects.add("regression_testing")

        # 基本的なパフォーマンステストがある場合はresource_limitationsもカバーとみなす
        if covered_aspects:
            covered_aspects.add("resource_limitations")

        uncovered_aspects = set(performance_aspects.keys()) - covered_aspects

        self.coverage_data["performance_coverage"] = {
            "total_aspects": len(performance_aspects),
            "covered_aspects": len(covered_aspects),
            "coverage_percentage": len(covered_aspects) / len(performance_aspects) * 100,
            "covered_list": [performance_aspects[a] for a in sorted(covered_aspects)],
            "uncovered_list": [performance_aspects[a] for a in sorted(uncovered_aspects)],
            "aspect_details": performance_aspects
        }

        print(f"パフォーマンステストカバレッジ: {len(covered_aspects)}/{len(performance_aspects)} ({len(covered_aspects) / len(performance_aspects) * 100:.1f}%)")

    def identify_missing_coverage(self) -> None:
        """不足カバレッジの特定"""
        print("不足カバレッジの特定中...")

        missing_items = []

        # コマンドカバレッジの不足
        uncovered_commands = self.coverage_data["command_coverage"]["uncovered_list"]
        for command in uncovered_commands[:10]:  # 上位10個
            missing_items.append({
                "type": "command",
                "item": command,
                "priority": "high" if command in ["write", "quality", "backup"] else "medium",
                "suggestion": f"{command}コマンドのE2Eテストを追加"
            })

        # シナリオカバレッジの不足
        uncovered_scenarios = self.coverage_data["scenario_coverage"]["uncovered_list"]
        for scenario in uncovered_scenarios[:5]:
            missing_items.append({
                "type": "scenario",
                "item": scenario,
                "priority": "high",
                "suggestion": f"{scenario}シナリオのテストケースを追加"
            })

        # ワークフローカバレッジの不足
        uncovered_workflows = self.coverage_data["workflow_coverage"]["uncovered_list"]
        for workflow in uncovered_workflows[:5]:
            missing_items.append({
                "type": "workflow",
                "item": workflow,
                "priority": "medium",
                "suggestion": f"{workflow}ワークフローのテストを追加"
            })

        self.coverage_data["missing_coverage"] = missing_items
        print(f"特定された不足項目: {len(missing_items)}")

    def generate_json_report(self) -> Path:
        """JSONレポートの生成"""
        report_file = self.reports_dir / f"e2e_coverage_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.coverage_data, f, indent=2, ensure_ascii=False)

        print(f"JSONレポート生成: {report_file}")
        return report_file

    def generate_html_report(self) -> Path:
        """HTMLレポートの生成"""
        report_file = self.reports_dir / f"e2e_coverage_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.html"

        html_content = self._build_html_report()

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTMLレポート生成: {report_file}")
        return report_file

    def _build_html_report(self) -> str:
        """HTMLレポートコンテンツの構築"""
        command_cov = self.coverage_data["command_coverage"]
        scenario_cov = self.coverage_data["scenario_coverage"]
        workflow_cov = self.coverage_data["workflow_coverage"]
        performance_cov = self.coverage_data["performance_coverage"]

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2Eテストカバレッジレポート</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 1.2em; }}
        .summary-card .percentage {{ font-size: 2.5em; font-weight: bold; }}
        .summary-card .description {{ opacity: 0.9; font-size: 0.9em; }}
        .coverage-bar {{ background: #ecf0f1; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .coverage-fill {{ background: linear-gradient(90deg, #2ecc71, #27ae60); height: 20px; transition: width 0.3s ease; }}
        .coverage-text {{ text-align: center; padding: 5px; font-weight: bold; }}
        .test-files {{ margin: 20px 0; }}
        .test-file {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; margin: 10px 0; padding: 15px; }}
        .test-file h4 {{ margin: 0 0 10px 0; color: #495057; }}
        .test-methods {{ display: flex; flex-wrap: wrap; gap: 5px; margin: 10px 0; }}
        .test-method {{ background: #e9ecef; padding: 3px 8px; border-radius: 15px; font-size: 0.85em; }}
        .covered-commands {{ color: #28a745; }}
        .uncovered-commands {{ color: #dc3545; }}
        .missing-items {{ margin: 20px 0; }}
        .missing-item {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 10px; margin: 5px 0; }}
        .missing-item.high {{ border-color: #ff7675; background: #ffe0e0; }}
        .missing-item.medium {{ border-color: #fdcb6e; }}
        .priority {{ font-weight: bold; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
        .priority.high {{ background: #e74c3c; color: white; }}
        .priority.medium {{ background: #f39c12; color: white; }}
        .list-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        footer {{ margin-top: 50px; text-align: center; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 E2Eテストカバレッジレポート</h1>
        <div class="timestamp">生成日時: {self.coverage_data['timestamp']}</div>

        <div class="summary">
            <div class="summary-card">
                <h3>コマンドカバレッジ</h3>
                <div class="percentage">{command_cov['coverage_percentage']:.1f}%</div>
                <div class="description">{command_cov['covered_commands']}/{command_cov['total_commands']} コマンド</div>
            </div>
            <div class="summary-card">
                <h3>シナリオカバレッジ</h3>
                <div class="percentage">{scenario_cov['coverage_percentage']:.1f}%</div>
                <div class="description">{scenario_cov['covered_scenarios']}/{scenario_cov['total_scenarios']} シナリオ</div>
            </div>
            <div class="summary-card">
                <h3>ワークフローカバレッジ</h3>
                <div class="percentage">{workflow_cov['coverage_percentage']:.1f}%</div>
                <div class="description">{workflow_cov['covered_workflows']}/{workflow_cov['total_workflows']} ワークフロー</div>
            </div>
            <div class="summary-card">
                <h3>パフォーマンステスト</h3>
                <div class="percentage">{performance_cov['coverage_percentage']:.1f}%</div>
                <div class="description">{performance_cov['covered_aspects']}/{performance_cov['total_aspects']} 観点</div>
            </div>
        </div>

        <h2>📁 テストファイル詳細</h2>
        <div class="test-files">
"""

        for test_file in self.coverage_data["test_files"]:
            html += f"""
            <div class="test-file">
                <h4>{test_file['file']}</h4>
                <div>📏 {test_file['lines']} 行 | 🧪 {len(test_file['test_methods'])} テスト | 🎯 {len(test_file['covered_commands'])} コマンドカバー</div>
                <div class="test-methods">
"""
            for method in test_file["test_methods"]:
                html += f'<span class="test-method">{method}</span>'

            html += f"""
                </div>
                <div><strong>カバー済みコマンド:</strong> <span class="covered-commands">{', '.join(test_file['covered_commands']) if test_file['covered_commands'] else 'なし'}</span></div>
                <div><strong>テストカテゴリ:</strong> {', '.join(test_file['test_categories']) if test_file['test_categories'] else 'なし'}</div>
            </div>
"""

        html += """
        </div>

        <h2>⚠️ 不足カバレッジ</h2>
        <div class="missing-items">
"""

        for item in self.coverage_data["missing_coverage"]:
            priority_class = item["priority"]
            html += f"""
            <div class="missing-item {priority_class}">
                <span class="priority {priority_class}">{item['priority'].upper()}</span>
                <strong>{item['type'].title()}:</strong> {item['item']}
                <div><em>提案:</em> {item['suggestion']}</div>
            </div>
"""

        html += f"""
        </div>

        <h2>📈 詳細カバレッジ情報</h2>

        <h3>コマンドカバレッジ詳細</h3>
        <div class="list-grid">
            <div>
                <h4 class="covered-commands">✅ カバー済み ({len(command_cov['covered_list'])})</h4>
                <ul>
"""
        for cmd in command_cov["covered_list"]:
            html += f"<li>{cmd}</li>"

        html += f"""
                </ul>
            </div>
            <div>
                <h4 class="uncovered-commands">❌ 未カバー ({len(command_cov['uncovered_list'])})</h4>
                <ul>
"""
        for cmd in command_cov["uncovered_list"]:
            html += f"<li>{cmd}</li>"

        html += f"""
                </ul>
            </div>
        </div>

        <footer>
            <p>このレポートは E2E Coverage Analyzer により自動生成されました。</p>
            <p>プロジェクトルート: {self.project_root}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html

    def run_analysis(self) -> dict[str, Path]:
        """完全なカバレッジ分析の実行"""
        print("E2Eテストカバレッジ分析開始...")

        # 各段階の分析実行
        self.analyze_test_files()
        self.analyze_command_coverage()
        self.analyze_scenario_coverage()
        self.analyze_workflow_coverage()
        self.analyze_performance_coverage()
        self.identify_missing_coverage()

        # レポート生成
        reports = {
            "json": self.generate_json_report(),
            "html": self.generate_html_report()
        }

        print("\n✅ E2Eカバレッジ分析完了")
        print(f"📊 HTMLレポート: {reports['html']}")
        print(f"📄 JSONレポート: {reports['json']}")

        return reports


def main():
    """メイン実行関数"""
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    if not project_root.exists():
        print(f"❌ エラー: プロジェクトルートが見つかりません: {project_root}")
        sys.exit(1)

    analyzer = E2ECoverageAnalyzer(project_root)
    analyzer.run_analysis()

    # サマリー出力
    coverage_data = analyzer.coverage_data
    print("\n🎯 カバレッジサマリー:")
    print(f"   コマンド: {coverage_data['command_coverage']['coverage_percentage']:.1f}%")
    print(f"   シナリオ: {coverage_data['scenario_coverage']['coverage_percentage']:.1f}%")
    print(f"   ワークフロー: {coverage_data['workflow_coverage']['coverage_percentage']:.1f}%")
    print(f"   パフォーマンス: {coverage_data['performance_coverage']['coverage_percentage']:.1f}%")

    # 改善提案
    missing_high = [item for item in coverage_data["missing_coverage"] if item["priority"] == "high"]
    if missing_high:
        print(f"\n🔥 優先改善項目 ({len(missing_high)}件):")
        for item in missing_high[:3]:
            print(f"   - {item['suggestion']}")


if __name__ == "__main__":
    main()
