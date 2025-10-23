"""Domain.services.dependency_repair_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from pathlib import Path

from noveler.domain.utils.domain_console import console

"依存関係修復サービス\n\nシステム修復の依存関係処理専用ドメインサービス\n"
import subprocess
import sys


class DependencyRepairService:
    """依存関係修復専用サービス"""

    def repair_dependencies(self, deps_check: dict, dry_run: bool = False, quiet: bool = False) -> dict:
        """依存関係の修復

        Args:
            deps_check: 依存関係チェック結果
            dry_run: ドライラン実行
            quiet: 静寂モード

        Returns:
            dict: 修復結果
        """
        result = {"success": True, "repairs_made": [], "repairs_failed": [], "packages_installed": []}
        if deps_check.get("status") != "ERROR":
            return result
        missing_packages = self._extract_missing_packages(deps_check)
        if not missing_packages:
            return result
        if not quiet:
            console.print("\n📦 不足しているパッケージをインストール...")
        req_result = self._update_requirements_file(dry_run, quiet)
        if req_result["success"]:
            result["repairs_made"].extend(req_result["repairs_made"])
        else:
            result["repairs_failed"].extend(req_result["repairs_failed"])
        install_result = self._install_packages(missing_packages, dry_run, quiet)
        result["packages_installed"] = install_result["packages_installed"]
        result["repairs_made"].extend(install_result["repairs_made"])
        result["repairs_failed"].extend(install_result["repairs_failed"])
        if install_result["repairs_failed"]:
            result["success"] = False
        return result

    def _extract_missing_packages(self, deps_check: dict) -> list[str]:
        """不足パッケージを抽出"""
        missing_packages = []
        required_packages = deps_check.get("details", {}).get("required_packages", {})
        for package, status in required_packages.items():
            if status == "Missing":
                missing_packages.append(package)
        return missing_packages

    def _update_requirements_file(self, dry_run: bool, quiet: bool) -> dict:
        """requirements.txtファイルの更新"""
        result = {"success": True, "repairs_made": [], "repairs_failed": []}
        Path("requirements.txt")  # TODO: IPathServiceを使用するように修正
        if dry_run:
            if not quiet:
                console.print("  💡 実行するアクション: requirements.txt を生成")
            result["repairs_made"].append("requirements.txt生成予定")
            return result
        try:
            self._create_requirements_file()
            result["repairs_made"].append("requirements.txt を作成しました")
            if not quiet:
                console.print("  ✅ requirements.txt を作成しました")
        except Exception as e:
            error_msg = f"requirements.txt作成失敗: {e}"
            result["repairs_failed"].append(error_msg)
            result["success"] = False
            if not quiet:
                console.print(f"  ❌ {error_msg}")
        return result

    def _install_packages(self, packages: list[str], dry_run: bool, quiet: bool) -> dict:
        """パッケージのインストール"""
        result = {"success": True, "packages_installed": [], "repairs_made": [], "repairs_failed": []}
        if dry_run:
            if not quiet:
                console.print(f"  💡 実行するコマンド: pip install {' '.join(packages)}")
            result["repairs_made"].append(f"パッケージインストール予定: {', '.join(packages)}")
            return result
        for package in packages:
            install_result = self._install_package_safely(package, quiet)
            if install_result["success"]:
                result["packages_installed"].append(package)
                result["repairs_made"].append(f"パッケージ '{package}' をインストールしました")
            else:
                result["repairs_failed"].append(install_result["error"])
                result["success"] = False
        return result

    def _install_package_safely(self, package: str, quiet: bool) -> dict:
        """安全なパッケージインストール"""
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package], capture_output=True, text=True, check=True
            )
            if not quiet:
                console.print(f"  ✅ {package} をインストールしました")
            return {"success": True}
        except subprocess.CalledProcessError as e:
            error_msg = f"パッケージ '{package}' のインストールに失敗: {e}"
            if not quiet:
                console.print(f"  ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def _create_requirements_file(self) -> None:
        """requirements.txtファイルの作成"""
        requirements_content = "# 小説執筆支援システム 必須パッケージ\n# 基本依存関係\npyyaml>=6.0\nrequests>=2.28.0\njanome>=0.4.0\n\n# オプション依存関係(推奨)\nbeautifulsoup4>=4.11.0\nlxml>=4.9.0\nmarkdown>=3.4.0\njinja2>=3.1.0\n\n# 開発依存関係\npytest>=7.0.0\npytest-cov>=4.0.0\nblack>=22.0.0\nruff>=0.1.0\nmypy>=1.0.0\n"
        requirements_path = Path("requirements.txt")  # TODO: IPathServiceを使用するように修正
        with requirements_path.open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            f.write(requirements_content)
