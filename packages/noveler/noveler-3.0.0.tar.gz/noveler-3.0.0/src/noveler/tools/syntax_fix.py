#!/usr/bin/env python3
"""統合構文エラー修正ツール（簡易インターフェース）

DDD準拠の実装に対する簡単なコマンドラインアクセスポイント。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from noveler.presentation.cli.commands.fix_syntax_command import main

if __name__ == "__main__":
    main()
