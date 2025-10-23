# SPEC-QUALITY-013: 品質チェックユースケース仕様書

## 概要
`QualityCheckUseCase`は、エピソードに対する品質チェックの実行を統合管理するユースケースです。品質ルールの適用、違反の検出、自動修正機能を提供し、ドメインロジックとインフラ層を調整します。

## クラス設計

### QualityCheckUseCase

**責務**
- エピソードの存在確認
- 品質ルールの取得・フィルタリング
- 品質チェックアグリゲートの調整
- 自動修正機能の提供
- 結果の永続化

## データ構造

### QualityCheckRequest (DataClass)
```python
@dataclass(frozen=True)
class QualityCheckRequest:
    episode_id: str                      # エピソードID
    project_id: str                      # プロジェクトID
    check_options: dict[str, Any]        # チェックオプション
```

**チェックオプション例**
```python
{
    "auto_fix": bool,                    # 自動修正フラグ
    "categories": list[str],             # 対象カテゴリ
    "severity_level": str,               # 重要度レベル
    "custom_rules": list[dict],          # カスタムルール
}
```

**デフォルト設定**
- `auto_fix`: False（自動修正無効）

### QualityCheckResponse (DataClass)
```python
@dataclass
class QualityCheckResponse:
    success: bool                        # 処理成功フラグ
    check_id: str | None = None          # チェックID
    episode_id: str | None = None        # エピソードID
    total_score: float | None = None     # 総合品質スコア
    violations: list[QualityViolation] | None = None  # 違反一覧
    is_passed: bool | None = None        # 品質基準合格フラグ
    executed_at: datetime | None = None  # 実行時刻
    auto_fix_applied: bool = False       # 自動修正適用フラグ
    fixed_content: str | None = None     # 修正後コンテンツ
    error_message: str | None = None     # エラーメッセージ
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: QualityCheckRequest) -> QualityCheckResponse:
```

**目的**
エピソードに対して品質チェックを実行し、結果を返す。

**引数**
- `request`: 品質チェック要求

**戻り値**
- `QualityCheckResponse`: 品質チェック結果

**処理フロー**
1. **エピソード存在確認**: 指定されたエピソードの取得
2. **品質ルール取得**: デフォルトルールの取得とフィルタリング
3. **アグリゲート作成**: QualityCheckAggregateの作成・設定
4. **品質チェック実行**: ドメインロジックによる品質検証
5. **自動修正処理**: オプション指定時の自動修正適用
6. **結果永続化**: チェック結果の保存
7. **レスポンス構築**: 統合結果の返却

**成功パターン**
- 品質チェック完了（合格）
- 品質チェック完了（不合格、違反あり）
- 自動修正適用後の品質改善

**エラーパターン**
- エピソード不存在
- 品質ルール未設定
- 無効な品質ルール（`InvalidQualityRuleError`）
- 一般的な実行エラー

## プライベートメソッド

### _filter_rules_by_options()

**シグネチャ**
```python
def _filter_rules_by_options(
    self,
    rules: list[QualityRule],
    options: dict[str, Any]
) -> list[QualityRule]:
```

**目的**
チェックオプションに基づいて品質ルールをフィルタリングする。

**フィルタリング条件**
- **有効性**: `rule.enabled`がTrueのもののみ
- **カテゴリ**: `categories`オプション指定時の絞り込み
- **重要度**: 将来的な拡張ポイント

**戻り値**
- フィルタリング済みの品質ルール一覧

### _apply_auto_fixes()

**シグネチャ**
```python
def _apply_auto_fixes(
    self,
    content: str,
    violations: list[QualityViolation],
    rules: list[QualityRule]
) -> tuple[str, bool]:
```

**目的**
検出された違反に対して自動修正を適用する。

**引数**
- `content`: 元のコンテンツ
- `violations`: 検出された違反一覧
- `rules`: 適用可能な品質ルール

**戻り値**
- `tuple[修正後コンテンツ, 修正適用フラグ]`

