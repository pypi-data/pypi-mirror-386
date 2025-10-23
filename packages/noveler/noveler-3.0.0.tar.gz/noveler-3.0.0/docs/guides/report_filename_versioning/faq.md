# Report Filename Versioning — FAQ

## Q1. バージョンなしと `v1` の違いは？
- **バージョンなし**: 最新・デフォルト版を指す。
- **`v1`**: 初回バージョンを明示。

```
episode_001_A41.md     # 最新版
episode_001_A41_v1.md  # 初回版
```

## Q2. タイムスタンプとバージョンは併用すべき？
- 長期保管や複数日にわたる反復では併用を推奨。
- 例: `episode_001_quality_20251013_124325_final.json`

## Q3. バージョン文字列に使える文字は？
- 英数字、ハイフン（-）、ドット（.）を推奨。
- アンダースコア `_` は区切り文字として予約済みのため避ける。

**Good**: `v1`, `1.0`, `alpha`, `2025-01`  
**Bad**: `v_1`, `version 1`

## Q4. どのツールがバージョンをサポートしている？
- ✅ `ReportFileNamingService`
- ✅ `PathServiceAdapter.generate_report_filename()`
- ⏳ CLI ツールは順次拡張予定（`export_quality_report_tool` など）

## References
- DEC-021: ReportFileNamingService による統一命名規則導入
- DEC-022: ReportFileNameConfig の導入
- ソースコード: `src/noveler/domain/services/report_file_naming_service.py`
- テスト: `tests/unit/domain/services/test_report_file_naming_service.py`
