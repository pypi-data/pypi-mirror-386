# 初回リリース手順ガイド（ローカル実行）

> **作成日**: 2025年10月22日
> **バージョン**: 1.0
> **対象**: noveler プロジェクトの PyPI 初回登録

---

## 📋 概要

このドキュメントは、noveler プロジェクトを PyPI に初回登録するための手順をまとめています。

初回リリース後は、GitHub Actions の deploy.yml が自動的にタグトリガーで PyPI 公開を行うようになります。

---

## 🎯 初回リリースの目的

1. **PyPI プロジェクト登録**: noveler パッケージを PyPI 上に新規作成
2. **初期バージョン公開**: v3.0.0 を初回リリースバージョンとして公開
3. **GitHub Actions 自動化テスト**: deploy.yml がトークンなしで正常に動作することを確認

---

## 🛠️ 前提条件

### **ローカルでの準備**

```bash
# 1. PyPI API トークン取得
# https://pypi.org/manage/account/tokens/ にアクセス
# 「Create token for repository」をクリック
# Scope: "Novel Writing Support (noveler)" を選択
# トークン値をコピー（例: pypi-AgXXXXXXXXXX...）

# 2. twine インストール確認
pip install twine

# 3. CHANGELOG.md のセクション確認
# 以下のセクションが存在すること:
# ## [3.0.0] - YYYY-MM-DD
```

### **GitHub 側の準備**

- [ ] `PYPI_API_TOKEN` が Secrets に登録済み（Phase 4 で実施済み）
- [ ] main ブランチ保護ルール が設定済み
- [ ] deploy.yml の修正が完了

---

## 📝 ステップバイステップ手順

### **STEP 1: CHANGELOG.md に初回リリースセクションを追加**

```bash
# エディタで CHANGELOG.md を開く
# [Unreleased] セクションの上に以下を追加:

## [3.0.0] - 2025-10-22

### 🎯 Initial Release

#### Highlights
- **MCP Server Integration**: Claude Code との完全統合
- **TDD + DDD Compliance**: テスト駆動開発とドメイン駆動設計
- **Comprehensive Quality System**: 品質管理システム統合
- **GitHub Actions CI/CD**: 自動テスト・デプロイパイプライン

#### Major Features
- ✨ MCP ツール 17 個の統合実装
- ✨ 品質チェック統合システム（rhythm/readability/grammar/style）
- ✨ 構造化ログ・分散トレーシング
- ✨ ブランチ保護ルール + CI/CD パイプライン

#### Quality Metrics
- Test Coverage: ≥ 80%
- Ruff Compliance: ✅ (with known exceptions)
- MyPy Strict: ✅
- ImportLinter DDD: ✅
- Code Quality Gate: ✅

#### Documentation
- Complete implementation guides (docs/guides/)
- Branch strategy and CI/CD documentation
- MCP integration documentation
```

保存後、git に追加:
```bash
git add CHANGELOG.md
git commit -m "docs: add v3.0.0 initial release notes"
git push origin main
```

---

### **STEP 2: ビルド成果物を生成**

```bash
# プロジェクトルートで実行
cd /path/to/noveler

# 既存のビルド成果物をクリーン
rm -rf build/ dist/ *.egg-info

# ビルド実行
python -m build
```

**確認**:
```bash
ls -lh dist/
# 以下のファイルが生成されていること:
# - noveler-3.0.0-py3-none-any.whl (wheel)
# - noveler-3.0.0.tar.gz (source distribution)
```

---

### **STEP 3: ビルド成果物を検証**

```bash
# twine を使ってメタデータを検証
twine check dist/*

# 出力例:
# Checking distribution dist/noveler-3.0.0-py3-none-any.whl: Passed
# Checking distribution dist/noveler-3.0.0.tar.gz: Passed
```

**エラーが出た場合**:
- pyproject.toml の description / readme フィールドを確認
- CHANGELOG.md のセクション形式を確認

---

### **STEP 4: TestPyPI にアップロード（推奨）**

