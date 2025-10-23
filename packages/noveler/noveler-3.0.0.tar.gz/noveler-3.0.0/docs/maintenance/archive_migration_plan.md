# アーカイブ系フォルダ移行計画

## 現状のアーカイブディレクトリ

### B20 Workflow関連
- `b20-outputs/`: B20ワークフロー成果物格納先
- `b20-test/`: B20テスト実行結果（存在確認が必要）

### 参照状況

#### 設定ファイル
1. **`.b20rc.yaml`** (line 111)
   ```yaml
   output_dir: "./b20-outputs"
   ```
   → B20ワークフローの成果物出力先として使用中

#### ドキュメント
2. **`.claude/agents/b20-workflow.md`**
   - B20ワークフロー説明文書内で言及

3. **`docs/guides/windows_onboarding_checklist.md`**
   - オンボーディングガイド内で参照

4. **`docs/maintenance/folder_structure_guidelines.md`**
   - 本整理方針書で言及

#### 成果物ドキュメント（b20-outputs内）
- `deliverables_checklist.md`
- `final_summary.md`
- `phase4-testing/*.md`
- `TODO.md`

## 移行方針

### 現状維持（推奨）
**理由**:
1. `.b20rc.yaml` で現在も使用中（アクティブな設定）
2. B20ワークフロー（`/b20-workflow` コマンド）が実運用中
3. Phase 4テスト成果物など重要ドキュメントを格納

### 代替案: 段階的移行

#### Phase 1: 過去成果物のアーカイブ化
```
b20-outputs/
├── archive/          # 過去フェーズの成果物
│   ├── phase1/
│   ├── phase2/
│   ├── phase3/
│   └── phase4/
└── current/          # 現在進行中の成果物
```

#### Phase 2: 将来的な統合（要検討）
```
archive/
└── b20/
    ├── outputs/     # 旧 b20-outputs
    └── test/        # 旧 b20-test
```

**移行時の変更箇所**:
1. `.b20rc.yaml` の `output_dir` パス更新
2. 関連ドキュメントのパス更新
3. B20ワークフロースクリプトのパス参照更新

## b20-test ディレクトリの調査

**確認事項**:
- [ ] ディレクトリの存在確認
- [ ] サイズ・ファイル数確認
- [ ] 最終更新日確認
- [ ] 参照スクリプト・設定の有無
- [ ] 削除可否の判断

## 推奨アクション

### 短期（即実施）
1. **現状維持**: `b20-outputs/` は現在の場所で運用継続
2. **内部整理**: `b20-outputs/` 内で過去成果物をサブディレクトリに整理
3. **b20-test調査**: 存在・使用状況を確認し、不要なら削除

### 中長期（要レビュー）
1. B20ワークフロー完全完了後
2. 成果物の重要度・参照頻度を評価
3. `archive/b20/` への移行を検討
4. 移行時は必ず `.b20rc.yaml` とスクリプトを同期更新

## .gitignore 更新

現状の除外設定を確認:
```bash
# b20-outputs/ の扱い
# - 成果物ドキュメント(.md)は追跡対象
# - 一時ファイル・ログは除外
```

適切な .gitignore パターン:
```
b20-outputs/**/*.log
b20-outputs/**/*.tmp
b20-outputs/**/temp/
!b20-outputs/**/*.md
!b20-outputs/**/*.yaml
```
