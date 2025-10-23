---
spec_id: SPEC-PLOT-004
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [REQ]
tags: [plot]
---
# SPEC-PLOT-004: プロット圧縮・最適化ユースケース仕様書

## 要件トレーサビリティ

**要件ID**: REQ-PLOT-004 (インタラクティブプロット編集)
**実装状況**: 🔄実装中
**テストカバレッジ**: tests/unit/test_plot_compression.py (予定)
**関連仕様書**: SPEC-PLOT-001_claude-code-integration-plot-generation.md

## 1. 概要

### 1.1 目的
DDD原則に基づき、長大化したプロット情報を圧縮・最適化するビジネスロジックを実装する。重要情報を保持しながら可読性と管理効率を向上させる包括的なプロット圧縮システムを提供。

### 1.2 スコープ
- プロット情報の重要度分析・優先順位付け
- 冗長表現の検出・最適化
- 階層構造の再編成・簡素化
- キーポイント抽出・サマリー生成
- 圧縮前後の比較・検証
- リバーシブル圧縮によるデータ保全

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── PlotCompressionUseCase                      ← Domain Layer
│   ├── PlotCompressionInput                   └── CompressedPlot (Entity)
│   ├── CompressionOptions                     └── PlotAnalyzer (Service)
│   ├── PlotCompressionOutput                  └── CompressionLevel (Enum)
│   └── execute(), preview_compression()       └── PlotElement (Value Object)
└── Analysis Functions                          └── PlotRepository (Interface)
    ├── analyze_plot_density()
    ├── detect_redundancies()
    └── optimize_structure()
```

### 1.4 ビジネス価値
- **管理効率の向上**: 肥大化したプロットの整理・簡素化
- **可読性の改善**: 重要情報への迅速なアクセス
- **一貫性の維持**: 構造化された情報管理
- **作業効率の向上**: 執筆時の参照効率化

## 2. 機能仕様

### 2.1 コアユースケース
```python
class PlotCompressionUseCase:
    def __init__(
        self,
        plot_repository: PlotRepository,
        project_repository: ProjectRepository,
        backup_service: BackupService
    ):
        """依存性注入による初期化"""

    def execute(
        self,
        input_data: PlotCompressionInput
    ) -> PlotCompressionOutput:
        """プロット圧縮実行"""

    def preview_compression(
        self,
        input_data: PlotCompressionInput
    ) -> dict[str, Any]:
        """圧縮プレビュー生成"""
```

### 2.2 入力・出力データ
```python
@dataclass
class PlotCompressionInput:
    """プロット圧縮入力"""
    project_name: str
    plot_type: str  # "master", "chapter", "all"
    chapter_number: int | None = None
    compression_level: CompressionLevel = CompressionLevel.STANDARD

@dataclass
class CompressionOptions:
    """圧縮オプション"""
    preserve_dialogue: bool = True
    merge_similar_scenes: bool = True
    extract_key_points: bool = True
    create_summary: bool = True
    backup_original: bool = True

@dataclass
class PlotCompressionOutput:
    """プロット圧縮出力"""
    success: bool
    original_size: int
    compressed_size: int
    compression_ratio: float
    backup_id: str | None
    key_points: list[str]
    summary: str
    message: str = ""
```

### 2.3 分析機能
```python
def analyze_plot_density(
    self,
    plot_content: dict[str, Any]
) -> dict[str, float]:
    """プロット密度分析"""

def detect_redundancies(
    self,
    plot_content: dict[str, Any]
) -> list[dict[str, Any]]:
    """冗長性検出"""

def optimize_structure(
    self,
    plot_content: dict[str, Any],
    options: CompressionOptions
) -> dict[str, Any]:
    """構造最適化"""
```

### 2.4 圧縮管理機能
```python
def create_backup(
    self,
    original_plot: dict[str, Any]
) -> str:
    """圧縮前バックアップ作成"""

def restore_from_backup(
    self,
    backup_id: str
) -> dict[str, Any]:
    """バックアップから復元"""

def generate_diff_report(
    self,
    original: dict[str, Any],
    compressed: dict[str, Any]
) -> str:
    """差分レポート生成"""
