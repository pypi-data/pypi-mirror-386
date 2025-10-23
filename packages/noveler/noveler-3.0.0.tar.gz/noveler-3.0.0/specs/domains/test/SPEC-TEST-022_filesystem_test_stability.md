---
spec_id: SPEC-TEST-022
status: draft
owner: quality-engineering
last_reviewed: 2025-10-01
category: Testing
tags: [test_stability, filesystem, mocking, sandbox]
---
# SPEC-TEST-022: ファイルシステムテスト安定性仕様

## 1. 目的

- テストコードにおけるハードコードされた絶対パス (`/nonexistent` 等) の使用を最小化する
- ファイルシステム操作のモッキングを一貫した方法で実施する
- テスト環境のサンドボックス化により、実ファイルシステムへの依存を排除する
- CI/CD環境でのテスト実行の安定性を向上させる

## 2. 前提条件

- pytest がテストランナーとして使用されている
- `pytest.tmpdir` / `tempfile.TemporaryDirectory` が利用可能である
- `unittest.mock` による Path オブジェクトのモッキングが可能である
- テストは AGENTS.md のコメント規約に従う

## 3. テスト分類と対応方針

### 3.1 カテゴリA: ファイルシステム操作を伴わないユニットテスト

**特徴**:
- Path オブジェクトを引数として受け取るが、実際には `exists()` や `open()` を呼ばない
- または完全にモックされている (`Path.exists` をモック)

**対応方針**:
- `/nonexistent` パスの使用は許容される (モック前提)
- ただし、テストの意図を明示するコメントを追加すること

**例**:
```python
def test_init_with_nonexistent_project_path(self) -> None:
    """存在しないプロジェクトパスでの初期化時エラー."""
    # Path.exists をモックしているため、実際のパスは無関係
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(ViewpointFileNotFoundError):
            PlotViewpointRepository(Path("/nonexistent/project"), enable_backup=False)
```

### 3.2 カテゴリB: ファイルシステム操作が部分的にモックされるテスト

**特徴**:
- 一部の Path メソッド (`exists()`, `open()`) はモックされるが、他の操作 (`mkdir()`, `glob()`) は実行される可能性がある

**対応方針**:
- **推奨**: `tempfile.TemporaryDirectory` を使用して実ディレクトリを作成
- **代替**: すべての Path メソッドを明示的にモック

**例**:
```python
def test_plot_dir_not_exists(self) -> None:
    """プロットディレクトリが存在しない場合."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        repo = PlotViewpointRepository(
            repo_path, enable_backup=False, path_service_factory=_path_service_stub
        )

        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = False

        with patch.object(repo, "plot_dir", mock_plot_dir):
            result = repo.get_episode_viewpoint_info("001")
            assert result is None
```

### 3.3 カテゴリC: 統合テストまたはファイルシステムに依存するテスト

**特徴**:
- 実際にファイルを作成・読み込み・削除する
- ディレクトリ構造を構築する

**対応方針**:
- **必須**: `pytest.tmpdir` フィクスチャまたは `tempfile.TemporaryDirectory` を使用
- **必須**: テスト後のクリーンアップを保証する (with ステートメントまたは fixture)

**例**:
```python
def test_error_handling_integration(self, tmp_path: Path) -> None:
    """エラーハンドリング統合テスト"""
    # Given: 一時ディレクトリ内に不正な構造を作成
    invalid_root = tmp_path / "project"
    invalid_root.mkdir()

    request = PromptSaveRequest(
        project_root=invalid_root,
        episode_number=1,
        # ...
    )

    # When & Then
    with pytest.raises(ExpectedError):
        use_case.execute(request)
```

## 4. モッキング規約

### 4.1 Path.exists のモック

```python
# ✅ 推奨: patch.object を使用
with patch.object(Path, "exists", return_value=False):
    # テストコード

# ❌ 非推奨: 文字列パスでのモック (すべてのPathインスタンスに影響)
with patch("pathlib.Path.exists", return_value=False):
    # すべてのPathインスタンスが影響を受ける可能性
```

### 4.2 ファイル読み込みのモック

```python
# ✅ 推奨: mock_open を使用
with patch("pathlib.Path.open", mock_open(read_data="test content")):
    # テストコード

# ✅ 推奨: 特定のファイルパスのみモック
mock_file = Mock()
mock_file.exists.return_value = True
with patch.object(repo, "target_file", mock_file):
    # テストコード
```

### 4.3 ディレクトリ操作のモック

```python
# ✅ 推奨: インスタンス属性のモック
mock_plot_dir = Mock()
mock_plot_dir.exists.return_value = True
mock_plot_dir.glob.return_value = [Path("file1.yaml"), Path("file2.yaml")]

with patch.object(repo, "plot_dir", mock_plot_dir):
    # テストコード
```

## 5. 移行ガイドライン

### 5.1 優先順位

1. **P0 (Critical)**: 実ファイルシステムに書き込みを行うテスト
2. **P1 (High)**: `/nonexistent` パスを使用し、部分的にモックされているテスト
3. **P2 (Medium)**: 完全にモックされているが、ベストプラクティスに従っていないテスト
4. **P3 (Low)**: コメントが不足しているモックテスト

