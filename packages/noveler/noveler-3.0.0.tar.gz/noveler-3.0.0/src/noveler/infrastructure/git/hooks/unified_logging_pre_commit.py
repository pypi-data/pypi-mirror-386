#!/usr/bin/env python3
"""統一ロギングPre-commitフック

新規コードでのレガシーロギング使用を防ぐpre-commitフック
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


def get_staged_python_files() -> list[str]:
    """ステージされたPythonファイルを取得"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True, check=True
        )

        python_files = []
        for file_path in result.stdout.strip().split("\n"):
            if file_path and file_path.endswith(".py"):
                # scriptsディレクトリ内のファイルのみ対象
                if file_path.startswith("noveler/"):
                    python_files.append(file_path)

        return python_files

    except subprocess.CalledProcessError:
        logger.exception("Gitステージファイルの取得に失敗")
        return []


def check_staged_files() -> bool:
    """ステージされたファイルの統一ロギング使用チェック"""
    staged_files = get_staged_python_files()

    if not staged_files:
        return True  # Python ファイルがステージされていない場合はスキップ

    logger.info("統一ロギングチェック: %s ファイル", len(staged_files))

    # 統一ロギング品質ゲート実行
    try:
        from noveler.infrastructure.quality_gates.unified_logging_gate import UnifiedLoggingGate

        project_root = Path.cwd()
        gate = UnifiedLoggingGate(project_root)

        # ステージされたファイルのみチェック
        violations: list[Any] = []
        for file_path in staged_files:
            full_path = project_root / file_path
            if full_path.exists():
                file_violations = gate.check_file(full_path)
                if file_violations:
                    violations.extend([(file_path, v) for v in file_violations])

        if violations:
            logger.error("❌ レガシーロギング検出 - コミット阻止")
            for file_path, (line_num, line, description) in violations:
                logger.error("  %s:%s - %s", file_path, line_num, description)
                logger.error("    %s", line)

            logger.info("修正方法:")
            logger.info("  python scripts/infrastructure/tools/logging_migration_tool.py --execute")
            return False
        logger.info("✅ 統一ロギングチェック: パス")
        return True

    except ImportError:
        logger.warning("統一ロギング品質ゲートが利用できません")
        return True


def main() -> None:
    """Pre-commitフックメイン処理"""
    logger.info("=== 統一ロギングPre-commitフック ===")

    success = check_staged_files()

    if not success:
        logger.error("Pre-commitフック: 失敗")
        sys.exit(1)

    logger.info("Pre-commitフック: 成功")
    sys.exit(0)


if __name__ == "__main__":
    main()
