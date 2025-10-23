# pytest Testing Guide

**Version**: 3.0.0
**Last Updated**: 2025-10-11
**Status**: ✅ Active

---

## 📋 概要

このガイドは、novelerプロジェクトにおけるpytestの使用方法を包括的に説明します。

**内容**:
- ✅ フィクスチャパターン（標準・MCP統合・E2E）
- ✅ レガシーパターンから新パターンへの移行方法
- ✅ トラブルシューティング
- ✅ ベストプラクティス

---

## ⚠️ 重要な変更（Phase 1 完了）

### 問題

**Phase 1 以前**、`temp_project_dir` フィクスチャが `path_service` を使用していたため、**実プロジェクトルート**にテストデータディレクトリ（`40_原稿`, `50_管理資料`）が作成されていました。

### 解決策

**Phase 1 で修正完了**。`temp_project_dir` は現在、pytest標準の `tmp_path_factory` のみを使用し、すべてのテストディレクトリを**一時ディレクトリ内**に作成します。

---

## 🆕 新パターン（推奨）

### ✅ パターン1: `tmp_path` 直接使用（最も推奨）

**対象**: 新規テスト、シンプルなテストケース

```python
def test_manuscript_creation(tmp_path):
    """新規テストでは tmp_path を直接使用"""
    # ✅ 一時ディレクトリを直接使用
    manuscript_dir = tmp_path / "40_原稿"
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    manuscript_file = manuscript_dir / "第001話_テスト.md"
    manuscript_file.write_text("テスト内容", encoding="utf-8")

    # テストロジック
    assert manuscript_file.exists()
    assert "テスト内容" in manuscript_file.read_text(encoding="utf-8")
```

**メリット**:
- ✅ pytestの標準パターン（公式ドキュメント推奨）
- ✅ シンプルで理解しやすい
- ✅ テスト間の独立性が高い
- ✅ 抽象化レイヤーがないため、予期しない副作用ゼロ

**デメリット**:
- パス構造をハードコード（`"40_原稿"` など）

---

### ✅ パターン2: `temp_project_dir` フィクスチャ使用

**対象**: 複数のテストで共通のプロジェクト構造が必要な場合

```python
def test_with_project_structure(temp_project_dir):
    """既存フィクスチャを使用（session scopeで効率的）"""
    # ✅ プロジェクト構造が自動的に作成される
    # - 40_原稿/
    # - 50_管理資料/
    # - 50_管理資料/plots/
    # - config/
    # - plots/
    # - quality/
    # - プロジェクト設定.yaml

    manuscript_dir = temp_project_dir / "40_原稿"
    assert manuscript_dir.exists()

    config_file = temp_project_dir / "プロジェクト設定.yaml"
    assert config_file.exists()
```

**メリット**:
- ✅ プロジェクト構造が自動作成（ボイラープレート削減）
- ✅ session scopeでパフォーマンス最適化
- ✅ 既存テストとの互換性維持

**デメリット**:
- テスト間で構造を共有（session scope）
- パス構造が固定（柔軟性低）

---

## ❌ 旧パターン（削除済み - Phase 3完了）

### ❌ パターン3: `path_service` 使用（✅ 削除完了 - 2025-10-09）

**ステータス**: ✅ **削除完了** - Phase 3（2025-10-09）

```python
# ❌ 非推奨: path_service を直接使用
def test_old_style(temp_project_dir):
    from tests.conftest import get_path_service

    path_service = get_path_service()
    manuscript_dir = path_service.get_manuscript_dir()
    # ⚠️ 問題: 実プロジェクトルートを参照する可能性がある
```

**問題点**:
- ❌ `path_service` が実プロジェクトルートの絶対パスを返却
- ❌ テストの独立性を損なう
- ❌ 予期しない副作用（実プロジェクトルート汚染）

**移行方法**:
```python
# ✅ 新パターンへ移行
def test_new_style(tmp_path):
    manuscript_dir = tmp_path / "40_原稿"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
```

---

### ✅ パターン3: `mcp_test_project` フィクスチャ使用（MCP統合テスト）

**対象**: MCP経由の `execute_novel_command` を使用するテスト

```python
@pytest.mark.asyncio
async def test_mcp_command(mcp_test_project):
    """MCP統合テスト - 共通フィクスチャ使用"""
    from noveler.presentation.mcp.server_runtime import execute_novel_command

    result = await execute_novel_command(
        command="write 1",
        project_root=str(mcp_test_project),
        options={"fresh-start": True},
    )
    assert result["result"]["data"]["status"] == "success"
```

