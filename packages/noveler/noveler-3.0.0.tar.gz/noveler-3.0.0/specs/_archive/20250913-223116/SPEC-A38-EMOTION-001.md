# SPEC-A38-EMOTION-001: A38 STEP 8感情表現強化システム

## 概要

A38_執筆プロンプトガイド.mdのSTEP 8「感情曲線追跡」を強化する6個のMCPツール群を実装し、五層感情表現システム（身体/内臓/心拍呼吸/神経歪み/比喩）によるLLM芯＋外骨格アーキテクチャを構築する。

## 仕様バージョン

- **Version**: 1.0.0
- **Created**: 2025-09-08
- **Status**: Draft

## 背景

A38 STEP 8の現行実装（EmotionCurveDesignerService）は基本的な感情設計のみを提供している。MCPサーバー統合により、より高度で専門的な感情表現チェック・生成機能を外部ツール化し、効率的なAI協創執筆を実現する必要がある。

## アーキテクチャ設計

### 基本構造
```
LLM芯（生成核心）
├── EmotionCurveDesignerService（既存）
└── 感情表現外骨格（6個MCPツール群）
    ├── CliqueDetectorTool（陳腐表現検出）
    ├── ContextualCueRetrieverTool（文脈手がかり抽出）
    ├── PhysiologyCheckerTool（生理反応検証）
    ├── MetaphorDiversityScorerTool（比喩多様性評価）
    ├── RegisterVerifierTool（表現レベル適性）
    └── MicroABEmotionTestTool（微細A/Bテスト）
```

### 五層感情表現システム
1. **身体層（Physical）**: 体温、震え、姿勢
2. **内臓層（Visceral）**: 胃のもたれ、息苦しさ
3. **心拍呼吸層（Cardiac）**: 動悸、呼吸の乱れ
4. **神経歪み層（Neural）**: 思考の混乱、集中力低下
5. **比喩層（Metaphorical）**: 抽象的表現、詩的比喩

## MCPツール仕様

### 1. CliqueDetectorTool (陳腐表現検出)
**役割**: 感情表現における定型表現・陳腐化した比喩の検出

**入力**:
- text: 検査対象テキスト
- emotion_layer: 対象感情層（physical/visceral/cardiac/neural/metaphorical）

**出力**:
- cliche_count: 陳腐表現検出数
- flagged_phrases: 検出された表現リスト
- severity: 深刻度（low/medium/high）
- alternatives: 代替表現提案

**検出基準**:
- 「ドキドキ」「胸がキュン」などの定型表現
- 過度に使用される比喩パターン
- 感情表現の陳腐化度合い

### 2. ContextualCueRetrieverTool (文脈手がかり抽出)
**役割**: 既存テキストから感情表現に活用可能な文脈要素を抽出

**入力**:
- context_text: 周辺文脈テキスト
- target_emotion: 目標感情（joy/anger/sadness/fear等）
- scene_setting: シーン設定情報

**出力**:
- contextual_elements: 抽出された文脈要素
- emotion_anchors: 感情の足がかりとなる要素
- consistency_score: 文脈整合性スコア
- enhancement_suggestions: 強化提案

### 3. PhysiologyCheckerTool (生理反応検証)
**役割**: 感情表現と生理学的反応の整合性検証

**入力**:
- emotion_description: 感情表現テキスト
- physiological_details: 生理的詳細描写
- emotion_intensity: 感情強度（1-10）

**出力**:
- accuracy_score: 生理学的正確性スコア
- inconsistencies: 不整合箇所
- corrections: 修正提案
- intensity_alignment: 強度整合性評価

**検証項目**:
- 心拍数と感情の対応
- 呼吸パターンの妥当性
- 自律神経系反応の適切性

### 4. MetaphorDiversityScorerTool (比喩多様性評価)
**役割**: 感情表現における比喩の多様性と独創性の評価

**入力**:
- text_sample: 評価対象テキスト
- comparison_corpus: 比較対象コーパス（オプション）
- creativity_threshold: 創造性閾値設定

**出力**:
- diversity_score: 多様性スコア（0-100）
- uniqueness_ratio: 独自性比率
- overused_metaphors: 過用比喩リスト
- novel_expressions: 新規表現候補

### 5. RegisterVerifierTool (表現レベル適性)
**役割**: 感情表現が対象読者層・作品ジャンルに適切かを検証

**入力**:
- emotion_text: 感情表現テキスト
- target_audience: 対象読者層（teen/adult/general等）
- genre: 作品ジャンル（romance/mystery/fantasy等）
- formality_level: 文体レベル（casual/formal/literary）

