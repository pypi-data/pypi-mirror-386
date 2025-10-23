# 品質チェックサービス統合計画

## 現状の課題
- 19個の品質関連サービスが散在
- 責任範囲の重複と不明確な境界
- メンテナンス性の低下
- 依存関係の複雑化

## 統合方針

### 1. コアサービスへの集約（3つの主要サービス）

#### 1.1 QualityCheckCore
**責任**: 品質チェックの実行と結果管理
```python
class QualityCheckCore:
    """品質チェックのコア機能を提供"""
    - analyze_quality()  # 統合的な品質分析
    - check_rhythm()     # リズム分析
    - check_readability() # 読みやすさ分析
    - check_grammar()    # 文法チェック
    - check_style()      # スタイルチェック
```

統合対象:
- quality_analysis_service.py
- quality_evaluation_service.py
- bulk_quality_check_service.py
- content_quality_service.py
- manual_analysis_quality_validator.py

#### 1.2 QualityConfigurationManager
**責任**: 品質設定の管理と標準の提供
```python
class QualityConfigurationManager:
    """品質設定と標準の管理"""
    - get_quality_standards()
    - update_configuration()
    - auto_update_config()
    - get_requirements()
```

統合対象:
- quality_configuration_service.py
- quality_config_auto_update_service.py
- quality_standard_factory.py
- quality_requirements_checker.py
- quality_requirements_auto_fixer.py

#### 1.3 QualityReportingService
**責任**: レポート生成と履歴管理
```python
class QualityReportingService:
    """品質レポートと履歴管理"""
    - generate_report()
    - analyze_trends()
    - get_history()
    - export_results()
```

統合対象:
- quality_reporting_service.py
- quality_history_service.py
- quality_trend_analysis_service.py
- quality_trend_analyzer.py
- quality_history_value_objects.py → value_objects/quality_value_objects.pyに統合

**依存方向の原則**:
- Value Objects → なし（純粋なデータ構造）
- Reporting Service → Value Objects（単方向依存）
- Core Service → Value Objects（単方向依存）
- 循環依存を防ぐため、Value ObjectsからServiceへの参照は禁止

### 2. 特殊化されたサービスの維持

以下は独立性が高いため、そのまま維持:
- claude_quality_analyzer.py (Claude統合固有)
- plot_quality_service.py (プロット固有)
- content_quality_enhancer.py (コンテンツ改善固有)
- enhanced_quality_evaluation_engine.py (高度な評価エンジン)

### 3. 実装ステップ

#### Phase 1: 基盤整備（Week 1）
1. 新しいディレクトリ構造の作成
   ```
   src/noveler/domain/services/quality/
   ├── core/
   │   ├── __init__.py
   │   ├── quality_check_core.py
   │   └── analyzers/
   │       ├── __init__.py
   │       ├── rhythm_analyzer.py
   │       ├── readability_analyzer.py
   │       ├── grammar_analyzer.py
   │       └── style_analyzer.py
   ├── configuration/
   │   ├── __init__.py
   │   └── quality_configuration_manager.py
   ├── reporting/
   │   ├── __init__.py
   │   └── quality_reporting_service.py
   ├── specialized/
   │   ├── __init__.py
   │   ├── claude_quality_analyzer.py
   │   ├── plot_quality_service.py
   │   ├── content_quality_enhancer.py
   │   └── enhanced_quality_evaluation_engine.py
   └── value_objects/
       ├── __init__.py
       └── quality_value_objects.py  # 統合されたValue Object
   ```

2. インターフェースの定義
   ```python
   # src/noveler/domain/interfaces/quality_service_protocol.py
   class IQualityCheckService(Protocol):
       def analyze_quality(...) -> QualityCheckResult: ...

   class IQualityConfiguration(Protocol):
       def get_standards(...) -> QualityStandards: ...

   class IQualityReporting(Protocol):
       def generate_report(...) -> QualityReport: ...
   ```

#### Phase 2: 段階的移行（Week 2-3）
1. 新サービスの実装（既存コードを活用）
2. アダプターパターンで既存APIを維持
3. テストの追加

**移行順序**（リスクを最小化）:
1. Week 2前半: `quality_analysis_service.py`を最初にアダプタ経由で移行
   - 最も多く依存されているサービスのため、アダプタで安全に移行
   - 既存の呼び出し箇所への影響を最小限に
2. Week 2後半: 設定系サービスの統合
   - `quality_configuration_service.py`
   - `quality_standard_factory.py`
   - 設定の一元管理により、以降の移行が容易に
3. Week 3前半: レポート系サービスの統合
   - `quality_reporting_service.py`
   - `quality_history_service.py`
   - データモデルの統一
4. Week 3後半: 補助的なサービスの統合
   - `bulk_quality_check_service.py`
   - その他の特殊サービス

