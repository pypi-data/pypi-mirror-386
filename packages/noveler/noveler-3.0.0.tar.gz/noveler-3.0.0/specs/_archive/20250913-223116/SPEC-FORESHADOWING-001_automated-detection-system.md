# SPEC-FORESHADOWING-001: 伏線自動検知システム

## 仕様概要

### 仕様ID
SPEC-FORESHADOWING-001

### 仕様名
伏線自動検知システム（Automated Foreshadowing Detection System）

### 作成日
2025-01-28

### バージョン
1.0

## ビジネス要件

### 目的
- 伏線の仕込み忘れを95%削減
- 伏線の回収忘れを100%防止
- 執筆時の手動チェック時間を80%短縮
- 品質チェック機能との統合による一元管理

### ステークホルダー
- **小説執筆者**: 伏線管理の自動化による執筆効率向上
- **システム利用者**: novel checkコマンドで伏線チェック実行
- **品質管理システム**: 統合品質チェックの一部として機能

## 機能要件

### FR-001: 伏線仕込み漏れ検知
**説明**: 指定エピソードで仕込み予定の伏線が実装されていない場合に警告

**入力**:
- エピソード番号
- 原稿内容
- 伏線管理.yaml

**処理**:
1. 該当エピソードで仕込み予定の伏線を抽出
2. 伏線のステータスが"planned"の場合に仕込み漏れとして検出
3. 重要度に応じて警告レベルを設定（重要度4-5: HIGH, 1-3: MEDIUM）

**出力**:
- 仕込み漏れ警告リスト
- 各伏線の詳細情報（タイトル、予定内容、重要度）

### FR-002: 伏線回収漏れ検知
**説明**: 指定エピソードで回収予定の伏線が実装されていない場合に警告

**入力**:
- エピソード番号
- 原稿内容
- 伏線管理.yaml

**処理**:
1. 該当エピソードで回収予定の伏線を抽出
2. 伏線のステータスが"planted"または"ready_to_resolve"の場合に回収漏れとして検出
3. 回収漏れは常にCRITICALレベルで警告

**出力**:
- 回収漏れ警告リスト
- 各伏線の回収方法提案

### FR-003: インタラクティブ確認機能
**説明**: 検知結果を作家が確認し、実装状況を更新する機能

**入力**:
- 検知結果
- 作家の確認回答

**処理**:
1. 検知された伏線について作家に確認を求める
2. 実装済み確認時に伏線管理.yamlのステータスを更新
3. 更新履歴をログに記録

**出力**:
- 更新された伏線管理.yaml
- 確認ログ

### FR-004: 品質チェック統合
**説明**: 既存の品質チェック機能に伏線検知を統合

**入力**:
- novel check コマンドの--include-foreshadowingオプション

**処理**:
1. 通常の品質チェックを実行
2. 伏線検知を追加実行
3. 結果をマージして統合レポートを生成

**出力**:
- 統合品質チェックレポート
- 伏線関連の改善提案

## 非機能要件

### NFR-001: パフォーマンス
- 10,000文字の原稿に対して5秒以内で検知完了
- メモリ使用量は100MB以下

### NFR-002: 拡張性
- 新しい検知ロジックを容易に追加可能
- 伏線管理ファイルの構造変更に対応可能

### NFR-003: 保守性
- DDDアーキテクチャに準拠した明確なレイヤー分離
- 100%のテストカバレッジ

## 制約事項

### 技術制約
- Python 3.11以上で動作
- 既存のDDDアーキテクチャを踏襲
- YAML形式の伏線管理ファイルを使用

### ビジネス制約
- 100%の自動判定は困難（人間の確認が必要）
- 文学的表現の解釈は人間判断に依存

## 受け入れ基準

### AC-001: 基本検知機能
- [x] 仕込み予定伏線の未実装を検知できる
- [x] 回収予定伏線の未実装を検知できる
- [x] 重要度に応じた警告レベル設定

### AC-002: インタラクティブ機能
- [x] 作家による実装確認が可能
- [x] 確認結果による伏線管理.yaml自動更新
- [x] 確認履歴の記録

### AC-003: 品質チェック統合
- [x] novel checkコマンドからの実行
- [x] 既存品質チェックとの結果統合
- [x] 統一された出力形式

## テストケース

### TC-001: 仕込み漏れ検知
```
Given: エピソード5で伏線F001の仕込み予定
And: 伏線F001のステータスが"planned"
When: エピソード5の品質チェックを実行
Then: 仕込み漏れ警告が出力される
```

### TC-002: 回収漏れ検知
```
Given: エピソード30で伏線F001の回収予定
And: 伏線F001のステータスが"planted"
When: エピソード30の品質チェックを実行
Then: 回収漏れ警告が出力される
```

### TC-003: 実装確認更新
```
Given: 仕込み漏れ警告が表示されている
When: 作家が「実装済み」を選択
Then: 伏線管理.yamlのステータスが"planted"に更新される
```

## 実装計画

### Phase 1: ドメインモデル実装
- ForeshadowingValidationService
- ForeshadowingIssue値オブジェクト
- ForeshadowingDetectionResult

### Phase 2: ユースケース実装
- ValidateForeshadowingUseCase
- UpdateForeshadowingStatusUseCase

### Phase 3: インフラ実装
- YamlForeshadowingRepository拡張
- 品質チェック統合

### Phase 4: プレゼンテーション層統合
- QualityCommandHandler拡張
- インタラクティブUI実装

## アーキテクチャ設計

### DDDレイヤー構造
```
📁 Domain Layer:
├── entities/ForeshadowingValidationSession
├── value_objects/ForeshadowingIssue
├── services/ForeshadowingValidationService
└── repositories/ForeshadowingValidationRepository

📁 Application Layer:
├── use_cases/ValidateForeshadowingUseCase
└── use_cases/UpdateForeshadowingStatusUseCase

📁 Infrastructure Layer:
├── repositories/YamlForeshadowingValidationRepository
└── services/InteractiveForeshadowingService

📁 Presentation Layer:
└── cli/ForeshadowingValidationHandler
```

## 関連仕様書
- SPEC-QUALITY-001: A31チェックリスト自動修正システム
- SPEC-WORKFLOW-001: プロジェクト構造検証

## 変更履歴
- 2025-01-28 v1.0: 初版作成
