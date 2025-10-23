# ブランチ戦略とCI/CD運用ガイド

> **作成日**: 2025年10月22日
> **バージョン**: 1.0
> **対象**: noveler プロジェクト（GitHub運用）

---

## 📋 概要

このガイドは、noveler プロジェクトのブランチ戦略と GitHub Actions による自動CI/CD パイプラインの統合運用を定めます。

**重要原則**：
- **main**: 常時デプロイ可能な安定ブランチ
- **dev**: 統合・QA用ブランチ
- **feature/\***: 開発者の機能ブランチ

---

## 🌳 ブランチ体系

### **3段階の開発フロー**

```
┌─────────────────┐
│  feature/*      │  開発ブランチ（個人開発）
├─────────────────┤
│  ↓ (PR)         │  PR → dev へマージ
├─────────────────┤
│  dev            │  統合ブランチ（QA・段階的テスト）
├─────────────────┤
│  ↓ (PR)         │  PR → main へマージ（厳格チェック）
├─────────────────┤
│  main           │  本番・リリース用（常時安定）
├─────────────────┤
│  ↓ (git tag)    │  セマンティック版タグ（v3.0.1）
├─────────────────┤
│  PyPI + Release │  自動デプロイ
└─────────────────┘
```

---

## 📌 各ブランチの役割と保護ルール

### **1️⃣ main ブランチ**

**目的**: 本番デプロイ用・常時安定版の保証

#### 保護ルール設定

| 項目 | 設定値 | 説明 |
|------|------|------|
| **直プッシュ** | 🚫 禁止 | PR経由のみ |
| **PR必須化** | ✅ 有効 | PR作成が必須 |
| **CI成功** | ✅ 必須 | `pr-check.yml` 合格が条件 |
| **レビュー承認** | ✅ 最低1名 | 1人以上の approve が必須 |
| **Dismiss stale reviews** | ✅ 有効 | 新コミット後、古いレビューを無効化 |
| **マージ前コミット必須** | ✅ 有効 | PR マージ前に最新 main を反映 |
| **削除許可** | ❌ 禁止 | ブランチ削除禁止 |

#### GitHub 管理画面での設定手順

```
Settings → Branches → Branch protection rules
├─ Pattern name: main
├─ Require a pull request before merging
│  ├─ Require approvals: 1
│  └─ Dismiss stale pull request approvals when new commits are pushed: ✅
├─ Require status checks to pass before merging
│  ├─ Lint (ruff + mypy + importlinter) ✅
│  ├─ Test Suite ✅
│  └─ Quality Gate ✅
├─ Require branches to be up to date before merging: ✅
└─ Allow force pushes: ❌
```

⚠️ **重要**: 必須チェック名は `.github/workflows/pr-check.yml` の各ジョブ `name:` フィールドと **完全一致** する必要があります。

| GitHub Actions ジョブ名 | branch protection で指定する名前 |
|------------------------|--------------------------------|
| `name: Lint (ruff + mypy + importlinter)` | `Lint (ruff + mypy + importlinter)` |
| `name: Test Suite` | `Test Suite` |
| `name: Quality Gate` | `Quality Gate` |

名前の誤りがあると「Required status check expected」エラーが発生し、マージできなくなります。

#### 運用フロー

```bash
# ローカル: feature ブランチで開発
git checkout -b feature/my-feature develop

# 開発完了後、PR を dev に送信
git push origin feature/my-feature
# GitHub: PR 作成 → feature/my-feature → dev

# dev でのテスト・QA合格後、main への PR を自動生成（または手動）
# main PR で CI 再実行 + レビュアーの承認を取得
# ✅ Merge pull request
```

---

### **2️⃣ dev ブランチ**

**目的**: 統合・段階的テスト用ブランチ

#### 保護ルール設定