#### Phase 3: 切り替えと検証（Week 4）
1. 既存サービスから新サービスへの切り替え
2. 統合テストの実行
3. パフォーマンステスト
4. **データ移行と互換性確保**
   - 既存品質レポートの移行
     ```python
     # 移行スクリプト例
     class QualityDataMigrator:
         def migrate_reports(self, old_format, new_format):
             """既存レポートを新フォーマットに変換"""
             pass

         def migrate_configurations(self):
             """設定ファイルの移行"""
             pass

         def create_snapshots(self):
             """移行前のスナップショット作成"""
             pass
     ```
   - 設定ファイルの互換性維持
     - 旧設定ファイルの自動検出と変換
     - 設定バージョニング（v1 → v2）
     - フォールバック機能の実装
   - レガシーAPIの維持
     ```python
     # アダプターパターンで既存APIを維持
     class LegacyQualityServiceAdapter:
         """旧APIとの互換性を保証"""
         def __init__(self, new_service: QualityCheckCore):
             self.new_service = new_service

         # 旧メソッドを新サービスにマッピング
         def analyze_quality_old_style(self, *args, **kwargs):
             return self.new_service.analyze_quality(*args, **kwargs)
     ```

#### Phase 4: クリーンアップ（Week 5）
1. 旧サービスファイルの削除
2. import文の更新
3. ドキュメントの更新

#### Phase 5: 安定化と最適化（Week 6-8）
1. パフォーマンスチューニング
2. メモリ使用量の最適化
3. エラーハンドリングの改善
4. 互換性レイヤーの段階的廃止準備

**統合成功基準**:
- 単体テストカバレッジ: 90%以上
- 統合テスト: 全ケース合格
- パフォーマンス: 旧実装比で同等以上
- メモリ使用量: 旧実装比で20%以上削減
- 既存APIの互換性: 100%維持
- エラーレート: 本番環境で0.1%未満

## 期待される効果

### 定量的効果
- ファイル数: 19 → 12 (37%削減)
  - core/配下: 5ファイル（quality_check_core.py + 4アナライザー）
  - configuration/配下: 1ファイル（quality_configuration_manager.py）
  - reporting/配下: 1ファイル（quality_reporting_service.py）
  - specialized/配下: 4ファイル（Claude、プロット、コンテンツ強化、評価エンジン）
  - value_objects/配下: 1ファイル（quality_value_objects.py）
  - 合計: 5 + 1 + 1 + 4 + 1 = 12ファイル（__init__.pyはカウント外）
- コード行数: 約35%削減（重複排除による）
- テスト実行時間: 約30%短縮

### 定性的効果
- 責任の明確化
- メンテナンス性の向上
- 新機能追加の容易化
- チーム開発の効率化

## リスクと対策

### リスク
1. 既存機能の破壊
2. パフォーマンスの低下
3. 移行期間中の混乱

### 対策
1. 包括的なテストスイートの作成
2. パフォーマンスベンチマークの実施
3. 段階的移行とフィーチャーフラグの使用

## データ移行詳細仕様

### 移行対象データ
1. **品質レポート履歴**
   - ファイル位置: `reports/quality/*.json`
   - フォーマット変換: JSON v1 → JSON v2
   - 保持期間: 過去6ヶ月分

2. **設定ファイル**
   - `.novelerrc.yaml`の品質設定セクション
   - プロジェクト固有の品質閾値
   - カスタムルール定義

3. **キャッシュデータ**
   - 分析結果キャッシュ
   - 学習パターンデータ

### 互換性戦略
1. **段階的廃止（Deprecation）**
   - Phase 3: 警告表示開始
   - Phase 4: 代替API誘導
   - Phase 5: 互換性レイヤーの維持（3ヶ月間）
   - Phase 5完了後3ヶ月: 旧API削除

2. **バージョニング**
   ```yaml
   # .novelerrc.yaml
   quality:
     version: 2  # 新バージョン
     migration:
       from_version: 1
       auto_migrate: true
   ```

## チェックリスト

- [ ] 全ステークホルダーへの説明と承認
- [ ] 移行計画のレビュー
- [ ] テスト計画の作成
- [ ] **データ移行計画の作成**
  - [ ] 既存データのバックアップ
  - [ ] 移行スクリプトの作成とテスト
  - [ ] ロールバック手順の文書化
- [ ] **互換性テストの実施**
  - [ ] 既存APIの動作確認
  - [ ] データフォーマット変換の検証
  - [ ] パフォーマンス比較
- [ ] ロールバック計画の準備

## 次のアクション

1. このプランのレビューと承認
2. Phase 1の詳細設計
3. 実装開始

---
作成日: 2025-01-29
作成者: Claude Code