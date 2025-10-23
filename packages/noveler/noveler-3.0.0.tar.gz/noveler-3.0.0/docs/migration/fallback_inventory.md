# Fallback Inventory - 全フォールバック処理の棚卸し

**作成日**: 2025-10-11
**目的**: フォールバック完全削除（Option A）に向けた、現状のフォールバック処理の完全な棚卸し

---

## 📊 概要統計

| カテゴリ | 件数 | 影響度 | 削除優先度 |
|---------|------|--------|-----------|
| Path Service | 🔴 約10件 | Critical | **High** |
| Configuration Service | 🟡 約15件 | Medium | **Medium** |
| Repository/Data層 | 🟢 約8件 | Low | **Low** |
| Application/UseCase層 | 🟡 約12件 | Medium | **Medium** |
| MCP Server層 | 🟢 約30件 | Low | **Low** |

**総計**: 約75件のフォールバック処理が検出されました

---

## 🔴 Priority High: Path Service のフォールバック

### 1. PathServiceAdapter - project_root フォールバック

**ファイル**: `src/noveler/infrastructure/adapters/path_service_adapter.py:962`

```python
def create_path_service(project_root: Path | str | None = None) -> PathServiceAdapter:
    root = Path(project_root) if project_root is not None else Path.cwd()  # ← フォールバック
    return PathServiceAdapter(root)
```

**問題点**:
- `project_root` が `None` の場合、カレントディレクトリにフォールバック
- ユーザーが意図しないディレクトリで実行される可能性

**影響範囲**:
- 全ての MCP ツール、CLI コマンドが依存
- フォールバック発動時、誤ったディレクトリのデータを操作するリスク

**削除後の挙動**:
```python
def create_path_service(project_root: Path | str | None = None) -> PathServiceAdapter:
    if project_root is None:
        raise MissingProjectRootError(
            "PROJECT_ROOT is required. Please set it via environment variable or argument."
        )
    return PathServiceAdapter(Path(project_root))
```

---

### 2. PathServiceAdapter - get_management_dir フォールバック

**ファイル**: `src/noveler/infrastructure/adapters/path_service_adapter.py:188-190`

```python
# 最終手段: カレントディレクトリ配下
fallback2 = _Path.cwd() / "noveler_management"
fallback2.mkdir(parents=True, exist_ok=True)
return fallback2
```

**問題点**:
- 管理ディレクトリが見つからない場合、カレントディレクトリに勝手に作成
- ユーザーが気づかずに不要なディレクトリが生成される

**影響範囲**:
- 管理データ（バックアップ、レポート等）の保存先

**削除後の挙動**:
- 設定ファイルに `management_dir` が明示されていない場合は即座にエラー

---

### 3. PathServiceAdapter - hierarchical config の fallback

**ファイル**: `src/noveler/infrastructure/adapters/hierarchical_config_adapter.py:46`

```python
current = Path.cwd()  # ← フォールバック: 設定検索の起点
```

**問題点**:
- プロジェクトルートが不明な場合、カレントディレクトリから設定を探す
- 意図しない設定ファイルを読み込む可能性

**削除後の挙動**:
- プロジェクトルートが明示的に指定されていない場合はエラー

---

## 🟡 Priority Medium: Configuration Service のフォールバック

### 4. ConfigurationServiceAdapter - 全メソッドのフォールバック値

**ファイル**: `src/noveler/infrastructure/adapters/configuration_service_adapter.py:45-46, 67-68, 77-78, 90-91, 100-101, 110-111, 120-121`

**パターン**: すべてのメソッドで以下の構造
```python
def get(self, key: str, default: Any = None) -> Any:
    if self._wrapped_manager:
        return self._wrapped_manager.get(key, default)
    return self._fallback_config.get(key, default)  # ← フォールバック
```

**検出箇所**:
- `get()` - 汎用取得
- `get_project_root()` - プロジェクトルート（デフォルト: `"."`）
- `get_environment()` - 環境名（デフォルト: `"development"`）
- `get_api_config()` - API設定（デフォルト: `{}`）
- `get_database_config()` - DB設定（デフォルト: `{}`）
- `get_logging_config()` - ログ設定（デフォルト: `{}`）
- `get_feature_flags()` - フィーチャーフラグ（デフォルト: `{}`）
- `is_feature_enabled()` - フラグ有効性（デフォルト: `False`）

**問題点**:
- 設定が見つからない場合、静かにデフォルト値を返す
- ユーザーは設定不足に気づけない

**削除後の挙動**:
```python
def get(self, key: str, default: Any = None) -> Any:
    if self._wrapped_manager:
        return self._wrapped_manager.get(key, default)
    # フォールバック削除: 必須設定がない場合はエラー
    if default is None:
        raise ConfigurationNotFoundError(f"Required configuration '{key}' is missing")
    return default
```

