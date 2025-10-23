---
spec_id: SPEC-LLM-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-25
category: LLM
tags: [llm, integration, polish, refactoring, mcp]
requirements:
  - REQ-QUALITY-001
  - REQ-QUALITY-002
  - REQ-WRITE-MCP-003
sources: [B20, DDD]
---

# SPEC-LLM-001: polish_manuscript_apply noveler write統合リファクタリング仕様書

**Version**: 1.0.0
**作成日**: 2025-09-23
**対象**: polish_manuscript_applyのnoveler write統合実装
**タイプ**: リファクタリング（外部契約不変）
**B20準拠**: 4コミット開発サイクル適用（事前準備追加）

---

## 1. 目的と原則

### 1.1 目的
- **現状**: `polish_manuscript_apply`が独自LLM実行でMCP環境問題を抱える
- **目標**: `noveler write`の成功済みLLM実行パターンに統合し、確実なMCP対応を実現
- **利点**: MCP対応統一・コード簡素化・保守性向上・パフォーマンス改善

### 1.2 非スコープ
- 外部API（MCPツール）の変更
- エンドユーザー向けパラメータの変更
- 出力形式の変更
- 他のLLMツールへの影響
- ProgressiveCheckManager は LangGraph ワークフローを介して UniversalLLMUseCase と連携し、available_tools/ハッシュ参照を扱うため SPEC-QUALITY-120 の要件に従う必要がある。その他の MCP ツールについては現時点で追加統合不要（2025-09-26 再評価）。

### 1.3 受け入れ基準
- ✅ MCP環境でLLM実行が確実に動作する
- ✅ 既存のテストが全てパスする
- ✅ パフォーマンス劣化10%以内
- ✅ `force_llm`パラメータは完全削除（設定ベース制御へ移行）
- ✅ CI/CDスモークテスト正常動作
- ✅ メモリリークなし

---

## 2. 事前準備と影響調査

### 2.1 Phase 0: 事前準備フェーズ（新規追加）

#### 2.1.1 パフォーマンスベースライン測定
```bash
# 現状のパフォーマンス測定
pytest tests/performance/test_polish_performance.py --benchmark-save=before
noveler mcp call polish_manuscript_apply '{"episode_number":1}' --measure-time
```

#### 2.1.2 MCP環境統合テスト環境構築
```python
# tests/integration/test_mcp_polish_integration.py
@pytest.mark.mcp_integration
async def test_polish_apply_mcp_environment():
    """MCP環境でのUniversalLLMUseCase動作検証"""
    # MCP環境シミュレーション
    with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
        tool = PolishManuscriptApplyTool()
        result = await tool.execute_unified_llm(project_root, test_prompt)
        assert result is not None  # フォールバック動作確認
```

#### 2.1.3 ロールバックシナリオ検証
```bash
# 緊急ロールバック手順のテスト
git stash  # 現在の変更を保存
git reset --hard HEAD~3  # 3コミット前に戻す
make test-full  # 全体テスト実行
make smoke-test  # CI/CDスモークテスト
git stash pop  # 変更を復元
```

### 2.2 変更対象ファイル
- **主要**: `src/mcp_servers/noveler/tools/polish_manuscript_apply_tool.py`
- **テスト**:
  - `tests/unit/mcp_servers/tools/test_polish_manuscript_apply_tool.py`
  - `tests/integration/test_mcp_polish_integration.py`（新規）
  - `tests/performance/test_polish_performance.py`（新規）
- **ドキュメント**: TODO.md（既に更新済み）

### 2.3 依存関係確認
- `noveler.application.use_cases.universal_llm_use_case`
- `noveler.infrastructure.integrations.universal_claude_code_service`
- `noveler.domain.value_objects.universal_prompt_execution`
- `noveler.infrastructure.factories.path_service_factory.is_mcp_environment`

---

## 3. 実装設計（DDD準拠）

### 3.0 プロンプト外部化ポリシー（A40/A41 連携）
- 目的: ハードコードされたプロンプトを廃止し、`templates/quality/checks/` 直下のテンプレートを LLM 入力のソース・オブ・トゥルースにする。
- 参照先: 
  - Stage 2 → `templates/quality/checks/polish_stage2_content.yaml`（Schema v2。レガシー互換で `.md` / `templates/writing/write_step26_polish_stage2.yaml` をフォールバック探索）
  - Stage 3 → `templates/quality/checks/polish_stage3_reader.yaml`（Schema v2。同上フォールバック手順）
  - （将来の A41 LLM チェック用）読みやすさ/文体などは `enhanced_*_prompt.md` 群