**メリット**:
- ✅ 実プロジェクトルート汚染の完全防止（`tmp_path` ベース）
- ✅ グローバルキャッシュ汚染防止（`ServiceLocatorManager.reset()`）
- ✅ 環境変数の自動クリーンアップ（`monkeypatch`）
- ✅ セットアップ/クリーンアップの自動化（25行 → 8行に削減）

**デメリット**:
- MCP統合テストに特化（汎用性は低い）

**フィクスチャ定義場所**:
- `tests/integration/mcp/conftest.py`

**使用方法**:
1. テストファイルで `pytest_plugins = ["tests.integration.mcp.conftest"]` を追加（オプション）
2. テスト関数の引数に `mcp_test_project` を追加
3. `str(mcp_test_project)` を `project_root` パラメータに渡す

**Background**:
このフィクスチャは `tests/test_mcp_fixed.py` の実装を共通化したものです。
MCP統合テストで `execute_novel_command` を呼び出す際の標準パターンとして推奨されます。

---

### ❌ パターン4: `get_test_manuscripts_path()` 使用（非推奨）

**ステータス**: 🔴 **Deprecated** - Phase 3 で削除予定

```python
# ❌ 非推奨: ヘルパー関数使用
def test_old_helper(temp_project_dir):
    from tests.conftest import get_test_manuscripts_path

    manuscripts_path = get_test_manuscripts_path(temp_project_dir)
    manuscript_dir = temp_project_dir / manuscripts_path
    # ⚠️ 問題: 不要な抽象化レイヤー
```

**移行方法**:
```python
# ✅ 新パターンへ移行
def test_new_direct(tmp_path):
    manuscript_dir = tmp_path / "40_原稿"
```

---

## 📊 パターン比較表

| パターン | 推奨度 | テスト独立性 | パフォーマンス | シンプルさ | Phase 3での扱い |
|---------|--------|-------------|---------------|-----------|---------------|
| `tmp_path` 直接使用 | ⭐⭐⭐⭐⭐ | 高 | 中 | 高 | **継続推奨** |
| `temp_project_dir` 使用 | ⭐⭐⭐⭐ | 中 | 高 | 中 | **継続サポート** |
| `mcp_test_project` 使用 | ⭐⭐⭐⭐⭐ | 高 | 中 | 高 | **✅ 新規追加（2025-10-11）MCP専用** |
| `path_service` 使用 | ❌ 削除済み | 低 | 低 | 低 | **✅ 削除完了（2025-10-09）** |
| `get_test_*_path()` 使用 | ❌ 削除済み | 中 | 低 | 低 | **✅ 削除完了（2025-10-09）** |

---

## 🔄 移行ガイドライン

### Phase 2（現在 - 今週）

**ステータス**: ✅ **進行中**

1. ✅ **このガイド作成**（完了）
2. 🔄 **CI チェック追加**（次タスク）
3. 🔄 **Deprecation 警告追加**（次タスク）

### Phase 3（来月）

**ステータス**: 📋 **計画中**

1. 既存32ファイルを `tmp_path` 直接使用へ移行（週2-3ファイルペース）
2. `FallbackPathService` クラス削除
3. `get_test_manuscripts_path()` 削除
4. `get_test_management_path()` 削除

---

## 📖 詳細な使用例

### 例1: 単一原稿ファイルのテスト

```python
def test_manuscript_quality_check(tmp_path):
    """単一ファイルのテスト - tmp_path 推奨"""
    # セットアップ
    manuscript_file = tmp_path / "第001話_テスト.md"
    manuscript_file.write_text("""
# 第1話 テスト

これはテスト用の原稿です。
長い文章でもテストできるように、複数の文を含む段落を用意しています。
    """.strip(), encoding="utf-8")

    # テスト実行
    from noveler.domain.quality.checkers import ReadabilityChecker
    checker = ReadabilityChecker()
    issues = checker.check(manuscript_file)

    # 検証
    assert len(issues) == 0  # 品質問題なし
```

### 例2: プロジェクト構造全体のテスト

