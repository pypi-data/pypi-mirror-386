# SPEC-{CATEGORY}-{NUMBER}: {機能名}

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-{CATEGORY}-{NUMBER} |
| E2EテストID | E2E-{CATEGORY}-{NUMBER} |
| test_type | e2e / integration / unit |
| バージョン | v1.0.0 |
| 作成日 | YYYY-MM-DD |
| 最終更新 | YYYY-MM-DD |
| ステータス | draft / approved / deprecated |
| 関連仕様 | SPEC-XXX-NNN（存在する場合） |

## 1. 概要

この機能/コンポーネントが解決する問題と提供する価値を簡潔に記述。

## 2. ビジネス要件

### 2.1 目的
- ビジネス上の目的
- ユーザーにとっての価値

### 2.2 成功基準
- 測定可能な成功指標
- KPI/メトリクス

## 3. 機能仕様

### 3.1 スコープ
- **含まれるもの**: この仕様に含まれる機能
- **含まれないもの**: 明確に除外される機能

### 3.2 ユースケース

#### UC-001: {ユースケース名}
```yaml
前提条件: システムの初期状態
アクター: ユーザーまたはシステム
入力: 具体的な入力データ例
処理手順:
  1. ステップ1の説明
  2. ステップ2の説明
  3. ...
期待出力: 期待される結果
事後条件: 処理後のシステム状態
```

## 4. 技術仕様

### 4.0 既存実装調査（必須）

**⚠️ 新機能実装前の必須確認事項**

1. **CODEMAP.yaml確認**
   ```bash
   # 関連機能の既存実装を確認
   grep -i "{機能名}" CODEMAP.yaml
   ```

2. **共有コンポーネント確認**
   ```yaml
   共有コンポーネントチェックリスト:
     - CommonPathService: パス関連処理
     - shared_utilities: Console, Logger, ErrorHandler
     - 既存Repository ABC: データアクセス層
     - 既存UseCase ABC: アプリケーション層
   ```

3. **類似機能検索**
   ```bash
   # 類似する既存実装の検索
   find src/ -name "*.py" -exec grep -l "{関連キーワード}" {} \;
   ```

4. **再利用可否判定**
   - ✅ 既存実装を拡張可能
   - ✅ 既存抽象クラスを継承可能
   - ❌ 新規実装が必要（理由を記載）

### 4.1 インターフェース定義

```python
# Python例
class SampleEntity:
    def sample_method(self, param1: str, param2: int) -> Result:
        """
        メソッドの説明

        Args:
            param1: パラメータ1の説明
            param2: パラメータ2の説明

        Returns:
            Result: 戻り値の説明

        Raises:
            ValueError: エラー条件
        """
        pass
```

### 4.2 データモデル

```yaml
EntityName:
  properties:
    id: string (required)
    name: string (max: 100)
    status: enum [active, inactive]
  constraints:
    - nameは一意である
```

## 5. 検証仕様

### 5.1 E2Eテストシナリオ (test_type: e2e)

```gherkin
Feature: {機能名}

  Scenario: 正常系シナリオ
    Given 初期条件
    When アクション実行
    Then 期待結果の検証
```

### 5.2 統合テスト項目 (test_type: integration)

| テストID | テスト内容 | 期待結果 |
|----------|----------|----------|
| INT-001 | 外部システム連携テスト | 正常にデータ交換できる |
| INT-002 | DB永続化テスト | データが正しく保存される |

### 5.3 単体テスト項目 (test_type: unit)

| テストID | テスト対象 | テスト内容 | 期待結果 |
|----------|------------|----------|----------|
| UNIT-001 | validate_input() | 正常値の検証 | True返却 |
| UNIT-002 | validate_input() | 異常値の検証 | ValueError発生 |

## 6. 非機能要件

### 6.1 パフォーマンス
- レスポンスタイム: < 200ms
- 同時実行数: 最大100

### 6.2 セキュリティ
- 認証: 必須/不要
- 認可: ロールベース/なし
- データ暗号化: 必要な場合

### 6.3 可用性
- SLA: 99.9%
- エラーリカバリ: 自動/手動

## 7. エラーハンドリング

| エラーコード | エラー内容 | 対処方法 |
|-------------|----------|---------|
| ERR-001 | 入力値不正 | バリデーションメッセージ表示 |
| ERR-002 | リソース不足 | リトライ後、管理者通知 |

## 8. 実装参照

### 8.1 実装ファイル
```yaml
production_code:
  - src/noveler/domain/entities/{entity_name}.py
  - src/noveler/application/use_cases/{use_case_name}.py

test_code:
  e2e:
    - tests/e2e/test_{category}_{feature}.py
  integration:
    - tests/integration/test_{category}_{feature}.py
  unit:
    - tests/unit/domain/entities/test_{entity_name}.py
```

### 8.2 関連ドキュメント
- 設計書: `docs/design/{feature}_design.md`
- API仕様: `docs/api/{feature}_api.md`

## 9. 移行計画

既存システムからの移行が必要な場合：

1. **Phase 1**: データ移行準備
2. **Phase 2**: 並行稼働
3. **Phase 3**: 切り替え

## 10. 補助仕様

E2Eテストで表現しにくい細部仕様がある場合：

### SUB-SPEC-001: {詳細機能名}
```yaml
test_type: unit
関連テスト: tests/unit/specific_test.py
内容: E2Eでカバーしにくい境界値テストなど
```

## 11. 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|----------|--------|
| v1.0.0 | YYYY-MM-DD | 初版作成 | - |

## 12. 承認

| 役割 | 氏名 | 承認日 |
|------|------|--------|
| プロダクトオーナー | - | - |
| テックリード | - | - |
| QAリード | - | - |

---

## 使用上の注意

1. **仕様IDの命名規則**
   - CATEGORY: EPISODE, QUALITY, PLOT, CLAUDE, CONFIG等
   - NUMBER: 001から連番（3桁）

2. **test_typeの選択基準**
   - **e2e**: ユーザー視点の機能全体をテスト
   - **integration**: 複数コンポーネント間の連携テスト
   - **unit**: 個別クラス/メソッドの詳細テスト

3. **E2Eテストとの紐付け**
   - 基本は仕様ID = E2EテストID（1対1）
   - E2Eで表現困難な場合のみ補助仕様IDを作成

4. **更新ルール**
   - 仕様変更時は必ずバージョンアップ
   - 破壊的変更はメジャーバージョンアップ
   - テストも同時に更新必須
