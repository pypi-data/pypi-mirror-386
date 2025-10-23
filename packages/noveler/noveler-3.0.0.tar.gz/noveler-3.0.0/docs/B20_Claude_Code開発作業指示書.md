# B20 Claude Code開発ガイド統合版

**最終更新**: 2025年9月22日
**対象**: 新機能実装・バグ修正時のClaude Code開発作業
**用途**: B20準拠開発プロセス + SPEC-901 DDD MessageBus統合リファレンス
**模範実装**: 4つの参照リポジトリパターン + MessageBus開発パターン統合
**新機能**: novelerコマンド・MCPサーバー・MessageBus/DDD対応

---

## 📋 目次

1. [目的と原則](#目的と原則) ⭐ **NEW**
2. [変更タイプ別プレイブック](#変更タイプ別プレイブック) ⭐ **NEW**
3. [標準フロー（全タイプ共通）](#標準フロー全タイプ共通) ⭐ **NEW**
4. [成果物と受け入れ基準（DoD）](#成果物と受け入れ基準dod) ⭐ **NEW**
5. [自動化コマンドとゲート](#自動化コマンドとゲート) ⭐ **NEW**
6. [ロールバックとリリース運用](#ロールバックとリリース運用) ⭐ **NEW**
7. [ケーススタディ: 行幅/強制改行撤廃](#ケーススタディ-行幅強制改行撤廃) ⭐ **NEW**
8. [既存実装優先開発](#既存実装優先開発)
9. [開発プロセス概要](#開発プロセス概要)
10. [MCPサーバー統合開発](#mcpサーバー統合開発)
11. [3コミット開発サイクル](#3コミット開発サイクル)
12. [アーキテクチャ指針](#アーキテクチャ指針)
13. [CODEMAP活用](#codemap活用)
14. [品質ゲート](#品質ゲート)
15. [Git Hooks統合](#git-hooks統合)

---

## 目的と原則

- 小さく安全で可逆な変更を積み上げる（Small, clear, safe steps）
- ドキュメント先行（PRD→仕様→要件）と実装の双方向同期（As-built）
- TDD/TCRを基本姿勢に「露出を先に消すテスト」から着手
- トレーサビリティ優先（requirements/specs/tests/docs/CHANGELOG を一気通貫）
- 依存の追加は最小・既存の再利用を最優先
- B20サイクルで得た教訓を標準フローとチェックリストで再利用し、水平展開時の迷いを排除する
- チーム外（LLM含む）へ依頼する場合でもフェーズの目的・完了条件を明示してアウトプット品質を担保する
- 影響調査は `scripts/tools/impact_audit.py` を軸にして、生成レポート（temp/impact_audit もしくは reports/impact-summary.md）を次フェーズのインプットへ引き継ぐ

---

## 変更タイプ別プレイブック

### 機能削除（破壊的変更、今回の型）
- 合意: 目的/非スコープ/受入基準をPRDで明文化（Breaking明示）
- 影響調査: スキーマ/CLI/設定/理由コード/プリセット/README/ガイド/要件/仕様/テストを網羅（B20では85箇所超を確認）
- LangGraph 常時有効: `WorkflowStateStore` と QC-015〜018 を含むハッシュ参照要件を SPEC-QUALITY-120 と突き合わせ、`progressive_check.start_session` の露出が無いことを確認。CLI では未対応コマンド呼び出し時に `progressive_check.get_tasks` への誘導メッセージを返す実装を必須化。
- TDD: 露出ゼロや挙動しないことを先に固定（スキーマ/メタ/CLIの「出ないテスト」）
- 実装: 露出遮断→ロジック撤廃の順に最小差分で適用（可逆性重視）
- 文書: requirements/とspecs/を更新→README/ガイド→CHANGELOG→SemVerメジャー
- チェック: コミット毎にDoDを確認し、段階統合パターンを守れているかレビュー

### 機能追加
- 合意: PRD/UX/API契約→スキーマから先に生やす（契約テスト）
- TDD: happy/edge/冪等/回帰の順で追加→実装→E2E最小
- 文書: 仕様/要件/README/使用例→CHANGELOG（Added）

### 振る舞い変更（互換）
- 合意: 変更点/互換性/移行をPRDに記載（Breakingでないことを明示）
- TDD: 新旧の期待差分をテストに落とす→実装→ドキュメント差分

### リファクタ
- 合意: 外部契約不変の宣言→計測指標（パフォ/メモリ）を事前定義
- TDD: ふるまい固定化テスト→内部置換→計測→回帰

### ドキュメントのみ
- 仕様/要件の整合→サンプル/ガイド更新→検証リンク（該当テスト）

---

## 標準フロー（全タイプ共通）

1) **合意/PRD作成** – 目的/スコープ/非スコープ/受入/影響/移行/リスク/ロールバックを明文化。
   - Lesson Learned: 合意形成が曖昧だと下流で手戻り。PRDテンプレを使い、LLMへの依頼時も必ず共有。
   - 成果物: PRD、想定コミット構成、品質ゲート一覧。
2) **影響調査** – `rg` 等で露出点を洗い出し、想定変更点とフォールバックパスを記録。
   - Lesson Learned: 85+箇所の露出棚卸で段階的移行戦略を立案できた。大型変更では必須ステップ。
   - 成果物: 影響調査シート（`impact_audit.py` 自動レポート + 露出一覧・優先度・移行案・検証方法メモ）。
3) **TDD（RED）** – 仕様書を実装ガイドとして先行させ、露出遮断テスト・品質ゲートテストを追加しFailを確認。
   - Lesson Learned: RED→GREEN→REFACTORを守ることで想定外挙動を防止。失敗テストは段階統合パターンの第1コミットに収める。
   - 成果物: 仕様書更新、Failする自動テスト、期待するログ/メトリクスの記載。
4) **最小実装（GREEN）** – フォールバック戦略を保ったまま最小差分実装。
   - Lesson Learned: デフォルト設定で互換性を維持しながら新挙動を提供。DDD原則でビジネスロジックを純粋化。
   - 成果物: ドメインサービス/インフラ層実装、成功する単体テスト、フォールバック確認メモ。
5) **段階的統合（REFACTOR）** – コミット2で最小実装、コミット3で既存統合とリファクタ。
   - Lesson Learned: 「仕様+失敗テスト」「最小実装」「既存統合」の3コミットでレビューとリリースが容易に。
   - 成果物: インテグレーション完了報告、品質ゲート結果、リファクタ記録。
6) **仕様/要件同期** – requirements/ と specs/ を同時更新し、トレーサビリティを担保。
   - Lesson Learned: ドキュメントが実装ガイドとして機能するため、差分を即同期。
   - 成果物: 更新済み仕様/要件、差分要約、関連JIRA/issueリンク。
7) **ドキュメント/リリース整備** – README/ガイド/設定例更新 → CHANGELOG → SemVerバンプ → `make ci` → `make build`。
   - Lesson Learned: リリース前に品質ゲート自動化を通し、戻し手順（コミット粒度）を確認。
   - 成果物: 更新ドキュメント、CHANGELOG、リリースノート草案、ロールバック手順。

---


## 成果物と受け入れ基準（DoD）

- Tests: 追加/更新テストが露出ゼロ・冪等性・回帰を固定し、RED→GREEN→REFACTORの痕跡が残っている
- LangGraph品質系: `progressive_check.get_tasks` で `session_id` を払い出すこと、`.noveler/checks/<session_id>/manifest.json` と LLM入出力ログを生成することをユニット/統合テストで検証し、`available_tools`/`manuscript_hash` 指標と併せて SPEC-QUALITY-120 の PoC 指標を測定する。`progressive_check.start_session` を呼び出した場合は CLI ガイダンス（"use progressive_check.get_tasks"）を返すことを確認する。
- Specs/Requirements: 破壊的変更や受入基準が明記され、PRD/仕様/テスト間でトレーサビリティが確保されている
- Docs: README/ガイド/設定例が最新の仕様に一致し、水平展開時の手順（チェックリスト）と最新のimpact_auditレポートへの導線を掲載
- CLI/Schema: 期待しないキーや理由コードが露出しておらず、フォールバック戦略が回帰テストで担保されている
- CHANGELOG: 背景と移行・影響が明記され、段階統合の要約とロールバック手順へリンク
- SemVer: バージョンバンプとタグ準備が完了し、リリース前品質ゲート（自動化コマンド含む）を通過
- レビュー記録: コミット毎にチェックリストをクリアした証跡（コメント・ツール出力）を残す

---

## 自動化コマンドとゲート

推奨コマンド例（*既存*と*改善案*を併記）:
```bash
# 行幅関連の露出禁止トークン（例）
rg -n "LINE_WIDTH_OVERFLOW|enable_line_wrap|max_line_width" -S src docs README.md

# 主要CIタスク
make ci      # lint + tests + dry-run + smoke
make build   # 本番配布物生成（dist/bin/）

# 影響調査の自動化（pre-commit/CI連携済み）
python scripts/tools/impact_audit.py --pattern ".yaml" --output temp/impact_audit/latest.md
# 手動レビューや共有用途では --output reports/impact-summary.md を指定

# チェックリスト生成（PRテンプレ連携・準備中）
python scripts/tools/generate_b20_checklist.py --spec SPEC-XXX-YYY --output .github/pull_request_template.md

# 品質ゲート段階実行（コミット毎の推奨運用）
python src/noveler/tools/quality_gate_check.py --stage commit1
python src/noveler/tools/quality_gate_check.py --stage commit2
python src/noveler/tools/quality_gate_check.py --stage commit3
```

---

## ロールバックとリリース運用

- コミット粒度: 仕様/テスト→実装→ドキュメント→バージョン/ビルドに分割（revert容易）
- CHANGELOG: Breaking/Removed/Changed/Docs/Tests/Migration の型で記述
- バージョニング: 破壊的変更はメジャー必須、タグ付けとリリースノートの連携

---

## ケーススタディ: 行幅/強制改行撤廃

背景: `noveler check 1 --auto-fix` が長行を強制改行し可読性を損ねていた。

決定: 日本語文への自動改行と行幅警告を全サブコマンドから撤廃し、`--auto-fix` でも改行を挿入しない。

実施ポイント:
- PRD/要件・仕様の合意（撤廃範囲、非スコープ=unwrap、受入=冪等/露出ゼロ）
- TDDで露出ゼロを先に固定
  - `check_rhythm` のスキーマから `line_width`/しきい値が出ない
  - `fix_quality_issues` に `enable_line_wrap`/`max_line_width` が無い、改行を挿入しない
  - qualityメタデータから line width を排除
- 実装: 露出遮断→ロジック撤廃の順で最小差分
- 同期: requirements/specs/README/ガイド/設定例/CHANGELOG を更新
- リリース: `2.0.0` へメジャー上げ、`make build` で生成物確認

---

## 既存実装優先開発

### 🚨 根本問題の解決

**問題**: 機能を新規実装するとき、往々にして既存のファイルを無視して新規開発してしまう

**解決策**: 5段階の包括的防止システム

### 📋 Phase 1: 実装前必須チェック

#### 仕様書作成時の既存実装調査（必須）
```bash
# 1. CODEMAP.yaml確認
grep -i "機能名" CODEMAP.yaml

# 2. 類似機能検索
find src/ -name "*.py" -exec grep -l "関連キーワード" {} \;

# 3. 実装前チェック実行
./scripts/tools/pre_implementation_check.sh "新機能名"
```

#### 仕様書テンプレート強化済み
- `specs/TEMPLATE_STANDARD_SPEC.md`に「**4.0 既存実装調査（必須）**」追加
- CODEMAP確認、共有コンポーネント確認、再利用可否判定を義務化

### 🛠️ Phase 2: 共有コンポーネント必須使用

#### ❌ 絶対禁止パターン
```python
# Console重複
from rich.console import Console
console = Console()  # 絶対禁止！

# Logger重複
import logging
logger = logging.getLogger(__name__)  # 絶対禁止！

# パスハードコーディング
path = "40_原稿"  # 絶対禁止！
```

#### ✅ 必須使用パターン
```python
# 統一Console使用
from noveler.presentation.shared.shared_utilities import console

# 統一Logger使用
from noveler.infrastructure.logging.unified_logger import get_logger
logger = get_logger(__name__)

# パス管理統一
from noveler.presentation.shared.shared_utilities import get_common_path_service
path_service = get_common_path_service()
manuscript_dir = path_service.get_manuscript_dir()
```

#### 詳細ガイド
- **完全リファレンス**: `docs/references/shared_components_catalog.md`
- **50+メソッド**: CommonPathServiceの全機能
- **Repository ABC**: 継承必須の抽象基底クラス

### 🔍 Phase 3: 自動検出システム

#### 重複実装検出ツール
```bash
# 重複実装検出実行
python scripts/tools/duplicate_implementation_detector.py

# 自動修正実行
python scripts/tools/duplicate_implementation_detector.py --fix
```

#### 検出対象
- Console()直接インスタンス化（Critical）
- import logging使用（High）
- パスハードコーディング（High）
- Repository ABC未継承（Medium）

### 🔧 Phase 4: Git Hooks統合

#### 自動防止システム設定
```bash
# Git Hooks設定（1回のみ実行）
./scripts/tools/setup_duplicate_prevention_hooks.sh
```

#### 動作内容
- **pre-commit**: 新規ファイル作成時の重複チェック
- **pre-push**: 統合品質チェック実行
- **自動ブロック**: 違反時のコミット/プッシュ阻止

### 📊 効果測定

| 項目 | 修正前 | 修正後 |
|------|---------|--------|
| Console重複 | 18件 | **0件** |
| Logger重複 | 604件 | **段階的0件** |
| パスハードコーディング | 87件 | **0件** |
| 開発効率 | - | **+30%** |
| 保守性 | 低 | **高** |

### ⚡ クイックスタート（テスト実行の既定）

1. **実装前**: `./scripts/tools/pre_implementation_check.sh "機能名"`
2. **開発中**: `docs/references/shared_components_catalog.md`参照
3. **コミット前**: 自動チェック実行（Git Hooks）
4. **テスト**: `bin/test --xdist-auto --timeout=300` を基本に、`-k`/`-m`/`--maxfail` で範囲・失敗閾値を調整
5. **定期確認**: `python scripts/tools/duplicate_implementation_detector.py`

---

## SPEC-901 MessageBus/DDD開発パターン ⭐ **NEW**

### 🔧 MessageBus実装パターン

#### Phase 1: MessageBus導入
```python
# 1. MessageBus設定
from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.uow import InMemoryUnitOfWork

bus = MessageBus(
    config=BusConfig(max_retries=3, dlq_max_attempts=5),
    uow_factory=lambda: InMemoryUnitOfWork(episode_repo=repo),
    idempotency_store=idempotency_store
)

# 2. コマンドハンドラー登録
async def handle_create_episode(data: Dict[str, Any], *, uow: UnitOfWork) -> Dict[str, Any]:
    episode_id = data.get("episode_id")
    # UseCase処理...
    uow.add_event("episode.created", {"episode_id": episode_id})
    return {"success": True, "episode_id": episode_id}

bus.command_handlers["create_episode"] = handle_create_episode
```

#### Phase 2: 既存UseCase統合
```python
# 3. UseCaseBusAdapter使用（段階的移行）
from noveler.application.adapters.usecase_bus_adapter import UseCaseBusAdapter

adapter = UseCaseBusAdapter(bus)
adapter.register_usecase("quality_check", QualityCheckUseCase, logger=logger)

# 4. 統一API経由実行
result = await adapter.execute_usecase_via_bus(
    "quality_check",
    {"episode_id": "ep-001", "check_types": ["grammar", "readability"]}
)
```

#### Phase 3: イベント駆動設計
```python
# 5. イベントハンドラー登録（名前空間付き）
async def handle_episode_created(event):
    # 自動品質チェック実行
    await bus.handle_command("check_quality", {"episode_id": event.payload["episode_id"]})

bus.event_handlers["episode.created"] = [handle_episode_created]

# 6. イベント発行
await bus.emit("episode.published", {"episode_id": "ep-001", "platform": "web"})
```

#### Phase 4: 信頼性/可観測性
```python
# 7. Outbox手動フラッシュ
processed_count = await bus.flush_outbox()
print(f"Processed {processed_count} outbox entries")

# 8. メトリクス確認
metrics = bus.get_metrics_summary()
print(f"Commands: {metrics['commands_processed']}, P95: {metrics['latency_p95_ms']}ms")

# 9. ヘルスチェック
health = bus.get_health_status()
if not health["healthy"]:
    print(f"Bus unhealthy: {health['issues']}")
```

### 🔍 DDD層設計原則

#### 依存関係ルール（Clean Architecture）
```python
# ✅ 正しい依存方向
# Presentation → Application → Domain ← Infrastructure

# Application層でのDomain使用（OK）
from noveler.domain.entities.episode import Episode
from noveler.domain.repositories.episode_repository import EpisodeRepository

# Domain層での他層参照（NG）
# from noveler.application.services.quality_service import QualityService  # 禁止！
# from noveler.infrastructure.adapters.file_repository import FileRepository  # 禁止！
```

#### MessageBus配置とDI
```python
# MessageBusはApplication層に配置
# Infrastructure層でのインスタンス化、Presentation層で使用

# Infrastructure層（インスタンス化）
def create_message_bus() -> MessageBus:
    repo = InMemoryEpisodeRepository()
    uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    return MessageBus(config=BusConfig(), uow_factory=uow_factory)

# Presentation層（使用）
bus = create_message_bus()
await bus.handle_command("create_episode", data)
```

### 🧪 MessageBusテストパターン

#### 単体テスト
```python
@pytest.mark.asyncio
async def test_episode_creation_command():
    # Given
    bus = create_test_message_bus()

    # When
    result = await bus.handle_command("create_episode", {
        "episode_id": "test-ep-001",
        "title": "Test Episode"
    })

    # Then
    assert result["success"] is True
    events = bus.outbox_repo.load_pending()
    assert len(events) == 1
    assert events[0].name == "episode.created"
```

#### パフォーマンステスト
```python
@pytest.mark.asyncio
async def test_messagebus_performance():
    # SPEC-901要件: P95 < 1ms
    bus = create_test_message_bus()
    latencies = []

    for _ in range(1000):
        start = time.perf_counter()
        await bus.handle_command("benchmark_command", {"data": "test"})
        latencies.append(time.perf_counter() - start)

    p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    assert p95 < 0.001  # < 1ms
```

## MCPサーバー統合開発

### 🔗 MCPサーバー概要
2025年8月30日より、Claude Codeとの統合を強化するMCPサーバー機能が追加されました。

#### 主要機能
- **コマンド名変更**: `novel` → `noveler` に統一
- **MCPサーバー**: Claude Codeから直接操作可能
- **JSON変換**: 95%のトークン削減を実現
- **リアルタイム統合**: AIによる執筆支援

#### 開発環境でのMCPサーバー起動
```bash
# 開発モードでMCPサーバー起動
noveler mcp-server --dev --port 3001

# デバッグ情報付きで起動
noveler mcp-server --dev --port 3001 --debug

# バックグラウンドで起動（開発時）
nohup noveler mcp-server --dev --port 3001 &
```

#### テスト実行
```bash
# MCPサーバー統合テスト
# 実務では `scripts/run_pytest.py` / `bin/test` を推奨（以下は直pytestの参考例）
python -m pytest tests/integration/test_mcp_server.py -v

# Claude Code統合テスト
python -m pytest tests/integration/test_claude_code_integration.py -v
```

### 🛠️ 開発時の注意点
- CLI 役割分離: check=評価, polish=改稿（破壊的変更を避けるため維持）
- テンプレ探索順: checks → backup → writing（正本優先、backupは参照専用）
1. **コマンド名**: 全て `noveler` に統一済み
2. **MCP連携**: Claude Codeからの操作を考慮した設計
3. **JSON出力**: 構造化データでの効率的な通信
4. **エラーハンドリング**: MCPサーバー経由のエラーも適切に処理
5. **Composition Root**: presentation/mcp 配下で委譲を集中（dispatcher/entrypoints/handlers/server_runtime）。`mcp_servers/noveler/main.py` は `noveler.presentation.mcp.server_runtime` を再輸入する薄いラッパーに統一
   - Outbox / Idempotency のファイルは `<project>/temp/outbox/` 配下に保存される（`pending/`・`processing/`・`sent/`・`errored/` ディレクトリ + `idempotency.json`）。
   - 開発／CI でリセットしたい場合は `rm -rf temp/outbox` を実行し、次回アクセス時に自動再生成される。
   - 将来の server 実装や差し替えは `noveler.presentation.mcp.server_runtime` を更新し、legacy パスは触らない運用とする


### 📦 軽量出力原則（B20準拠）
- 本文は原則レスポンスに含めない。識別は `issue_id` / `file_hash` / `line_hash` / `block_hash` を用いる。
- 具体的な文脈が必要な場合のみ `get_issue_context` で前後数行のスニペットを取得。
- `run_quality_checks` の標準オプション:
  - `format: "summary"` で要約のみ（行数/文数/会話比率/最長行/件数/各アスペクトスコア）。
  - `page` / `page_size` によるページネーションを必須運用（応答肥大化防止）。
  - 既定安全上限: 詳細は最大200件。超過時は `metadata.pagination` と `truncated: true` を返す。
  - `format: "ndjson"` は、ページ適用後の範囲のみを `metadata.ndjson` に同梱。
  - 付与メタ: `total_issues` / `returned_issues` / `aspect_scores` / `pagination` / `truncated`。
  - 対応範囲: `run_quality_checks` / `improve_quality_until` / `fix_quality_issues` / `export_quality_report` に加え、`check_readability` / `check_grammar` / `check_style` / `check_rhythm` / `polish_manuscript` / `polish_manuscript_apply` / `polish` / `restore_manuscript_from_artifact` / `analyze_test_results` / `backup_management` でも同じ `format` / `page` / `page_size` / `ndjson` を受け付ける。`get_issue_context` はスニペット用途のため全文取得を維持。
  - CI/本番では `MCP_LIGHTWEIGHT_DEFAULT=1` を既定値として運用し、必要時のみ `MCP_LIGHTWEIGHT_DEFAULT=0` でフル出力へフォールバックする。
 - 開発/検証のクイックコマンド例:
```bash
MCP_LIGHTWEIGHT_DEFAULT=1 noveler mcp call run_quality_checks '{"episode_number": 1, "page": 2, "page_size": 25}'
noveler mcp call check_readability '{"episode_number": 1, "format": "ndjson", "page_size": 10}'
noveler mcp call fix_quality_issues '{"episode_number": 1, "format": "summary", "page_size": 20}'
```
- `fix_quality_issues` の標準オプション:
  - `include_diff: false` を既定（必要時のみ短縮diffを返す）。
  - `max_diff_lines` でdiff行数を制限（省略表示）。
  - 自動修正は安全な `reason_codes` に限定（三点リーダ/ダッシュ統一・短文/長文の安全分割/連結・句読点の基本正規化等）。

### 🗃️ MessageBus 運用メモ（SPEC-901完全実装）
- **出力先**: `<project>/temp/bus_outbox/`
  - `pending/` ディレクトリに配信待ちイベントが JSON で保存される
  - `dlq/` ディレクトリに配信失敗イベント（5回試行後）が退避される
  - べき等性情報は InMemory で管理（プロセス終了でリセット）
- **初期化**: テストや検証後にクリアしたい場合は `rm -rf temp/bus_outbox` を実行。次のコマンド実行時に自動で再生成される。
- **運用機能**（完全実装済み）:
  - ✅ 背景フラッシュタスク（30秒間隔、`NOVELER_DISABLE_BACKGROUND_FLUSH=1` で無効化）
  - ✅ Dead Letter Queue（5回失敗で DLQ 移行、エラー情報保持）
  - ✅ メトリクス収集（処理時間 P50/P95、失敗率）
  - ✅ 運用 CLI: `noveler bus flush|list|replay|health|metrics`
- **運用コマンド例**:
  ```bash
  noveler bus health --detailed         # ヘルス状況とDLQ統計
  noveler bus list --type dlq          # 失敗イベント一覧
  noveler bus flush --dry-run          # フラッシュ対象の確認
  noveler bus metrics --reset          # パフォーマンス指標の表示とリセット
  ```
- **注意**: ファイルベースで軽量実装のため、CI では並列実行時の競合を避けるためワークスペースを分離。

### 🔁 段階ゲート方式（評価項目ごとの反復）
- 各評価項目で「自動修正 → 再評価」を反復し、合格（既定 `target_score: 80`）で次項目へ進む。
- 反復制御: `max_iterations: 3` / `min_delta: 0.5`（改善が頭打ちなら打ち切り）。
- 推奨順序: 内容/会話比率の確認 → リズム → 可読性 → 文法 → 最終総合確認。
- 単位: シーン単位での実行を推奨（副作用とトークンを局所化）。
- オーケストレーター: `improve_quality_until` ツールで自動実行に対応（本文非同梱・ハッシュ/ID中心）。

---

## Functional Core / Imperative Shell アーキテクチャ

### 🏗️ FC/IS パターンの基本原則

**Functional Core（機能核）**:
- ビジネスロジック = 純粋関数（副作用なし）
- 100+の純粋関数が実装・検証済み
- 決定論的で予測可能な計算
- 単体テストで完全に検証可能

**Imperative Shell（命令殻）**:
- I/O・CLI・永続化 = 薄いラッパー層
- 外部システムとの境界面
- E2Eテストで動作保証
- 副作用を局所化

### 🔧 実装済みツール

#### 契約テストフレームワーク
```python
# tests/contracts/ - 純粋関数の契約保証
from tests.contracts import FunctionalCoreContract

class MyDomainService(FunctionalCoreContract):
    def is_pure(self) -> bool: ...
    def is_deterministic(self) -> bool: ...
```

#### 純粋関数検証
```python
# src/noveler/domain/value_objects/function_signature.py
def ensure_pure_function(func) -> bool:
    """純粋関数であることを保証（Functional Core強化）"""
```

#### ガイドライン
- **Domain層**: 純粋関数のみ（副作用禁止）
- **Infrastructure層**: 薄いShell実装
- **Application層**: Core→Shell調整
- **Presentation層**: 最薄のユーザーインターフェース

---

## 開発プロセス概要

### 🎯 必須遵守事項

1. **仕様書先行開発** - 全ての実装は仕様書（SPEC-XXX-YYY）から開始
2. **3コミット開発サイクル** - 仕様→実装→統合の3段階を厳守
3. **CODEMAP事前確認** - 実装前の類似機能確認が必須
4. **B30品質基準準拠** - テストカバレッジ80%以上を維持

### 開発フロー

```mermaid
graph LR
    A[仕様書作成] --> B[CODEMAP確認]
    B --> C[テスト作成]
    C --> D[実装]
    D --> E[統合・リファクタリング]
    E --> F[品質ゲート]
```

---

## 3コミット開発サイクル

### 事前準備（実装着手前必須）

```bash
# 1. システム理解・競合チェック
noveler codemap overview                           # アーキテクチャ全体把握
noveler codemap discover-existing <機能概要>       # 類似機能発見（NIH症候群防止）

# 2. 事前実装チェック（必須）
noveler codemap pre-check <機能名> --target-layer domain --create-missing-spec

# 3. Git Hooks統合（初回のみ）
noveler codemap install-hooks --git-root <プロジェクトパス>

# 4. 模範実装パターン参照（推奨）
# ../___code-master          - Unit of Work, Event-driven Architecture
# ../___python-ddd-main      - AggregateRoot, Domain Rules
# ../___pytest-archon-main   - Architecture Boundary Testing
# ../___import-linter-main   - Import Contract Management
```

### 第1コミット: 仕様書+失敗テスト

```bash
# ブランチ作成
git checkout -b feature/SPEC-XXX-YYY-機能名

# 仕様書作成
echo "# SPEC-XXX-YYY: 機能名" > specs/SPEC-XXX-YYY.md

# テスト作成（失敗する状態）
cat > tests/unit/test_xxx.py << EOF
import pytest

@pytest.mark.spec("SPEC-XXX-YYY")
def test_機能名():
    # Arrange
    # Act
    # Assert
    assert False  # RED状態
EOF

# コミット
git add specs/ tests/
git commit -m "docs+test: SPEC-XXX-YYY 仕様書作成 + 失敗テスト作成"
```

### 第2コミット: 最小実装

```bash
# 実装（テストがGREENになる最小限）
# Domain層から実装開始

# 実装進捗追跡
noveler codemap track-implementation <機能名>

# テスト実行
noveler test run --unit

# コミット
git add src/noveler/domain/
git commit -m "feat: SPEC-XXX-YYY 最小実装 - 全テストパス"
```

### 第3コミット: 統合+リファクタリング

```bash
# 全層統合
noveler codemap integration-check <機能名>

# リファクタリング
# - DDD原則適用
# - CommonPathService統合
# - エラーハンドリング追加

# CODEMAP更新
python src/noveler/tools/dependency_analyzer.py

# コミット
git add -A
git commit -m "refactor: SPEC-XXX-YYY DDD適用 + CLI統合完了"
```

---

## アーキテクチャ指針

### DDD層構造（模範実装パターン適用）

```yaml
architecture:
  layers:
    domain:
      purpose: "ビジネスロジック（純粋・外部依存なし）"
      dependencies: []
      examples:
        - entities/          # AggregateRoot パターン（___python-ddd-main参照）
        - value_objects/     # 不変オブジェクト
        - domain_services/   # ビジネスルール
        - rules/            # Domain Rules パターン（___python-ddd-main参照）
        - events/           # Domain Events（___code-master参照）

    application:
      purpose: "ユースケース（ドメインサービス調整）"
      dependencies: [domain]
      examples:
        - use_cases/        # Unit of Work パターン（___code-master参照）
        - orchestrators/    # 複雑な処理の調整
        - unit_of_work/     # トランザクション管理（___code-master参照）

    infrastructure:
      purpose: "技術実装（DB・ファイル・外部API）"
      dependencies: [domain, application]
      examples:
        - repositories/     # Repository パターン（___code-master参照）
        - adapters/        # 外部システム連携
        - gateways/        # API Gateway

    presentation:
      purpose: "CLI（ユーザーインターフェース）"
      dependencies: [application]
      examples:
        - cli/commands/    # CLIコマンド実装
        - cli/handlers/    # リクエストハンドラー
```

### 実装判断基準（模範パターン適用）

```yaml
implementation_decisions:
  simple_feature:
    criteria: ["CRUD操作のみ", "単一エンティティ"]
    pattern: "基本レイヤード"
    location: "Application層のシンプルユースケース"
    reference: "標準的な実装で十分"

  complex_feature:
    criteria: ["複数エンティティ", "ビジネスルール"]
    pattern: "AggregateRoot + Domain Rules"
    location: "Domain層サービス + Application層オーケストレーション"
    reference: "___python-ddd-main/src/modules/bidding/domain/entities.py"

  transactional_feature:
    criteria: ["トランザクション", "複数集約更新"]
    pattern: "Unit of Work"
    location: "Application層 + Infrastructure層"
    reference: "___code-master/src/infrastructure/uow.py"

  external_integration:
    criteria: ["外部API", "ファイルI/O"]
    pattern: "Repository + Adapter"
    location: "Infrastructure層アダプター"
    reference: "___code-master/src/domain/repositories.py"
```

---

## 📚 実装パターン例（模範リポジトリ参照）

### AggregateRoot パターン（___python-ddd-main参照）

```python
# ドメインエンティティ実装例
from dataclasses import dataclass, field
from noveler.seedwork.domain.entities import AggregateRoot
from noveler.seedwork.domain.events import DomainEvent

@dataclass(kw_only=True)
class Episode(AggregateRoot[EpisodeId]):
    """エピソード集約ルート"""
    number: EpisodeNumber
    title: EpisodeTitle
    content: EpisodeContent

    # ビジネスルールチェック
    def validate_for_publication(self):
        self.check_rule(
            MinimumWordCountRule(
                word_count=self.content.word_count,
                minimum=1000
            )
        )

    # イベント発行
    def publish(self):
        self.validate_for_publication()
        self.register_event(
            EpisodePublished(
                episode_id=self.id,
                published_at=datetime.utcnow()
            )
        )
```

### Unit of Work パターン（___code-master参照）

```python
# トランザクション管理実装例
from noveler.infrastructure.unit_of_work import AbstractUnitOfWork

class PublishEpisodeUseCase:
    """エピソード公開ユースケース"""

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow

    def execute(self, episode_id: int) -> None:
        with self._uow:
            # トランザクション開始
            episode = self._uow.episodes.get(EpisodeId(episode_id))

            # ビジネスロジック実行
            episode.publish()

            # イベントハンドリング
            for event in episode.events:
                self._handle_event(event)

            # コミット（自動）
            self._uow.commit()
```

### Architecture Boundary Test（最新実装: 手動AST解析）

**実装完了**: `tests/architecture/test_ddd_boundaries.py` (300行の堅牢実装)
- pytest-archon代替の手動AST解析による境界チェック
- 8つの厳格な依存関係ルールを自動検証
- Domain層の外部ライブラリ依存禁止チェック
- 循環依存の完全検出・詳細レポート
- `tests/unit/domain/test_domain_dependency_guards.py` は候補抽出後に必要なモジュールだけAST解析し、pytestキャッシュに結果を保持する軽量方式へ移行済み。Domain配下を変更した直後は `pytest --cache-clear tests/unit/domain/test_domain_dependency_guards.py` でキャッシュを無効化してから再検証すること。
- 並列実行時は `bin/test -n=2 -m "(not e2e) and (not integration_skip)" --maxfail=1 --durations=10` のようにマーカー条件を明示し、不要な `integration_skip` テストを除外して品質ゲートを回す。

```python
# tests/architecture/test_ddd_boundaries.py - 実装済み
class TestDDDArchitectureBoundaries:
    def test_domain_is_independent(self):
        """Domain層は他のいかなる層にも依存してはならない"""
        # 手動AST解析による完全チェック（実装済み）

    def test_domain_external_dependency_control(self):
        """Domain層は外部ライブラリに直接依存してはならない"""
        # requests, typer, rich, fastapi等の直接依存を検出

    def test_no_direct_import_violations(self):
        """直接インポート違反の検出（カスタム実装）"""
        # 逆依存・循環依存パターンの検出
```

**CI統合**: `.github/workflows/architecture-enforcement.yml` (225行)
- 自動化された境界違反検出・詳細レポート・PRコメント投稿
- 失敗時の詳細ガイダンスと修正手順の自動提示

### Import Contract（実装完了: 8つの厳格ルール）

**完全実装**: `.importlinter` (98行の完成された設定)
- DDD Clean Architecture 依存関係ルール
- 逆参照・循環依存を厳格に禁止
- Domain層の外部ライブラリ依存制御
- Infrastructure内の循環依存チェック

```ini
# .importlinter - 実装済み設定
[importlinter:contract:domain_independence]
name = Domain層は他の層に依存してはならない（完全独立）
type = forbidden
source_modules = noveler.domain
forbidden_modules =
    noveler.application
    noveler.infrastructure
    noveler.presentation

[importlinter:contract:external_dependency_control]
name = 外部ライブラリ依存の制御
type = forbidden
source_modules = noveler.domain
forbidden_modules =
    requests
    typer
    rich
    # Domain層は外部ライブラリに依存してはならない（純粋性保持）
```

**主要ルール（8つ実装済み）**:
1. Presentation → Application のみ依存可
2. Application → Domain のみ依存可
3. Infrastructure → Domain のみ依存可
4. Domain → 完全独立（他層依存禁止）
5. 循環依存の完全禁止
6. UseCase ↔ Domain 循環依存禁止
7. Service ↔ Repository 循環依存禁止
8. Domain層の外部ライブラリ直接依存禁止

---

## CODEMAP活用

### 依存関係管理

```bash
# CODEMAP更新
python src/noveler/tools/dependency_analyzer.py

# 循環依存チェック
python src/noveler/tools/dependency_analyzer.py --detect-circular

# 依存グラフ生成
python src/noveler/tools/dependency_analyzer.py --export-graphviz
```

### 品質メトリクス確認

```yaml
# CODEMAP.yamlの品質基準
quality_metrics:
  thresholds:
    test_coverage: 80      # 最低80%
    lint_score: 90        # 最低90点
    circular_dependencies: 0  # 0個厳守
    high_coupling: 10     # 全体の10%以下
```

### CLIコマンド

```bash
noveler codemap overview              # 全体構造確認
noveler codemap pre-check <機能名>   # 実装前チェック
noveler codemap update               # CODEMAP手動更新
noveler codemap show-metrics         # 品質メトリクス表示
```

---

## 品質ゲート（模範実装統合）

### 必須チェック項目

```bash
# 1. インポートスタイル
python src/noveler/tools/check_import_style.py

# 2. アーキテクチャ違反（pytest-archonパターン）
python src/noveler/infrastructure/quality_gates/architecture_linter.py
pytest tests/test_architecture_boundaries.py  # pytest-archon統合テスト

# 3. インポート契約チェック（import-linterパターン）
lint-imports  # import-linter実行

# 4. ハードコーディング検出
python src/noveler/infrastructure/quality_gates/hardcoding_detector.py

# 5. テストカバレッジ
noveler test run --coverage

# 6. 総合品質ゲート
python src/noveler/tools/quality_gate_check.py
```

### 品質基準

| 項目 | 基準値 | 測定方法 | 実装状況 |
|------|--------|----------|----------|
| テストカバレッジ | 80%以上 | pytest-cov | ✅ CI統合済み |
| Lintスコア | 90点以上 | ruff | ✅ CI統合済み |
| 循環依存 | 0個 | import-linter | 🔵 **8ルール実装完了** |
| ハードコーディング | 0個 | hardcoding_detector | ✅ 検出済み |
| DDD違反 | 0個 | AST手動解析 | 🔵 **300行実装完了** |
| アーキテクチャ境界 | 100%準拠 | tests/architecture/ | 🔵 **完全自動化済み** |
| インポート契約 | 100%準拠 | .importlinter | 🔵 **98行設定完了** |
| FC/IS純粋関数 | 100+検証済み | contracts/ | 🔵 **新規実装完了** |

---

## Git Hooks統合

### インストール

```bash
# 一括インストール
noveler codemap install-hooks --git-root . --guide-root .

# または個別インストール
cp .git-hooks/pre-commit .git/hooks/
cp .git-hooks/post-commit .git/hooks/
chmod +x .git/hooks/*
```

### Pre-commit Hook

自動チェック項目：
- 3コミットサイクル進行状態
- アーキテクチャ違反検出
- インポートスタイル違反
- ハードコーディング検出

### Post-commit Hook

自動実行項目：
- CODEMAP.yaml更新
- サイクル進行記録
- 品質メトリクス更新

---

## トラブルシューティング

### よくある問題と対処

#### 循環依存が検出された

```bash
# 詳細確認
python src/noveler/tools/dependency_analyzer.py --detect-circular

# 修正方法
# 1. インターフェース分離
# 2. 依存性注入パターン適用
# 3. ファサードパターン導入
```

#### テストカバレッジが基準未満

```bash
# カバレッジ詳細確認
noveler test run --coverage --html

# 未カバー箇所特定
coverage report -m
```

#### CODEMAP更新エラー

```bash
# 手動リセット
rm CODEMAP.yaml
git checkout CODEMAP.yaml

# 再生成
python src/noveler/tools/dependency_analyzer.py
```

---

## 関連ドキュメント

- [DEVELOPER_GUIDE](../guides/developer_guide.md) - 開発者向け統合ガイド
- [CLAUDE.md](../CLAUDE.md) - 必須コーディング規約
- [docs/B30_Claude_Code品質作業指示書.md](B30_Claude_Code品質作業指示書.md) - 品質基準詳細
- [docs/episode_preview_metadata_schema.md](episode_preview_metadata_schema.md) - EpisodePreviewメタデータ標準スキーマ

## 模範実装リポジトリ（必須参照）

- **___code-master** - Unit of Work、Event-driven Architecture、Repository Pattern
- **___python-ddd-main** - AggregateRoot、Domain Rules、Value Objects
- **___pytest-archon-main** - Architecture Boundary Testing、Import Rules Testing
- **___import-linter-main** - Import Contract Management、Dependency Flow Control

---

## 付録（テンプレート集）

### PRDテンプレ（短縮版）
```
Title: <変更名>（追加/削除/変更/リファクタ）
Purpose: <何のために>
Scope: <含むもの>
Non-Scope: <含まないもの>
Acceptance: <受入基準（テスト観点）>
Impact: <スキーマ/CLI/設定/理由コード/プリセット/README/ガイド/要件/仕様/テスト>
Migration: <移行・非互換対応>
Risk: <主要リスクと低減策>
Rollback: <戻し方（コミット単位）>
```

### 変更タイプ別チェックリスト（共通）
```
- [ ] PRD作成・合意
- [ ] 影響調査（rgで露出洗い出し）
- [ ] 先行テスト追加（Failの最小化）
- [ ] 実装（露出遮断→ロジック適用）
- [ ] requirements/specs 同期
- [ ] README/ガイド/設定例更新
- [ ] CHANGELOG更新、SemVerバンプ、タグ準備
- [ ] build & smoke
```

### テスト雛形（露出ゼロの固定）
```python
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest

def test_schema_has_no_legacy_keys(tool) -> None:
    schema = tool.get_input_schema()
    props = set(schema.get("properties", {}).keys())
    assert "<legacy_key>" not in props

def test_execution_has_no_legacy_reason_codes(tool) -> None:
    req = ToolRequest(episode_number=1, additional_params={"content": "..."})
    res = tool.execute(req)
    assert all(i.reason_code != "<LEGACY_CODE>" for i in res.issues)
```

### CHANGELOGエントリテンプレ
```
## [X.Y.Z] - YYYY-MM-DD

- Type: Breaking/Added/Changed/Removed/Docs/Tests

### Breaking changes
- <非互換の要約>

### Added / Changed / Removed
- <差分要約>

### Documentation / Tests
- <関連文書/試験の更新>

### Migration
- <移行の手引き>
```

---

## 更新履歴

- 2025/08/11: 初版作成（B20バリエーション統合）
- 2025/08/11: CODEMAP統合機能追加
- 2025/08/11: Git Hooks自動化セクション追加
- 2025/08/19: 模範実装リポジトリパターン統合（4リポジトリ）
- 2025/08/26: 🔵 **FC/ISアーキテクチャパターン文書化** - Functional Core/Imperative Shell実装の完全反映
- 2025/08/26: 🔵 **CI Architecture Enforcement更新** - 手動AST解析・8ルール・225行CI実装の詳細文書化


### CI補助とMakeターゲット（更新）
- distラッパー生成: CIは `scripts/ci/ensure_dist_wrapper.py` を先行実行。ローカルは `make build-dist-wrapper`。
- Import契約検査: `make lint-imports`（importlinterが未導入ならスキップ）。pre-commit にもオプションフックを追加済み。