```python
def test_project_initialization(temp_project_dir):
    """プロジェクト全体のテスト - temp_project_dir 推奨"""
    # すでにプロジェクト構造が存在
    assert (temp_project_dir / "40_原稿").exists()
    assert (temp_project_dir / "50_管理資料").exists()
    assert (temp_project_dir / "config").exists()

    # プロジェクト設定の検証
    config_file = temp_project_dir / "プロジェクト設定.yaml"
    import yaml
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["project"]["title"] == "テストプロジェクト"
```

### 例3: E2Eワークフローのテスト

```python
@pytest.mark.e2e
def test_complete_writing_workflow(tmp_path):
    """E2Eワークフロー - カスタム構造なら tmp_path"""
    # カスタムプロジェクト構造を作成
    project_root = tmp_path / "my_novel_project"
    project_root.mkdir()

    manuscripts = project_root / "manuscripts"  # カスタム名
    manuscripts.mkdir()

    plots = project_root / "plot_designs"  # カスタム名
    plots.mkdir()

    # ワークフロー実行
    # ...
```

---

## 🛠️ トラブルシューティング

### 問題1: テストが実プロジェクトルートにファイルを作成する

**症状**:
```bash
ls 40_原稿/
# → ファイルが存在する（実プロジェクトルート内）
```

**原因**: `path_service` を使用している（旧パターン）

**解決策**:
```python
# ❌ Before
path_service = get_path_service()
manuscript_dir = path_service.get_manuscript_dir()

# ✅ After
def test_fixed(tmp_path):
    manuscript_dir = tmp_path / "40_原稿"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
```

---

### 問題2: テスト間でファイルが共有される

**症状**: テストAで作成したファイルがテストBで見える

**原因**: `temp_project_dir` の `scope="session"` により共有されている

**解決策1**: `tmp_path` を使用（function scope）
```python
def test_isolated_a(tmp_path):
    # 完全に独立したディレクトリ
    file = tmp_path / "test.txt"
```

**解決策2**: `isolated_temp_dir` を使用（function scope）
```python
def test_isolated_b(isolated_temp_dir):
    # temp_project_dir のfunction scope版
    file = isolated_temp_dir / "test.txt"
```

---

### 問題3: パス構造のカスタマイズが必要

**症状**: `40_原稿` 以外のディレクトリ名を使いたい

**解決策**: `tmp_path` を直接使用
```python
def test_custom_structure(tmp_path):
    # ✅ 自由にカスタマイズ可能
    custom_dir = tmp_path / "my_custom_manuscripts"
    custom_dir.mkdir()
```

---

## 📚 参考資料

### 公式ドキュメント

- [pytest: How to use temporary directories](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [pytest: Fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html)

### プロジェクト内ドキュメント

- **Phase 1 実装サマリー**: `b20-outputs/pytest_fixture_fix_phase1_summary.md`
- **決定ログ**: `b20-outputs/decision_log.yaml` (DEC-010)
- **Codexレビュー結果**: `temp/codex_review_result.yaml`

### 関連仕様

- **B20 設定**: `.b20rc.yaml`
- **Root Structure Policy**: `docs/proposals/root-structure-policy-v2.md`

---

## 🔍 FAQ

### Q1: 既存テストを移行する必要はありますか？

**A**: Phase 2（現在）では**移行不要**です。既存の `temp_project_dir` は動作し続けます。Phase 3（来月）で段階的に移行予定です。

### Q2: 新規テストはどちらのパターンを使うべきですか？

**A**: **`tmp_path` 直接使用**を推奨します。シンプルで、pytestの標準パターンです。

### Q3: `temp_project_dir` はいつ削除されますか？

**A**: 削除予定は**ありません**。既存テストとの互換性維持のため、Phase 3 以降も継続サポートします。

### Q4: Phase 3 の移行で何が変わりますか？

**A**: 以下が削除されます:
- `get_test_manuscripts_path()` 関数
- `get_test_management_path()` 関数
- `FallbackPathService` クラス

これらを使用している約32ファイルを `tmp_path` 直接使用へ移行します。

---

## 📞 サポート

質問や問題がある場合:

1. **このガイドを確認**: まず FAQ とトラブルシューティングを参照
2. **決定ログを確認**: `b20-outputs/decision_log.yaml` (DEC-010) で背景を理解
3. **Issue作成**: 解決しない場合は GitHub Issue を作成

---

**Version**: 1.0.0
**Last Updated**: 2025-10-09
**Status**: Active (Phase 2)
**Next Review**: 2025-10-11 (Phase 2 完了確認)
