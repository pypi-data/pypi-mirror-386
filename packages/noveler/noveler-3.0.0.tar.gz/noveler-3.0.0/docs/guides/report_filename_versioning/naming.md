# Report Filename Versioning — 命名規約とベストプラクティス

## 推奨パターン

| パターン | 例 | 用途 |
| --- | --- | --- |
| 連番 (`v1`, `v2`, …) | `episode_001_A41_v1.md` | 順次推敲 |
| 段階ラベル (`initial`, `revised`, `final`) | `episode_005_quality_final.json` | ワークフロー段階 |
| セマンティック (`1.0`, `1.1`, `2.0`) | `episode_010_A41_2.0.md` | 大規模改訂管理 |
| 日付ベース (`2025-01`, `q3`) | `episode_015_quality_2025-02.json` | 時系列管理 |

## バージョン解析と自然ソート
- エピソード番号は 3 桁ゼロ埋めで整列。
- バージョンなしが「最新版」として最上位に並ぶ。
- バージョン接尾辞の形式を統一することで、辞書順ソートでも時系列が崩れない。

## ベストプラクティス

1. **バージョンなし = 最新版**
   ```
   episode_001_A41.md          # 最新版
   episode_001_A41_v1.md       # 過去版
   episode_001_A41_v2.md       # 過去版
   ```

2. **形式を揃える**
   - 悪例: `episode_001_A41_version2.md`, `episode_001_A41_rev-3.md`
   - 良例: `episode_001_A41_v1.md`, `episode_001_A41_v2.md`

3. **タイムスタンプ + バージョンで長期保管**
   ```python
   filename = ps.generate_report_filename(
       episode_number=1,
       report_type="quality",
       extension="json",
       include_timestamp=True,
       version="final"
   )
   # episode_001_quality_20251013_124325_final.json
   ```

4. **ライフサイクルを意識したディレクトリ構造**
   ```
   reports/quality/
   ├── current/
   │   └── episode_001_A41.md
   └── archive/
       ├── episode_001_A41_v1.md
       └── episode_001_A41_v2.md
   ```
