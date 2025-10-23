# 開発支援ツール群

## 概要
本ディレクトリには、プロジェクトの開発効率化とコード品質向上のための自動化ツールが格納されています。
これらのツールはDDD準拠のアプリケーション本体とは別管理される開発支援用ツールです。

## ツール一覧

### 1. batch_test_generator.py
**一括テスト生成ツール**
- 未テストモジュールの自動検出
- SPEC準拠テストファイルの一括生成
- DDD準拠テンプレート適用
- 依存関係モックの自動生成

使用例：
```bash
python -m scripts.tools.batch_test_generator --template ddd_compliant
```

### 2. spec_marker_injector.py
**SPEC準拠マーカー自動注入ツール**
- 既存テストファイルへのSPECマーカー自動付与
- pytest.mark.spec()の自動追加
- テスト関数の分類・命名規約準拠
- バックアップとロールバック機能

使用例：
```bash
python -m scripts.tools.spec_marker_injector --dry-run
```

### 3. ddd_violation_fixer.py
**DDD違反自動検出・修正ツール**
- レイヤー違反の検出と修正
- 依存性注入パターンの提案
- TYPE_CHECKINGパターンの適用
- 循環インポートの検出

使用例：
```bash
python -m scripts.tools.ddd_violation_fixer --dry-run --confidence-threshold 0.9
```

## 品質ステータス

### Ruffチェック結果
- ✅ 型ヒント更新完了（List→list, Dict→dict）
- ✅ インポート順序の整理
- ✅ 未使用インポートの削除
- ⚠️ ログ出力のf-string警告（動作に影響なし）
- ⚠️ datetimeのタイムゾーン未指定（改善推奨）

### 改善推奨事項
1. ログ出力を`logger.info("メッセージ", extra={"value": value})`形式に変更
2. `datetime.now(timezone.utc)`でタイムゾーンを明示
3. エラーハンドリングで`logger.exception()`を使用

## 使用上の注意

### インポート方法
これらのツールは開発支援用のため、以下のfallbackパターンを使用：

```python
try:
    from noveler.infrastructure.logging.unified_logger import get_logger
    logger = get_logger(__name__)
except Exception:
    # Fallback: minimal stderr logger without importing `logging`
    class _Stub:
        def info(self, *a, **k):
            try:
                import sys as _sys
                _sys.stderr.write(str(a[0] if a else "") + "
")
            except Exception:
                pass
        warning = info
        error = info
        debug = info
    logger = _Stub()
```

### 実行環境
- Python 3.9以上推奨
- プロジェクトルートから実行すること
- 本番環境では使用しないこと

## メンテナンス

### 品質チェック
```bash
# Ruffによる品質チェック
python -m ruff check scripts/tools/*.py

# 自動修正
python -m ruff check scripts/tools/*.py --fix
```

### テスト実行
```bash
# ツールの動作確認
python -c "from noveler.tools.batch_test_generator import BatchTestGenerator; print('OK')"
```

## ライセンス
プロジェクト本体のライセンスに準拠

## 更新履歴
- 2025-08-27: 初版作成、Ruff準拠の改善実施
- 2025-08-27: 型ヒント更新、インポート整理完了