- エンコード: UTF-8（BOM なし）。
- プレースホルダ: `{manuscript}`, `{episode_number}`, `{project_title}`, `{project_genre}`, `{target_word_count}` ほか（A41系は `{episode_content}`, `{character_profiles}`, `{target_category}` を追加で許容）。
- 検証: 未解決プレースホルダと不正サイズ（512B未満/200KB超）を検知。失敗時は内蔵デフォルトにフォールバックし WARN ログ＋`metadata.template_source=embedded_default` を付与。
- キャッシュ: パス＋mtime をキーにした軽量メモリキャッシュを許可（任意）。
- 探索順序: `templates/quality/checks/` → `templates/quality/checks/backup/` → `templates/writing/`。最初の成功テンプレートを採用。

### 3.1 現状の問題分析
```python
# 現在の実装（問題あり）
def _run_llm(self, project_root: Path, prompt: str, force_llm: bool = False) -> str | None:
    if is_mcp_environment() and not force_llm:
        return None
    # 問題：
    # 1. 独自実装でMCP環境問題が残る
    # 2. force_llmでも基盤サービスレベルでブロック
    # 3. スレッド管理の複雑性
```

### 3.2 統合後の設計
```python
# 統合後の実装（UniversalLLMUseCase統合版）
def _run_llm(self, project_root: Path, prompt: str) -> str | None:
    from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
    from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService

    use_case = UniversalLLMUseCase(UniversalClaudeCodeService())
    request = UniversalPromptRequest(
        prompt_content=prompt,
        prompt_type=PromptType.WRITING,
        project_context=ProjectContext(project_root=project_root),
        output_format="json",
        max_turns=3,
    )

    try:
        try:
            asyncio.get_running_loop()
            response = self._run_async_in_thread(use_case, request)
        except RuntimeError:
            response = asyncio.run(use_case.execute_with_fallback(request, fallback_enabled=True))

        if response.is_success():
            if response.get_metadata_value("mode") == "fallback" or response.extracted_data.get("fallback_mode"):
                logger.info("LLMフォールバック検出: 改稿適用をスキップ")
                return None
            return response.get_writing_content()

        logger.warning("LLM実行失敗: レスポンス不正")
        return None

    except Exception:
        logger.error("LLM実行エラー", exc_info=True)
        return None
```

### 3.3 A40 ステージ別プロンプトの取得手順（擬似コード）
```python
def _load_stage_prompt(stage: str, ctx: dict) -> str:
    names = {"stage2": "stage2_content_refiner.md", "stage3": "stage3_reader_experience.md"}
    base = project_root / "templates/quality/checks"
    path = base / names[stage]
    try:
        text = path.read_text(encoding="utf-8")
        _validate_template(text)  # 未解決プレースホルダ/サイズ
    except Exception:
        logger.warning("テンプレート読み込み失敗、内蔵デフォルトにフォールバック", extra={"stage": stage, "path": str(path)})
        text = _embedded_default(stage)
    return text.format(**ctx)
```

受入基準（追加）
- `templates/quality/checks/*.md` の変更が LLM 入力に反映されること
- 不在/検証失敗時に内蔵デフォルトへフォールバックし、WARN ログと `metadata.template_source=embedded_default` を記録すること
- 未解決プレースホルダを検知してフォールバックすること（実行失敗にはしない）

### 3.3 アーキテクチャ準拠確認
```yaml
# DDD層設計確認
Presentation層: PolishManuscriptApplyTool（MCPツール）
Application層: UniversalLLMUseCase（ビジネスロジック）
Infrastructure層: UniversalClaudeCodeService（技術実装）
Domain層: UniversalPromptRequest（ドメインオブジェクト）

# 依存方向確認
Presentation → Application → Infrastructure
Domain ← Application（ドメインオブジェクト使用）
```

---

## 4. B20準拠実装計画（4コミット拡張）

