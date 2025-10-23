"""軽量ファイル品質チェッカー(DDD準拠システム統合版)

構文チェックのみの高速ツール
CI/CDパイプライン・基本チェック用途
"""
import subprocess
import sys
from pathlib import Path


def check_file(file_path: str) -> bool:
    """ファイルをチェック"""
    path = Path(file_path)
    if not path.exists():
        return False
    if path.suffix != ".py":
        return True
    try:
        result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, check=False)
        return result.returncode == 0
    except Exception:
        return False
if __name__ == "__main__":
    from noveler.presentation.shared.shared_utilities import console
    if len(sys.argv) < 2:
        console.print("Usage: python simple_file_check.py <file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if check_file(file_path):
        console.print(f"✅ {file_path}: OK")
        sys.exit(0)
    else:
        console.print(f"❌ {file_path}: ERROR")
        sys.exit(1)