**出力**:
- appropriateness_score: 適切性スコア
- register_mismatches: レベル不一致箇所
- adjustments: 調整提案
- style_consistency: スタイル一貫性評価

### 6. MicroABEmotionTestTool (微細A/Bテスト)
**役割**: 複数の感情表現候補から最適解を選択するための微細比較

**入力**:
- variant_a: 表現候補A
- variant_b: 表現候補B
- evaluation_criteria: 評価基準
- context_weight: 文脈重要度

**出力**:
- winner: 推奨候補（A/B/tie）
- score_breakdown: 項目別スコア
- reasoning: 選択理由
- hybrid_suggestion: ハイブリッド提案

## 統合フロー

### STEP 8実行シーケンス
1. **EmotionCurveDesignerService**: 基本感情曲線設計
2. **CliqueDetectorTool**: 陳腐表現チェック
3. **ContextualCueRetrieverTool**: 文脈要素抽出
4. **PhysiologyCheckerTool**: 生理学的検証
5. **MetaphorDiversityScorerTool**: 比喩多様性評価
6. **RegisterVerifierTool**: 表現レベル確認
7. **MicroABEmotionTestTool**: 最終候補選択
8. **統合レポート生成**: 全項目統合評価

### EmotionCurveDesignerService拡張
既存のEmotionCurveDesignerServiceに以下の統合ポイントを追加：

```python
class EmotionCurveDesignerService(BaseWritingStep):
    def __init__(self, mcp_tools: MCPToolCollection):
        super().__init__(step_number=8, step_name="感情曲線追跡")
        self.emotion_tools = mcp_tools

    async def execute_enhanced_emotion_design(self, content: str) -> dict:
        # 基本感情曲線設計
        base_result = await self._design_base_emotion_curve(content)

        # 6ツール順次実行
        enhanced_result = await self._apply_emotion_enhancement_pipeline(
            base_result, content
        )

        return enhanced_result
```

## 実装計画

### Phase 1: 基盤構築（コミット1）
- MCPツール基底クラス設計
- 6ツールのスケルトン実装
- 統合テストフレームワーク

### Phase 2: 個別ツール実装（コミット2）
- 各ツールのコア機能実装
- 単体テスト作成
- エラーハンドリング

### Phase 3: 統合・最適化（コミット3）
- EmotionCurveDesignerServiceとの統合
- パフォーマンス最適化
- 統合テスト・品質保証

## 品質基準

### コード品質
- すべてのMCPツールがDDD準拠
- 単体テストカバレッジ90%以上
- エラーハンドリング完備
- JSON応答の95%トークン削減対応

### 機能品質
- 各ツールの独立実行可能性
- 統合パイプラインの堅牢性
- パフォーマンス要件（1ツール5秒以内）

### 文書品質
- 各ツールの使用例完備
- トラブルシューティングガイド
- A38ガイドとの整合性確保

## 設計原則

1. **単一責任**: 各MCPツールは特定の感情表現チェック機能に特化
2. **独立実行**: ツール間の依存関係を最小化
3. **拡張性**: 新しい感情層・評価基準の追加が容易
4. **効率性**: JSON変換による95%トークン削減活用
5. **統合性**: 既存のA38フローとの自然な統合

## 技術仕様

### ディレクトリ構造
```
src/mcp_servers/noveler/tools/emotion/
├── __init__.py
├── base_emotion_tool.py
├── cliche_detector_tool.py
├── contextual_cue_retriever_tool.py
├── physiology_checker_tool.py
├── metaphor_diversity_scorer_tool.py
├── register_verifier_tool.py
├── micro_ab_emotion_test_tool.py
└── emotion_pipeline_coordinator.py
```

### 依存関係
- 既存: EmotionCurveDesignerService
- 新規: MCPツール基盤
- 外部: 感情表現コーパス（オプション）

## 成功基準

1. 6個のMCPツールがすべて独立実行可能
2. EmotionCurveDesignerServiceとの統合完了
3. A38 STEP 8の実行時間が既存比150%以内
4. 感情表現の質的向上が定量評価で確認
5. B20準拠の3コミット開発サイクル完了

## リスク・制約

### 技術リスク
- MCPツール間の依存関係複雑化
- パフォーマンス劣化の可能性
- LLM応答の予測困難性

### 制約事項
- B20開発ガイドライン厳守
- 既存A38ガイドとの後方互換性
- プロジェクト独立性の保持

## 参考資料

- A38_執筆プロンプトガイド.md
- B20_Claude_Code開発作業指示書.md
- B31_MCPマイクロサービス設計ガイド.md
- B33_MCPツール統合ガイド.md

---

**承認**: 要承認
**実装予定**: 2025-09-08～
**レビュー**: 実装完了後
