# Docstring/コメント規約準拠 - クイックスタートガイド

**対象読者**: Noveler開発者、コントリビューター
**更新日**: 2025-10-12

---

## 規約の要点

### 1. モジュールヘッダーコメント（必須）
```python
# File: src/noveler/domain/services/example_service.py
# Purpose: [モジュールの責任と存在理由を1-2行で要約]
# Context: [主要な依存関係、ドメイン制約、利用者を記載]
```

### 2. モジュールdocstring（必須）
```python
"""モジュールの簡潔な説明（1行）

Purpose:
    このモジュールが担う責任を詳述。

Side Effects:
    - ファイルI/Oの有無
    - ログ出力の有無
    - 状態変更の有無
    - または "None"
"""
```

### 3. クラスdocstring（必須）
```python
class ExampleService:
    """クラスの簡潔な説明（1行）

    Purpose:
        このクラスが担う責任を詳述。

    Side Effects:
        - 内部状態の管理
        - イベント発行の有無
        - または "None"
    """
```

### 4. 関数/メソッドdocstring（必須）
```python
def process_data(self, input_data: dict, validate: bool = True) -> Result:
    """データ処理を実行する

    Purpose:
        ビジネスルールに従ってデータを検証・変換する。

    Args:
        input_data: 処理対象のデータ辞書
        validate: 検証を実行するか（デフォルト: True）

    Returns:
        処理結果を含むResultオブジェクト

    Raises:
        ValidationError: データが検証に失敗した場合
        ProcessingError: 処理ロジックでエラーが発生した場合

    Side Effects:
        - 処理結果をリポジトリに書き込む
        - ProcessedEventを発行する
        - メトリクスをログに記録する
    """
```

---

## クイックチェックリスト

修正前に以下を確認してください：

- [ ] ファイル先頭に `# File: ...` ヘッダーがある
- [ ] モジュールdocstringに `Purpose:` セクションがある
- [ ] モジュールdocstringに `Side Effects:` セクションがある
- [ ] 全クラスに `Purpose:` セクション付きdocstringがある
- [ ] 全クラスに `Side Effects:` セクション付きdocstringがある
- [ ] 全関数/メソッドに `Purpose:` セクション付きdocstringがある
- [ ] パラメータがある関数に `Args:` セクションがある
- [ ] 戻り値がある関数に `Returns:` セクションがある
- [ ] 例外を送出する関数に `Raises:` セクションがある
- [ ] 全関数/メソッドに `Side Effects:` セクションがある

---

## コマンドリファレンス

### 違反チェック
```bash
# 単一ファイル
python scripts/comment_header_audit.py src/noveler/domain/services/example_service.py

# ディレクトリ全体
python scripts/comment_header_audit.py src/noveler/domain/services/

# プロジェクト全体
python scripts/comment_header_audit.py
```

### docstringテンプレート生成
```bash
# 違反箇所のテンプレートを生成
python scripts/generate_docstring_templates.py src/noveler/domain/services/example_service.py
```

### 違反サマリー
```bash
# Top 30の違反ファイルリスト
python scripts/extract_audit_files.py
```

---

## Side Effectsセクションの判断フローチャート

```
関数/メソッドを分析
    ↓
ファイルI/Oがある？ (read/write) → YES → 明示的に記載
    ↓ NO
ログ出力がある？ (logger.info など) → YES → 明示的に記載
    ↓ NO
イベント発行がある？ (event_bus.emit など) → YES → 明示的に記載
    ↓ NO
属性を変更する？ (self.xxx = ... など) → YES → 明示的に記載
    ↓ NO
外部サービスを呼ぶ？ (API, DB など) → YES → 明示的に記載
    ↓ NO
グローバル状態を変更する？ → YES → 明示的に記載
    ↓ NO
"None" と記載
```

---

## よくある質問

### Q1: `# File: ...` のパスは絶対パス？相対パス？
**A**: `src/` からの相対パスを使用します。
```python
# Good
# File: src/noveler/domain/services/example_service.py

# Bad
# File: /home/user/project/src/noveler/domain/services/example_service.py
# File: example_service.py
```

### Q2: Purposeセクションは日本語？英語？
**A**: **英語推奨**。技術用語は英語、説明文も英語が望ましいです。
```python
# Good
"""Example service for business logic operations.

Purpose:
    Coordinate business operations between entities and repositories.
"""

# OK (but less preferred)
"""ビジネスロジック操作のサービス例。

Purpose:
    エンティティとリポジトリ間のビジネス操作を調整する。
"""
```

### Q3: 純粋関数（副作用なし）の場合はどう書く？
**A**: `Side Effects: None` と明示してください。
```python
def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two integers.

    Purpose:
        Perform simple arithmetic addition.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        Sum of a and b.

    Side Effects:
        None - pure function.
    """
    return a + b
```

### Q4: private関数（`_`始まり）もdocstringが必要？
**A**: **Yes**。規約上、全関数にdocstringが必要です。
```python
def _internal_helper(self, data: dict) -> dict:
    """Internal helper for data transformation.

    Purpose:
        Transform data format for internal use only.

    Args:
        data: Input data dictionary.

    Returns:
        Transformed data dictionary.

    Side Effects:
        None - read-only transformation.
    """
```

### Q5: `__init__` や `__str__` などの特殊メソッドは？
**A**: **必要です**。特に `__init__` は重要です。
```python
def __init__(self, repository: Repository, logger: ILogger) -> None:
    """Initialize service with dependencies.

    Purpose:
        Set up service with required repository and logger.

    Args:
        repository: Data repository instance.
        logger: Logger instance for operation tracking.

    Side Effects:
        - Stores references to dependencies
        - Initializes internal state dictionaries
    """
```

