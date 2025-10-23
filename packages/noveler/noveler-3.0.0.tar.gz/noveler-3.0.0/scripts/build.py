#!/usr/bin/env python3
"""
本番用ビルドスクリプト（復活版）
Development to Production Build Script

開発用src/コードから本番用dist/への配布を作成
- MCPサーバー統合対応
- 依存関係チェック
- テスト実行
- 本番用パッケージ作成
- 既存MCPサーバープロセスの停止（必要に応じて起動）
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート（scripts/ の1つ上のディレクトリをプロジェクトルートとみなす）
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def setup_logging():
    """統一ロガー設定（スクリプト用）"""
    # scripts配下からでも import 可能に
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from noveler.infrastructure.logging.unified_logger import (
        configure_logging,
        get_logger,
        LogFormat,
    )
    # ビルドスクリプトは人向け出力優先（Rich）、詳細はINFO
    configure_logging(console_format=LogFormat.RICH, verbose=1)
    return get_logger(__name__)

logger = setup_logging()

def clean_build_directories():
    """ビルドディレクトリのクリーン"""
    logger.info("🧹 ビルドディレクトリをクリーン中...")

    dirs_to_clean = [DIST_DIR, BUILD_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            logger.info(f"   削除: {dir_path}")

    # 作成
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    logger.info("✅ ビルドディレクトリクリーン完了")

def run_tests():
    """テスト実行"""
    logger.info("🧪 テスト実行中...")

    test_command = [sys.executable, "-m", "pytest", "-v", "tests/"]
    result = subprocess.run(
        test_command,
        check=False, cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("❌ テストが失敗しました")
        logger.error(result.stdout)
        logger.error(result.stderr)
        return False

    logger.info("✅ テスト成功")
    return True

def copy_source_code():
    """ソースコード複製"""
    logger.info("📄 ソースコードを本番用にコピー中...")

    # src/noveler → dist/noveler
    src_noveler = SRC_DIR / "noveler"
    dist_noveler = DIST_DIR / "noveler"

    if src_noveler.exists():
        # 既存ディレクトリがあれば安全に置き換え
        if dist_noveler.exists():
            shutil.rmtree(dist_noveler)
        shutil.copytree(
            src_noveler,
            dist_noveler,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            dirs_exist_ok=False,
        )
        logger.info(f"   コピー: {src_noveler} → {dist_noveler}")

    # src/mcp_servers → dist/mcp_servers
    src_mcp = SRC_DIR / "mcp_servers"
    dist_mcp = DIST_DIR / "mcp_servers"

    if src_mcp.exists():
        # 既存ディレクトリがあれば安全に置き換え
        if dist_mcp.exists():
            shutil.rmtree(dist_mcp)
        shutil.copytree(
            src_mcp,
            dist_mcp,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            dirs_exist_ok=False,
        )
        logger.info(f"   コピー: {src_mcp} → {dist_mcp}")

    logger.info("✅ ソースコードコピー完了")

def create_production_entry_points():
    """本番用エントリーポイント作成"""
    logger.info("🚀 本番用エントリーポイント作成中...")

    # bin/noveler（本番用）
    production_noveler_script = '''#!/usr/bin/env python3
"""
小説執筆支援システム統合CLI（本番版）
Novel Writing Support System Integrated CLI (Production)