| 項目 | 設定値 | 説明 |
|------|------|------|
| **直プッシュ** | ✅ 許可 | 統合スピード優先 |
| **PR必須化** | ❌ 不要 | 柔軟な統合 |
| **CI成功** | ❌ 不要 | 任意の段階ビルド可 |
| **レビュー承認** | ❌ 不要 | スピード優先 |
| **削除許可** | ❌ 禁止 | 重要な統合ブランチ |

#### GitHub 管理画面での設定手順

```
Settings → Branches → Branch protection rules
├─ Pattern name: dev
├─ Require a pull request before merging: ❌
├─ Require status checks to pass before merging: ❌
├─ Allow force pushes: ❌
└─ Include administrators: ❌
```

#### 運用フロー

```bash
# feature ブランチから dev へ PR
git push origin feature/my-feature
# GitHub: PR 作成 → feature/my-feature → dev

# dev でテスト・動作確認（CI 実行を待たずに進行可）
# 合格後、main への PR を作成

# or 直接 dev へマージ（push 権限があれば）
git checkout dev
git pull origin dev
git merge feature/my-feature
git push origin dev
```

---

### **3️⃣ feature/\* ブランチ**

**目的**: 個人開発用・一時的ブランチ

#### ブランチ命名規則

```
feature/<ticket-id>-<description>

例：
- feature/GH-123-add-quality-gate
- feature/GH-124-fix-imports-linter
- feature/GH-125-refactor-path-service
```

#### 保護ルール設定

- **保護なし**：開発者の自由に任せる

#### 運用フロー

```bash
# main or dev から新規ブランチを作成（dev 推奨）
git checkout -b feature/my-feature origin/dev

# 開発・コミット
git add .
git commit -m "feat: description"

# PR 作成（対象: dev）
git push origin feature/my-feature
# GitHub: Create Pull Request → dev

# dev でレビュー・マージ後、ブランチ削除
git branch -D feature/my-feature
```

---

## 🤖 GitHub Actions 統合

### **pr-check.yml（PR 時 自動実行）**

**トリガー**: main / dev への PR

```yaml
on:
  pull_request:
    branches: [main, dev]
```

**実行内容**:
1. **lint** (並列)：ruff + mypy + importlinter
2. **test** (並列)：pytest フルスイート
3. **quality-gate**：lint/test 結果を確認

**必須チェック**（main へのマージ条件）:
- ✅ lint: 合格
- ✅ test: 合格
- ✅ quality-gate: 成功

**dev への PR**: テスト確認用（必須ではない）

---

### **deploy.yml（タグ push 時 自動実行）**

**トリガー**: `git tag v*` を push

```bash
git tag v3.0.1
git push origin v3.0.1
```

**実行内容**:
1. **build**: wheel + sdist 生成
2. **publish-pypi**: PyPI に公開（API Token 認証）
3. **create-release**: GitHub Release 自動作成（CHANGELOG.md から抽出）
4. **notify-deployment**: デプロイ成功ログ

**前提条件**:
- GitHub Secrets に `PYPI_API_TOKEN` を登録
- CHANGELOG.md に対応セクション記載（`## [v3.0.1] - YYYY-MM-DD`）

---

## 📝 運用手順

### **新機能の開発フロー（例）**

#### **ステップ1：feature ブランチ作成**

```bash
git checkout -b feature/GH-123-add-feature origin/dev
```

#### **ステップ2：開発・テスト・コミット**

```bash
# 開発
echo "新機能のコード" > src/noveler/new_feature.py

# ローカルテスト
make test

# コミット（AGENTS.md 準拠）
git add .
git commit -m "feat: add new feature with comprehensive tests

- Implement NewFeature domain service
- Add unit tests (10 cases)
- Update documentation

Closes #123"
```

#### **ステップ3：PR 作成（dev へ）**

```bash
git push origin feature/GH-123-add-feature
```

GitHub 上で PR を作成：
- **Base**: dev
- **Head**: feature/GH-123-add-feature
- **Description**: PR テンプレートに従う

#### **ステップ4：レビュー・マージ**