**自動修正例**
- **三点リーダー**: `。。。` → `…`
- **感嘆符**: `！！` → `！`
- **句読点**: 全角・半角の統一
- **敬語**: 一貫性のない敬語レベルの修正

**制限事項**
- 安全な修正のみ実行
- 文意を変更する可能性がある修正は避ける
- ルールで`auto_fixable`が設定されたもののみ対象

## 依存関係

### ドメイン層
- `QualityCheckAggregate`: 品質チェックアグリゲートルート
- `QualityRule`: 品質ルールエンティティ
- `QualityViolation`: 品質違反値オブジェクト
- `InvalidQualityRuleError`: ドメイン例外

### リポジトリ
- `EpisodeRepository`: エピソードリポジトリ
- `QualityCheckRepository`: 品質チェックリポジトリ

## 設計原則遵守

### DDD準拠
- ✅ ドメインロジックは`QualityCheckAggregate`に委譲
- ✅ 値オブジェクト（`QualityViolation`）の適切な使用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ ドメイン例外の適切なハンドリング

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な例外処理
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# リポジトリの準備
episode_repo = YamlEpisodeRepository()
quality_repo = YamlQualityCheckRepository()

# ユースケース作成
use_case = QualityCheckUseCase(episode_repo, quality_repo)

# 基本的な品質チェック
request = QualityCheckRequest(
    episode_id="episode_001",
    project_id="sample_novel",
    check_options={
        "categories": ["basic_writing", "story_structure"],
        "auto_fix": False
    }
)

response = use_case.execute(request)

if response.success:
    print(f"品質スコア: {response.total_score}")
    print(f"合格: {response.is_passed}")

    if response.violations:
        print("検出された違反:")
        for violation in response.violations:
            print(f"- {violation.rule_name}: {violation.message}")
else:
    print(f"エラー: {response.error_message}")

# 自動修正付き品質チェック
auto_fix_request = QualityCheckRequest(
    episode_id="episode_001",
    project_id="sample_novel",
    check_options={
        "auto_fix": True,
        "categories": ["punctuation", "format"]
    }
)

auto_fix_response = use_case.execute(auto_fix_request)

if auto_fix_response.success and auto_fix_response.auto_fix_applied:
    print("自動修正が適用されました")
    print(f"修正前スコア: {response.total_score}")
    print(f"修正後スコア: {auto_fix_response.total_score}")
```

## 品質ルール設定例

```python
# カテゴリ別ルール設定
check_options = {
    "categories": [
        "basic_writing",      # 基本的な文章作法
        "story_structure",    # 物語構造
        "character_voice",    # キャラクターの一人称
        "punctuation",        # 句読点・記号
        "formatting",         # フォーマット
    ],
    "severity_level": "normal",  # low, normal, high, strict
    "auto_fix": True,
    "custom_rules": [
        {
            "rule_id": "custom_001",
            "name": "プロジェクト固有ルール",
            "pattern": r"特定のパターン",
            "auto_fixable": False
        }
    ]
}
```

## エラーハンドリング

### InvalidQualityRuleError
- 無効な品質ルール設定
- ルール間の矛盾
- 必須パラメータの不足

### 一般例外
- ファイルアクセスエラー
- ネットワークエラー（外部API使用時）
- メモリ不足（大容量テキスト処理時）

## テスト観点

### 単体テスト
- 正常な品質チェックフロー
- エピソード不存在時の処理
- ルールフィルタリングの正確性
- 自動修正機能の動作
- 各種エラー条件での動作

### 統合テスト
- 実際のエピソードファイルでの品質チェック
- ドメインアグリゲートとの協調動作
- リポジトリとの連携

## 品質基準

- **正確性**: 品質ルールの正確な適用と違反検出
- **信頼性**: エラー時の安全な処理と適切な情報提供
- **性能**: 大容量テキストでの効率的な処理
- **保守性**: 明確な責務分離と拡張可能な設計
- **ユーザビリティ**: 分かりやすい違反メッセージと修正提案
