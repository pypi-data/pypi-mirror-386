# Generator Retry Policy & Rich Metrics 実装計画

## 概要

TODO.mdの「Nice to Have」セクションにある2機能の実装計画書：
1. **Generator retry policy**: `by_task`失敗時の自動リトライとdeltaプロンプト生成
2. **Rich metrics**: STEP10非視覚センス比率推定器（ヒューリスティック）

## 現状分析

### 既存実装の調査結果

#### 1. by_task検証システム（既存）
- **場所**: `src/noveler/domain/services/progressive_write_manager.py:693-815`
- **機能**:
  - `_apply_by_task_validation()`: YAMLテンプレートの`control_settings.by_task`ルールに基づく自動検証
  - フィールド存在チェック、enum/range/nonempty検証
  - `required`フラグによる必須/任意の判定
  - 検証結果: `pass`/`warn`/`fail`の3段階
- **問題点**: 失敗時のリトライ機構はあるが、deltaプロンプト生成機能がない

#### 2. Retryシステム（既存）
- **場所**: `src/noveler/domain/services/progressive_write_manager.py:98, 571-645`
- **機能**:
  - `MAX_RETRIES = 3`: デフォルトリトライ回数
  - `execute_writing_step()`: ユーザー確認型リトライ
  - フィードバックシステムとの統合
- **問題点**: 汎用的なエラーリトライのみで、`by_task`失敗に特化した改善提案がない

#### 3. STEP10関連（既存）
- **場所**: `src/noveler/presentation/mcp/plugins/design_senses_plugin.py`
- **機能**: 五感描写設計ツール（会話IDベース）
- **問題点**: 非視覚センス比率の定量評価機能がない

---

## Feature 1: Generator Retry Policy with Delta Prompt

### 要件定義

#### 機能要件
1. **by_task失敗検出**: 既存の`_apply_by_task_validation()`結果を利用
2. **失敗サマリー生成**: 失敗したタスクIDとその理由をリスト化
3. **Deltaプロンプト合成**:
   - 失敗したタスクIDを明示
   - 期待されるルール（enum/range/nonempty）を再提示
   - 前回の出力との差分を指摘
4. **自動リトライ**: `MAX_RETRIES`範囲内で自動再実行

#### 非機能要件
- **DDD準拠**: Domain層での実装
- **B20準拠**: 既存の`progressive_write_manager.py`を拡張
- **後方互換性**: 既存の`execute_writing_step()`インターフェースを維持
- **ログ**: 統一ロギング（`ILogger`）でretry履歴を記録

### 技術設計

#### コンポーネント構成
```
progressive_write_manager.py
├─ _apply_by_task_validation()           # 既存: 検証実行
├─ _compose_delta_prompt()               # 新規: deltaプロンプト生成
├─ _extract_failed_tasks()               # 新規: 失敗タスク抽出
├─ _format_task_guidance()               # 新規: ルールガイダンス整形
└─ execute_writing_step_async()          # 改修: delta prompt統合
```

#### Deltaプロンプト構造
```markdown
## 前回実行の検証結果

以下のタスクが要件を満たしていません：

### タスク: {task_id}
- **期待**: {expected_rule}
- **実際**: {actual_value}
- **理由**: {failure_reason}

## 修正指示

上記タスクについて、以下の点を改善してください：
1. [task_id]: {specific_guidance}
2. ...

## 再実行用プロンプト

{original_prompt}

---
**Note**: これは {retry_count}/{MAX_RETRIES} 回目のリトライです。
```

#### 実装手順（Phase 1: 最小実装）
1. **Step 1**: `_extract_failed_tasks()` 実装
   - `validation["by_task"]`から`status == "fail"`を抽出
   - 失敗理由（notes）を整理
2. **Step 2**: `_compose_delta_prompt()` 実装
   - テンプレートベースのプロンプト生成
   - `template_data`から期待ルールを取得
3. **Step 3**: `execute_writing_step_async()` 改修
   - validation失敗時にdeltaプロンプトを生成
   - LLM再実行時にdeltaプロンプトを追加
4. **Step 4**: テスト追加
   - `tests/unit/domain/services/test_progressive_write_manager.py`
   - by_task失敗→deltaプロンプト生成→リトライ成功のシナリオ

#### 実装手順（Phase 2: 拡張機能）
1. **差分ハイライト**: 前回出力と今回出力のdiff生成
2. **学習機能**: 頻出失敗パターンのキャッシュ
3. **動的閾値**: retry回数に応じてルール緩和

### 受入基準
- [ ] by_task検証失敗時にdeltaプロンプトが生成される
- [ ] deltaプロンプトに失敗タスクID・期待ルール・具体的ガイダンスが含まれる
- [ ] 自動リトライが`MAX_RETRIES`回まで実行される
- [ ] リトライ履歴がログに記録される
- [ ] 既存テストが全てパスする

---

## Feature 2: STEP10 Non-Visual Sense Ratio Estimator

### 要件定義

#### 機能要件
1. **テキスト解析**: 生原稿から五感描写を抽出
2. **センス分類**: 視覚/聴覚/触覚/嗅覚/味覚の5分類
3. **比率計算**: 非視覚センスの割合を算出
4. **ヒューリスティック**: 形態素解析不要の軽量実装

#### 非機能要件
- **Domain層実装**: `src/noveler/domain/services/sense_analysis/`
- **軽量**: regex/辞書ベースのヒューリスティック
- **拡張性**: 将来的に機械学習モデルへ置換可能
- **統一ロギング**: `ILogger`使用

### 技術設計