---

### 5. Infrastructure Service - fallback_service 設定

**ファイル**: `src/noveler/application/infrastructure_services/infrastructure_configuration.py:37`

```python
@dataclass
class ServiceConfig:
    fallback_service: str | None = None  # ← フォールバックサービス名
```

**ファイル**: `src/noveler/application/infrastructure_services/infrastructure_integration_aggregate.py:383-402`

```python
def execute_service_with_fallback(self, service: Service, execution_context: ExecutionContext):
    ...
    fallback_name = service.configuration.get("fallback_service")
    if fallback_name and self.service_registry.is_registered(fallback_name):
        fallback_result = self.execute_service(fallback_name, execution_context)
        fallback_result.used_fallback = True  # ← フォールバック使用フラグ
        fallback_result.fallback_service = fallback_name
        fallback_result.metadata["fallback_reason"] = "メインサービスエラー"
        return fallback_result
```

**問題点**:
- サービス実行失敗時、自動的に別サービスにフォールバック
- ユーザーは元のサービスが失敗したことに気づきにくい
- **ただし、`used_fallback` フラグで検出可能**（現状は部分的に透明性あり）

**削除後の挙動**:
- サービス失敗時は即座にエラー送出（フォールバックなし）

---

## 🟢 Priority Low: Repository/Data層のフォールバック

### 6. FileEpisodeRepository - デフォルトディレクトリ

**ファイル**: `src/noveler/infrastructure/adapters/file_episode_repository.py:20`

```python
self.base_dir = base_dir or (Path.cwd() / "temp" / "ddd_repo")  # ← フォールバック
```

**ファイル**: `src/noveler/infrastructure/adapters/file_outbox_repository.py:25`

```python
self.base_dir = base_dir or (Path.cwd() / "temp" / "bus_outbox")  # ← フォールバック
```

**問題点**:
- `base_dir` が指定されない場合、カレントディレクトリ配下に自動作成
- 一時ファイルが散らばる原因

**削除後の挙動**:
- `base_dir` 必須化（インスタンス化時にエラー）

---

### 7. OutboxMessage のデフォルト値取得

**ファイル**: `src/noveler/infrastructure/adapters/file_outbox_repository.py:66-77`

```python
payload=data.get("payload", {}),  # ← フォールバック: 空dict
attempts=int(data.get("attempts", 0)),  # ← フォールバック: 0
dispatched_at=datetime.fromisoformat(data["dispatched_at"]) if data.get("dispatched_at") else None,
last_error=data.get("last_error"),  # ← フォールバック: None
```

**問題点**:
- JSON が不完全でも静かにデフォルト値で補完
- データ破損時に検出できない

**削除後の挙動**:
- 必須フィールドが欠けている場合は `DataIntegrityError` を送出

---

## 🟡 Priority Medium: Application/UseCase層のフォールバック

### 8. ErrorHandlingOrchestrator - fallback_func

**ファイル**: `src/noveler/application/orchestrators/error_handling_orchestrator.py:364, 418-426`

```python
def execute_with_error_handling(
    self,
    func: Callable,
    fallback_func: Callable | None = None,  # ← フォールバック関数
    ...
):
    ...
    # Try fallback function if available and recovery didn't work
    if fallback_func and not handling_result.recovery_successful:
        try:
            fallback_result = fallback_func()
            return ErrorHandlingResult(
                data=fallback_result,
                success=True,
                suggestions=["Used fallback function due to main function failure"],
            )
```

**問題点**:
- メイン処理失敗時、自動的にフォールバック処理を実行
- **ただし、`suggestions` で明示される**（透明性あり）

**削除後の挙動**:
- `fallback_func` 引数を削除し、失敗は即座にエラーとして伝播

---

### 9. PlotGenerationOrchestrator - fallback strategies

**ファイル**: `src/noveler/application/orchestrators/plot_generation_orchestrator.py:61, 142`

```python
# ドキュメントでの言及
# - Manage fallback strategies for plot generation

strategies = [
    {"name": "combined", "description": "Combined approach with fallback strategy"},
]
```

**問題点**:
- プロット生成失敗時のフォールバック戦略が存在する可能性
- **要詳細調査**（コメントのみで具体的コードは未確認）

---

### 10. A30CompatibilityAdapter - _create_fallback_prompt

**ファイル**: `src/noveler/application/services/a30_compatibility_adapter.py:128, 141`

```python
return self._create_fallback_prompt(stage, context_data)
```

**問題点**:
- プロンプト生成失敗時、フォールバックプロンプトを使用
- **要詳細調査**（実装確認が必要）

