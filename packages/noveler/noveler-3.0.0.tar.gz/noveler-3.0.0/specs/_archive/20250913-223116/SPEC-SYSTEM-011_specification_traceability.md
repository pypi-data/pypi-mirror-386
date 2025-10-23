# 仕様書トレーサビリティシステム

## SPEC-TEST-001: 仕様書とテストの紐付けシステム

### 概要
テストコードと仕様書を双方向に紐付け、トレーサビリティを確保するシステム。

### 要件
#### 主要要件（要件定義書準拠）
- **REQ-PLOT-001〜008**: プロット管理機能の仕様トレーサビリティ
- **REQ-WRITE-001〜052**: AI協創執筆機能の仕様トレーサビリティ
- **REQ-QUALITY-001〜008**: 品質管理機能の仕様トレーサビリティ

#### 詳細要件
- REQ-3.1.1: すべての仕様書に対してテストが存在することを保証
- REQ-3.1.2: テストから仕様書を参照可能にする
- REQ-3.1.3: 仕様変更時の影響範囲を特定可能にする

### 機能仕様

#### 1. pytestカスタムマーカー
```python
@pytest.mark.spec("SPEC-XXX-001")
@pytest.mark.requirement("REQ-X.X.X")
def test_機能名():
    """
    仕様書: docs/specs/xxx.md#SPEC-XXX-001
    要件: 要件の説明
    """
    pass
```

#### 2. 仕様書ID命名規則
- フォーマット: `SPEC-[ドメイン]-[連番]`
- オプション: `SPEC-[ドメイン]-[サブドメイン]-[連番]`
- 連番は3桁のゼロパディング（001, 002, ...）

#### 3. トレーサビリティレポート
- 仕様カバレッジ率の算出
- 未実装仕様の検出
- 孤立したテストの検出
- 影響分析レポート

### テストケース
- `tests/unit/domain/specification/test_entities.py`
- `tests/integration/test_specification_traceability.py`
- `tests/unit/test_marker_demo.py`

### 実装
- `src/noveler/domain/specification/` - ドメイン層
- `src/noveler/application/use_cases/generate_traceability_report_use_case.py`
- `src/noveler/infrastructure/repositories/yaml_specification_repository.py`
- （参考）旧ツール: `scripts/tools/generate_traceability.py`（現行はユースケース経由で実行）

### 使用例
```bash
# トレーサビリティレポート生成（ユースケース経由の例）
python -c "from noveler.application.use_cases.generate_traceability_report_use_case import main; main()" \
  --spec-dir specs \
  --test-dirs tests \
  --output docs/traceability_report.md

# 仕様書ID生成
python src/noveler/tools/spec_id_generator.py generate EPISODE
```

---

## SPEC-TEST-002: 仕様書ID管理システム

### 概要
仕様書IDの一意性を保証し、体系的に管理するシステム。

### 要件
- REQ-3.2.1: IDの重複を防止する
- REQ-3.2.2: ドメインごとに連番を管理する
- REQ-3.2.3: 予約機能により将来使用するIDを確保できる

### 機能仕様

#### 1. ID生成機能
- ドメインコードの検証
- 自動連番割り当て
- 予約済みIDのスキップ

#### 2. ドメイン管理
標準ドメイン:
- `EPISODE`: エピソード管理
- `QUALITY`: 品質チェック
- `PLOT`: プロット管理
- `CHAR`: キャラクター
- `WORLD`: 世界観設定
- `PUBLISH`: 公開・投稿
- その他（ツール内で定義）

#### 3. 設定ファイル
`.spec_id_config.yaml`に以下を保存:
- ドメイン定義
- 次の連番
- 予約済みID

### テストケース
- 手動テスト実施済み（CLIツールのため）

### 実装
- `scripts/tools/spec_id_generator.py`

### コマンド仕様
```bash
# ID生成
spec_id_generator.py generate <domain> [--subdomain <name>] [--count <n>]

# ID予約
spec_id_generator.py reserve <spec_id>

# 一覧表示
spec_id_generator.py list domains|reserved|next [--domain <domain>]

# ドメイン追加
spec_id_generator.py add-domain <code> <description>
```

---

## SPEC-TEST-003: トレーサビリティレポート生成

### 概要
プロジェクト全体の仕様書とテストの紐付け状況をレポート化する機能。

### 要件
- REQ-3.3.1: Markdown形式でレポートを出力
- REQ-3.3.2: カバレッジ率を算出し、閾値判定を行う
- REQ-3.3.3: AST解析によりテストコードから自動的に仕様IDを抽出

### 機能仕様

#### 1. レポート内容
- カバレッジサマリー（総数、カバー率）
- カバー済み仕様一覧（テスト参照付き）
- 未カバー仕様一覧
- 孤立テスト一覧

#### 2. カバレッジ判定
- 完全実装: 2つ以上のテスト
- 部分実装: 1つのテスト
- 未実装: テストなし

#### 3. 影響分析
特定の仕様に対して:
- 影響を受けるテスト
- 影響を受ける実装
- 関連する他の仕様

### テストケース
- `tests/integration/test_specification_traceability.py::test_トレーサビリティレポート生成`
- `tests/integration/test_specification_traceability.py::test_カバレッジ閾値チェック`

### 実装
- `scripts/application/use_cases/generate_traceability_report_use_case.py`
- `scripts/domain/specification/value_objects.py::TraceabilityReport`

### 出力例
```markdown
# 仕様カバレッジレポート

生成日時: 2025-01-24 12:00:00

## カバレッジサマリー
- 総仕様数: 10
- カバー済み: 8 (80.0%)
- 未カバー: 2
- 部分カバー: 1

## カバー済み仕様

### SPEC-EPISODE-001
#### テスト
- ✅ tests/test_episode.py::test_エピソード作成
- ✅ tests/test_episode.py::test_エピソード検証

## 未カバー仕様
- ❌ SPEC-WORLD-003
```
