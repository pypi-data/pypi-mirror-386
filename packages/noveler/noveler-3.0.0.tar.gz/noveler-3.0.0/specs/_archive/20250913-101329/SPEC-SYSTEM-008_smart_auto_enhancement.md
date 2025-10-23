# Smart Auto-Enhancement システム仕様書

## SPEC-SAE-001～006: Smart Auto-Enhancement 統合仕様

## 概要

Smart Auto-Enhancement は、従来の段階的品質チェックを統合し、デフォルトで全段階（基本→A31→Claude分析）を自動実行する革新的品質管理システムです。

**核心価値提案:**
- **デフォルト実行**: `novel check 4` で Smart Auto-Enhancement が標準動作
- **情報統合表示**: 分離されていた品質情報を統合して表示
- **品質ロジック改善**: 平均値文字数チェック廃止、構造的品質重視
- **DDD準拠設計**: ドメイン駆動設計による高い保守性・拡張性

## アーキテクチャ設計

### ドメイン層 (Domain Layer)

#### エンティティ (Entities)
```
SmartAutoEnhancement
├── EnhancementRequest (Value Object)
├── EnhancementResult (Value Object)
├── EnhancementStage (Enum)
└── EnhancementMode (Enum)
```

**不変条件:**
- リクエストは有効なエピソード番号とプロジェクト情報を持つ
- Smart Auto-Enhancement モードでは全段階を自動実行
- 各段階の結果は累積的に管理される
- 失敗時は適切なエラー情報を保持する

#### ドメインサービス (Domain Services)
```python
class SmartAutoEnhancementService:
    def execute_enhancement(self, enhancement: SmartAutoEnhancement, episode_content: str) -> SmartAutoEnhancement
    def should_enable_smart_auto_mode(self, request: EnhancementRequest) -> bool
    def determine_display_mode(self, enhancement: SmartAutoEnhancement) -> str
```

### アプリケーション層 (Application Layer)

#### ユースケース
```python
class SmartAutoEnhancementUseCase:
    def execute(self, request: SmartAutoEnhancementUseCaseRequest) -> SmartAutoEnhancementUseCaseResponse
    def should_use_smart_auto_enhancement(self, request: SmartAutoEnhancementUseCaseRequest) -> bool
```

### インフラストラクチャ層 (Infrastructure Layer)

#### アダプター
- `BasicQualityCheckerAdapter`: 改善された基本品質チェック
- `A31EvaluatorAdapter`: 既存A31評価システム連携
- `ClaudeAnalyzerAdapter`: Claude分析システム連携

## 機能仕様

### 1. デフォルト動作変更

**従来:**
```bash
novel check 4  # → 段階的実行、情報分離表示
```

**Smart Auto-Enhancement:**
```bash
novel check 4  # → 全段階統合実行、詳細情報統合表示
```

**オプトアウト:**
```bash
novel check 4 --standard  # → 従来の段階的実行モード
```

### 2. 品質評価ロジック改善

#### 従来の基本品質チェック（廃止）
- ❌ 平均値による画一的文字数評価
- ❌ A31評価との重複チェック項目

#### 改善された基本品質チェック
```python
def _calculate_improved_basic_score(self, content: str) -> float:
    score = 70.0  # ベーススコア

    # 1. 最小文字数チェック（極端に短いもののみ）
    if len(content) < 500:
        score -= 30.0  # 明らかに不足
    elif len(content) < 1000:
        score -= 10.0  # やや不足

    # 2. 基本的な文章構造チェック
    if self._has_basic_structure(content):
        score += 10.0

    # 3. 明らかな文章エラーのチェック
    if not self._has_obvious_errors(content):
        score += 10.0

    # 4. 段落構造の基本チェック
    if self._has_proper_paragraphs(content):
        score += 10.0

    return min(100.0, max(0.0, score))
```

### 3. 統合表示システム

#### 実行フロー表示
```
✨ Smart Auto-Enhancement モード
全段階統合実行: 基本→A31→Claude分析

🎉 Smart Auto-Enhancement 完了
最終品質スコア: 85.2
改善提案総数: 12件
実行時間: 2500ms

🌟 優秀な品質基準をクリア
```

#### 品質判定基準
- **80.0 以上**: 🌟 優秀な品質基準をクリア
- **70.0 以上**: 📈 良好な品質（さらなる向上推奨）
- **70.0 未満**: 🔧 要改善（具体的提案を確認してください）

## テスト仕様

### 単体テスト (Unit Tests)

#### ドメインエンティティテスト
```python
@pytest.mark.spec("SPEC-SAE-001")
class TestSmartAutoEnhancement:
    def test_create_smart_auto_enhancement_with_valid_request()
    def test_enhanced_mode_forces_detailed_review()
    def test_smart_auto_mode_prevents_all_stages_skip()
    def test_advance_to_stage_successfully()
    def test_domain_invariants_validation()
```

#### ユースケーステスト
```python
@pytest.mark.spec("SPEC-SAE-003")
class TestSmartAutoEnhancementUseCase:
    def test_execute_smart_auto_enhancement_successfully()
    def test_execute_enhanced_mode_forces_all_stages()
    def test_execute_handles_episode_not_found()
    def test_should_use_smart_auto_enhancement_with_explicit_mode()
```

### 統合テスト (Integration Tests)

#### CLI統合テスト
```python
@pytest.mark.spec("SPEC-SAE-007")
class TestSmartAutoEnhancementCLI:
    def test_novel_check_default_uses_smart_auto_enhancement()
    def test_novel_check_standard_option_uses_legacy_mode()
    def test_novel_check_displays_integrated_results()
```

## 品質ゲート

### 必須要件
- [ ] 全単体テストが SPEC-SAE-001～006 を満たす
- [ ] CLI統合テストが SPEC-SAE-007 を満たす
- [ ] `novel check 4` がデフォルトで Smart Auto-Enhancement を実行
- [ ] 品質スコア統合表示が正常動作
- [ ] 改善提案統合表示が正常動作

### 性能要件
- [ ] 実行時間: 従来比 120% 以内（統合処理による若干の増加は許容）
- [ ] メモリ使用量: 従来比 150% 以内
- [ ] エラー率: 1% 未満

## 運用要件

### 監視対象
- Smart Auto-Enhancement 実行成功率
- 各段階の実行時間分布
- ユーザーの `--standard` オプション使用率

### アラート条件
- Smart Auto-Enhancement 実行成功率が 95% を下回る
- 平均実行時間が 5秒を超える
- エラー率が 1% を超える

## 移行計画

### Phase 1: 実装完了 ✅
- Smart Auto-Enhancement システム実装
- DDD準拠アーキテクチャ構築
- 基本品質ロジック改善
- CLI統合実装

### Phase 2: 検証・調整
- ユーザーフィードバック収集
- 性能調整
- エラーハンドリング改善

### Phase 3: 最適化
- 実行時間最適化
- メモリ使用量最適化
- ユーザビリティ向上

## 関連ドキュメント

- [developer guide](../docs/guides/developer_guide.md) - 開発者向けガイド
- [README.md](../README.md) - システム概要とクイックスタート
- [docs/guides/quick_start.md](../docs/guides/quick_start.md) - ユーザー向けガイド
- [CLAUDE.md](../CLAUDE.md) - 開発規約

## 変更履歴

- **2025-08-05**: 初版作成、Smart Auto-Enhancement システム実装完了
- **2025-08-05**: Option B本来仕様実装、平均値文字数チェック廃止