### 4.1 Phase 0: 事前準備（新規コミット）
```bash
# ブランチ作成
git checkout -b feature/SPEC-LLM-001-polish-unify-llm

# パフォーマンステスト追加
cat > tests/performance/test_polish_performance.py << EOF
import pytest
import time
from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool

@pytest.mark.benchmark
def test_polish_apply_performance_baseline():
    """統合前のパフォーマンスベースライン測定"""
    tool = PolishManuscriptApplyTool()
    start_time = time.perf_counter()
    # 現在の実装でのベンチマーク
    result = tool._run_llm(Path("/test"), "test prompt")
    duration = time.perf_counter() - start_time
    assert duration < 5.0  # 5秒以内
EOF

# MCP統合テスト追加
cat > tests/integration/test_mcp_polish_integration.py << EOF
import pytest
from unittest.mock import patch
from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool

@pytest.mark.mcp_integration
async def test_polish_apply_mcp_environment():
    """MCP環境での動作確認"""
    with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
        tool = PolishManuscriptApplyTool()
        # MCP環境での統合テスト
        assert False  # Phase 1で実装
EOF

# コミット
git add tests/
git commit -m "test: SPEC-LLM-001 事前準備 - パフォーマンステスト・MCP統合テスト追加"
```

### 4.2 Phase 1: 仕様書+失敗テスト
> **Historical Note (v3.0.0)**: 初期フェーズでは `_run_llm_unified` 追加を前提にしていたが、最終版では `_run_llm` に統合され `_run_async_in_thread` との組み合わせで提供される。
```bash
# 現行仕様に合わせた統合失敗テスト（フォールバック挙動をREDで明示）
cat > tests/unit/mcp_servers/tools/test_polish_llm_integration.py <<'EOF'
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool


@pytest.mark.spec("SPEC-LLM-001")
def test_run_llm_skips_fallback_response():
    """UniversalLLMUseCaseフォールバック時は改稿適用を避ける（RED）"""
    tool = PolishManuscriptApplyTool()

    with patch("noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase") as mock_use_case_cls:
        mock_use_case = mock_use_case_cls.return_value
        fallback = AsyncMock()
        fallback.is_success.return_value = True
        fallback.get_metadata_value.return_value = "fallback"
        fallback.extracted_data = {"fallback_mode": True}
        fallback.get_writing_content.return_value = "fallback"
        mock_use_case.execute_with_fallback = AsyncMock(return_value=fallback)

        with patch("noveler.infrastructure.integrations.universal_claude_code_service.UniversalClaudeCodeService"):
            result = tool._run_llm(Path("/tmp"), "prompt")
            assert result is None  # RED: 実装がフォールバックを無視すると失敗
EOF

# コミット
git add specs/ tests/
git commit -m "docs+test: SPEC-LLM-001 fallback handling test"
```

### 4.3 Phase 2: 最小実装
```bash
# UniversalLLMUseCase統合実装
# src/mcp_servers/noveler/tools/polish_manuscript_apply_tool.py 修正

# テスト実行
pytest tests/unit/mcp_servers/tools/test_polish_llm_integration.py
pytest tests/performance/test_polish_performance.py --benchmark-compare=before

# コミット
git add src/mcp_servers/noveler/tools/polish_manuscript_apply_tool.py
git commit -m "feat: SPEC-LLM-001 UniversalLLMUseCase統合実装 - MCP環境対応"
```

### 4.4 Phase 3: 統合+リファクタリング
```bash
# レガシーコード削除とリファクタリング
# 1. _run_async_in_thread整備（イベントループ競合解消）
# 2. force_llmパラメータ削除（設定制御へ移行）
# 3. フォールバック検出で改稿適用を停止
# 4. MCP統合テスト完成（フォールバックを含む統一挙動の検証）

# 統合テスト実行
pytest tests/integration/test_mcp_polish_integration.py
pytest tests/performance/ --benchmark-compare=before

# コミット
git add -A
git commit -m "refactor: SPEC-LLM-001 レガシーコード削除 + force_llm段階的廃止"
```

---

## 5. 段階的廃止戦略（詳細）

### 5.1 force_llmパラメータ廃止とフォールバック制御

