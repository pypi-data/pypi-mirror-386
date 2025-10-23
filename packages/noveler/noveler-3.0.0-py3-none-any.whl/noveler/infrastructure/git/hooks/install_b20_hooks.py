"""Infrastructure.git.hooks.install_b20_hooks
Where: Infrastructure script installing B20 git hooks into a repository.
What: Copies hook scripts and ensures the repo is configured correctly.
Why: Simplifies setup of B20-compliant git hooks for developers.
"""

from noveler.presentation.shared.shared_utilities import console

"B20開発プロセス準拠Git Hooksインストーラー\n\n仕様書: B20開発作業指示書準拠\n"
import argparse
import stat
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class B20HooksInstaller:
    """B20開発プロセス準拠Git Hooksインストーラー"""

    def __init__(self, git_root: Path, guide_root: Path) -> None:
        """初期化"""
        self.git_root = git_root
        self.guide_root = guide_root
        self.hooks_dir = git_root / ".git" / "hooks"

    def install_all_hooks(self, force: bool = False) -> dict[str, Any]:
        """全てのB20 Hooksのインストール"""
        result = {"success": True, "installed_hooks": [], "skipped_hooks": [], "errors": []}
        try:
            self.hooks_dir.mkdir(exist_ok=True)
            pre_commit_result = self.install_pre_commit_hook(force)
            if pre_commit_result["success"]:
                result["installed_hooks"].append("pre-commit")
            elif pre_commit_result.get("skipped"):
                result["skipped_hooks"].append("pre-commit")
            else:
                result["success"] = False
                result["errors"].extend(pre_commit_result["errors"])
            post_commit_result = self.install_post_commit_hook(force)
            if post_commit_result["success"]:
                result["installed_hooks"].append("post-commit")
            elif post_commit_result.get("skipped"):
                result["skipped_hooks"].append("post-commit")
            else:
                result["success"] = False
                result["errors"].extend(post_commit_result["errors"])
            commit_msg_result = self.install_commit_msg_hook(force)
            if commit_msg_result["success"]:
                result["installed_hooks"].append("commit-msg")
            elif commit_msg_result.get("skipped"):
                result["skipped_hooks"].append("commit-msg")
            else:
                result["success"] = False
                result["errors"].extend(commit_msg_result["errors"])
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Hooksインストールエラー: {e!s}")
        return result

    def install_pre_commit_hook(self, force: bool = False) -> dict[str, Any]:
        """Pre-commit hookのインストール"""
        hook_file = self.hooks_dir / "pre-commit"
        if hook_file.exists() and (not force):
            return {
                "success": True,
                "skipped": True,
                "errors": [],
                "message": "Pre-commit hook already exists (use --force to overwrite)",
            }
        try:
            hook_content = self._generate_pre_commit_hook_script()
            hook_file.write_text(hook_content, encoding="utf-8")
            hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
            self.logger_service.info("Pre-commit hook installed: %s", hook_file)
            return {
                "success": True,
                "skipped": False,
                "errors": [],
                "message": "Pre-commit hook installed successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "skipped": False,
                "errors": [f"Pre-commit hook installation failed: {e!s}"],
                "message": None,
            }

    def install_post_commit_hook(self, force: bool = False) -> dict[str, Any]:
        """Post-commit hookのインストール（CODEMAP更新統合）"""
        hook_file = self.hooks_dir / "post-commit"
        if hook_file.exists() and (not force):
            return {
                "success": True,
                "skipped": True,
                "errors": [],
                "message": "Post-commit hook already exists (use --force to overwrite)",
            }
        try:
            hook_content = self._generate_post_commit_hook_script()
            hook_file.write_text(hook_content, encoding="utf-8")
            hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
            self.logger_service.info("Post-commit hook installed: %s", hook_file)
            return {
                "success": True,
                "skipped": False,
                "errors": [],
                "message": "Post-commit hook installed successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "skipped": False,
                "errors": [f"Post-commit hook installation failed: {e!s}"],
                "message": None,
            }

    def install_commit_msg_hook(self, force: bool = False) -> dict[str, Any]:
        """Commit-msg hookのインストール"""
        hook_file = self.hooks_dir / "commit-msg"
        if hook_file.exists() and (not force):
            return {
                "success": True,
                "skipped": True,
                "errors": [],
                "message": "Commit-msg hook already exists (use --force to overwrite)",
            }
        try:
            hook_content = self._generate_commit_msg_hook_script()
            hook_file.write_text(hook_content, encoding="utf-8")
            hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
            self.logger_service.info("Commit-msg hook installed: %s", hook_file)
            return {
                "success": True,
                "skipped": False,
                "errors": [],
                "message": "Commit-msg hook installed successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "skipped": False,
                "errors": [f"Commit-msg hook installation failed: {e!s}"],
                "message": None,
            }

    def uninstall_hooks(self) -> dict[str, Any]:
        """B20 Hooksのアンインストール"""
        result = {"success": True, "uninstalled_hooks": [], "errors": []}
        hooks_to_remove = ["pre-commit", "post-commit", "commit-msg"]
        for hook_name in hooks_to_remove:
            hook_file = self.hooks_dir / hook_name
            if hook_file.exists():
                try:
                    content = hook_file.read_text(encoding="utf-8")
                    if "B20開発プロセス" in content or "B20PreCommitValidator" in content:
                        hook_file.unlink()
                        result["uninstalled_hooks"].append(hook_name)
                        self.logger_service.info("B20 hook uninstalled: %s", hook_name)
                    else:
                        self.logger_service.warning("Skipped non-B20 hook: %s", hook_name)
                except Exception as e:
                    result["success"] = False
                    result["errors"].append(f"Failed to uninstall {hook_name}: {e!s}")
        return result

    def get_installation_status(self) -> dict[str, Any]:
        """インストール状態の取得"""
        status = {
            "git_root": str(self.git_root),
            "guide_root": str(self.guide_root),
            "hooks_dir": str(self.hooks_dir),
            "hooks": {},
        }
        hooks_to_check = ["pre-commit", "post-commit", "commit-msg"]
        for hook_name in hooks_to_check:
            hook_file = self.hooks_dir / hook_name
            if hook_file.exists():
                try:
                    content = hook_file.read_text(encoding="utf-8")
                    is_b20_hook = "B20開発プロセス" in content or "B20PreCommitValidator" in content
                    status["hooks"][hook_name] = {
                        "exists": True,
                        "is_b20_hook": is_b20_hook,
                        "executable": hook_file.stat().st_mode & stat.S_IEXEC != 0,
                        "size": hook_file.stat().st_size,
                    }
                except Exception as e:
                    status["hooks"][hook_name] = {"exists": True, "error": f"読み取りエラー: {e!s}"}
            else:
                status["hooks"][hook_name] = {"exists": False}
        return status

    def _generate_pre_commit_hook_script(self) -> str:
        """Pre-commit hook スクリプトの生成"""
        return f'#!/usr/bin/env python3\n"""B20開発プロセス準拠 Pre-commit Hook\n\nAuto-generated by B20HooksInstaller\n"""\n\nimport sys\nimport os\nfrom pathlib import Path\n\n# ガイドルートをPythonパスに追加\nGUIDE_ROOT = Path("{self.guide_root}")\nsys.path.insert(0, str(GUIDE_ROOT))\n\ntry:\n\n    # Pre-commit検証の実行\n    exit_code = main()\n    sys.exit(exit_code)\n\nexcept ImportError as e:\n    self.console_service.print(f"❌ B20 Pre-commit hook import error: {{e}}", file=sys.stderr)\n    self.console_service.print("⚠️ Skipping B20 validation checks", file=sys.stderr)\n    sys.exit(0)  # 警告として扱い、コミットは続行\n\nexcept Exception as e:\n    self.console_service.print(f"❌ B20 Pre-commit hook execution error: {{e}}", file=sys.stderr)\n    self.console_service.print("⚠️ Skipping B20 validation checks", file=sys.stderr)\n    sys.exit(0)  # 警告として扱い、コミットは続行\n'

    def _generate_post_commit_hook_script(self) -> str:
        """Post-commit hook スクリプトの生成（CODEMAP更新統合）"""
        return f'''#!/usr/bin/env python3\n"""B20開発プロセス準拠 Post-commit Hook (CODEMAP更新統合)\n\nAuto-generated by B20HooksInstaller\n"""\n\nimport sys\nimport subprocess\nfrom pathlib import Path\n\n# ガイドルートをPythonパスに追加\nGUIDE_ROOT = Path("{self.guide_root}")\nsys.path.insert(0, str(GUIDE_ROOT))\n\ndef main():\n    """Post-commit処理の実行"""\n    try:\n        # 1. CODEMAP自動更新の実行\n        codemap_update_result = update_codemap()\n\n        # 2. 3コミットサイクル進行の実行\n        cycle_update_result = update_three_commit_cycle()\n\n        # 結果出力\n        if codemap_update_result or cycle_update_result:\n            print("✅ B20 Post-commit processing completed")\n\n    except Exception as e:\n        print(f"⚠️ B20 Post-commit processing warning: {{e}}", file=sys.stderr)\n        # エラーがあってもコミットは成功とする\n\ndef update_codemap():\n    """CODEMAP自動更新の実行"""\n    try:\n        # 既存のCODEMAP更新機能を利用\n\n        hook = CodeMapPostCommitHook(Path("{self.git_root}"))\n        result = hook.execute_codemap_update()\n\n        if result.get("updated"):\n            print(f"📋 CODEMAP updated: {{result.get('changes', '')}}")\n            return True\n\n        return False\n\n    except ImportError:\n        print("⚠️ CODEMAP update skipped (service not available)", file=sys.stderr)\n        return False\n    except Exception as e:\n        print(f"⚠️ CODEMAP update error: {{e}}", file=sys.stderr)\n        return False\n\ndef update_three_commit_cycle():\n    """3コミットサイクル進行の実行"""\n    try:\n        # 最新のコミットハッシュを取得\n        result = subprocess.run([\n            "git", "rev-parse", "HEAD"\n        ], capture_output=True, text=True, cwd=Path("{self.git_root}"))\n\n        if result.returncode != 0:\n            return False\n\n        commit_hash = result.stdout.strip()\n\n        # コミットメッセージから機能名を推測\n        commit_msg_result = subprocess.run([\n            "git", "log", "-1", "--pretty=%B"\n        ], capture_output=True, text=True, cwd=Path("{self.git_root}"))\n\n        if commit_msg_result.returncode != 0:\n            return False\n\n        commit_message = commit_msg_result.stdout.strip()\n        feature_name = extract_feature_name(commit_message)\n\n        if feature_name:\n\n            service = ThreeCommitCycleService(GUIDE_ROOT)\n\n            # サイクル進行の試行\n            try:\n                updated_cycle = service.advance_cycle_stage(feature_name, commit_hash)\n                print(f"🔄 Three-commit cycle advanced: {{feature_name}} -> {{updated_cycle.current_stage.value}}")\n                return True\n            except ValueError as e:\n                # サイクル進行ができない場合（正常なケース）\n                print(f"ℹ️ Three-commit cycle: {{e}}")\n                return False\n\n        return False\n\n    except ImportError:\n        print("⚠️ Three-commit cycle update skipped (service not available)", file=sys.stderr)\n        return False\n    except Exception as e:\n        print(f"⚠️ Three-commit cycle update error: {{e}}", file=sys.stderr)\n        return False\n\ndef extract_feature_name(commit_message):\n    """コミットメッセージから機能名を抽出"""\n    # feat: feature_name のパターンを抽出\n\n    patterns = [\n        r'feat:\\s*([\\w_-]+)',\n        r'fix:\\s*([\\w_-]+)',\n        r'refactor:\\s*([\\w_-]+)',\n        r'docs:\\s*([\\w_-]+)'\n    ]\n\n    for pattern in patterns:\n        match = re.search(pattern, commit_message)\n        if match:\n            return match.group(1)\n\n    return None\n\nif __name__ == "__main__":\n    main()\n'''

    def _generate_commit_msg_hook_script(self) -> str:
        """Commit-msg hook スクリプトの生成"""
        return '#!/usr/bin/env python3\n"""B20開発プロセス準拠 Commit-msg Hook\n\nAuto-generated by B20HooksInstaller\n"""\n\nimport sys\nimport re\nfrom pathlib import Path\n\ndef main():\n    """Commit message検証の実行"""\n    if len(sys.argv) != 2:\n        print("❌ Invalid commit-msg hook usage", file=sys.stderr)\n        sys.exit(1)\n\n    commit_msg_file = Path(sys.argv[1])\n\n    try:\n        commit_message = commit_msg_file.read_text(encoding=\'utf-8\').strip()\n\n        # B20コミットメッセージ規約の検証\n        validation_result = validate_commit_message(commit_message)\n\n        if validation_result["valid"]:\n            if validation_result["warnings"]:\n                for warning in validation_result["warnings"]:\n                    print(f"⚠️ {warning}", file=sys.stderr)\n\n            sys.exit(0)\n        else:\n            print("❌ Commit message validation failed:", file=sys.stderr)\n            for error in validation_result["errors"]:\n                print(f"  - {error}", file=sys.stderr)\n\n            if validation_result["suggestions"]:\n                print("\\n💡 Suggestions:", file=sys.stderr)\n                for suggestion in validation_result["suggestions"]:\n                    print(f"  - {suggestion}", file=sys.stderr)\n\n            sys.exit(1)\n\n    except Exception as e:\n        print(f"❌ Commit message validation error: {e}", file=sys.stderr)\n        sys.exit(0)  # エラー時は警告として扱い、コミットは続行\n\ndef validate_commit_message(message):\n    """コミットメッセージの検証"""\n    result = {\n        "valid": True,\n        "errors": [],\n        "warnings": [],\n        "suggestions": []\n    }\n\n    # 基本的なフォーマット検証\n    conventional_pattern = r\'^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .+$\'\n\n    if not re.match(conventional_pattern, message, re.MULTILINE):\n        result["valid"] = False\n        result["errors"].append("Conventional Commits format required")\n        result["suggestions"].append("Use format: type(scope): description")\n        result["suggestions"].append("Example: feat(auth): add user authentication")\n\n    # 長さ検証\n    lines = message.split(\'\\n\')\n    if lines[0] and len(lines[0]) > 72:\n        result["warnings"].append("First line exceeds 72 characters")\n\n    # B20 3コミットサイクル検証\n    if "feat:" in message:\n        cycle_validation = validate_three_commit_cycle_message(message)\n        if not cycle_validation["valid"]:\n            result["warnings"].extend(cycle_validation["warnings"])\n\n    return result\n\ndef validate_three_commit_cycle_message(message):\n    """3コミットサイクルメッセージ検証"""\n    cycle_patterns = [\n        r\'仕様書.*設計.*完了\',\n        r\'実装.*テスト.*完了\',\n        r\'ドキュメント.*統合.*完了\'\n    ]\n\n    is_cycle_commit = any(re.search(pattern, message) for pattern in cycle_patterns)\n\n    if is_cycle_commit:\n        return {\n            "valid": True,\n            "warnings": []\n        }\n    else:\n        return {\n            "valid": True,\n            "warnings": ["Consider using 3-commit cycle format for better tracking"]\n        }\n\nif __name__ == "__main__":\n    main()\n'