本番 PyPI の前に、テスト用の TestPyPI にアップロードして検証します。

```bash
# TestPyPI アカウント作成（未登録の場合）
# https://test.pypi.org/account/register/

# ~/.pypirc ファイルを作成（初回のみ）
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <TestPyPI API トークン>

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <PyPI API トークン>
EOF

# パーミッション設定
chmod 600 ~/.pypirc

# TestPyPI にアップロード
twine upload --repository testpypi dist/*

# 確認
# https://test.pypi.org/project/noveler/
```

**検証項目**:
- [ ] TestPyPI に noveler-3.0.0 が表示されている
- [ ] プロジェクト説明が正しく表示されている
- [ ] CHANGELOG.md が Releases タブに表示されている

---

### **STEP 5: PyPI に本番アップロード**

```bash
# PyPI の本番環境にアップロード
twine upload dist/*

# 確認メッセージが表示されたら、アップロード確認
# 出力例:
# Uploading noveler-3.0.0-py3-none-any.whl
# Uploading noveler-3.0.0.tar.gz
# View at:
# https://pypi.org/project/noveler/3.0.0/
```

**確認**:
- [ ] https://pypi.org/project/noveler/ に v3.0.0 が表示されている
- [ ] wheel と tarball の両方がアップロードされている
- [ ] プロジェクト説明が正しく表示されている

---

### **STEP 6: ローカルインストール検証**

```bash
# 新しい Python 環境でテスト（推奨）
python -m venv /tmp/test-noveler
source /tmp/test-noveler/bin/activate  # Linux/macOS
# または
# \tmp\test-noveler\Scripts\activate  # Windows

# PyPI からインストール
pip install noveler==3.0.0

# 動作確認
noveler --help
# または
python -m noveler mcp-server --help

# MCP サーバー起動テスト
noveler mcp-server --port 3001 &
sleep 2
# Ctrl+C で停止

# 環境クリーンアップ
deactivate
rm -rf /tmp/test-noveler
```

---

### **STEP 7: GitHub タグ作成（自動デプロイ準備）**

本番 PyPI へのアップロードが完了したら、GitHub タグを作成します。

以降は GitHub Actions の deploy.yml が自動実行されるようになります。

```bash
# タグ作成（ローカル）
git tag v3.0.0

# タグ push（GitHub へ）
git push origin v3.0.0

# GitHub Actions で deploy.yml が実行される
# 確認: https://github.com/<user>/noveler/actions
```

**deploy.yml の確認項目**:
- [ ] build ジョブ: wheel + sdist 生成 ✅
- [ ] publish-pypi ジョブ: PyPI へ公開 ✅ (既に公開済み)
- [ ] create-release ジョブ: GitHub Release を自動作成 ✅
- [ ] GitHub Releases タブに v3.0.0 が表示される ✅

---

## 📊 初回リリース後の自動化フロー

```
┌─────────────────────────────────────────┐
│  STEP 1-5: 手動（初回のみ）             │
│  - ビルド・PyPI アップロード            │
└─────────────────────────────────────────┘
                 ↓
         ✅ PyPI に v3.0.0 公開
                 ↓
┌─────────────────────────────────────────┐
│  STEP 7: GitHub タグ作成                 │
│  git push origin v3.0.0                 │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  自動化フロー（以降）                    │
│                                         │
│  deploy.yml が自動実行:                 │
│  ├─ build                               │
│  ├─ publish-pypi（API Token 使用）      │
│  ├─ create-release（Release 自動作成）  │
│  └─ notify-*（成否通知）                │
└─────────────────────────────────────────┘
```

---

## 🔑 PyPI API トークン管理

### **トークン生成手順**

1. https://pypi.org/manage/account/tokens/ にアクセス
2. "Add API token" をクリック
3. トークン名: `github-actions-noveler`
4. Scope:
   - **推奨（セキュリティ最適）**: "Novel Writing Support (noveler)" 限定
   - **代替**: "Entire account" （セキュリティは低下）
