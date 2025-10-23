"""開発者体験改善ツール

DX (Developer Experience) とUX改善を自動化するツール
Claude Code使用環境の最適化
"""
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console

try:
    logger = get_logger(__name__)
except ImportError:
    logger = None

@dataclass
class DXEnhancementResult:
    """DX改善結果"""
    command_shortcuts_created: int
    documentation_improvements: int
    tool_integrations_enhanced: int
    performance_optimizations: int
    user_interface_improvements: int
    error_experience_enhancements: int
    recommendations: list[str]
    execution_time_seconds: float

class DeveloperExperienceEnhancer:
    """開発者体験改善器

    責務:
    - コマンドショートカット自動生成
    - ドキュメントアクセス改善
    - ツール統合最適化
    - エラー体験向上
    - パフォーマンス最適化
    """

    def __init__(self, project_root: Path | None=None) -> None:
        self.project_root = project_root or Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.docs_dir = self.project_root / "docs"
        self.tools_dir = self.project_root / "scripts" / "tools"

    def enhance_developer_experience(self) -> DXEnhancementResult:
        """DX改善実行"""
        self.logger_service.info("開発者体験改善開始")
        start_time = self._get_current_time()
        shortcuts = self._create_command_shortcuts()
        docs = self._improve_documentation_access()
        tools = self._enhance_tool_integrations()
        perf = self._optimize_performance()
        ui = self._improve_user_interfaces()
        errors = self._enhance_error_experience()
        recommendations = self._generate_recommendations()
        end_time = self._get_current_time()
        execution_time = end_time - start_time
        result = DXEnhancementResult(command_shortcuts_created=shortcuts, documentation_improvements=docs, tool_integrations_enhanced=tools, performance_optimizations=perf, user_interface_improvements=ui, error_experience_enhancements=errors, recommendations=recommendations, execution_time_seconds=execution_time)
        self.logger_service.info(f"DX改善完了 ({execution_time:.2f}秒)")
        return result

    def _create_command_shortcuts(self) -> int:
        """コマンドショートカット作成"""
        shortcuts_created = 0
        shortcuts = [("ntest", "PYTHONPATH=$PWD pytest tests/ -v"), ("ncheck", "python scripts/tools/check_tdd_ddd_compliance.py"), ("ncoverage", "python scripts/tools/test_coverage_analyzer.py"), ("nwrite", "python scripts/presentation/cli/novel_cli.py write"), ("nplot", "python scripts/presentation/cli/novel_cli.py plot"), ("nquality", "ruff check scripts/ && mypy scripts/")]
        alias_file = self.project_root / ".novel_aliases"
        alias_content = "#!/bin/bash\n# Novel Writing System Aliases\n\n"
        for (alias, command) in shortcuts:
            alias_content += f'alias {alias}="{command}"\n'
            shortcuts_created += 1
        alias_content += '\necho "Novel Writing System aliases loaded. Use ntest, ncheck, ncoverage, etc."\n'
        alias_file.write_text(alias_content, encoding="utf-8")
        bashrc_note = self.project_root / "docs" / "guides" / "setup_aliases.md"
        bashrc_note.write_text(f"""# Aliases Setup\n\n## 使い方\n```bash\nsource {alias_file.resolve()}\n```\n\n## 永続化（推奨）\n```bash\necho "source {alias_file.resolve()}" >> ~/.bashrc\n```\n\n## 使用可能なエイリアス\n{chr(10).join(f'- `{alias}`: {cmd}' for (alias, cmd) in shortcuts)}\n""", encoding="utf-8")
        self.logger_service.info(f"コマンドショートカット {shortcuts_created}件作成")
        return shortcuts_created

    def _improve_documentation_access(self) -> int:
        """ドキュメントアクセス改善"""
        improvements = 0
        quick_ref = self.docs_dir / "references" / "quick_reference.md"
        quick_content = '# Quick Reference\n\n## 🚀 よく使用するコマンド\n```bash\n# テスト実行\nntest                          # 全テスト実行\nntest tests/unit/              # ユニットテストのみ\n\n# 品質チェック\nncheck                         # DDD準拠性チェック\nnquality                       # Ruff + mypy チェック\nncoverage                      # カバレッジ分析\n\n# 執筆\nnwrite 5                       # 第5話執筆\nnplot 5                        # 第5話プロット作成\n```\n\n## 📁 重要なファイル\n- `CLAUDE.md`: 必須開発ルール\n- `docs/_index.yaml`: ドキュメント索引\n- `pyproject.toml`: プロジェクト設定\n\n## 🔧 トラブルシューティング\n- インポートエラー → `PYTHONPATH=$PWD`\n- テスト失敗 → `docs/04_よくあるエラーと対処法.md`\n- DDD違反 → `docs/B00_情報システム開発ガイド.md`\n\n## 🎯 開発フロー\n1. `ntest` でテスト確認\n2. `ncheck` で品質確認\n3. コード修正\n4. `git add . && git commit -m "fix: ..."`\n'
        quick_ref.write_text(quick_content, encoding="utf-8")
        improvements += 1
        index_html = self.project_root / "index.html"
        html_content = '<!DOCTYPE html>\n<html>\n<head>\n    <title>Novel Writing System - Documentation</title>\n    <meta charset="utf-8">\n    <style>\n        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; }\n        .header { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 1rem; }\n        .section { margin: 1.5rem 0; }\n        .link { display: block; padding: 0.5rem; background: #f9fafb; border-radius: 0.375rem; text-decoration: none; color: #374151; margin: 0.25rem 0; }\n        .link:hover { background: #e5e7eb; }\n    </style>\n</head>\n<body>\n    <h1 class="header">📖 Novel Writing System Documentation</h1>\n\n    <div class="section">\n        <h2>🚀 Quick Start</h2>\n        <a href="docs/references/quick_reference.md" class="link">📋 Quick Reference - よく使用するコマンド</a>\n        <a href="CLAUDE.md" class="link">⚡ CLAUDE.md - 必須開発ルール</a>\n        <a href="docs/guides/setup_aliases.md" class="link">🔧 Aliases Setup - コマンドショートカット</a>\n    </div>\n\n    <div class="section">\n        <h2>📚 Developer Guides</h2>\n        <a href="docs/B20_Claude_Code開発作業指示書.md" class="link">🛠️ Claude Code開発作業指示書</a>\n        <a href="docs/B30_Claude_Code品質作業指示書.md" class="link">✅ 品質作業指示書</a>\n        <a href="docs/B00_情報システム開発ガイド.md" class="link">🏗️ システム開発ガイド</a>\n    </div>\n\n    <div class="section">\n        <h2>📝 Writing Guides</h2>\n        <a href="docs/A00_総合実践ガイド.md" class="link">📖 総合実践ガイド</a>\n        <a href="docs/A30_執筆ワークフロー.md" class="link">✍️ 執筆ワークフロー</a>\n        <a href="docs/A38_執筆プロンプトガイド.md" class="link">🤖 AI執筆プロンプト</a>\n    </div>\n</body>\n</html>'
        index_html.write_text(html_content, encoding="utf-8")
        improvements += 1
        self.logger_service.info(f"ドキュメントアクセス改善 {improvements}件完了")
        return improvements

    def _enhance_tool_integrations(self) -> int:
        """ツール統合改善"""
        enhancements = 0
        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        tasks_json = vscode_dir / "tasks.json"
        tasks_config = {"version": "2.0.0", "tasks": [{"label": "Novel Test", "type": "shell", "command": "PYTHONPATH=${workspaceFolder} pytest", "args": ["tests/", "-v"], "group": "test", "presentation": {"echo": True, "reveal": "always", "panel": "new"}}, {"label": "Novel Quality Check", "type": "shell", "command": "python", "args": ["noveler/tools/check_tdd_ddd_compliance.py"], "group": "build", "presentation": {"echo": True, "reveal": "always"}}, {"label": "Novel Coverage", "type": "shell", "command": "python", "args": ["noveler/tools/test_coverage_analyzer.py"], "group": "test"}]}
        tasks_json.write_text(json.dumps(tasks_config, indent=2, ensure_ascii=False), encoding="utf-8")
        enhancements += 1
        launch_json = vscode_dir / "launch.json"
        launch_config = {"version": "0.2.0", "configurations": [{"name": "Novel CLI Debug", "type": "python", "request": "launch", "program": "${workspaceFolder}/scripts/presentation/cli/novel_cli.py", "args": ["--help"], "console": "integratedTerminal", "envFile": "${workspaceFolder}/.env", "python": "${workspaceFolder}/.venv/bin/python"}, {"name": "Test Current File", "type": "python", "request": "launch", "module": "pytest", "args": ["${file}", "-v"], "console": "integratedTerminal", "env": {"PYTHONPATH": "${workspaceFolder}"}}]}
        launch_json.write_text(json.dumps(launch_config, indent=2, ensure_ascii=False), encoding="utf-8")
        enhancements += 1
        self.logger_service.info(f"ツール統合改善 {enhancements}件完了")
        return enhancements

    def _optimize_performance(self) -> int:
        """パフォーマンス最適化"""
        optimizations = 0
        temp_dir = self.project_root / "temp"
        cache_dirs = ["cache/mypy", "cache/ruff", "cache/pytest", "coverage"]
        for cache_dir in cache_dirs:
            cache_path = temp_dir / cache_dir
            cache_path.mkdir(parents=True, exist_ok=True)
            optimizations += 1
        perf_monitor = self.tools_dir / "performance_monitor.py"
        if not perf_monitor.exists():
            perf_content = '#!/usr/bin/env python3\n"""パフォーマンス監視ツール"""\n\nimport psutil\nimport sys\nfrom pathlib import Path\n\ndef monitor_command_performance(command_args):\n    """コマンド実行パフォーマンス監視"""\n    process = psutil.Process()\n    start_memory = process.memory_info().rss / 1024 / 1024\n    start_time = time.perf_counter()\n\n    self.console_service.print(f"🚀 実行開始: {\' \'.join(command_args)}")\n    self.console_service.print(f"📊 初期メモリ: {start_memory:.2f} MB")\n\n    # ここでコマンド実行（実際の実装では subprocess.run等を使用）\n\n    end_time = time.perf_counter()\n    end_memory = process.memory_info().rss / 1024 / 1024\n\n    self.console_service.print(f"⏱️  実行時間: {end_time - start_time:.2f}秒")\n    self.console_service.print(f"💾 最終メモリ: {end_memory:.2f} MB")\n    self.console_service.print(f"📈 メモリ増加: {end_memory - start_memory:.2f} MB")\n\nif __name__ == "__main__":\n    monitor_command_performance(sys.argv[1:])\n'
            perf_monitor.write_text(perf_content, encoding="utf-8")
            optimizations += 1
        self.logger_service.info(f"パフォーマンス最適化 {optimizations}件完了")
        return optimizations

    def _improve_user_interfaces(self) -> int:
        """ユーザーインターフェース改善"""
        improvements = 0
        ui_utils = self.project_root / "scripts" / "presentation" / "cli" / "ui_enhancements.py"
        if not ui_utils.exists():
            ui_content = '#!/usr/bin/env python3\n"""UI表示改善ユーティリティ"""\n\nfrom noveler.presentation.shared.shared_utilities import console\nfrom rich.progress import Progress, SpinnerColumn, TextColumn\nfrom rich.table import Table\nfrom rich.panel import Panel\n\ndef print_success(message: str, details: str = None):\n    """成功メッセージ表示"""\n    panel = Panel(f"✅ {message}\\n{details or \'\'}",\n                  title="Success", border_style="green")\n    console.print(panel)\n\ndef print_error(message: str, suggestion: str = None):\n    """エラーメッセージ表示"""\n    panel = Panel(f"❌ {message}\\n💡 {suggestion or \'\'}",\n                  title="Error", border_style="red")\n    console.print(panel)\n\ndef print_info(message: str):\n    """情報メッセージ表示"""\n    console.print(f"ℹ️  {message}", style="blue")\n\ndef create_progress_spinner(description: str):\n    """プログレススピナー作成"""\n    return Progress(\n        SpinnerColumn(),\n        TextColumn("[progress.description]{task.description}"),\n        console=console\n    )\n\ndef create_results_table(title: str, data: list):\n    """結果テーブル作成"""\n    table = Table(title=title)\n    if data:\n        # 最初の行をヘッダーとして使用\n        for header in data[0].keys():\n            table.add_column(header)\n        for row in data:\n            table.add_row(*[str(v) for v in row.values()])\n    return table\n'
            ui_utils.write_text(ui_content, encoding="utf-8")
            improvements += 1
        self.logger_service.info(f"UI改善 {improvements}件完了")
        return improvements

    def _enhance_error_experience(self) -> int:
        """エラー体験改善"""
        enhancements = 0
        error_guide = self.docs_dir / "ERROR_RESOLUTION_GUIDE.md"
        error_content = '# エラー解決ガイド\n\n## 🚨 よくあるエラーと解決法\n\n### ModuleNotFoundError: No module named \'scripts\'\n```bash\n# 解決法\nexport PYTHONPATH=$PWD\n# または\nPYTHONPATH=$PWD python your_script.py\n```\n\n### pytest collection failed\n```bash\n# 解決法1: パスを明示指定\nPYTHONPATH=$PWD pytest tests/\n\n# 解決法2: __init__.pyファイル確認\nfind tests/ -name "__init__.py" | head -5\n```\n\n### DDD違反エラー\n```bash\n# 解決法\npython scripts/tools/check_tdd_ddd_compliance.py\n# 詳細は CLAUDE.md を参照\n```\n\n### Import循環参照エラー\n```python\n# 解決パターン: TYPE_CHECKINGを使用\nfrom typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from noveler.domain.interfaces.service import IService\n\nlogger: "IService | None" = None  # 依存性注入\n```\n\n### カバレッジ不足エラー\n```bash\n# 現状分析\npython scripts/tools/test_coverage_analyzer.py\n\n# テスト作成\nmkdir -p tests/unit/application/services/\n# テストファイルを作成\n```\n\n## 🛠️ デバッグコマンド\n```bash\n# システム状態確認\nncheck                    # 品質チェック\nncoverage                # カバレッジ分析\nntest -v                 # 詳細テスト実行\n\n# ログ確認\ntail -f temp/logs/*.log  # ログファイル監視\n```\n\n## 📞 サポート\n- エラーが解決しない場合は `docs/B20_Claude_Code開発作業指示書.md` を参照\n- システム改善が必要な場合は `/serena "改善可能な箇所を改善して" -d -s -c` を実行\n'
        error_guide.write_text(error_content, encoding="utf-8")
        enhancements += 1
        self.logger_service.info(f"エラー体験改善 {enhancements}件完了")
        return enhancements

    def _generate_recommendations(self) -> list[str]:
        """改善提案生成"""
        return ["🔧 コマンドエイリアスを活用してコマンド入力を簡素化", "📖 index.html をブラウザで開いてドキュメントに素早くアクセス", "⚡ VSCode tasks を使用して統合開発環境を最適化", "📊 パフォーマンス監視ツールで処理時間を継続追跡", "🎨 Rich ライブラリで視覚的にわかりやすいCLI出力を活用", "🚨 ERROR_RESOLUTION_GUIDE.md でエラー解決を効率化"]

    def _get_current_time(self) -> float:
        """現在時刻取得（秒）"""
        return time.perf_counter()

    def export_results(self, result: DXEnhancementResult, output_path: Path | None=None) -> None:
        """結果エクスポート"""
        if output_path is None:
            output_path = self.project_root / "temp" / "dx_enhancement_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)
        self.logger_service.info(f"DX改善結果をエクスポート: {output_path}")

    def print_summary(self, result: DXEnhancementResult) -> None:
        """サマリー表示"""
        self.console_service.print("\n" + "=" * 60)
        self.console_service.print("🚀 DX/UX改善結果")
        self.console_service.print("=" * 60)
        self.console_service.print(f"⌨️  コマンドショートカット: {result.command_shortcuts_created}件")
        self.console_service.print(f"📚 ドキュメント改善: {result.documentation_improvements}件")
        self.console_service.print(f"🔧 ツール統合改善: {result.tool_integrations_enhanced}件")
        self.console_service.print(f"⚡ パフォーマンス最適化: {result.performance_optimizations}件")
        self.console_service.print(f"🎨 UI改善: {result.user_interface_improvements}件")
        self.console_service.print(f"🚨 エラー体験改善: {result.error_experience_enhancements}件")
        total_improvements = result.command_shortcuts_created + result.documentation_improvements + result.tool_integrations_enhanced + result.performance_optimizations + result.user_interface_improvements + result.error_experience_enhancements
        self.console_service.print(f"\n📊 総改善項目数: {total_improvements}件")
        self.console_service.print(f"⏱️  実行時間: {result.execution_time_seconds:.2f}秒")
        if result.recommendations:
            self.console_service.print("\n💡 活用推奨:")
            for rec in result.recommendations:
                self.console_service.print(f"  {rec}")
        self.console_service.print("\n🎯 次のステップ:")
        self.console_service.print("  1. `source .novel_aliases` でエイリアスを有効化")
        self.console_service.print("  2. `index.html` をブラウザで開いてドキュメント確認")
        self.console_service.print("  3. VSCode で tasks (Ctrl+Shift+P -> Tasks) を活用")
        self.console_service.print("=" * 60)

def main():
    """メイン実行"""
    enhancer = DeveloperExperienceEnhancer()
    try:
        result = enhancer.enhance_developer_experience()
        enhancer.print_summary(result)
        enhancer.export_results(result)
        console.print("\n✅ DX/UX改善が完了しました")
        sys.exit(0)
    except Exception:
        logger.exception("DX改善エラー")
        sys.exit(1)
if __name__ == "__main__":
    main()
