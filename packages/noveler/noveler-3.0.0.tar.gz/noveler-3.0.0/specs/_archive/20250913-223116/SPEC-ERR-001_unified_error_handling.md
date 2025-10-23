# SPEC-ERR-001: 統一エラーハンドリングシステム

## 概要
B20/B30準拠の統一エラーハンドリングシステムを実装し、システム全体のエラー処理を標準化する。

## 背景と目的
- **現状**: print文やlogger直接呼び出しが混在し、エラー処理が不統一
- **目的**: 一貫したエラーハンドリングとログ記録の実現
- **効果**: 保守性向上、デバッグ効率化、ユーザー体験の一貫性

## 要求仕様

### 機能要件
1. **統一エラー型定義**
   - BaseError: 全エラーの基底クラス
   - DomainError: ドメイン層エラー
   - ApplicationError: アプリケーション層エラー
   - InfrastructureError: インフラ層エラー

2. **エラー処理サービス**
   - ErrorHandlingService: エラー処理の中央管理
   - エラーレベル分類（Critical, Error, Warning, Info）
   - 自動ログ記録とユーザー通知

3. **Functional Core原則**
   - エラー判定ロジックは純粋関数として実装
   - 副作用（ログ出力等）はImperative Shellで処理

### 非機能要件
- **パフォーマンス**: エラー処理オーバーヘッド < 1ms
- **拡張性**: 新規エラータイプの追加が容易
- **テスタビリティ**: 100%単体テストカバレッジ

## 設計

### クラス構造
```python
# Domain層（Functional Core）
class ErrorClassifier:
    """エラー分類純粋関数"""
    @staticmethod
    def classify(error: Exception) -> ErrorLevel:
        # 副作用なしの分類ロジック
        pass

# Application層
class ErrorHandlingService:
    """エラー処理サービス"""
    def handle_error(self, error: Exception) -> ErrorResult:
        level = ErrorClassifier.classify(error)
        # ログ記録とユーザー通知の調整
        pass

# Infrastructure層（Imperative Shell）
class ErrorLogger:
    """エラーログ出力実装"""
    def log(self, error: Exception, level: ErrorLevel) -> None:
        # 実際のログ出力（副作用）
        pass
```

## 受け入れ基準
1. 全層でエラーハンドリングが統一される
2. print文によるエラー出力が0件になる
3. エラー処理の単体テストが100%カバレッジ
4. B20/B30品質基準を満たす

## 実装優先度
- Priority: High
- 推定工数: 4時間
- 影響範囲: システム全体

## 参照
- B20_Claude_Code開発作業指示書.md
- B30_Claude_Code品質作業指示書.md
- Functional Core/Imperative Shell パターン
