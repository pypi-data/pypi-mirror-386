# SPEC-FIVE-STAGE-SESSION-002: セッション分離実行システム

**仕様書ID**: SPEC-FIVE-STAGE-SESSION-002
**作成日**: 2025年8月9日
**優先度**: P0 (CRITICAL)
**対応課題**: 5段階生成システムのメタデータのみ応答問題・セッション累積ターン消費問題

## 📋 概要

現在の5段階実行システムが同一セッション内で全段階を実行することで累積ターン消費が発生し、Claude Code実行でメタデータのみが返される根本問題を解決するため、**段階別独立セッション実行システム**を実装する。

## 🎯 解決対象の根本問題

### 現在の問題
1. **セッション累積ターン消費**: 全段階を同一セッションで実行→各段階のターン消費が累積
2. **ターン制限到達**: Stage 4(原稿執筆)でmax_turnsに到達し、メタデータのみ返却
3. **コンテキスト肥大化**: セッション内でのコンテキスト累積による実行効率低下
4. **段階間依存関係の複雑化**: 全段階の結果を同一セッションで管理する複雑性

### 目標アーキテクチャ
- **段階別独立セッション**: 各段階を独立したClaude Code セッションで実行
- **段階間データ連携**: 軽量データオブジェクトによる段階間データ受け渡し
- **ターンリセット**: 各段階開始時にターンカウンターリセット
- **動的ターン配分**: 段階の重要度に応じた最適ターン数割り当て

## 🏗️ 設計仕様

### 1. セッション分離アーキテクチャ

```python
# 現在（問題あり）: 単一セッション実行
class FiveStageExecutionService:
    async def execute_all_stages_in_single_session(self):
        session = claude_service.create_session()
        for stage in all_stages:
            result = session.execute(stage_prompt)  # ターン累積

# 新設計: 段階別独立セッション
class IndependentStageExecutionService:
    async def execute_stage_with_independent_session(self, stage: ExecutionStage):
        session = claude_service.create_independent_session()  # 新セッション
        result = session.execute(stage_prompt)  # ターンリセット
        session.close()
        return result
```

### 2. 段階別ターン配分システム

```yaml
stage_turn_allocation:
  data_collection:
    base_turns: 4
    importance_weight: 1.0
    max_turns: 6

  plot_analysis:
    base_turns: 4
    importance_weight: 1.2
    max_turns: 6

  episode_design:
    base_turns: 5
    importance_weight: 1.4
    max_turns: 8

  manuscript_writing:  # 最重要段階
    base_turns: 8
    importance_weight: 2.0
    max_turns: 12

  quality_finalization:
    base_turns: 4
    importance_weight: 1.1
    max_turns: 6
```

### 3. 段階間データ連携システム

```python
@dataclass
class StageDataTransfer:
    """段階間データ転送オブジェクト"""
    stage: ExecutionStage
    key_data: Dict[str, Any]  # 必要最小限データのみ
    metadata: Dict[str, Any]
    compression_applied: bool = True

class StageDataConnector:
    """段階間データ接続管理"""

    def extract_essential_data(self, stage_result: StageExecutionResult) -> StageDataTransfer:
        """段階結果から必要最小限データ抽出"""

    def inject_previous_data(self, prompt: str, previous_data: StageDataTransfer) -> str:
        """前段階データを次段階プロンプトに注入"""
```

## 🔧 実装コンポーネント

### 1. IndependentSessionExecutor
**責務**: 段階別独立セッション実行制御
**主要機能**:
- 段階ごとの新セッション作成・実行・破棄
- ターン制限の段階別適用
- セッション実行状態監視

### 2. StageDataTransferManager
**責務**: 段階間データ転送管理
**主要機能**:
- 段階結果からの必要最小限データ抽出
- データ圧縮・最適化
- 次段階への軽量データ注入

