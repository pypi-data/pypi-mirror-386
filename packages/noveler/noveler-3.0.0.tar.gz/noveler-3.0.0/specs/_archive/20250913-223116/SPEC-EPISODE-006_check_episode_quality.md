# SPEC-EPISODE-006: エピソード品質チェックユースケース仕様書

## SPEC-QUALITY-013: エピソード品質チェック (Smart Auto-Enhancement 統合)

**⚠️ 重要**: 2025年8月5日より、デフォルトで Smart Auto-Enhancement モードが適用されます。

## 概要
`CheckEpisodeQualityUseCase`は、Smart Auto-Enhancement システムと統合され、エピソードのテキストに対して統合的な品質チェックを実行するユースケースです。基本チェック→A31評価→Claude分析の全段階を自動実行し、統合された品質レポートを提供します。

**新機能:**
- **デフォルト動作**: `novel check 4` で Smart Auto-Enhancement が自動実行
- **統合表示**: 分離されていた品質情報を統合表示
- **改善された基本評価**: 平均値文字数チェック廃止、構造的品質重視

## クラス設計

### CheckEpisodeQualityUseCase

**責務**
- エピソードテキストの品質検証
- 複数の品質チェッカーの統合
- 品質レポートの生成・保存
- 自動修正機能の提供

## データ構造

### CheckEpisodeQualityCommand (DataClass)
```python
@dataclass(frozen=True)
class CheckEpisodeQualityCommand:
    project_id: str              # プロジェクトID
    episode_id: str              # エピソードID
    content: str                 # チェック対象のコンテンツ
    auto_fix: bool = False       # 自動修正フラグ
```

### CheckEpisodeQualityResult (DataClass)
```python
@dataclass(frozen=True)
class CheckEpisodeQualityResult:
    success: bool                        # 処理成功フラグ
    report: QualityReport | None = None  # 品質レポート
    fixed_content: str | None = None     # 修正後コンテンツ
    error_message: str | None = None     # エラーメッセージ
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, command: CheckEpisodeQualityCommand) -> CheckEpisodeQualityResult:
```

**目的**
指定されたエピソードに対して包括的な品質チェックを実行し、結果をレポートとして返す。

**引数**
- `command`: 品質チェックコマンド

**戻り値**
- `CheckEpisodeQualityResult`: 品質チェック結果

**処理フロー**
1. **基本文体チェック**: `TextQualityChecker.check_basic_style()`を使用
2. **構成チェック**: `TextQualityChecker.check_composition()`を使用
3. **違反統合**: 全ての品質違反をマージ
4. **レポート生成**: `QualityReportGenerator.generate_report()`でレポート作成
5. **自動修正**: オプション指定時の自動修正適用
6. **レポート保存**: リポジトリが設定されている場合の永続化
7. **結果返却**: 統合結果の構築

**成功パターン**
- 品質チェック完了（違反なし）
- 品質チェック完了（違反あり、レポート生成）
- 自動修正適用後の結果提供

**エラーパターン**
- テキスト解析エラー
- レポート生成エラー
- ファイルアクセスエラー

## プライベートメソッド

### _apply_auto_fixes()

**シグネチャ**
```python
def _apply_auto_fixes(self, content: str, violations: list[QualityViolation]) -> str:
```

**目的**
検出された品質違反に対して自動修正を適用する。

**引数**
- `content`: 元のコンテンツ
- `violations`: 自動修正可能な違反一覧

**戻り値**
- `str`: 修正後のコンテンツ

**修正処理**
1. **行単位修正**: `line_number`が指定された違反の処理
   - インデント修正（`missing_indentation`）
   - 行レベルの置換・修正
2. **全体修正**: 行番号がない場合の全体置換
3. **段階的適用**: 複数の違反を順次適用

**修正例**
- **インデント修正**: 不適切なインデントの修正
- **文字置換**: 全角・半角の統一
- **句読点修正**: 句読点の適切な配置
- **記号修正**: 三点リーダーや感嘆符の修正

## 品質チェック項目

### 基本文体チェック
- **句読点**: 適切な句読点の使用
- **記号使用**: 三点リーダー、感嘆符等の正しい使用
- **文字統一**: 全角・半角の一貫性
- **敬語レベル**: 敬語の一貫性
- **語尾統一**: 「だ・である調」「です・ます調」の統一

### 構成チェック
- **段落構成**: 適切な段落分け
- **文章長**: 一文の長さの適切性
- **読みやすさ**: 文章の流れとリズム
- **論理構造**: 内容の論理的な構成