#### コンポーネント構成
```
src/noveler/domain/services/sense_analysis/
├─ __init__.py
├─ sense_ratio_estimator.py              # メインサービス
├─ sense_dictionaries.py                 # 五感語彙辞書
└─ heuristic_patterns.py                 # パターンマッチング

tests/unit/domain/services/sense_analysis/
└─ test_sense_ratio_estimator.py         # ユニットテスト
```

#### 辞書設計（ヒューリスティック）
```python
SENSE_DICTIONARIES = {
    "visual": {
        "keywords": ["見る", "眺める", "輝く", "光る", "色", "赤い", ...],
        "patterns": [r".*目.*", r".*瞳.*", r".*視.*"],
    },
    "auditory": {
        "keywords": ["聞く", "聞こえる", "音", "声", "響く", ...],
        "patterns": [r".*耳.*", r".*響.*", r".*鳴.*"],
    },
    "tactile": {
        "keywords": ["触る", "触れる", "柔らかい", "硬い", "温かい", ...],
        "patterns": [r".*手.*", r".*肌.*", r".*感触.*"],
    },
    "olfactory": {
        "keywords": ["香る", "匂う", "香り", "臭い", ...],
        "patterns": [r".*鼻.*", r".*香.*", r".*匂.*"],
    },
    "gustatory": {
        "keywords": ["味わう", "甘い", "苦い", "辛い", ...],
        "patterns": [r".*舌.*", r".*味.*"],
    },
}
```

#### アルゴリズム（Phase 1: 基本実装）
1. **前処理**: 会話文（「」『』）を除外（地の文のみ評価）
2. **マッチング**: キーワード・パターンで各センスをスコアリング
3. **正規化**: センス別出現頻度を総出現数で除算
4. **比率計算**: `non_visual_ratio = (auditory + tactile + olfactory + gustatory) / total`

#### 実装手順（Phase 1: 基本実装）
1. **Step 1**: 辞書・パターン定義
   - `sense_dictionaries.py`: 初期語彙100語/センス
2. **Step 2**: `SenseRatioEstimator`実装
   - `estimate(text: str) -> SenseRatioResult`
   - 結果構造: `{"visual": 0.6, "auditory": 0.2, ...}`
3. **Step 3**: STEP10統合
   - `design_senses_plugin.py`でメトリクス追加
   - MCP出力に`sense_metrics`フィールド追加
4. **Step 4**: テスト追加
   - 視覚優位サンプル: 80%以上視覚
   - バランス型サンプル: 各センス均等
   - 非視覚優位サンプル: 60%以上非視覚

#### 実装手順（Phase 2: 精度向上）
1. **機械学習モデル**: BERTベースの分類器
2. **文脈考慮**: 前後文を考慮した判定
3. **ユーザー辞書**: プロジェクト固有語彙の追加機能

### 受入基準
- [ ] テキストから五感描写を検出できる
- [ ] 非視覚センス比率が0.0～1.0で算出される
- [ ] 会話文が除外される
- [ ] STEP10ツール出力に`sense_metrics`が含まれる
- [ ] ユニットテストで80%以上の精度

---

## 実装優先度

### P0（緊急）
*なし*

### P1（高優先度）
1. **Generator retry policy - Phase 1** (工数: 2-3日)
   - 既存コードベースへの統合が容易
   - ユーザー体験への直接的改善
   - リスク: 低（既存retry機構の拡張）

### P2（中優先度）
2. **Sense ratio estimator - Phase 1** (工数: 3-4日)
   - 新規ドメインサービス
   - STEP10の品質向上に貢献
   - リスク: 中（辞書品質に依存）

### P3（低優先度）
3. **Phase 2拡張機能** (工数: 各1-2週間)
   - 差分ハイライト
   - 機械学習モデル統合

---

## リスク管理

### リスク1: Deltaプロンプトの効果不明
- **対策**: A/Bテストでリトライ成功率を測定
- **軽減**: 最小実装で効果検証後に拡張

### リスク2: ヒューリスティック辞書の精度
- **対策**: 100エピソード分の手動評価で閾値設定
- **軽減**: 初期は参考値として提示、機械学習モデルへ段階移行

### リスク3: 既存コードへの影響
- **対策**: 機能フラグで新機能を制御（`enable_delta_prompt_retry`）
- **軽減**: 既存テスト全通過を必須とする

---

## 次のアクション

### 即座に実行可能
1. **仕様レビュー**: このドキュメントのチームレビュー
2. **PoC実装**: `_compose_delta_prompt()`の最小実装（30分）
3. **辞書初稿**: 五感語彙50語/センスの収集（1時間）

### Phase 1実装（推奨スケジュール）
- **Week 1**: Generator retry policy Phase 1
- **Week 2**: Sense ratio estimator Phase 1
- **Week 3**: 統合テスト・ドキュメント更新

### 検証指標
- **Retry policy**: リトライ成功率（目標: 70%以上）
- **Sense ratio**: 人手評価との一致率（目標: 80%以上）

---

## 参考資料

### コードベース
- `src/noveler/domain/services/progressive_write_manager.py`: 既存retry実装
- `src/noveler/domain/services/v2_prompt_synthesis_service.py`: プロンプト合成パターン
- `src/noveler/presentation/mcp/plugins/design_senses_plugin.py`: STEP10ツール

### 仕様書
- `specs/SPEC-YAML-021_array_addressing.md`: テンプレート検証仕様
- `TODO.md:67-99`: Nice to Have セクション

---

**作成日**: 2025-10-01
**作成者**: Claude Code (Serena MCP)
**ステータス**: Draft → Review待ち
