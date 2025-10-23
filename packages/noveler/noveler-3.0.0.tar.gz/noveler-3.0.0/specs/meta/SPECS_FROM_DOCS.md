# docs/specs から移動したファイル一覧

**移動日時**: 2025-08-17
**移動理由**: 仕様書は本来 ./specs に配置すべきため

## 📁 移動したディレクトリ・ファイル

### design/ ディレクトリ
- **SDD-PROMPT-GENERATION-001.md** - プロンプト生成システム設計書

### functional/ ディレクトリ
- **SPEC-PROMPT-SAVE-001.md** - プロンプト保存機能仕様書
- **SPEC-STAGE5-SEPARATION.md** - Stage5分離とClaude Code品質チェック実装仕様

### その他
- **README.md** - 仕様書管理システムガイド（docs/specs用）

## 🔧 実施作業

1. ✅ `docs/specs/design/` → `specs/design/` へ移動
2. ✅ `docs/specs/functional/` → `specs/functional/` へ移動
3. ✅ 移動記録の作成
4. 🔄 `docs/specs/` ディレクトリの整理（予定）
5. 🔄 _index.yamlの参照更新（予定）

## 📊 影響範囲

- **docs/_index.yaml**: specs/への参照更新が必要
- **開発者**: 仕様書参照先の変更
- **テストコード**: specマーカーの参照先変更は不要（ファイル名同じ）

## 🎯 今後の方針

仕様書は統一的に `./specs` で管理し、docs/specsは削除する方向で整理を進めます。
