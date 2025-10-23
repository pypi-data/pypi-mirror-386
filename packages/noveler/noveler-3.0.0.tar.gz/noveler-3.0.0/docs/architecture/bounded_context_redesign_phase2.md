# 境界コンテキスト再編設計 - Phase 2

## 実施概要
段階的改善ロードマップ Phase 2 Week 5-8: 境界コンテキスト再編設計を実行

## 現状分析

### 問題点
1. **過度な細分化**: 119個のサブディレクトリによる複雑性
2. **責務境界の曖昧性**: domain内に複数の専門領域が混在
3. **認知負荷の増大**: 開発者が全体構造を把握困難

### 黄金サンプル原則
- **単純性**: 境界コンテキストは最小限に抑制
- **凝集性**: 関連する機能は同一コンテキスト内
- **疎結合**: コンテキスト間の依存性最小化

## 新境界コンテキスト設計

### コンテキスト1: Writing Context（執筆コンテキスト）
**責務**: 小説執筆の核心業務
```
scripts/contexts/writing/
├── domain/
│   ├── entities/
│   │   ├── episode.py                    # ✅ 既存維持
│   │   ├── episode_publisher.py          # ✅ 既存維持
│   │   ├── episode_quality.py            # ✅ 既存維持
│   │   ├── episode_metadata.py           # ✅ 既存維持
│   │   └── chapter_plot.py
│   ├── value_objects/
│   │   ├── episode_number.py
│   │   ├── episode_title.py
│   │   ├── word_count.py
│   │   └── quality_score.py
│   └── services/
│       ├── episode_management_service.py
│       └── quality_evaluation_service.py
├── application/
│   └── use_cases/
│       ├── create_episode_use_case.py
│       ├── complete_episode_use_case.py
│       └── quality_check_use_case.py
└── infrastructure/
    ├── repositories/
    │   └── yaml_episode_repository.py
    └── adapters/
        └── claude_writing_adapter.py
```

### コンテキスト2: Planning Context（企画コンテキスト）
**責務**: プロット・世界観設定
```
scripts/contexts/planning/
├── domain/
│   ├── entities/
│   │   ├── plot_version.py
│   │   ├── character_profile.py
│   │   └── world_setting.py
│   ├── value_objects/
│   │   ├── plot_schema.py
│   │   └── character_consistency.py
│   └── services/
│       └── plot_generation_service.py
├── application/
│   └── use_cases/
│       ├── generate_plot_use_case.py
│       └── character_consistency_use_case.py
└── infrastructure/
    └── repositories/
        └── yaml_plot_repository.py
```

### コンテキスト3: Quality Context（品質管理コンテキスト）
**責務**: 品質チェック・分析
```
scripts/contexts/quality/
├── domain/
│   ├── entities/
│   │   ├── quality_check_session.py
│   │   └── quality_record.py
│   ├── value_objects/
│   │   ├── quality_threshold.py
│   │   └── quality_report.py
│   └── services/
│       └── adaptive_quality_service.py
├── application/
│   └── use_cases/
│       └── integrated_quality_check_use_case.py
└── infrastructure/
    └── repositories/
        └── yaml_quality_repository.py
```

### コンテキスト4: System Context（システム管理コンテキスト）
**責務**: インフラ・設定管理
```
scripts/contexts/system/
├── domain/
│   ├── entities/
│   │   ├── project.py
│   │   └── configuration.py
│   └── value_objects/
│       └── project_info.py
├── application/
│   └── use_cases/
│       └── system_diagnosis_use_case.py
└── infrastructure/
    ├── config/
    ├── logging/
    └── di/
```

## 移行計画

### Week 5-6: 構造準備
1. 新ディレクトリ構造作成
2. コンテキスト間インターフェース定義
3. 移行対象ファイル特定

### Week 7-8: 段階的移行
1. Writing Context移行（最重要）
2. Planning Context移行
3. Quality Context移行
4. System Context統合

## 期待効果

### 認知負荷軽減
- サブディレクトリ数: 119 → 16（86%削減）
- コンテキスト数: 4個（理解容易）

### 開発効率向上
- 関連機能の局所化
- 依存関係の単純化
- テスト範囲の明確化

### 保守性向上
- 責務境界の明確化
- 変更影響の局所化
- 新機能追加の容易化

## 実装状況

### Phase 1完了項目
- ✅ Domain純粋性回復（Infrastructure依存除去）
- ✅ Episode.py肥大化解決（4クラス分割）
- ✅ DI設定完了（simple_di_container.py設定済み）

### Phase 2開始
- 🔄 境界コンテキスト再編設計（このドキュメント）
- ⏳ アーキテクチャテスト強化実装
