# ADR-001: ワークフローオーケストレーションの段階的移行戦略

**ステータス**: 承認済み
**日付**: 2025-10-03
**決定者**: 開発チーム
**関連コンポーネント**: Progressive Check Manager, WorkflowStateStore, IterationPolicy

---

## コンテキスト

小説原稿の品質チェックシステムでは、以下の要件が明らかになった:

1. **反復的品質改善**: 一度のチェックで合格するとは限らない
   - チェック → 修正 → 再チェック のループが必要
   - 収束判定(until_pass, min_improvement)が必要

2. **将来的な拡張要件**:
   - 並列チェック実行(複数アスペクトの同時評価)
   - 動的ワークフロー分岐(修正タイプに応じた次ステップ決定)
   - LangSmithによる反復プロセスの可視化・デバッグ支援

3. **既存実装状況**:
   - `IterationPolicy` で基本的な反復ロジックは実装済み
   - `FilesystemWorkflowStateStore` でファイルベースの状態管理
   - `_should_stop_iteration()` で収束判定ロジック
   - LangGraph依存関係は存在するが、実際のimportは0件

---

## 決定

**段階的移行戦略を採用し、LangGraph依存関係を保持する**

### Phase 1: Simple (現状) - 2025-10 ✅
- `IterationPolicy` + `FilesystemWorkflowStateStore` を使用
- 単一スレッド実行、シーケンシャルな反復
- 収束判定: `until_pass`, `min_improvement`, `count`

### Phase 2: Hybrid (2026-Q1予定)
- `WorkflowExecutor` プロトコルを導入
- 環境変数 `NOVELER_USE_LANGGRAPH=1` で切り替え可能
- LangGraphとSimpleの並行運用期間

実装例:
```python
class WorkflowExecutor(Protocol):
    """ワークフロー実行の抽象インターフェース"""
    def execute_step(self, step_id: int, context: SessionContext) -> StepResult: ...
    def should_stop(self, policy: IterationPolicy, history: list[StepResult]) -> bool: ...

class SimpleWorkflowExecutor:
    """現在のファイルベース実装"""
    pass

class LangGraphWorkflowExecutor:
    """LangGraphベース実装(並列・動的分岐対応)"""
    pass
```

### Phase 3: Full LangGraph (2026-Q2以降)
- 並列チェック実行
- 動的ワークフロー分岐
- LangSmith統合による可視化
- Simple実装はレガシーサポートとして残す

---

## 根拠

### なぜLangGraphを削除しないか

1. **YAGNI vs YAGNNI**:
   - ❌ "You Aren't Gonna Need It" (削除すべき)
   - ✅ "You Aren't Gonna Need It... **Now**" (将来必要)

2. **段階的移行のコスト削減**:
   - 依存関係を今削除 → 将来再追加 = 2回のPRレビュー・テスト
   - 依存関係を保持 → コメントで意図明示 = 0回の追加作業

3. **プロトコル駆動設計の利点**:
   - `WorkflowStateStore` プロトコルは変更不要
   - 実装の切り替えがDI層のみで完結
   - 既存コードへの影響を最小化

### なぜSimpleを残すか

1. **デバッグ容易性**: LangGraphのステートマシンより単純なファイルベースの方が問題切り分けしやすい
2. **エッジケース**: 小規模プロジェクトではSimpleで十分
3. **フォールバック**: LangGraph障害時の代替手段

---

## 結果

### ポジティブ

- ✅ 既存の `IterationPolicy` 実装が活用される
- ✅ 将来の拡張に備えて依存関係を保持(コメントで意図明示)
- ✅ プロトコル駆動設計により移行コストを最小化
- ✅ Simpleとの並行運用でリスク低減

### ネガティブ

- ⚠️ 使用していない依存関係が一時的に存在(ドキュメント化で対応)
- ⚠️ Phase 2移行時の実装コスト(プロトコル+2実装)

### リスク緩和策

1. **ドキュメント化**:
   - pyproject.toml に日本語コメントで意図を明示
   - workflow_state_store.py のdocstringを更新
   - この ADR で設計方針を記録

2. **段階的移行**:
   - Phase 1 で既存実装を安定化
   - Phase 2 で環境変数切り替え対応
   - Phase 3 で完全移行

3. **テスト戦略**:
   - `WorkflowExecutor` プロトコルの契約テスト
   - Simple/LangGraph両実装で同じテストスイート実行

---

## 関連ファイル

- [pyproject.toml:74-79](../../pyproject.toml#L74-L79) - LangGraph依存関係の説明コメント
- [pyproject.toml:102-107](../../pyproject.toml#L102-L107) - LangGraph依存関係の説明コメント(test)
- [src/noveler/domain/services/workflow_state_store.py:1-12](../../src/noveler/domain/services/workflow_state_store.py#L1-L12) - モジュールdocstring
- [src/noveler/domain/services/workflow_state_store.py:46-56](../../src/noveler/domain/services/workflow_state_store.py#L46-L56) - IterationPolicy docstring
- [docs/mcp/progressive_check_api.md:1](../mcp/progressive_check_api.md#L1) - API仕様書タイトル

---

## 参照

- [CLAUDE.md](../../CLAUDE.md) - プロジェクト規約
- [AGENTS.md](../../AGENTS.md) - 開発原則
- [LangGraph公式ドキュメント](https://langchain-ai.github.io/langgraph/)
- [LangSmith統合](https://docs.smith.langchain.com/)