5. トークン生成 → コピー

### **トークン値の形式**

```
pypi-AgXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### **ローカル ~/.pypirc での設定**

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### **GitHub Secrets での登録**

```
Name: PYPI_API_TOKEN
Value: pypi-AgXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## ⚠️ トラブルシューティング

### **問題: twine check で Failed**

**症状**:
```
Checking distribution dist/noveler-3.0.0.tar.gz: Failed
```

**原因**: pyproject.toml の description / readme フィールドが無効

**解決策**:
```bash
# pyproject.toml を確認
cat pyproject.toml | grep -A 2 description

# description は短いテキスト、readme は長いテキスト
# readme は "README.md" と指定するか、直接内容を記載

# 修正後、再ビルド
rm -rf dist/
python -m build
```

---

### **問題: PyPI アップロード時にエラー**

**症状**:
```
ERROR: HTTPError: 403 Forbidden
User 'example' is not allowed to upload to project 'noveler'
```

**原因**: PyPI の noveler プロジェクト所有権の問題

**解決策**:
1. https://pypi.org/project/noveler/ で所有権確認
2. 必要に応じてプロジェクト削除 → 再作成
3. トークン権限確認（限定か全体か）

---

### **問題: twine でユーザー認証エラー**

**症状**:
```
ERROR: HTTPError: 403 Forbidden
Invalid or expired authentication credentials.
```

**原因**: PyPI API トークンが無効 or 形式が違う

**解決策**:
```bash
# トークンが pypi- で始まることを確認
# ~/.pypirc の password フィールドが正しいか確認

# 新しいトークンを生成
# https://pypi.org/manage/account/tokens/

# ~/.pypirc を更新
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers = pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-<new_token_here>
EOF

chmod 600 ~/.pypirc
```

---

## 📋 チェックリスト

### **リリース前**
- [ ] CHANGELOG.md に `## [3.0.0] - YYYY-MM-DD` セクション追加
- [ ] git に CHANGELOG.md をコミット
- [ ] pyproject.toml の version = "3.0.0" を確認
- [ ] PyPI API トークン を生成済み

### **ビルド・アップロード**
- [ ] `python -m build` でエラーなし
- [ ] `twine check dist/*` で全て Passed
- [ ] TestPyPI へのアップロード成功
- [ ] PyPI へのアップロード成功

### **検証**
- [ ] https://pypi.org/project/noveler/3.0.0/ で確認
- [ ] ローカル `pip install noveler==3.0.0` で動作確認
- [ ] GitHub Secrets に `PYPI_API_TOKEN` 登録済み

### **自動化**
- [ ] `git tag v3.0.0` でタグ作成
- [ ] `git push origin v3.0.0` で push
- [ ] GitHub Actions deploy.yml が実行
- [ ] GitHub Releases に v3.0.0 自動作成

---

## 🚀 次のリリース（v3.0.1 以降）

初回リリース後は、以下の手順で自動化されます：

```bash
# 1. main で開発・テスト（PR で CI 実行）
# 2. main へマージ（レビュー + CI 必須）
# 3. CHANGELOG.md に新セクション追加

## [3.0.1] - 2025-10-29
### 🐛 Bug Fixes
- ...

# 4. タグ作成
git tag v3.0.1

# 5. タグ push（deploy.yml が自動実行）
git push origin v3.0.1

# 以降、自動で：
# ├─ PyPI へ公開
# ├─ GitHub Release 作成
# └─ リリースノート自動抽出
```

---

## 📞 参考資料

- **PyPI Help**: https://pypi.org/help/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Python Packaging**: https://packaging.python.org/
- **[cicd_implementation_summary.md](cicd_implementation_summary.md)**: CI/CD パイプライン総括
- **[branch_strategy.md](branch_strategy.md)**: ブランチ戦略詳細

---

**最終更新**: 2025年10月22日
**作成者**: Claude Code Assistant
**ステータス**: 初回リリース前ガイド
