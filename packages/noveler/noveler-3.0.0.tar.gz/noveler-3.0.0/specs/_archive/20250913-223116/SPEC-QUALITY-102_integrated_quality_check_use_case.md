# SPEC-QUALITY-102: IntegratedQualityCheckUseCase 仕様書

## 1. 目的
統合品質チェックユースケース。複数の品質チェッカーを統合実行し、ファイルの品質を総合評価する。DDD設計に基づくアプリケーション層の中核機能。

## 2. 前提条件
- 品質評価サービス（QualityEvaluationService）が実装されていること
- 各種品質チェッカーがチェッカーレジストリに登録済みであること
- ドメインエンティティ（QualityCheckSession, QualityCheckResult等）が定義済み
- ファイルシステムへのアクセス権限があること

## 3. 主要な振る舞い

### 3.1 品質チェックフロー
**入力**: QualityCheckRequest（プロジェクトID、ファイルパス、チェックタイプ、自動修正フラグ等）
**処理**:
1. ファイル内容の読み込みと検証
2. 品質チェックセッションの作成（UUID生成）
3. 指定された各種チェッカーの順次実行
4. チェック結果の集約と総合評価
5. 自動修正の適用（オプション）
6. セッション完了とサマリー出力
**出力**: QualityCheckResponse（成功/失敗、スコア、グレード、問題リスト、修正内容等）

### 3.2 一括チェック機能
**入力**: プロジェクトID、ファイルパターンリスト、設定
**処理**:
1. ファイルパターンのグロブ展開
2. 各ファイルに対する品質チェック実行
3. 結果リストの集約
**出力**: QualityCheckResponseのリスト

### 3.3 セッション管理
**機能**:
- チェックセッションの生成と管理
- セッションIDによる結果の永続化
- セッションサマリーの取得機能

## 4. インターフェース仕様

### 4.1 リクエスト/レスポンス
```python
@dataclass(frozen=True)
class QualityCheckRequest:
    project_id: str                        # プロジェクトID（必須）
    filepath: Path                         # チェック対象ファイルパス（必須）
    check_types: list[CheckType] | None    # チェックタイプリスト（デフォルト: 全種類）
    auto_fix: bool = False                 # 自動修正フラグ
    verbose: bool = True                   # 詳細出力フラグ
    config: dict[str, Any] | None = None   # チェッカー設定

@dataclass
class QualityCheckResponse:
    success: bool                          # 成功/失敗
    session_id: str | None = None          # セッションID
    total_score: float | None = None       # 総合スコア（0-100）
    grade: str | None = None              # グレード（S/A/B/C/D）
    check_results: list[dict] | None = None # 各チェック結果
    issues: list[dict] | None = None       # 発見された問題リスト
    suggestions: list[str] | None = None   # 改善提案リスト
    auto_fixed_content: str | None = None  # 自動修正後内容
    error_message: str | None = None       # エラーメッセージ
```

### 4.2 ユースケースクラス
```python
class IntegratedQualityCheckUseCase:
    def __init__(
        self,
        quality_evaluation_service: QualityEvaluationService,
        checker_registry: dict[CheckType, Any] | None = None
    )

    def check_quality(request: QualityCheckRequest) -> QualityCheckResponse
    def get_session_summary(session_id: str) -> dict[str, Any] | None
    def bulk_check(
        project_id: str,
        file_patterns: list[str],
        config: dict[str, Any] | None = None
    ) -> list[QualityCheckResponse]
```

## 5. チェックタイプ

### 5.1 サポート対象
```python
class CheckType(Enum):
    BASIC_STYLE = "basic_style"           # 基本文体チェック
    STORY_STRUCTURE = "story_structure"   # 物語構造チェック
    CHARACTER_CONSISTENCY = "character"   # キャラ一貫性チェック
    DIALOGUE_QUALITY = "dialogue"         # 会話品質チェック
    PACING = "pacing"                     # ペース配分チェック
    READABILITY = "readability"           # 読みやすさチェック
    TECHNICAL_ACCURACY = "technical"      # 技術的正確性チェック
```

### 5.2 チェッカー実行仕様
- 各チェッカーは独立して実行される
- エラー発生時は該当チェッカーのみ失敗扱い（他に影響なし）
- チェッカーレジストリから動的に実行対象を決定
- 実行時間の測定と記録

## 6. スコアリング仕様