dev でのレビュー（簡易）後、マージ：
```bash
✅ Squash and merge (推奨)
```

#### **ステップ5：main へのマージ（リリース時）**

```bash
git checkout -b release/v3.0.1 origin/dev
git push origin release/v3.0.1
```

GitHub で PR を作成（main へ）:
- **Base**: main
- **Head**: release/v3.0.1

**必須チェック**:
- ✅ pr-check: 全て合格
- ✅ レビュアー 1 名が approve

マージ後、タグを作成：
```bash
git checkout main
git pull origin main
git tag v3.0.1
git push origin v3.0.1
```

#### **ステップ6：自動デプロイ**

タグ push により、deploy.yml が自動実行：
- ✅ PyPI に公開
- ✅ GitHub Release に自動作成
- ✅ CHANGELOG から抽出したリリースノート記載

確認：
- PyPI: https://pypi.org/project/noveler/3.0.1/
- GitHub Releases: v3.0.1 に wheel + tarball 添付

---

## 🚨 緊急対応（ホットフィックス）

### **本番で問題が発生した場合**

#### **ステップ1：ホットフィックス用ブランチ作成**

```bash
git checkout -b hotfix/GH-999-critical-bug origin/main
```

#### **ステップ2：修正・テスト**

```bash
# 修正
# テスト
make test
git add .
git commit -m "fix: critical bug in production

Closes #999"
```

#### **ステップ3：main への PR（優先処理）**

```bash
git push origin hotfix/GH-999-critical-bug
```

GitHub：
- **Base**: main
- **PR Title**: `[HOTFIX] Critical bug fix`
- **PR Description**: 影響範囲・テスト結果を詳記

**レビュー**: 最小限（1名承認）で即マージ

#### **ステップ4：dev への バックポート**

ホットフィックスを dev へも反映：

```bash
git checkout dev
git pull origin dev
git merge main
git push origin dev
```

#### **ステップ5：リリース**

```bash
git checkout main
git pull origin main
git tag v3.0.2
git push origin v3.0.2
# deploy.yml が自動実行
```

---

## 📋 チェックリスト（初期設定）

GitHub リポジトリ管理者は、以下を実行してください：

### **Branch Protection Rules**

- [ ] main ブランチ保護ルール設定（上記 main セクション参照）
- [ ] dev ブランチ保護ルール設定（上記 dev セクション参照）

### **Secrets 登録**

Settings → Secrets and variables → Actions:

- [ ] `PYPI_API_TOKEN`: PyPI API トークン登録
- [ ] `GITHUB_TOKEN`: 自動供給（確認のみ）

### **環境設定（Actions）**

Settings → Environments:

- [ ] `pypi` 環境を作成
  - **Deployment branches**: Protected branches のみ
  - **Required reviewers**: オプション

### **ワークフロー確認**

- [ ] `.github/workflows/pr-check.yml`: PR 時 lint/test 実行
- [ ] `.github/workflows/deploy.yml`: タグトリガーでリリース

---

## 📚 参考資料

- **AGENTS.md**: コード品質・TDD/DDD 原則
- **CLAUDE.md**: MCP 統合・レイヤリング契約
- **.github/pull_request_template.md**: PR テンプレート
- **CHANGELOG.md**: リリースノート管理

---

## 🔄 改善提案と将来の拡張

### **Phase 5 で検討する項目**

1. **Slack 統計・通知**：
   - CI 失敗時に Slack 通知
   - リリース完了をアナウンス

2. **自動バージョン更新**：
   - conventional commits から version を自動更新
   - CHANGELOG.md を自動生成

3. **複数環境対応**：
   - Ubuntu → macOS / Windows matrix テスト
   - Python 3.11 / 3.12 への拡張

4. **セキュリティ強化**：
   - PYPI 認証を OIDC に移行
   - 署名済みリリース（cosign）

---

**最終更新**: 2025年10月22日
**作成者**: Claude Code Assistant