## 依存関係

### ドメイン層
- `QualityReport`: 品質レポートエンティティ
- `QualityViolation`: 品質違反値オブジェクト
- `TextQualityChecker`: テキスト品質チェッカーサービス
- `QualityReportGenerator`: 品質レポート生成サービス

### リポジトリ
- `QualityReportRepository`: 品質レポートリポジトリ

## 設計原則遵守

### DDD準拠
- ✅ ドメインサービス（`TextQualityChecker`, `QualityReportGenerator`）の活用
- ✅ エンティティ（`QualityReport`）の適切な使用
- ✅ 値オブジェクト（`QualityViolation`）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な例外処理
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# 依存関係の準備
quality_checker = TextQualityChecker()
report_generator = QualityReportGenerator()
report_repository = YamlQualityReportRepository()

# ユースケース作成
use_case = CheckEpisodeQualityUseCase(
    quality_checker=quality_checker,
    report_generator=report_generator,
    report_repository=report_repository
)

# 基本的な品質チェック
command = CheckEpisodeQualityCommand(
    project_id="sample_novel",
    episode_id="episode_001",
    content="チェック対象のエピソード本文...",
    auto_fix=False
)

result = use_case.execute(command)

if result.success and result.report:
    print(f"総合スコア: {result.report.total_score}")
    print(f"違反数: {len(result.report.violations)}")

    # 重要な違反のみ表示
    for violation in result.report.violations:
        if violation.severity.value == "error":
            print(f"エラー: {violation.rule_name} - {violation.message}")
        elif violation.severity.value == "warning":
            print(f"警告: {violation.rule_name} - {violation.message}")
else:
    print(f"品質チェック失敗: {result.error_message}")

# 自動修正付き品質チェック
auto_fix_command = CheckEpisodeQualityCommand(
    project_id="sample_novel",
    episode_id="episode_001",
    content="修正対象のエピソード本文...",
    auto_fix=True
)

auto_fix_result = use_case.execute(auto_fix_command)

if auto_fix_result.success:
    if auto_fix_result.fixed_content:
        print("自動修正が適用されました")
        print(f"修正前違反数: {len(auto_fix_result.report.violations)}")
        print(f"自動修正数: {auto_fix_result.report.auto_fixed_count}")
        # 修正後のコンテンツを保存
        with open("fixed_episode.md", "w", encoding="utf-8") as f:
            f.write(auto_fix_result.fixed_content)

    # 残存する違反を確認
    remaining_violations = [
        v for v in auto_fix_result.report.violations
        if not v.auto_fixable
    ]
    if remaining_violations:
        print(f"手動修正が必要な違反: {len(remaining_violations)}件")
```

## 品質レポート活用

### レポート内容
```python
quality_report = QualityReport(
    episode_id=str,                     # エピソードID
    total_score=float,                  # 総合品質スコア
    violations=list[QualityViolation],  # 違反一覧
    auto_fixed_count=int,               # 自動修正数
    checked_at=datetime,                # チェック実行時刻
)
```

### 違反情報
```python
quality_violation = QualityViolation(
    rule_name=str,                      # ルール名
    message=str,                        # 違反メッセージ
    severity=Severity,                  # 重要度（error/warning/info）
    line_number=LineNumber,             # 行番号
    suggestion=str,                     # 修正提案
    auto_fixable=bool,                  # 自動修正可能フラグ
)
```

## エラーハンドリング

### チェック実行エラー
- テキスト解析の失敗
- 不正な文字エンコーディング
- メモリ不足（大容量テキスト）

### レポート生成エラー
- レポート生成サービスの失敗
- 違反データの不整合

### 自動修正エラー
- 修正適用時の例外
- ファイル保存の失敗

## テスト観点

### 単体テスト
- 正常な品質チェックフロー
- 各種品質違反の検出
- 自動修正機能の動作
- エラー条件での動作
- レポート生成の正確性

### 統合テスト
- 実際のエピソードファイルでの品質チェック
- ドメインサービスとの協調動作
- リポジトリとの連携

## 品質基準

- **検出精度**: 品質問題の正確な特定
- **修正安全性**: 自動修正による文意の保持
- **性能**: 大容量テキストでの効率的な処理
- **拡張性**: 新しい品質ルールへの対応
- **ユーザビリティ**: 分かりやすい違反メッセージと修正提案