### 6.1 総合スコア計算
```
総合スコア = Σ(各チェッカースコア × 重み) / チェッカー数
重み: BASIC_STYLE=1.5, STORY_STRUCTURE=2.0, その他=1.0
```

### 6.2 グレード判定
- S: 95-100点（優秀）
- A: 85-94点（良好）
- B: 70-84点（普通）
- C: 50-69点（要改善）
- D: 0-49点（要大幅改善）

## 7. 自動修正機能

### 7.1 対応可能な修正
- 句読点の重複削除（。。→。）
- 全角スペースの重複削除（　　→　）
- 基本的な文体統一
- 明らかな誤字脱字の修正

### 7.2 制限事項
- 内容の意味を変える修正は行わない
- 作者の意図的な表現は保持する
- 修正可能性の事前判定が必要

## 8. エラーハンドリング

### 8.1 ファイルエラー
- **ファイル不在**: "ファイルが見つかりません: {filepath}"
- **読み込みエラー**: "ファイル読み込みエラー: {詳細}"
- **エンコーディングエラー**: UTF-8での読み込み失敗時の処理

### 8.2 チェッカーエラー
- **個別チェッカー失敗**: 該当チェックのみスコア0、他は継続
- **レジストリ未登録**: 指定チェックタイプが未登録の場合はスキップ
- **設定エラー**: 不正な設定値の場合はデフォルト値を使用

### 8.3 システムエラー
- **一般的なエラー**: "品質チェックエラー: {詳細}"
- **メモリ不足**: 大容量ファイル処理時の制限

## 9. パフォーマンス要件

### 9.1 実行時間制限
- 単一ファイル: 10秒以内
- 一括チェック: ファイル数×5秒以内
- セッション管理: 0.1秒以内

### 9.2 メモリ使用量
- 単一セッション: 100MB以内
- 同時セッション: 最大10セッション
- ファイルサイズ制限: 10MB/ファイル

## 10. 使用例

### 10.1 基本的な品質チェック
```python
# ユースケースの準備
quality_service = QualityEvaluationService()
use_case = IntegratedQualityCheckUseCase(quality_service, checker_registry)

# リクエスト作成
request = QualityCheckRequest(
    project_id="my-novel",
    filepath=Path("第001話_始まりの朝.md"),
    check_types=[CheckType.BASIC_STYLE, CheckType.STORY_STRUCTURE],
    auto_fix=True,
    verbose=True
)

# 実行
response = use_case.check_quality(request)

if response.success:
    print(f"総合スコア: {response.total_score}")
    print(f"グレード: {response.grade}")
    for issue in response.issues:
        print(f"問題: {issue['message']}")
```

### 10.2 一括品質チェック
```python
# 複数ファイルの一括チェック
responses = use_case.bulk_check(
    project_id="my-novel",
    file_patterns=["40_原稿/*.md"],
    config={"strict_mode": True}
)

for response in responses:
    print(f"ファイル: {response.filepath}, スコア: {response.total_score}")
```

### 10.3 セッション情報の取得
```python
# セッションサマリーの取得
summary = use_case.get_session_summary(response.session_id)
print(f"チェック実行時間: {summary['total_execution_time']}")
print(f"発見問題数: {summary['total_issues']}")
```

## 11. 実装メモ
- 実装ファイル: `scripts/application/use_cases/integrated_quality_check_use_case.py`
- テストファイル: `tests/unit/application/use_cases/test_integrated_quality_check_use_case.py`
- 依存: QualityEvaluationService, QualityCheckSession, FileContent
- 作成日: 2025-07-21
- DDD準拠: ドメインロジックとインフラの分離実装済み

## 12. 技術的決定事項
- **セッション管理**: インメモリ（将来的にはRedis等での永続化検討）
- **チェッカーレジストリ**: 依存注入による柔軟な拡張性
- **ファイル処理**: 同期処理（大量ファイル処理時は非同期化検討）
- **エラー回復**: 個別チェッカー失敗時の継続実行
- **設定管理**: プロジェクト固有設定とグローバル設定の階層化

## 13. 今後の拡張計画
- [ ] 非同期実行による大量ファイル処理の高速化
- [ ] プラグイン機能による外部チェッカーの動的読み込み
- [ ] 機械学習による品質評価の精度向上
- [ ] Webインターフェースでのリアルタイム品質チェック
- [ ] 品質履歴の統計分析とトレンド表示