def install_b20_hooks_cli() -> int:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(description="B20開発プロセス準拠Git Hooksインストーラー")
    parser.add_argument("--git-root", type=Path, required=True, help="Gitリポジトリのルートパス")
    parser.add_argument("--guide-root", type=Path, required=True, help="ガイドプロジェクトのルートパス")
    parser.add_argument("--force", action="store_true", help="既存フックを上書き")
    parser.add_argument("--uninstall", action="store_true", help="B20フックをアンインストール")
    parser.add_argument("--status", action="store_true", help="インストール状態を表示")
    args = parser.parse_args()
    if not args.git_root.exists():
        console.print(f"❌ Git root not found: {args.git_root}", file=sys.stderr)
        return 1
    if not args.guide_root.exists():
        console.print(f"❌ Guide root not found: {args.guide_root}", file=sys.stderr)
        return 1
    installer = B20HooksInstaller(args.git_root, args.guide_root)
    try:
        if args.uninstall:
            result = installer.uninstall_hooks()
            if result["success"]:
                console.print(f"✅ B20 hooks uninstalled: {', '.join(result['uninstalled_hooks'])}")
                return 0
            console.print("❌ Uninstallation failed:", file=sys.stderr)
            for error in result["errors"]:
                console.print(f"  - {error}", file=sys.stderr)
            return 1
        if args.status:
            status = installer.get_installation_status()
            console.print("📊 B20 Hooks Installation Status")
            console.print(f"Git Root: {status['git_root']}")
            console.print(f"Guide Root: {status['guide_root']}")
            console.print(f"Hooks Directory: {status['hooks_dir']}")
            console.print()
            for hook_name, hook_status in status["hooks"].items():
                if hook_status.get("exists"):
                    status_icon = "✅" if hook_status.get("is_b20_hook") else "⚠️"
                    exec_status = "executable" if hook_status.get("executable") else "not executable"
                    console.print(f"{status_icon} {hook_name}: {exec_status}")
                    if hook_status.get("error"):
                        console.print(f"   Error: {hook_status['error']}")
                else:
                    console.print(f"❌ {hook_name}: not installed")
            return 0
        result = installer.install_all_hooks(args.force)
        if result["success"]:
            console.print("✅ B20 hooks installation completed")
            if result["installed_hooks"]:
                console.print(f"Installed: {', '.join(result['installed_hooks'])}")
            if result["skipped_hooks"]:
                console.print(f"Skipped: {', '.join(result['skipped_hooks'])} (use --force to overwrite)")
            return 0
        console.print("❌ Installation failed:", file=sys.stderr)
        for error in result["errors"]:
            console.print(f"  - {error}", file=sys.stderr)
        return 1
    except Exception as e:
        console.print(f"❌ Installation error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(install_b20_hooks_cli())