本番モード：
- dist/ディレクトリの安定版コードを使用
- MCPサーバー専用エントリーポイント
- プロダクション最適化
"""

import os
import sys
import subprocess
from pathlib import Path

# 本番用フラグを設定
os.environ["NOVEL_PRODUCTION_MODE"] = "1"

# ガイドルートを特定
def find_guide_root():
    """ガイドルート（00_ガイド）を確実に特定"""
    current_file = Path(__file__).resolve()

    # bin/novelerからの相対パス
    if current_file.name == "noveler" and current_file.parent.name == "bin":
        return current_file.parent.parent

    # フォールバック
    return current_file.parent.parent

BASE_DIR = find_guide_root()

# 本番用ディストリビューションのパス
DIST_DIR = BASE_DIR / "dist"
MAIN_SCRIPT = DIST_DIR / "noveler" / "main.py"

# 本番モード表示
print("🏭 本番モードで実行中 - 安定版コードを使用しています")
print("")

# dist/パスの設定
if DIST_DIR.exists():
    os.environ["PYTHONPATH"] = f"{str(DIST_DIR)}:{os.environ.get('PYTHONPATH', '')}"
    os.environ["GUIDE_ROOT"] = str(BASE_DIR)
    os.environ["NOVEL_USE_DIST"] = "1"  # dist/ディレクトリ使用フラグ

# 本番用main.pyの実行
try:
    result = subprocess.run([sys.executable, str(MAIN_SCRIPT)] + sys.argv[1:])
    sys.exit(result.returncode)
except Exception as e:
    print(f"❌ 本番用novelerコマンド実行エラー: {e}")
    sys.exit(1)
'''

    bin_noveler = PROJECT_ROOT / "bin" / "noveler"
    # 親ディレクトリが無ければ作成
    bin_noveler.parent.mkdir(parents=True, exist_ok=True)
    bin_noveler.write_text(production_noveler_script, encoding="utf-8")
    bin_noveler.chmod(0o755)

    logger.info(f"   作成: {bin_noveler} （本番用エントリーポイント）")

    logger.info("✅ 本番用エントリーポイント作成完了")

def create_production_mcp_config():
    """本番用MCP設定作成

    Uses the same SSOT (Single Source of Truth) function as setup_mcp_configs.py
    to ensure consistent environment detection and path resolution across
    development and production builds.
    """
    logger.info("⚙️ 本番用MCP設定作成中...")

    # Import the SSOT function from setup scripts
    sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "setup"))
    try:
        from update_mcp_configs import ensure_mcp_server_entry
    finally:
        sys.path.pop(0)

    # Generate using the SSOT function with explicit production environment
    # This ensures dist-only deployments are correctly configured
    server_entry = ensure_mcp_server_entry(
        PROJECT_ROOT,
        name="Noveler MCP",
        description="小説執筆支援システム（本番版MCPサーバー）",
        env="production"  # Explicitly request production config
    )

    production_mcp_config = {
        "mcpServers": {
            "noveler": server_entry
        }
    }

    # .mcp.production.json として保存
    production_mcp_file = PROJECT_ROOT / ".mcp.production.json"
    production_mcp_file.write_text(
        json.dumps(production_mcp_config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    logger.info(f"   作成: {production_mcp_file}")
    logger.info("   💡 本番環境では .mcp.production.json を .mcp.json にリネームしてください")

    logger.info("✅ 本番用MCP設定作成完了")

def create_build_manifest():
    """ビルド情報ファイル作成"""
    logger.info("📋 ビルド情報ファイル作成中...")

    build_info = {
        "build_time": datetime.now().isoformat(),
        "version": "2.0.0-production",
        "source_directory": "src/",
        "output_directory": "dist/",
        "mode": "production",
        "python_version": sys.version,
        "platform": sys.platform,
        "features": [
            "MCP Server Integration",
            "JSON Conversion",
            "Novel Writing Support",
            "Quality Gate System"
        ]
    }

    manifest_file = DIST_DIR / "BUILD_MANIFEST.json"
    manifest_file.write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    logger.info(f"   作成: {manifest_file}")
    logger.info("✅ ビルド情報ファイル作成完了")

def verify_build():
    """ビルド検証"""
    logger.info("🔍 ビルド検証中...")

    required_files = [
        DIST_DIR / "noveler" / "main.py",
        DIST_DIR / "mcp_servers" / "noveler" / "main.py",
        DIST_DIR / "BUILD_MANIFEST.json",
        PROJECT_ROOT / "bin" / "noveler",
        PROJECT_ROOT / ".mcp.production.json"
    ]

    missing_files = []
    for required_file in required_files:
        if not required_file.exists():
            missing_files.append(required_file)

    if missing_files:
        logger.error("❌ ビルド検証失敗 - 以下のファイルが見つかりません:")
        for missing_file in missing_files:
            logger.error(f"   - {missing_file}")
        return False

    logger.info("✅ ビルド検証成功")
    return True


def _find_mcp_server_processes():
    """現在動作中のMCPサーバープロセス(noveler)を列挙

    戻り値: list[tuple[pid:int, cmdline:list[str]]]
    """
    procs = []
    try:
        import psutil  # type: ignore

        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = p.info.get("cmdline") or []
                # 一部環境ではcmdlineが取得できないことがある
                cmd_text = " ".join(cmd).lower() if isinstance(cmd, list) else str(cmd).lower()
                if (
                    "mcp_servers" in cmd_text
                    and "noveler" in cmd_text
                    and "main.py" in cmd_text
                ):
                    procs.append((p.pid, cmd if isinstance(cmd, list) else [cmd_text]))
            except Exception:
                continue
    except Exception:
        # psutilが無い環境ではベストエフォート（非対応）
        logger.warning("psutil未利用のため、既存MCPプロセスの自動検出はスキップします")
    return procs


def stop_existing_mcp_servers(timeout_seconds: float = 5.0) -> int:
    """既存のMCPサーバープロセス(noveler)を停止

    Returns: 停止したプロセス数
    """
    stopped = 0
    try:
        import psutil  # type: ignore

        targets = _find_mcp_server_processes()
        if not targets:
            logger.info("🔎 停止対象のMCPサーバープロセスは検出されませんでした")
            return 0

        for pid, cmd in targets:
            try:
                proc = psutil.Process(pid)
                logger.info(f"🛑 停止: PID={pid} CMD={' '.join(cmd)[:120]}")
                proc.terminate()
            except Exception:
                continue

        # 待機と強制終了
        psutil.wait_procs([psutil.Process(pid) for pid, _ in targets], timeout=timeout_seconds)
        for pid, cmd in targets:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    proc.kill()
            except Exception:
                pass
        stopped = len(targets)
    except Exception as e:
        logger.warning(f"MCPサーバー停止処理で警告: {e}")
    return stopped


def start_mcp_server(use_dist: bool = True) -> bool:
    """MCPサーバー(noveler)を起動

    use_dist=True の場合、dist/mcp_servers/noveler/main.py を直接起動
    """
    try:
        env = dict(**os.environ)
        env.setdefault("PYTHONUNBUFFERED", "1")
        env["NOVEL_PRODUCTION_MODE"] = "1"
        if use_dist:
            # distを優先使用
            env["NOVEL_USE_DIST"] = "1"
            env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
            target = DIST_DIR / "mcp_servers" / "noveler" / "main.py"
        else:
            target = SRC_DIR / "mcp_servers" / "noveler" / "main.py"

        if not target.exists():
            logger.error(f"MCPサーバー起動ターゲットが見つかりません: {target}")
            return False

        # 二重起動防止: 既に同種のMCPサーバーが稼働中なら起動しない
        existing = _find_mcp_server_processes()
        if existing:
            logger.info("♻️ 既にMCPサーバーが稼働中のため新規起動をスキップします")
            return True

        cmd = [sys.executable, str(target)]
        logger.info(f"🚀 MCPサーバー起動: {' '.join(cmd)}")
        subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env)
        return True
    except Exception as e:
        logger.error(f"MCPサーバー起動に失敗: {e}")
        return False

def main():
    """メインビルドプロセス"""
    logger.info("🏗️ 本番用ビルド開始")
    logger.info("=" * 60)

    try:
        # 1. ビルドディレクトリクリーン
        clean_build_directories()

        # 2. テスト実行（optional - テストが失敗しても続行）
        logger.info("\n" + "-" * 40)
        if not run_tests():
            logger.warning("⚠️ テストが失敗しましたが、ビルドを続行します")

        # 3. ソースコードコピー
        logger.info("\n" + "-" * 40)
        copy_source_code()

        # 4. 本番用エントリーポイント作成
        logger.info("\n" + "-" * 40)
        create_production_entry_points()

        # 5. 本番用MCP設定作成
        logger.info("\n" + "-" * 40)
        create_production_mcp_config()

        # 6. ビルド情報ファイル作成
        logger.info("\n" + "-" * 40)
        create_build_manifest()

        # 7. ビルド検証
        logger.info("\n" + "-" * 40)
        if not verify_build():
            logger.error("❌ ビルド検証失敗")
            return 1

        # 8. MCPサーバー再起動（デフォルト有効）
        logger.info("\n" + "-" * 40)
        logger.info("🔁 MCPサーバーを再起動します（既存プロセスの停止→起動）")
        stopped = stop_existing_mcp_servers()
        if stopped:
            logger.info(f"   停止したプロセス: {stopped}件")
        else:
            logger.info("   停止対象なし、または検出不可")
        autostart = os.environ.get("NOVELER_AUTOSTART_MCP", "0").strip().lower() not in ("0", "false", "off", "no", "")
        if autostart:
            if start_mcp_server(use_dist=True):
                logger.info("✅ MCPサーバー再起動完了")
            else:
                logger.warning("⚠️ MCPサーバーの起動に失敗しました。必要に応じて手動で起動してください。")
        else:
            logger.info("⏭️  MCP自動起動はスキップしました（NOVELER_AUTOSTART_MCP=1 で有効化可能）")

        # 完了レポート
        logger.info("\n" + "=" * 60)
        logger.info("🎉 本番用ビルド完了!")
        logger.info("")
        logger.info("📁 生成されたファイル:")
        logger.info(f"   📦 本番用コード: {DIST_DIR}/")
        logger.info("   🚀 本番用実行ファイル: bin/noveler")
        logger.info("   ⚙️ 本番用MCP設定: .mcp.production.json")
        logger.info("")
        logger.info("💡 次のステップ:")
        logger.info("   1. 本番環境では bin/noveler を使用")
        logger.info("   2. Claude Code使用時は .mcp.production.json を .mcp.json にリネーム")
        logger.info("   3. MCPサーバーは必要に応じて自動起動（環境変数で有効化）します。未起動なら手動で起動してください。")

        return 0

    except Exception as e:
        logger.error(f"❌ ビルドエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