```

## 3. 圧縮レベル仕様

### 3.1 軽量圧縮（LIGHT）
```python
軽量圧縮特徴 = {
    "target_reduction": "10-20%",
    "actions": [
        "空白行・重複改行の削除",
        "冗長な接続詞の削減",
        "繰り返し表現の統合"
    ],
    "preserve": ["全ての会話", "全てのシーン", "全ての設定"]
}
```

### 3.2 標準圧縮（STANDARD）
```python
標準圧縮特徴 = {
    "target_reduction": "30-40%",
    "actions": [
        "類似シーンの統合",
        "説明文の要約",
        "サブプロットの整理"
    ],
    "preserve": ["重要会話", "主要シーン", "コア設定"]
}
```

### 3.3 高圧縮（AGGRESSIVE）
```python
高圧縮特徴 = {
    "target_reduction": "50-60%",
    "actions": [
        "シーンの大幅統合",
        "詳細説明の削除",
        "キーポイントのみ抽出"
    ],
    "preserve": ["必須会話", "転換点シーン", "基本設定"]
}
```

## 4. プロット分析仕様

### 4.1 密度分析メトリクス
```python
def analyze_plot_density(self, plot_content: dict[str, Any]) -> dict[str, float]:
    """プロット密度分析ロジック"""
    metrics = {
        "scene_density": len(scenes) / total_words,  # シーン密度
        "dialogue_ratio": dialogue_words / total_words,  # 会話比率
        "description_ratio": description_words / total_words,  # 描写比率
        "action_density": action_count / scene_count,  # アクション密度
        "complexity_score": calculate_complexity()  # 複雑度スコア
    }
    return metrics
```

### 4.2 冗長性パターン
```python
冗長性パターン = {
    "repetitive_phrases": "同一フレーズの繰り返し",
    "similar_scenes": "類似シーンの重複",
    "excessive_description": "過剰な描写",
    "redundant_explanation": "重複する説明",
    "circular_logic": "循環的な論理展開"
}
```

### 4.3 構造最適化ルール
```python
構造最適化ルール = [
    {
        "rule": "連続する移動シーンは統合",
        "condition": "scene.type == 'movement' and next_scene.type == 'movement'",
        "action": "merge_scenes"
    },
    {
        "rule": "10行以上の描写は要約",
        "condition": "description.lines > 10",
        "action": "summarize_description"
    },
    {
        "rule": "3回以上の繰り返しは削減",
        "condition": "phrase.count >= 3",
        "action": "reduce_repetition"
    }
]
```

## 5. データ構造仕様

### 5.1 圧縮入力構造
```python
# マスタープロット圧縮例
master_compression_input = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="master",
    compression_level=CompressionLevel.STANDARD
)

# 章別プロット圧縮例
chapter_compression_input = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="chapter",
    chapter_number=5,
    compression_level=CompressionLevel.LIGHT
)

# 全プロット一括圧縮例
all_compression_input = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="all",
    compression_level=CompressionLevel.AGGRESSIVE
)
```

### 5.2 圧縮出力構造
```python
# 圧縮成功レスポンス
success_output = PlotCompressionOutput(
    success=True,
    original_size=25600,  # 文字数
    compressed_size=15360,  # 文字数
    compression_ratio=0.40,  # 40%削減
    backup_id="backup_20250721_143022",
    key_points=[
        "主人公が異世界転生",
        "魔法学校入学",
        "最初の試練で覚醒",
        "ライバルとの出会い",
        "第一章クライマックス：ドラゴン討伐"
    ],
    summary="異世界に転生した主人公が魔法学校で才能を開花させ、仲間と共に成長していく物語。第一章では入学から最初の大きな試練までを描く。",
    message="プロットを40%圧縮しました（バックアップID: backup_20250721_143022）"
)
```

### 5.3 圧縮プレビュー構造
```python
# プレビュー結果
preview_result = {
    "original_stats": {
        "total_words": 25600,
        "scene_count": 48,
        "chapter_count": 5,
        "dialogue_lines": 320
    },
    "compressed_stats": {
        "total_words": 15360,
        "scene_count": 32,
        "chapter_count": 5,
        "dialogue_lines": 280
    },
    "changes": [
        {
            "type": "scene_merge",
            "description": "移動シーン3つを1つに統合",
            "word_reduction": 800
        },
        {
            "type": "description_summary",
            "description": "世界観説明を要約",
            "word_reduction": 1200
        }
    ],
    "preserved_elements": [
        "全ての重要会話",
        "主要キャラクター設定",
        "ストーリー転換点"
    ]
}
```

### 5.4 圧縮オプション構造
```python
# カスタム圧縮オプション
custom_options = CompressionOptions(
    preserve_dialogue=True,      # 会話を保持
    merge_similar_scenes=True,   # 類似シーン統合
    extract_key_points=True,     # キーポイント抽出
    create_summary=True,         # サマリー生成
    backup_original=True         # オリジナル保存
)