---

## 🟢 Priority Low: MCP Server層のフォールバック

### 11. MCP ToolBase - PathService fallback 収集機構

**ファイル**: `src/mcp_servers/noveler/domain/entities/mcp_tool_base.py:109, 171-188`

```python
self._fallback_events: list[dict] = []

def _ps_collect_fallback(self, *services: Any) -> None:
    """Collect fallback events emitted by path service instances."""
    for ps in services:
        if ps:
            if hasattr(ps, "get_and_clear_fallback_events"):
                ev = ps.get_and_clear_fallback_events() or []
                if ev:
                    self._fallback_events.extend(ev)

def _apply_fallback_metadata(self, response: "ToolResponse") -> None:
    """Attach collected fallback events to the response metadata."""
    if getattr(self, "_fallback_events", None):
        response.metadata["path_fallback_used"] = True
        response.metadata["path_fallback_events"] = list(self._fallback_events)
        self._fallback_events.clear()
```

**検出箇所**: 約30箇所のツールで使用
- `backup_tool.py`
- `check_grammar_tool.py`
- `check_readability_tool.py`
- `check_rhythm_tool.py`
- `check_style_tool.py`
- `export_quality_report_tool.py`
- `fix_quality_issues_tool.py`
- `fix_style_extended_tool.py`
- 他多数...

**問題点**:
- **これは既に透明性を担保する仕組み**
- フォールバック発動時に `metadata["path_fallback_used"] = True` で明示
- **Phase 1 で目指す「検出＋警告＋メタデータ」は既に実装済み！**

**今後の方針**:
- **Phase 1 は既に達成済み** → **Phase 2（削除）に直行可能**
- この仕組みを活用し、strict mode で `path_fallback_used=True` の場合はエラーに昇格

---

### 12. JSON 変換サーバーの fallback 処理

**ファイル**: `src/mcp_servers/noveler/async_json_conversion_server.py:730-755`

```python
def _parse_json_block(stdout: str) -> dict[str, Any]:
    """
    Try to parse a JSON block from CLI stdout; fallback to text.

    Returns:
        dict[str, Any]: Parsed JSON or a fallback structure.
    """
    ...
    # Fallback: wrap as text
    return {
        "raw_output": stdout,
        "extraction_method": "text_fallback"
    }
```

**問題点**:
- JSON パース失敗時、テキストとして返す
- **ただし、`extraction_method: "text_fallback"` で明示される**（透明性あり）

**削除後の挙動**:
- JSON パース失敗時は `JSONDecodeError` を送出

---

## 📝 削除戦略のまとめ

### Phase 0 完了事項
✅ フォールバック箇所の完全棚卸し（75件）
✅ 影響度・優先度の分類
✅ 既存の透明性担保機構の発見（MCP ToolBase）

### Phase 1 への影響
**重要な発見**: MCP Server 層では既に `path_fallback_used` メタデータで透明性が確保されている
- Phase 1 で実装予定の「FallbackDetector」は **部分的に実装済み**
- 新規実装は Path Service / Configuration Service に限定可能

### Phase 2 実行順序（修正版）

#### 2.1 Path Service（優先度 High）
1. `create_path_service()` の `Path.cwd()` フォールバック削除
2. `get_management_dir()` の自動作成ロジック削除
3. `hierarchical_config_adapter` のカレントディレクトリ探索削除

#### 2.2 Configuration Service（優先度 Medium）
4. `ConfigurationServiceAdapter` の全デフォルト値削除
5. `.env.example` に必須設定を明記

#### 2.3 Repository層（優先度 Low）
6. `FileEpisodeRepository` / `FileOutboxRepository` の `base_dir` 必須化
7. JSON データの必須フィールド検証強化

#### 2.4 Application層（優先度 Medium）
8. `ErrorHandlingOrchestrator` の `fallback_func` 削除
9. `PlotGenerationOrchestrator` のフォールバック戦略削除（要調査）
10. `A30CompatibilityAdapter` のフォールバックプロンプト削除（要調査）

#### 2.5 MCP Server層（優先度 Low）
11. JSON パース失敗時のフォールバックを削除（strict mode のみ）

---

## 🎯 次のアクション（Phase 0.2）

1. **影響範囲分析**: 各フォールバック削除時の依存関係を洗い出し
2. **テストカバレッジ確認**: 既存テストがフォールバック処理をカバーしているか検証
3. **Phase 1 設計**: StrictModeConfig と FallbackDetector の詳細設計

---

## 📚 参考

このドキュメントは、Option A（フォールバック完全削除）の安全な移行を実現するための Phase 0（準備フェーズ）の成果物です。