### Q6: 既存コードの修正中にロジックの問題を見つけたら？
**A**: **絶対にロジックを変更しないでください**。docstring修正のPRとは別にissueを作成してください。
```
理由: docstring修正は「非破壊的変更」であり、ロジック修正を混ぜると
      レビューが困難になり、バグ混入のリスクが高まります。
```

---

## サンプルテンプレート集

### シンプルな関数
```python
def get_episode_count(self) -> int:
    """Get total number of episodes.

    Purpose:
        Retrieve count of all episodes in the project.

    Returns:
        Total episode count as integer.

    Side Effects:
        - Reads from episode repository
    """
```

### 複雑な関数（複数の引数・例外）
```python
def process_episode(
    self,
    episode_number: int,
    content: str,
    metadata: dict[str, Any] | None = None,
    *,
    validate: bool = True,
    dry_run: bool = False
) -> ProcessingResult:
    """Process episode content with validation and metadata.

    Purpose:
        Validate, transform, and persist episode content according to
        business rules. Optionally run in dry-run mode for testing.

    Args:
        episode_number: Episode number (1-based index).
        content: Raw episode content in Markdown format.
        metadata: Optional metadata dictionary (defaults to empty dict).
        validate: Whether to run validation (default: True).
        dry_run: Test mode without persistence (default: False).

    Returns:
        ProcessingResult containing success status, processed content,
        validation errors, and metadata.

    Raises:
        ValidationError: When content fails validation checks.
        RepositoryError: When persistence operation fails.
        ValueError: When episode_number is invalid (<= 0).

    Side Effects:
        - Reads validation rules from configuration
        - Writes processed content to repository (unless dry_run=True)
        - Emits EpisodeProcessedEvent via event bus
        - Logs processing metrics and errors
    """
```

### ファクトリーメソッド
```python
@classmethod
def create_from_config(cls, config: dict[str, Any]) -> "ExampleService":
    """Create service instance from configuration dictionary.

    Purpose:
        Factory method for creating fully configured service instance.

    Args:
        config: Configuration dictionary containing service settings.

    Returns:
        Initialized ExampleService instance.

    Raises:
        ConfigurationError: When required config keys are missing.

    Side Effects:
        - Instantiates dependency objects
        - May read additional config files
    """
```

### プロパティ
```python
@property
def is_ready(self) -> bool:
    """Check if service is ready for operations.

    Purpose:
        Determine if all dependencies are initialized and service
        is in operational state.

    Returns:
        True if service is ready, False otherwise.

    Side Effects:
        None - read-only property.
    """
```

---

## トラブルシューティング

### エラー: `Docstring must include 'Purpose:' section`
**原因**: docstringに `Purpose:` セクションがない
**解決**: docstring内に以下を追加
```python
Purpose:
    [関数/クラス/モジュールの責任を記述]
```

### エラー: `Docstring must include 'Args:' section for parameters`
**原因**: パラメータがあるのに `Args:` セクションがない
**解決**: 全パラメータを記述（`self`, `cls` は除外可）
```python
Args:
    param1: 説明
    param2: 説明
```

### エラー: `Docstring must include 'Returns:' section when values are returned`
**原因**: `return` 文があるのに `Returns:` セクションがない
**解決**: 戻り値の型と意味を記述
```python
Returns:
    戻り値の型と意味の説明
```

### エラー: `Docstring must describe side effects using 'Side Effects:' section`
**原因**: `Side Effects:` セクションがない
**解決**: 副作用を明示（ない場合は "None"）
```python
Side Effects:
    - I/O操作の説明
    - または "None"
```

### エラー: `Missing header comment (expected '# File: ...')`
**原因**: ファイル先頭にヘッダーコメントがない
**解決**: ファイル最上部（shebang行の後）に追加
```python
#!/usr/bin/env python3  # ← あれば
# File: src/noveler/domain/services/example_service.py  # ← 必須
# Purpose: [モジュールの責任]
# Context: [依存関係や制約]
```

---

## 継続的な準拠維持

### pre-commitフックの設定（将来対応）
```yaml
# .pre-commit-config.yaml に追加予定
- repo: local
  hooks:
    - id: docstring-audit
      name: Docstring Compliance Check
      entry: python scripts/comment_header_audit.py
      language: system
      types: [python]
      pass_filenames: true
```

### CI/CDパイプラインでのチェック（将来対応）
```yaml
# .github/workflows/compliance.yml に追加予定
- name: Check docstring compliance
  run: |
    python scripts/comment_header_audit.py
    if [ $? -ne 0 ]; then
      echo "Docstring compliance check failed!"
      exit 1
    fi
```

---

## 参考資料

- **規約**: [AGENTS.md](../../AGENTS.md) - 詳細な規約定義
- **規約**: [CLAUDE.md](../../CLAUDE.md) - プロジェクト固有ルール
- **分析レポート**: [reports/docstring_compliance_analysis.md](../../reports/docstring_compliance_analysis.md)
- **監査スクリプト**: [scripts/comment_header_audit.py](../../scripts/comment_header_audit.py)
- **テンプレート生成**: [scripts/generate_docstring_templates.py](../../scripts/generate_docstring_templates.py)

---

**作成**: Claude Code (Sonnet 4.5)
**最終更新**: 2025-10-12
