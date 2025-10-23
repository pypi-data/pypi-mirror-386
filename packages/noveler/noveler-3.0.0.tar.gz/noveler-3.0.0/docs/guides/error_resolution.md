# エラー解決ガイド

## 🚨 よくあるエラーと解決法

最短のフィードバックを得たい場合は次を試してください：

```bash
make test-last      # 直近で失敗したテストを優先実行（-x）
```

### ModuleNotFoundError: No module named 'scripts'
```bash
# 解決法
export PYTHONPATH=$PWD
# または
PYTHONPATH=$PWD python your_script.py
```

### pytest collection failed
```bash
# 解決法1: パスを明示指定
PYTHONPATH=$PWD pytest tests/

# 解決法2: __init__.pyファイル確認
find tests/ -name "__init__.py" | head -5
```

### DDD違反エラー
```bash
# 解決法
python scripts/tools/check_tdd_ddd_compliance.py
# 詳細は CLAUDE.md を参照
```

### Import循環参照エラー
```python
# 解決パターン: TYPE_CHECKINGを使用
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.domain.interfaces.service import IService

logger: "IService | None" = None  # 依存性注入
```

### カバレッジ不足エラー
```bash
# 現状分析
python scripts/tools/test_coverage_analyzer.py

# テスト作成
mkdir -p tests/unit/application/services/
# テストファイルを作成
```

## 🛠️ デバッグコマンド
```bash
# システム状態確認
ncheck                    # 品質チェック
ncoverage                # カバレッジ分析
ntest -v                 # 詳細テスト実行

# ログ確認
tail -f temp/logs/*.log  # ログファイル監視
```

## 📞 サポート
- エラーが解決しない場合は `docs/B20_Claude_Code開発作業指示書.md` を参照
- システム改善が必要な場合は `/serena "改善可能な箇所を改善して" -d -s -c` を実行
# LLM用途で要約が必要な場合（推奨ランナー）
bin/test -q
# LLM最小出力（JSON要約のみ）
bin/test-json -q
# fail-only NDJSON を無効化したい場合
LLM_REPORT_STREAM_FAIL=0 bin/test -q