- v3.0.0 で `force_llm` 入力は完全削除済み。LLM 強制制御は `.novelerrc.yaml` または `NOVELER_FORCE_EXTERNAL_LLM` で行う。
- `polish_manuscript_apply` は UniversalLLMUseCase のフォールバック結果（`response.metadata.get("mode") == "fallback"` または `response.extracted_data.get("fallback_mode")`）を検知した場合、改稿本文の適用をスキップし、元原稿を保持する。
- この挙動により MCP 環境でフォールバックが発生しても破壊的な上書きが起きない。
- テスト: `tests/unit/mcp_servers/tools/test_polish_llm_integration.py::test_run_llm_skips_fallback_response` でフォールバック検出、`::test_execute_does_not_write_when_llm_returns_none` で適用スキップを保証する。

### 5.2 代替制御手段
```yaml
# .novelerrc.yaml での制御
llm_execution:
  respect_mcp_environment: false  # MCP環境判定を無視
  fallback_enabled: true          # フォールバック有効
  force_external_api: false       # 外部API強制使用

# 環境変数での制御
NOVELER_FORCE_EXTERNAL_LLM=true  # 外部LLM強制使用
NOVELER_LLM_FALLBACK_ENABLED=true  # フォールバック有効
```

---

## 6. テスト戦略（拡張）

### 6.1 単体テスト
```python
@pytest.mark.spec("SPEC-LLM-001")
class TestPolishLLMIntegration:
    def test_run_llm_skips_fallback_response(self, tool):
        """UniversalLLMUseCaseフォールバック時は改稿適用を避ける"""
        fallback = UniversalPromptResponse(
            success=True,
            response_content="fallback",
            extracted_data={"fallback_mode": True},
            prompt_type=PromptType.WRITING,
            metadata={"mode": "fallback"},
        )
        with patch('noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase') as mock_use_case_cls:
            mock_use_case = mock_use_case_cls.return_value
            mock_use_case.execute_with_fallback = AsyncMock(return_value=fallback)
            with patch('noveler.infrastructure.integrations.universal_claude_code_service.UniversalClaudeCodeService'):
                assert tool._run_llm(Path('/tmp'), 'prompt') is None

    def test_execute_does_not_write_when_llm_returns_none(self, tool, sample_request):
        """フォールバック検出時は原稿を書き戻さない"""
        with patch.object(tool, '_resolve_target_path', return_value=Path('/tmp/manuscript.md')):
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.read_text', return_value='元の内容'), \
                 patch('pathlib.Path.write_text') as mock_write, \
                 patch.object(tool, '_run_llm', return_value=None):
                result = tool.execute(
                    ToolRequest(
                        episode_number=sample_request.episode_number,
                        project_name=sample_request.project_name,
                        additional_params={
                            "dry_run": False,
                            "stages": ["stage2", "stage3"],
                            "save_report": False,
                        },
                    )
                )
        assert result.success
        mock_write.assert_not_called()
```

### 6.2 統合テスト
```python
@pytest.mark.integration
def test_polish_manuscript_apply_integration():
    """noveler writeとの動作一貫性テスト"""
    # 同じプロンプトでの出力比較

@pytest.mark.mcp_integration
def test_mcp_environment_end_to_end():
    """MCP環境でのエンドツーエンドテスト"""
    # 実際のMCP環境でのテスト
```

### 6.3 パフォーマンステスト
```python
@pytest.mark.benchmark
def test_polish_apply_performance_after_integration():
    """統合後のパフォーマンステスト"""
    # 統合前後のパフォーマンス比較
    # 劣化10%以内を確認
```

---

## 7. 品質ゲート（定量化）

### 7.1 必須チェック項目（定量的基準）
- [ ] 全テストパス（単体・統合）: **100%**
- [ ] MCP環境での動作確認: **成功率100%**
- [ ] パフォーマンス劣化: **10%以内**
- [ ] テストカバレッジ維持: **95%以上**
- [ ] CI/CDスモークテスト: **100%成功**
- [ ] メモリリーク: **なし**
- [ ] ログレベル適正性確認: **WARNING以下**
- [ ] アーキテクチャ境界違反: **0件**

### 7.2 自動化コマンド
```bash
# 統合前後の動作比較
noveler mcp call polish_manuscript_apply '{"episode_number":1}' --measure

# パフォーマンステスト
pytest tests/performance/test_polish_performance.py --benchmark-compare

# アーキテクチャチェック
pytest tests/architecture/test_ddd_boundaries.py

# CI/CDスモークテスト
make smoke-test

# メモリリークチェック
python -m pytest tests/integration/ --memray
```

