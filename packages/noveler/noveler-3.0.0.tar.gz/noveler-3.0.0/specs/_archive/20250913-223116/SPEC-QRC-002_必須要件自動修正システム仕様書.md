# SPEC-QRC-002: 必須要件自動修正システム仕様書

**作成日**: 2025年8月30日
**バージョン**: v1.0.0
**関連**: SPEC-QRC-001 (Quality Requirements Checker)
**ステータス**: 仕様策定中

## 1.0 概要

### 1.1 目的
必須要件（文字数、文章リズム）不合格時に自動で修正を試行し、合格するまで規定回数まで繰り返し実行するシステムを実装する。

### 1.2 背景
現在のQuality Requirements Checker (SPEC-QRC-001)では、必須要件不合格時に修正指示を提供するのみで、実際の修正・再チェックは手動で行う必要がある。ユーザー効率性向上のため、自動修正ループ機能の実装が要求された。

### 1.3 対象範囲
- 必須要件不合格時の自動修正実行
- 修正後の自動再チェック
- 最大試行回数制限による無限ループ防止
- 修正履歴トラッキングと進捗可視化

## 2.0 要件定義

### 2.1 機能要件

#### 2.1.1 自動修正ループ機能
- **FR-001**: 必須要件不合格時に自動で修正を実行する
- **FR-002**: 修正後に自動で再チェックを実行する
- **FR-003**: 合格するまで修正→再チェックを繰り返す
- **FR-004**: 最大試行回数（デフォルト5回）で停止する

#### 2.1.2 修正機能
- **FR-005**: 文字数不足時の自動文章拡張
- **FR-006**: 文字数超過時の自動削減
- **FR-007**: 連続短文問題の自動文結合
- **FR-008**: 連続長文問題の自動文分割

#### 2.1.3 履歴トラッキング
- **FR-009**: 各修正試行の詳細記録
- **FR-010**: 修正前後の問題比較
- **FR-011**: 修正成功率の算出
- **FR-012**: 実行時間の計測

### 2.2 非機能要件

#### 2.2.1 性能要件
- **NFR-001**: タイムアウト制限（デフォルト300秒）
- **NFR-002**: 1回の修正実行は30秒以内で完了
- **NFR-003**: メモリ使用量は修正対象コンテンツの10倍以内

#### 2.2.2 信頼性要件
- **NFR-004**: 修正失敗時も元コンテンツを保持
- **NFR-005**: 修正ループ中の例外処理
- **NFR-006**: 修正履歴の完全性保証

## 3.0 アーキテクチャ設計

### 3.1 コンポーネント構成

```
QualityRequirementsAutoFixer
├── quality_requirements_checker: QualityRequirementsChecker
├── max_attempts: int
├── timeout_seconds: int
└── project_name: str

AutoFixerResult
├── status: AutoFixerStatus
├── final_content: str
├── fix_attempts: List[FixAttempt]
└── final_check_result: RequirementsCheckResult

FixAttempt
├── attempt_number: int
├── original_content: str
├── fixed_content: str
├── issues_before/after: List[RequirementIssue]
└── success: bool
```

### 3.2 既存実装調査（必須）

#### 3.2.1 CODEMAP確認
- ✅ `quality_requirements_checker.py` - 既存のチェック機能を再利用
- ✅ `smart_auto_enhancement_adapter.py` - 既存アダプターに統合
- ❌ 自動修正機能の類似実装は存在しない（新規実装必要）

#### 3.2.2 共有コンポーネント確認
- ✅ `TextRhythmAnalysisService` - リズム分析機能を再利用
- ✅ `WordCount` - 文字数計算機能を再利用
- ✅ `YamlProjectConfigRepository` - プロジェクト設定読み込み機能を再利用

#### 3.2.3 再利用可否判定
- **再利用対象**: QualityRequirementsChecker、TextRhythmAnalysisService
- **新規実装対象**: 自動修正エンジン、修正ループ制御、履歴トラッキング
- **統合対象**: Smart Auto-Enhancement Adapter

## 4.0 実装設計

### 4.1 クラス設計

#### 4.1.1 QualityRequirementsAutoFixer
```python
class QualityRequirementsAutoFixer:
    """品質必須要件自動修正サービス"""

    def __init__(self, project_name: str, max_attempts: int, timeout_seconds: int)
    def auto_fix_requirements(self, content: str) -> AutoFixerResult
    def _apply_fixes(self, content: str, issues: List[RequirementIssue]) -> str
    def _fix_word_count_issue(self, content: str, issue: RequirementIssue) -> str
    def _fix_rhythm_issue(self, content: str, issue: RequirementIssue) -> str
    def get_fix_summary(self, result: AutoFixerResult) -> str
```

#### 4.1.2 修正戦略詳細

##### 文字数修正戦略
- **不足時**: 既存文章への描写追加、詳細化
- **超過時**: 冗長表現の削減、不要部分のカット

##### リズム修正戦略
- **連続短文**: 文の結合による中文化
- **連続長文**: 句読点による文分割

### 4.2 統合ポイント

#### 4.2.1 Smart Auto-Enhancement統合
```python
# BasicQualityCheckerAdapterに修正ループ機能を追加
def check_quality_with_auto_fix(self, episode_content: str) -> tuple[QualityScore, list[str]]:
    """必須要件チェック＋自動修正機能"""

    # 1. 基本チェック
    requirements_result = self.requirements_checker.check_must_pass_requirements(episode_content)

    # 2. 不合格時は自動修正実行
    if not requirements_result.all_passed:
        auto_fixer = QualityRequirementsAutoFixer(self.project_name)
        fix_result = auto_fixer.auto_fix_requirements(episode_content)

        # 修正結果の評価とスコア計算
        if fix_result.status == AutoFixerStatus.COMPLETED_SUCCESS:
            # 修正成功時の処理
        else:
            # 修正失敗時の処理
```

## 5.0 テスト戦略

### 5.1 単体テスト

#### 5.1.1 修正機能テスト
- 文字数不足コンテンツの修正テスト
- 文字数超過コンテンツの修正テスト
- 連続短文問題の修正テスト
- 連続長文問題の修正テスト

#### 5.1.2 ループ制御テスト
- 最大試行回数制限テスト
- タイムアウト機能テスト
- 修正成功時の早期終了テスト

### 5.2 統合テスト

#### 5.2.1 Smart Auto-Enhancement統合テスト
- 修正ループ付きSmart Auto-Enhancement実行
- プロジェクト設定連携テスト
- 修正履歴トラッキング検証

## 6.0 運用要件

### 6.1 設定項目
- `auto_fix_enabled`: 自動修正機能有効化フラグ
- `max_fix_attempts`: 最大修正試行回数（デフォルト: 5）
- `fix_timeout_seconds`: 修正タイムアウト秒数（デフォルト: 300）

### 6.2 ログ出力
- 修正試行開始/終了ログ
- 各修正の成功/失敗ログ
- 最終結果サマリログ

## 7.0 今後の拡張

### 7.1 AI修正エンジン統合
- OpenAI/Claude API連携による高品質修正
- コンテキスト保持型修正
- 文体・トーン一貫性保持

### 7.2 学習機能
- 修正成功パターンの学習
- プロジェクト別修正戦略最適化
- ユーザー好み反映機能

## 8.0 実装スケジュール

### Phase 1: コア機能実装（本PR）
- QualityRequirementsAutoFixer実装
- 基本修正戦略実装
- Smart Auto-Enhancement統合

### Phase 2: 高度化（次期PR）
- AI修正エンジン統合
- 学習機能実装
- UIダッシュボード追加