# 軽量圧縮専用オプション
light_options = CompressionOptions(
    preserve_dialogue=True,
    merge_similar_scenes=False,  # シーン統合なし
    extract_key_points=False,
    create_summary=False,
    backup_original=True
)
```

## 6. 圧縮アルゴリズム仕様

### 6.1 テキスト圧縮処理
```python
def compress_text(self, text: str, level: CompressionLevel) -> str:
    """テキスト圧縮アルゴリズム"""

    # Step 1: 基本的なクリーンアップ
    text = remove_extra_whitespace(text)
    text = normalize_punctuation(text)

    # Step 2: レベル別処理
    if level >= CompressionLevel.LIGHT:
        text = remove_redundant_connectors(text)
        text = merge_short_paragraphs(text)

    if level >= CompressionLevel.STANDARD:
        text = summarize_long_descriptions(text)
        text = consolidate_similar_expressions(text)

    if level >= CompressionLevel.AGGRESSIVE:
        text = extract_key_sentences_only(text)
        text = remove_subplots(text)

    return text
```

### 6.2 構造圧縮処理
```python
def compress_structure(
    self,
    plot_structure: dict[str, Any],
    options: CompressionOptions
) -> dict[str, Any]:
    """構造圧縮アルゴリズム"""

    compressed = plot_structure.copy()

    if options.merge_similar_scenes:
        compressed = self._merge_similar_scenes(compressed)

    if options.extract_key_points:
        compressed["key_points"] = self._extract_key_points(compressed)

    # 階層の平坦化
    compressed = self._flatten_deep_nesting(compressed)

    # 空要素の削除
    compressed = self._remove_empty_elements(compressed)

    return compressed
```

### 6.3 インテリジェント要約
```python
def create_intelligent_summary(
    self,
    plot_content: dict[str, Any]
) -> str:
    """AI支援要約生成"""

    # 重要度スコアリング
    scored_elements = self._score_plot_elements(plot_content)

    # 上位要素の抽出
    top_elements = self._get_top_elements(scored_elements, n=10)

    # 要約文生成
    summary = self._generate_summary_text(top_elements)

    return summary
```

## 7. エラーハンドリング仕様

### 7.1 ドメイン例外
```python
# プロジェクト不存在エラー
try:
    compressed = use_case.execute(input_data)
except DomainException as e:
    # "プロジェクトが存在しません: {project_name}"

# プロット不存在エラー
try:
    compressed = use_case.execute(input_data)
except PlotNotFoundException as e:
    # "指定されたプロットが見つかりません"
```

### 7.2 圧縮エラー
```python
# 圧縮失敗エラー
try:
    compressed = use_case.execute(input_data)
except CompressionException as e:
    # "プロット圧縮に失敗しました: {reason}"

# 最小サイズ違反エラー
if compressed_size < MIN_PLOT_SIZE:
    raise ValueError("圧縮後のプロットが最小サイズを下回ります")
```

### 7.3 バックアップエラー
```python
# バックアップ作成失敗（警告レベル）
try:
    backup_id = self.create_backup(original_plot)
except BackupException as e:
    warnings.warn(f"バックアップ作成に失敗しました: {e}")
    # 処理は継続

# 復元失敗エラー
try:
    restored = use_case.restore_from_backup(backup_id)
except RestoreException as e:
    # "バックアップからの復元に失敗しました"
```

## 8. 使用例

### 8.1 基本的な圧縮実行
```python
# ユースケース初期化
plot_repository = YamlPlotRepository(project_path)
project_repository = YamlProjectRepository(base_path)
backup_service = BackupService(backup_path)

use_case = PlotCompressionUseCase(
    plot_repository=plot_repository,
    project_repository=project_repository,
    backup_service=backup_service
)

# 標準圧縮実行
input_data = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="master",
    compression_level=CompressionLevel.STANDARD
)

result = use_case.execute(input_data)

if result.success:
    print(f"✅ 圧縮成功")
    print(f"  元サイズ: {result.original_size:,} 文字")
    print(f"  圧縮後: {result.compressed_size:,} 文字")
    print(f"  削減率: {result.compression_ratio:.1%}")
    print(f"  バックアップID: {result.backup_id}")

    print("\n📌 キーポイント:")
    for point in result.key_points:
        print(f"  • {point}")
```

### 8.2 プレビューと確認
```python
# 圧縮プレビュー生成
preview = use_case.preview_compression(input_data)

print("📊 圧縮プレビュー:")
print(f"シーン数: {preview['original_stats']['scene_count']} → {preview['compressed_stats']['scene_count']}")
print(f"文字数: {preview['original_stats']['total_words']:,} → {preview['compressed_stats']['total_words']:,}")