---

## 8. 監視・アラート体制

### 8.1 統合後監視項目
```yaml
metrics:
  - name: polish_apply_success_rate
    threshold: "> 95%"
    alert_channel: "#dev-alerts"

  - name: polish_apply_latency_p95
    threshold: "< 30s"
    alert_channel: "#dev-alerts"

  - name: mcp_environment_error_rate
    threshold: "< 5%"
    alert_channel: "#dev-alerts"
```

### 8.2 アラート設定
```python
# monitoring/polish_apply_monitor.py
class PolishApplyMonitor:
    def check_integration_health(self):
        """統合後のヘルスチェック"""
        metrics = {
            "success_rate": self.calculate_success_rate(),
            "avg_latency": self.calculate_average_latency(),
            "error_rate": self.calculate_error_rate()
        }

        if metrics["success_rate"] < 0.95:
            self.send_alert("PolishApply success rate below threshold")
```

---

## 9. リスク分析と対策（拡張）

### 9.1 主要リスク
| リスク | 影響度 | 発生確率 | 対策 | 緊急時手順 |
|--------|---------|----------|------|------------|
| 統合時の非互換 | 中 | 低 | 段階的統合・十分なテスト | ロールバック手順実行 |
| パフォーマンス劣化 | 中 | 中 | 統合前後の計測・ベンチマーク | パフォーマンス調整 |
| MCP環境での動作不安定 | 低 | 低 | noveler writeの実績パターン採用 | フォールバック強化 |
| CI/CDスモークテスト失敗 | 高 | 低 | 事前テスト・段階的統合 | 緊急ロールバック |

### 9.2 緊急時ロールバック手順（詳細）
```bash
# Phase 3ロールバック
git revert <phase3-commit-hash>
make test-full
make smoke-test

# Phase 2ロールバック
git revert <phase2-commit-hash>
make test-full

# Phase 1ロールバック
git revert <phase1-commit-hash>
make test-full

# 完全ロールバック
git revert <phase0-commit-hash>
make test-full
```

---

## 10. 成果物と完了基準（拡張）

### 10.1 成果物
- [ ] 統合済み`polish_manuscript_apply_tool.py`
- [ ] 対応する単体テスト・統合テスト・パフォーマンステスト
- [ ] パフォーマンステスト結果（統合前後比較）
- [ ] 統合前後の動作比較レポート
- [ ] MCP環境テスト結果
- [ ] CI/CDスモークテスト結果
- [ ] メモリリーク検証結果

### 10.2 完了基準（DoD）
- [ ] MCP環境でのLLM実行が確実に動作（成功率100%）
- [ ] 既存テストが全てパス（カバレッジ95%維持）
- [ ] パフォーマンス劣化10%以内
- [x] force_llmパラメータの削除とフォールバック制御の実装
- [ ] CI/CDスモークテスト100%成功
- [ ] アーキテクチャ境界違反0件
- [ ] ドキュメント更新（TODO.md既完了）
- [ ] 監視・アラート設定完了

---

## 11. 関連ドキュメント・更新対象

### 11.1 直接更新が必要
- **SPEC-A40A41-STAGE23-POLISH.md**: polish_manuscript_applyのフォールバック挙動と入力仕様を反映
- **SPEC-MCP-002_mcp-tools-specification.md**: force_llm削除とフォールバック動作の記載更新

### 11.2 参照更新が必要
- **SPEC-CLAUDE-001_claude_code_integration_system.md**: 後継仕様への参照追加
- **B20_Claude_Code開発作業指示書.md**: 開発プロセス詳細
- **TODO.md**: 実装優先度管理（既完了）

### 11.3 テンプレート化推奨
- **SPEC-INTEGRATION-XXX テンプレート**: LLM統合パターンの標準化

---

## 12. 後続作業

### 12.1 水平展開対象
- `polish_manuscript`ツール
- その他のLLM実行ツール
- MCP環境対応が必要な機能

### 12.2 継続改善項目
- UniversalLLMUseCaseのパフォーマンス最適化
- MCP環境での追加機能対応
- 監視体制の強化

---

**承認**: 本仕様書はレビュー指摘事項を反映し、事前準備フェーズ・定量的品質基準・監視体制を強化した完全版です。