### 3. DynamicTurnAllocationService
**責務**: 動的ターン配分管理
**主要機能**:
- エピソード特性に基づくターン数計算
- 段階重要度による配分調整
- リアルタイムターン消費監視

### 4. ContentValidationService
**責務**: 保存前内容検証
**主要機能**:
- JSONメタデータと実コンテンツの判別
- 最低文字数・形式・内容妥当性チェック
- 品質基準不達時のアラート

## 📊 期待される効果

### 品質向上
- ✅ **メタデータのみ応答問題解決**: 各段階でターンリセットにより十分な実行時間確保
- ✅ **原稿生成成功率向上**: Stage 4に十分なターン数を配分
- ✅ **コンテンツ品質向上**: 段階ごとの集中実行による品質向上

### パフォーマンス向上
- ✅ **実行効率化**: コンテキスト肥大化回避による高速実行
- ✅ **メモリ使用量削減**: 段階終了時のセッションリソース解放
- ✅ **並列実行可能性**: 独立セッションによる将来的な並列化対応

### 保守性向上
- ✅ **段階間疎結合**: 段階間の依存関係最小化
- ✅ **エラー分離**: 一段階のエラーが他段階に波及しない設計
- ✅ **拡張性確保**: 新段階追加時の影響範囲最小化

## 🧪 テスト戦略

### 単体テスト
```python
@pytest.mark.spec("SPEC-FIVE-STAGE-SESSION-002")
class TestIndependentSessionExecution:

    def test_stage_independent_session_creation(self):
        """段階別独立セッション作成テスト"""

    def test_turn_counter_reset_between_stages(self):
        """段階間ターンカウンターリセットテスト"""

    def test_data_transfer_between_stages(self):
        """段階間データ転送テスト"""

    def test_content_validation_prevents_metadata_only_save(self):
        """メタデータのみ保存防止テスト"""
```

### 統合テスト
```python
@pytest.mark.integration
@pytest.mark.spec("SPEC-FIVE-STAGE-SESSION-002")
class TestFiveStageSessionIntegration:

    async def test_full_five_stage_independent_execution(self):
        """5段階独立実行フルテスト"""

    async def test_manuscript_generation_success_with_adequate_turns(self):
        """十分ターン数での原稿生成成功テスト"""
```

## 📋 実装チェックリスト

### P0 (即座対応): セッション分離とターン配分根本修正
- [ ] IndependentSessionExecutor実装
- [ ] 段階別ターン配分システム実装
- [ ] セッション管理ライフサイクル実装
- [ ] 既存5段階サービスとの統合

### P1 (緊急): 保存前内容検証システム
- [ ] ContentValidationService実装
- [ ] JSONメタデータ検出・防止システム
- [ ] 品質基準チェック機能
- [ ] ファイル保存前検証フック

### P2 (重要): 動的最適化システム
- [ ] DynamicTurnAllocationService実装
- [ ] エピソード特性分析システム
- [ ] リアルタイム監視・調整機能
- [ ] 実行最適化レポート機能

## 🔗 関連仕様書・ドキュメント

- **SPEC-FIVE-STAGE-001**: 5段階分割実行システム基盤仕様
- **CLAUDE.md**: 統合インポート管理・共通コンポーネント強制利用ルール
- **B30_Claude_Code品質作業指示書.md**: 実装品質基準・テスト戦略

## 📅 実装スケジュール

| フェーズ | 内容 | 期間 | 担当 |
|---------|------|------|------|
| Phase 1 | P0実装・基本動作確認 | 1日 | Claude Code |
| Phase 2 | P1実装・品質検証強化 | 0.5日 | Claude Code |
| Phase 3 | P2実装・最適化システム | 0.5日 | Claude Code |
| Phase 4 | 統合テスト・品質ゲート通過 | 0.5日 | Claude Code |

**総工数**: 2.5日
**完了目標**: 2025年8月11日

---

**承認**: Claude Code開発チーム
**レビュー状態**: 承認済み
**実装開始**: 即座開始
