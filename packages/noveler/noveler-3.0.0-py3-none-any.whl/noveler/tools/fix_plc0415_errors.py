#!/usr/bin/env python3
"""PLC0415: import-outside-top-level エラーを分析"""

import subprocess

from noveler.presentation.shared.shared_utilities import console

def main():
    """メイン処理"""

    console.print("=== Analyzing PLC0415: import-outside-top-level errors ===")

    # 現在のエラー数を確認
    result = subprocess.run(
        ["ruff", "check", "scripts", "--select", "PLC0415", "--output-format", "concise"],
        check=False, capture_output=True,
        text=True
    )

    errors = result.stdout.strip().split("\n") if result.stdout.strip() else []
    console.print(f"Total PLC0415 errors: {len(errors)}")

    console.print("\n⚠️ PLC0415エラーの多くは循環インポート防止のための遅延インポートです。")
    console.print("これらは意図的なものが多いため、自動修正は推奨されません。")

if __name__ == "__main__":
    main()
