# SPEC-QUALITY-101: content_quality_enhancer 仕様書

## 1. 目的
この機能は、小説の文章品質を自動的に改善するシステムです。入力された文章を分析し、文学的表現の向上、読みやすさの改善、スタイルの統一を行います。執筆者が高品質な文章を書けるよう支援することで、読者の満足度向上と執筆効率の改善を実現します。

## 2. 前提条件
- 既存の品質チェックシステムが動作している
- Episode エンティティが正しく定義されている
- QualityScore 値オブジェクトが利用可能
- プロジェクト設定（30_設定集）が適切に配置されている
- 固有名詞保護システムが動作している

## 3. 主要な振る舞い

### 3.1 文章品質の自動改善
- **入力**: 改善対象のテキスト文章（str）
- **処理**: 以下の改善を自動実行
  - 文章の冗長性を削減
  - 感情表現の具体化（「悲しい」→「涙が頬を伝った」）
  - 文末表現の多様化（「だった」の連続を回避）
  - 描写の五感活用（視覚以外の感覚を追加）
  - 会話文の自然さ向上
- **出力**: 改善されたテキスト文章とその改善ポイント一覧

### 3.2 品質スコアの向上提案
- **入力**: 現在のQualityScore、改善目標スコア
- **処理**:
  - 現在のスコアを分析
  - 改善効果の高い項目を特定
  - 具体的な改善提案を生成
- **出力**: 優先度付きの改善提案リスト

### 3.3 固有名詞保護機能
- **入力**: 改善対象テキスト、プロジェクト設定
- **処理**:
  - 30_設定集から固有名詞を自動抽出
  - 固有名詞を改善対象から除外
  - 改善後も固有名詞の整合性を保持
- **出力**: 固有名詞が保護された改善結果

## 4. 入出力仕様

### 4.1 ContentQualityEnhancer クラス
```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ImprovementSuggestion:
    """改善提案"""
    category: str  # "emotion", "style", "dialogue", "description"
    original_text: str
    improved_text: str
    reason: str
    priority: int  # 1-5, 1が最高優先度

@dataclass
class EnhancementResult:
    """改善結果"""
    original_text: str
    enhanced_text: str
    improvements: List[ImprovementSuggestion]
    quality_score_before: float
    quality_score_after: float
    success: bool
    error_message: Optional[str] = None

class ContentQualityEnhancer:
    def enhance_text(self, text: str, target_score: float = 80.0) -> EnhancementResult:
        """文章の品質を自動改善"""
        pass

    def suggest_improvements(self, text: str) -> List[ImprovementSuggestion]:
        """改善提案を生成"""
        pass

    def protect_proper_nouns(self, text: str, project_path: str) -> List[str]:
        """固有名詞を保護対象として抽出"""
        pass
```

### 4.2 改善カテゴリ
- **emotion**: 感情表現の具体化
- **style**: 文体・文末表現の改善
- **dialogue**: 会話文の自然さ向上
- **description**: 描写の豊かさ向上
- **readability**: 読みやすさの改善

## 5. エラーハンドリング

### 5.1 入力データエラー
- **EmptyTextError**: 空文字列または空白のみの入力
- **TextTooLongError**: 10,000文字を超える入力
- **InvalidEncodingError**: 文字エンコーディングが不正

### 5.2 処理エラー
- **ProperNounExtractionError**: 固有名詞の抽出に失敗
- **QualityAnalysisError**: 品質分析に失敗
- **EnhancementError**: 改善処理に失敗

### 5.3 設定エラー
- **ProjectSettingsNotFoundError**: プロジェクト設定が見つからない
- **InvalidTargetScoreError**: 目標スコアが不正な値（0-100外）

## 6. パフォーマンス要件

- **レスポンスタイム**:
  - 1,000文字以下: 200ms以内
  - 1,000-5,000文字: 500ms以内
  - 5,000-10,000文字: 1秒以内
- **メモリ使用量**: 実行中のメモリ使用量は50MB以下
- **品質向上率**: 改善前後で品質スコアを平均15%以上向上

## 7. セキュリティ考慮事項

- **データ保護**:
  - 改善対象のテキストは一時的にのみメモリに保持
  - 処理完了後は即座にメモリから削除
- **固有名詞保護**:
  - 小説固有の重要な名詞（キャラクター名、地名等）は改変禁止
  - 設定ファイルの改竄検出
- **入力検証**:
  - 不正な制御文字の除去
  - HTMLタグの無害化

## 8. 実装チェックリスト

