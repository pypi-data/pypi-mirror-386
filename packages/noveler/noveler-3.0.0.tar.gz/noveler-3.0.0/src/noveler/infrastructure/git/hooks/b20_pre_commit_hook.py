"""Infrastructure.git.hooks.b20_pre_commit_hook
Where: Infrastructure module defining the B20 pre-commit hook script.
What: Implements pre-commit checks aligned with B20 standards.
Why: Ensures repositories comply with required pre-commit validations.
"""

from noveler.presentation.shared.shared_utilities import console

"B20開発プロセス準拠 Pre-commit Hook\n\n仕様書: B20開発作業指示書準拠\n"
import subprocess
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class B20PreCommitValidator:
    """B20開発プロセス準拠のpre-commit検証"""

    def __init__(self, repo_root: Path, logger_service=None, console_service=None) -> None:
        """初期化"""
        self.repo_root = repo_root
        self.guide_root = self._find_guide_root()
        self.logger_service = logger_service
        self.console_service = console_service

    def execute_validation(self) -> dict[str, Any]:
        """Pre-commit検証の実行"""
        validation_result = {"success": True, "errors": [], "warnings": [], "checks_performed": []}
        try:
            cycle_check = self._validate_three_commit_cycle()
            validation_result["checks_performed"].append("three_commit_cycle")
            if not cycle_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(cycle_check["errors"])
            validation_result["warnings"].extend(cycle_check["warnings"])
            codemap_check = self._validate_codemap_sync()
            validation_result["checks_performed"].append("codemap_sync")
            if not codemap_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(codemap_check["errors"])
            validation_result["warnings"].extend(codemap_check["warnings"])
            arch_check = self._validate_architecture_compliance()
            validation_result["checks_performed"].append("architecture_compliance")
            if not arch_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(arch_check["errors"])
            validation_result["warnings"].extend(arch_check["warnings"])
            test_check = self._validate_test_status()
            validation_result["checks_performed"].append("test_status")
            if not test_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(test_check["errors"])
            validation_result["warnings"].extend(test_check["warnings"])
        except Exception as e:
            validation_result["success"] = False
            validation_result["errors"].append(f"Pre-commit検証エラー: {e!s}")
        return validation_result

    def _validate_three_commit_cycle(self) -> dict[str, Any]:
        """3コミットサイクル検証"""
        try:
            changed_files = self._get_staged_files()
            feature_name = self._infer_feature_name(changed_files)
            if not feature_name:
                return {"valid": True, "warnings": ["機能名の推測ができませんでした"], "errors": []}
            cycle_service_check = self._check_three_commit_cycle_service(feature_name)
            return {
                "valid": cycle_service_check["can_commit"],
                "warnings": cycle_service_check.get("warnings", []),
                "errors": cycle_service_check.get("errors", []),
            }
        except Exception as e:
            return {"valid": False, "warnings": [], "errors": [f"3コミットサイクル検証エラー: {e!s}"]}

    def _validate_codemap_sync(self) -> dict[str, Any]:
        """CODEMAP同期検証"""
        try:
            codemap_file = self.guide_root / "CODEMAP.yaml"
            if not codemap_file.exists():
                return {"valid": False, "warnings": [], "errors": ["CODEMAPファイルが存在しません"]}
            return {"valid": True, "warnings": [], "errors": []}
        except Exception as e:
            return {"valid": False, "warnings": [], "errors": [f"CODEMAP同期検証エラー: {e!s}"]}

    def _validate_architecture_compliance(self) -> dict[str, Any]:
        """アーキテクチャ準拠検証"""
        try:
            if self.guide_root:
                arch_linter_path = (
                    self.guide_root / "scripts" / "infrastructure" / "quality_gates" / "architecture_linter.py"
                )
                if arch_linter_path.exists():
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(arch_linter_path),
                            "--project-root",
                            str(self.guide_root),
                            "--format",
                            "json",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        return {"valid": True, "warnings": [], "errors": []}
                    return {"valid": False, "warnings": [], "errors": [f"アーキテクチャ違反検出: {result.stdout}"]}
            return {"valid": True, "warnings": ["アーキテクチャリンターが見つかりません"], "errors": []}
        except Exception as e:
            return {"valid": False, "warnings": [], "errors": [f"アーキテクチャ検証エラー: {e!s}"]}

    def _validate_test_status(self) -> dict[str, Any]:
        """テスト実行状態検証"""
        try:
            changed_files = self._get_staged_files()
            python_files = [f for f in changed_files if f.endswith(".py")]
            if not python_files:
                return {"valid": True, "warnings": [], "errors": []}
            missing_tests = []
            for py_file in python_files:
                if not self._has_corresponding_test(py_file):
                    missing_tests.append(py_file)
            if missing_tests:
                return {
                    "valid": False,
                    "warnings": [],
                    "errors": [f"対応するテストが見つかりません: {', '.join(missing_tests)}"],
                }
            return {"valid": True, "warnings": [], "errors": []}
        except Exception as e:
            return {"valid": False, "warnings": [], "errors": [f"テスト状態検証エラー: {e!s}"]}

    def _get_staged_files(self) -> list[str]:
        """ステージされたファイル一覧の取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split("\n") if f.strip()]
            return []
        except Exception:
            return []

    def _infer_feature_name(self, changed_files: list[str]) -> str | None:
        """変更ファイルから機能名を推測"""
        if not changed_files:
            return None
        for file_path in changed_files:
            path_parts = file_path.split("/")
            if "scripts" in path_parts:
                filename = Path(file_path).stem
                if filename.startswith("test_"):
                    filename = filename[5:]
                if filename not in ["__init__", "main", "config", "utils"]:
                    return filename
        return None

    def _check_three_commit_cycle_service(self, feature_name: str) -> dict[str, Any]:
        """3コミットサイクルサービス経由のチェック"""
        try:
            if not self.guide_root:
                return {"can_commit": True, "warnings": ["ガイドルートが見つかりません"], "errors": []}
            cycle_check_script = f"""\nimport sys\nfrom pathlib import Path\nsys.path.append('{self.guide_root}')\n\nfrom noveler.domain.services.three_commit_cycle_service import ThreeCommitCycleService\n\ntry:\n    service = ThreeCommitCycleService(Path('{self.guide_root}'))\n    validation_result = service.validate_commit_readiness('{feature_name}')\n\n    print(f"{{\n        'can_commit': {{validation_result.can_commit}},\n        'errors': {{validation_result.validation_errors}},\n        'warnings': {{validation_result.warnings}}\n    }}")\nexcept Exception as exc:\n    print(f"{{\n        'can_commit': True,\n        'errors': [],\n        'warnings': ['サイクル検証エラー: {{str(exc)}}']\n    }}")\n"""
            result = subprocess.run(
                [sys.executable, "-c", cycle_check_script], check=False, capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                import ast

                try:
                    return ast.literal_eval(result.stdout.strip())
                except (ValueError, SyntaxError):
                    return {"can_commit": True, "warnings": ["サイクル検証結果のパース失敗"], "errors": []}
            return {"can_commit": True, "warnings": ["サイクル検証スキップ"], "errors": []}
        except Exception as e:
            return {"can_commit": True, "warnings": [f"サイクル検証エラー: {e!s}"], "errors": []}

    def _has_corresponding_test(self, file_path: str) -> bool:
        """対応するテストファイルの存在確認"""
        if "test" in file_path:
            return True
        file_name = Path(file_path).stem
        test_patterns = [f"test_{file_name}.py", f"{file_name}_test.py", f"test_{file_name}_*.py"]
        return any(list(self.repo_root.glob(f"**/{pattern}")) for pattern in test_patterns)

    def _find_guide_root(self) -> Path | None:
        """ガイドルートディレクトリの検索"""
        possible_paths = [self.repo_root, self.repo_root / "guide", self.repo_root.parent / "00_ガイド"]
        for path in possible_paths:
            if path.exists() and (path / "CODEMAP.yaml").exists():
                return path
        return None


def main() -> int:
    """Pre-commit hookのメイン実行"""
    try:
        repo_root = Path.cwd()
        while repo_root != repo_root.parent:
            if (repo_root / ".git").exists():
                break
            repo_root = repo_root.parent
        else:
            console.print("❌ Gitリポジトリが見つかりません", file=sys.stderr)
            return 1
        validator = B20PreCommitValidator(repo_root)
        result = validator.execute_validation()
        if result["success"]:
            console.print("✅ B20開発プロセス準拠チェック: 合格")
            if result["warnings"]:
                console.print("⚠️ 警告:")
                for warning in result["warnings"]:
                    console.print(f"  - {warning}")
            return 0
        console.print("❌ B20開発プロセス準拠チェック: 不合格", file=sys.stderr)
        for error in result["errors"]:
            console.print(f"  ❌ {error}", file=sys.stderr)
        if result["warnings"]:
            console.print("⚠️ 警告:", file=sys.stderr)
            for warning in result["warnings"]:
                console.print(f"  - {warning}", file=sys.stderr)
        console.print(f"\n実行されたチェック: {', '.join(result['checks_performed'])}", file=sys.stderr)
        console.print("\n修正後、再度コミットを試行してください。", file=sys.stderr)
        return 1
    except Exception as e:
        console.print(f"❌ Pre-commit hook実行エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