### 5.2 移行手順

#### ステップ1: 影響調査
```bash
# ハードコードされたパスを検索
grep -r "/nonexistent" tests/
grep -r "Path('/" tests/
```

#### ステップ2: カテゴリ分類
各テストファイルを分析し、カテゴリA/B/Cに分類する。

#### ステップ3: 修正実施
- カテゴリA: コメント追加のみ
- カテゴリB: `tempfile.TemporaryDirectory` への切り替え
- カテゴリC: `pytest.tmpdir` フィクスチャへの切り替え

#### ステップ4: 検証
```bash
# 並列実行での安定性確認
pytest -n auto tests/unit/
pytest -n auto tests/integration/

# サンドボックス分離の確認
pytest --basetemp=/tmp/pytest-sandbox tests/
```

## 6. 検証基準

### 6.1 成功基準

- [ ] `/nonexistent` パス使用箇所が50%以上削減される
- [ ] 実ファイルシステムへの書き込みを行うテストがすべて一時ディレクトリを使用する
- [ ] `pytest -n auto` での並列実行が安定する (失敗率 < 1%)
- [ ] すべてのモックが明示的にコメントされる

### 6.2 品質指標

- **Isolation Score**: 実ファイルシステムに依存しないテストの割合 (目標: 95%以上)
- **Mock Coverage**: モックが適用されている Path 操作の割合 (目標: 100%)
- **Comment Coverage**: モック理由が説明されているテストの割合 (目標: 80%以上)

## 7. 対象ファイルリスト

### 7.1 P0: 実ファイルシステム操作あり (優先度: Critical)

該当なし (調査結果による)

### 7.2 P1: 部分的モック (優先度: High)

1. `tests/unit/infrastructure/persistence/test_plot_viewpoint_repository_error_handling.py`
   - Line 44: `/nonexistent/project` (exists モック済み)
   - Line 75-88: `tempfile.TemporaryDirectory` 使用済み (Good Practice)
   - Action: Line 44 にコメント追加

2. `tests/unit/infrastructure/repositories/test_yaml_a31_checklist_repository.py`
   - Line 95: `/nonexistent` (FileNotFoundError テスト)
   - Action: コメント追加 (モック不要な負のテストケース)

3. `tests/integration/test_enhanced_prompt_save_integration.py`
   - Line 214: `/nonexistent/path`
   - Action: 統合テストのため `tmp_path` フィクスチャに変更

4. `tests/integration/test_enhanced_previous_episode_integration.py`
   - Line 306: `/nonexistent/path`
   - Action: 統合テストのため `tmp_path` フィクスチャに変更

5. `tests/unit/presentation/mcp/test_plugin_registry.py`
   - Line 241: `/nonexistent/directory`
   - Action: テストの意図を明示するコメント追加

### 7.3 P2: 完全モック (優先度: Medium)

1. `tests/unit/application/use_cases/test_prompt_generation_use_case.py`
   - Line 175: `/nonexistent/path`
   - Action: コメント追加

2. `tests/unit/domain/entities/test_integrated_writing_session.py`
   - Line 113: `/nonexistent/path`
   - Action: コメント追加 (ValueError テスト)

3. `tests/unit/application/use_cases/test_integrated_quality_check_use_case.py`
   - Line 73: `/nonexistent/file.md`
   - Action: コメント追加

## 8. 実装例

### 8.1 Before: ハードコードされたパス

```python
def test_nonexistent_path_error(self) -> None:
    with pytest.raises(FileNotFoundError):
        repo = Repository(Path("/nonexistent/path"))
```

### 8.2 After: コメント追加 (完全モック時)

```python
def test_nonexistent_path_error(self) -> None:
    """存在しないパスでのエラーハンドリング.

    Note: Path オブジェクトはエラー検出のトリガーとしてのみ使用され、
    実ファイルシステムへのアクセスは発生しない。
    """
    # 実パスは無関係 (Repository.__init__ が exists() チェックで即座に失敗)
    with pytest.raises(FileNotFoundError):
        repo = Repository(Path("/nonexistent/path"))
```

### 8.3 After: 一時ディレクトリ使用 (統合テスト)

```python
def test_error_handling_integration(self, tmp_path: Path) -> None:
    """エラーハンドリング統合テスト"""
    # Given: 一時ディレクトリ内に不正な構造を作成
    invalid_root = tmp_path / "project"
    invalid_root.mkdir()

    # When & Then
    with pytest.raises(ExpectedError):
        use_case.execute(PromptSaveRequest(project_root=invalid_root))
```

## 9. 参照

- TODO.md line 67-70: Test Stability (Filesystem / sandbox)
- AGENTS.md: Comment & Docstring Standards
- pytest documentation: tmpdir and tmp_path fixtures
- Python unittest.mock documentation

## 10. 将来の拡張

- [ ] テスト実行時のファイルシステムアクセス監視
- [ ] 自動リファクタリングスクリプトの作成
- [ ] CI/CD パイプラインでの Isolation Score 計測