### Phase 1: 基本実装
- [x] ContentQualityEnhancer クラスの基本構造実装
- [x] enhance_text メソッドの最小実装
- [x] EnhancementResult データクラスの実装
- [x] 基本的なエラーハンドリング実装

### Phase 2: 改善機能実装
- [x] 感情表現の具体化機能
- [x] 文末表現の多様化機能
- [x] 描写の五感活用機能
- [x] 会話文の自然さ向上機能

### Phase 3: 品質分析統合
- [x] 品質スコア計算との統合
- [x] 改善提案生成機能
- [x] 優先度付けアルゴリズム実装

### Phase 4: 固有名詞保護
- [x] 30_設定集からの固有名詞抽出
- [x] 固有名詞保護機能の実装
- [x] 保護対象の自動更新機能

### Phase 5: パフォーマンス最適化
- [x] パフォーマンス要件（6）の確認
- [x] メモリ使用量の最適化
- [x] レスポンスタイムの改善

### Phase 6: 品質保証
- [x] セキュリティ考慮事項（7）の実装
- [x] 全エラーケースのテスト
- [x] 品質向上率の検証

### Phase 7: 統合・完成
- [x] 型定義（4）の完全性確認
- [x] 統合テストの実施
- [x] ドキュメント更新
- [x] コードレビュー

### **実装完了状況** (2025年7月22日更新)

✅ **TDD GREEN段階完了**: 全テストが通る最小実装を完成（681行）
✅ **核心機能実装**: 感情表現具体化、文末表現多様化、会話文改善、描写改善
✅ **固有名詞保護**: YAML設定ファイルからの自動抽出・保護機能
✅ **エラーハンドリング**: 全エラーケースの実装完了
✅ **パフォーマンス対応**: レスポンスタイム・メモリ使用量の最適化
✅ **DDD準拠リファクタリング版**: `content_quality_enhancer_refactored.py`（358行）

### **リファクタリング版の改善点**
- **リポジトリパターンの採用**: ConfigurationRepository, ManuscriptRepository
- **新しいデータ構造**: QualityAnalysisResult, ContentEnhancementResult（frozen dataclass）
- **依存性注入**: テスタビリティとモジュラリティの向上
- **簡潔な実装**: 681行から358行への削減（47%削減）

### **実装された改善パターン**
- **感情表現**: 悲しかった、嬉しかった、怒っていた、疲れていた、困っていた
- **文末表現**: 「だった」「ました」の多様化
- **描写の五感活用**: 視覚→聴覚、触覚、嗅覚への変換
- **会話文改善**: 自然な話し言葉への調整

## 9. 使用例

### 9.1 基本的な使用方法
```python
# 基本的な改善実行
enhancer = ContentQualityEnhancer()
result = enhancer.enhance_text("彼は悲しかった。雨が降っていた。")

print(f"改善前: {result.original_text}")
print(f"改善後: {result.enhanced_text}")
print(f"品質スコア: {result.quality_score_before:.1f} → {result.quality_score_after:.1f}")

# 改善提案の確認
for suggestion in result.improvements:
    print(f"[{suggestion.category}] {suggestion.reason}")
    print(f"  変更前: {suggestion.original_text}")
    print(f"  変更後: {suggestion.improved_text}")
```

### 9.2 改善提案のみ取得
```python
# 改善提案のみ生成（実際の変更は行わない）
suggestions = enhancer.suggest_improvements("彼は悲しかった。雨が降っていた。")
for suggestion in suggestions:
    print(f"優先度{suggestion.priority}: {suggestion.reason}")
```

### 9.3 固有名詞保護を使用した改善
```python
# プロジェクト設定を考慮した改善
result = enhancer.enhance_text(
    "綾瀬カノンは悲しかった。BUG.CHURCHのことを思い出していた。",
    project_path="../01_記憶共有世界/30_設定集"
)
# → "綾瀬カノン"と"BUG.CHURCH"は固有名詞として保護される
```

## 10. 関連ファイル

- **仕様書**: `scripts/specs/content_quality_enhancer.spec.md`
- **テスト**: `scripts/tests/spec_content_quality_enhancer.py`
- **実装**: `scripts/domain/services/content_quality_enhancer.py`
- **統合品質チェッカー**: `scripts/quality/integrated_quality_checker.py`
- **固有名詞保護**: `scripts/domain/services/proper_noun_protection.py`

## 11. 今後の拡張予定

- AI（大規模言語モデル）を活用した高度な改善提案
- ジャンル別の改善パターン（ファンタジー、SF、ミステリー等）
- 学習機能による個人的な文体の維持
- 改善履歴の分析による執筆技術向上支援