print("\n変更内容:")
for change in preview['changes']:
    print(f"• {change['description']} (-{change['word_reduction']} 文字)")

# ユーザー確認
if input("圧縮を実行しますか？ (y/n): ").lower() == 'y':
    result = use_case.execute(input_data)
```

### 8.3 章別圧縮とカスタムオプション
```python
# カスタムオプションで章別圧縮
options = CompressionOptions(
    preserve_dialogue=True,       # 会話は全て保持
    merge_similar_scenes=False,   # シーン統合しない
    extract_key_points=True,      # キーポイント抽出する
    create_summary=True,          # サマリー作成する
    backup_original=True          # バックアップ必須
)

# 第3章のみ軽量圧縮
chapter_input = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="chapter",
    chapter_number=3,
    compression_level=CompressionLevel.LIGHT
)

# オプション付き実行
use_case.options = options
result = use_case.execute(chapter_input)

# 差分レポート生成
if result.success and result.backup_id:
    diff_report = use_case.generate_diff_report(
        original=use_case.restore_from_backup(result.backup_id),
        compressed=plot_repository.get_chapter_plot(
            chapter_input.project_name,
            chapter_input.chapter_number
        )
    )
    print(diff_report)
```

### 8.4 一括圧縮と復元
```python
# 全プロット一括圧縮
all_input = PlotCompressionInput(
    project_name="転生したら最強の魔法使いだった件",
    plot_type="all",
    compression_level=CompressionLevel.AGGRESSIVE
)

# 実行前の確認
preview = use_case.preview_compression(all_input)
total_reduction = preview['original_stats']['total_words'] - preview['compressed_stats']['total_words']
print(f"⚠️ 高圧縮モード: 約{total_reduction:,}文字削減されます")

if input("続行しますか？ (y/n): ").lower() == 'y':
    result = use_case.execute(all_input)

    if result.success:
        print(f"✅ 全プロット圧縮完了")
        print(f"バックアップID: {result.backup_id}")

        # 必要に応じて復元
        if input("元に戻しますか？ (y/n): ").lower() == 'y':
            restored = use_case.restore_from_backup(result.backup_id)
            print("✅ プロットを復元しました")
```

## 9. テスト仕様

### 9.1 単体テスト
```python
class TestPlotCompressionUseCase:
    def test_light_compression_success(self):
        """軽量圧縮成功テスト"""

    def test_standard_compression_success(self):
        """標準圧縮成功テスト"""

    def test_aggressive_compression_success(self):
        """高圧縮成功テスト"""

    def test_compression_with_backup(self):
        """バックアップ付き圧縮テスト"""

    def test_restore_from_backup(self):
        """バックアップ復元テスト"""

    def test_preview_generation(self):
        """プレビュー生成テスト"""

    def test_key_points_extraction(self):
        """キーポイント抽出テスト"""

    def test_project_not_found(self):
        """プロジェクト不存在テスト"""

    def test_minimum_size_validation(self):
        """最小サイズ検証テスト"""
```

### 9.2 統合テスト
```python
class TestPlotCompressionIntegration:
    def test_full_compression_workflow(self):
        """完全圧縮ワークフローテスト"""

    def test_chapter_by_chapter_compression(self):
        """章別順次圧縮テスト"""

    def test_compression_and_restoration(self):
        """圧縮・復元往復テスト"""

    def test_concurrent_compression(self):
        """並行圧縮処理テスト"""
```

### 9.3 パフォーマンステスト
```python
class TestPlotCompressionPerformance:
    def test_large_plot_compression(self):
        """大規模プロット圧縮性能テスト"""

    def test_compression_speed_by_level(self):
        """レベル別圧縮速度テスト"""

    def test_memory_usage_during_compression(self):
        """圧縮時メモリ使用量テスト"""
```

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/plot_compression_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_plot_compression_use_case.py`
- **統合テスト**: `tests/integration/test_plot_compression_workflow.py`

### 10.2 設計方針
- **DDD原則の厳格遵守**: アプリケーション層でのビジネスロジック集約
- **可逆性の確保**: 常にオリジナルへの復元可能性を保証
- **段階的圧縮**: レベルに応じた適切な圧縮強度
- **情報保全**: 重要情報の確実な保持

### 10.3 今後の改善点
- [ ] AI による重要度判定の精度向上
- [ ] カスタム圧縮ルールの定義機能
- [ ] 圧縮履歴の分析・最適化
- [ ] リアルタイム圧縮プレビュー
- [ ] 他フォーマットへの圧縮エクスポート
- [ ] 圧縮レベルの自動推奨機能
