# SPEC-GENERAL-031: プロジェクトエクスポートユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、小説プロジェクトを様々な形式でエクスポートするビジネスロジックを実装する。なろう投稿形式、電子書籍形式、印刷用PDF、バックアップアーカイブなど、多様な出力ニーズに対応する包括的なエクスポートシステムを提供。

### 1.2 スコープ
- 複数形式へのエクスポート対応
- フォーマット別の最適化処理
- メタデータの適切な変換・埋め込み
- 選択的エクスポート（章・話数指定）
- エクスポート履歴管理
- 品質チェック統合

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── ProjectExportUseCase                        ← Domain Layer
│   ├── ProjectExportInput                     └── ExportedProject (Entity)
│   ├── ExportOptions                          └── ExportFormatter (Service)
│   ├── ProjectExportOutput                    └── ExportFormat (Enum)
│   └── execute(), preview_export()            └── ExportMetadata (Value Object)
└── Export Functions                            └── ProjectRepository, EpisodeRepository (Interfaces)
    ├── export_to_narou()
    ├── export_to_epub()
    └── export_to_pdf()
```

### 1.4 ビジネス価値
- **配布の効率化**: 複数プラットフォームへの迅速な展開
- **品質の統一**: フォーマット間での一貫した品質維持
- **作業の自動化**: 手動変換作業の大幅削減
- **柔軟な公開**: 部分公開・試し読み版の容易な作成

## 2. 機能仕様

### 2.1 コアユースケース
```python
class ProjectExportUseCase:
    def __init__(
        self,
        project_repository: ProjectRepository,
        episode_repository: EpisodeRepository,
        export_service: ExportService,
        quality_checker: QualityChecker
    ):
        """依存性注入による初期化"""

    def execute(
        self,
        input_data: ProjectExportInput
    ) -> ProjectExportOutput:
        """プロジェクトエクスポート実行"""

    def preview_export(
        self,
        input_data: ProjectExportInput
    ) -> dict[str, Any]:
        """エクスポートプレビュー生成"""
```

### 2.2 入力・出力データ
```python
@dataclass
class ProjectExportInput:
    """エクスポート入力"""
    project_name: str
    export_format: ExportFormat
    output_path: str
    episode_range: tuple[int, int] | None = None  # (start, end)
    chapters: list[int] | None = None

@dataclass
class ExportOptions:
    """エクスポートオプション"""
    include_metadata: bool = True
    include_illustrations: bool = False
    include_author_notes: bool = True
    quality_check: bool = True
    compress_output: bool = False
    split_by_chapter: bool = False
    custom_styling: dict[str, Any] | None = None

@dataclass
class ProjectExportOutput:
    """エクスポート出力"""
    success: bool
    output_files: list[str]
    total_size: int
    export_id: str
    quality_report: dict[str, Any] | None
    warnings: list[str]
    message: str = ""
```

### 2.3 フォーマット別エクスポート
```python
def export_to_narou(
    self,
    project: Project,
    episodes: list[Episode],
    options: ExportOptions
) -> list[str]:
    """なろう形式エクスポート"""

def export_to_epub(
    self,
    project: Project,
    episodes: list[Episode],
    options: ExportOptions
) -> str:
    """EPUB形式エクスポート"""

def export_to_pdf(
    self,
    project: Project,
    episodes: list[Episode],
    options: ExportOptions
) -> str:
    """PDF形式エクスポート"""

def export_to_markdown(
    self,
    project: Project,
    episodes: list[Episode],
    options: ExportOptions
) -> list[str]:
    """Markdown形式エクスポート"""
```

### 2.4 補助機能
```python
def validate_export_request(
    self,
    input_data: ProjectExportInput
) -> list[str]:
    """エクスポートリクエスト検証"""

def prepare_metadata(
    self,
    project: Project,
    format: ExportFormat
) -> dict[str, Any]:
    """メタデータ準備"""

def create_export_manifest(
    self,
    export_id: str,
    files: list[str]
) -> dict[str, Any]:
    """エクスポートマニフェスト作成"""
```

## 3. エクスポート形式仕様

### 3.1 なろう形式（NAROU）
```python
なろう形式仕様 = {
    "file_extension": ".txt",
    "encoding": "UTF-8",
    "line_ending": "CRLF",
    "features": {
        "ruby_support": True,  # ルビ記法対応
        "emphasis_markers": True,  # 強調記法
        "scene_breaks": "◆◇◆◇◆◇◆◇◆◇",
        "episode_separator": "\n\n========\n\n"
    },
    "metadata_format": {
        "title": "【タイトル】{title}",
        "author": "【作者】{author}",
        "genre": "【ジャンル】{genre}",
        "tags": "【タグ】{tags}"
    }
}
```

### 3.2 EPUB形式
```python
EPUB形式仕様 = {
    "version": "3.0",
    "file_structure": {
        "mimetype": "application/epub+zip",
        "META-INF/": ["container.xml"],
        "OEBPS/": ["content.opf", "toc.ncx", "toc.xhtml"],
        "OEBPS/Text/": ["chapter*.xhtml"],
        "OEBPS/Styles/": ["style.css"],
        "OEBPS/Images/": ["cover.jpg", "illustrations/*"]
    },
    "metadata": {
        "dc:title": "プロジェクトタイトル",
        "dc:creator": "作者名",
        "dc:language": "ja",
        "dc:identifier": "UUID",
        "dc:date": "発行日",
        "dc:publisher": "出版社名"
    }
}
```

### 3.3 PDF形式
```python
PDF形式仕様 = {
    "page_size": "A5",  # 文庫本サイズ
    "margins": {
        "top": 20,
        "bottom": 20,
        "left": 15,
        "right": 15
    },
    "font": {
        "family": "游明朝",
        "size": 10,
        "line_height": 1.8
    },
    "layout": {
        "columns": 1,
        "header": True,
        "footer": True,
        "page_numbers": True
    },
    "toc": {
        "include": True,
        "depth": 2
    }
}
```

### 3.4 アーカイブ形式（ARCHIVE）
```python
アーカイブ形式仕様 = {
    "format": "zip",
    "compression": "deflate",
    "structure": {
        "project.yaml": "プロジェクト設定",
        "episodes/": "全エピソード",
        "plots/": "プロット情報",
        "characters/": "キャラクター設定",
        "settings/": "世界観設定",
        "quality/": "品質記録",
        "metadata.json": "エクスポートメタデータ"
    },
    "include_history": True,
    "include_backups": False
}
```

## 4. 変換処理仕様

### 4.1 テキスト変換
```python
def convert_text_format(
    self,
    text: str,
    from_format: str,
    to_format: ExportFormat
) -> str:
    """テキスト形式変換"""

    # Markdown → なろう形式
    if to_format == ExportFormat.NAROU:
        # ルビ変換: {漢字|かんじ} → ｜漢字《かんじ》
        text = re.sub(r'\{([^|]+)\|([^}]+)\}', r'｜\1《\2》', text)

        # 強調変換: **太字** → 《《太字》》
        text = re.sub(r'\*\*([^*]+)\*\*', r'《《\1》》', text)

        # 傍点変換: ~~傍点~~ → ・・・・（傍点表現）
        text = re.sub(r'~~([^~]+)~~', lambda m: add_bouten(m.group(1)), text)

    # Markdown → HTML (EPUB用)
    elif to_format == ExportFormat.EPUB:
        text = markdown_to_html(text)
        text = add_epub_specific_tags(text)

    return text
```

### 4.2 メタデータ変換
```python
def prepare_format_metadata(
    self,
    project: Project,
    format: ExportFormat
) -> dict[str, Any]:
    """フォーマット別メタデータ準備"""

    base_metadata = {
        "title": project.title,
        "author": project.author,
        "description": project.description,
        "genre": project.genre,
        "tags": project.tags,
        "created_date": project.created_date,
        "updated_date": project.updated_date
    }

    if format == ExportFormat.EPUB:
        # EPUB特有のメタデータ
        metadata = {
            "dc:title": base_metadata["title"],
            "dc:creator": base_metadata["author"],
            "dc:language": "ja",
            "dc:identifier": generate_uuid(),
            "dc:date": base_metadata["updated_date"].isoformat(),
            "dc:subject": ", ".join(base_metadata["tags"])
        }

    elif format == ExportFormat.PDF:
        # PDF特有のメタデータ
        metadata = {
            "Title": base_metadata["title"],
            "Author": base_metadata["author"],
            "Subject": base_metadata["description"],
            "Keywords": ", ".join(base_metadata["tags"]),
            "Creator": "Novel Writing System",
            "Producer": "ReportLab"
        }

    return metadata
```

### 4.3 スタイル適用
```python
def apply_format_styling(
    self,
    content: str,
    format: ExportFormat,
    custom_styles: dict[str, Any] | None
) -> str:
    """フォーマット別スタイル適用"""

    if format == ExportFormat.EPUB:
        # デフォルトCSS
        default_css = """
        body { font-family: serif; line-height: 1.8; }
        h1 { font-size: 1.5em; margin: 2em 0 1em; }
        h2 { font-size: 1.3em; margin: 1.5em 0 0.5em; }
        p { text-indent: 1em; margin: 0; }
        .scene-break { text-align: center; margin: 2em 0; }
        """

        # カスタムスタイルのマージ
        if custom_styles:
            css = merge_styles(default_css, custom_styles.get("css", ""))
        else:
            css = default_css

        return wrap_with_html(content, css)

    return content
```

## 5. データ構造仕様

### 5.1 エクスポート入力構造
```python
# 全話なろう形式エクスポート
narou_export_input = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.NAROU,
    output_path="/exports/narou/",
    episode_range=None,  # 全話
    chapters=None  # 全章
)

# 第1章のみEPUBエクスポート
epub_chapter_input = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.EPUB,
    output_path="/exports/epub/",
    episode_range=None,
    chapters=[1]  # 第1章のみ
)

# 1-10話のPDFエクスポート
pdf_sample_input = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.PDF,
    output_path="/exports/pdf/",
    episode_range=(1, 10),  # 1-10話
    chapters=None
)
```

### 5.2 エクスポート出力構造
```python
# 成功レスポンス例
success_output = ProjectExportOutput(
    success=True,
    output_files=[
        "/exports/narou/転生したら最強の魔法使いだった件_第001話.txt",
        "/exports/narou/転生したら最強の魔法使いだった件_第002話.txt",
        # ... 省略
    ],
    total_size=2457600,  # バイト
    export_id="export_20250721_150000",
    quality_report={
        "total_episodes": 50,
        "checked_episodes": 50,
        "quality_issues": 3,
        "average_quality_score": 92.5
    },
    warnings=[
        "第15話: 文字数が規定を超えています（5200文字）",
        "第23話: 未解決の伏線があります"
    ],
    message="50話をなろう形式でエクスポートしました"
)
```

### 5.3 エクスポートプレビュー構造
```python
# プレビュー結果
preview_result = {
    "export_summary": {
        "format": "EPUB",
        "total_episodes": 30,
        "total_chapters": 3,
        "estimated_size": 1536000,  # バイト
        "estimated_pages": 320  # PDF/EPUB用
    },
    "included_content": {
        "episodes": ["第1話", "第2話", "...", "第30話"],
        "chapters": ["第1章: 転生", "第2章: 覚醒", "第3章: 試練"],
        "extras": ["あとがき", "設定資料", "キャラクター紹介"]
    },
    "format_specific": {
        "cover_image": "cover.jpg",
        "illustrations": 5,
        "toc_depth": 2,
        "font_embedded": True
    },
    "quality_preview": {
        "episodes_to_check": 30,
        "estimated_check_time": 45  # 秒
    }
}
```

### 5.4 エクスポートマニフェスト構造
```python
# エクスポートマニフェスト
export_manifest = {
    "export_id": "export_20250721_150000",
    "timestamp": "2025-07-21T15:00:00+09:00",
    "project": {
        "name": "転生したら最強の魔法使いだった件",
        "version": "1.2.0",
        "author": "作者名"
    },
    "export_details": {
        "format": "EPUB",
        "episodes": {
            "total": 50,
            "exported": 50,
            "range": [1, 50]
        },
        "options": {
            "include_metadata": True,
            "include_illustrations": True,
            "quality_checked": True
        }
    },
    "files": [
        {
            "path": "novel.epub",
            "size": 2457600,
            "checksum": "sha256:abcdef123456..."
        }
    ],
    "quality_summary": {
        "score": 92.5,
        "issues_found": 3,
        "issues_fixed": 2
    }
}
```

## 6. 品質チェック統合仕様

### 6.1 エクスポート前品質チェック
```python
def pre_export_quality_check(
    self,
    episodes: list[Episode],
    format: ExportFormat
) -> dict[str, Any]:
    """エクスポート前品質チェック"""

    issues = []

    for episode in episodes:
        # 文字数チェック（フォーマット別）
        if format == ExportFormat.NAROU:
            if episode.word_count > 5000:
                issues.append({
                    "episode": episode.number,
                    "type": "word_count",
                    "severity": "warning",
                    "message": f"文字数超過: {episode.word_count}文字"
                })

        # 形式固有のチェック
        if format == ExportFormat.EPUB:
            # 画像参照チェック
            missing_images = check_image_references(episode.content)
            if missing_images:
                issues.append({
                    "episode": episode.number,
                    "type": "missing_resource",
                    "severity": "error",
                    "message": f"画像が見つかりません: {missing_images}"
                })

    return {
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues,
        "statistics": calculate_quality_stats(episodes)
    }
```

### 6.2 自動修正機能
```python
def auto_fix_export_issues(
    self,
    content: str,
    format: ExportFormat,
    issues: list[dict[str, Any]]
) -> tuple[str, list[str]]:
    """エクスポート用自動修正"""

    fixed_content = content
    fixes_applied = []

    for issue in issues:
        if issue["type"] == "encoding" and format == ExportFormat.NAROU:
            # 文字化け防止
            fixed_content = normalize_unicode(fixed_content)
            fixes_applied.append("Unicode正規化を適用")

        elif issue["type"] == "line_ending":
            # 改行コード統一
            fixed_content = unify_line_endings(fixed_content, format)
            fixes_applied.append("改行コードを統一")

        elif issue["type"] == "invalid_markup":
            # 不正なマークアップ修正
            fixed_content = fix_markup(fixed_content, format)
            fixes_applied.append("マークアップを修正")

    return fixed_content, fixes_applied
```

## 7. エラーハンドリング仕様

### 7.1 ドメイン例外
```python
# プロジェクト不存在エラー
try:
    result = use_case.execute(input_data)
except ProjectNotFoundException as e:
    # "プロジェクトが存在しません: {project_name}"

# エピソード不存在エラー
try:
    result = use_case.execute(input_data)
except EpisodeNotFoundException as e:
    # "指定された範囲にエピソードが存在しません"
```

### 7.2 エクスポートエラー
```python
# 出力先アクセスエラー
try:
    result = use_case.execute(input_data)
except OutputPathException as e:
    # "出力先にアクセスできません: {output_path}"

# フォーマット変換エラー
try:
    converted = convert_to_format(content, format)
except FormatConversionException as e:
    # "フォーマット変換に失敗しました: {reason}"
```

### 7.3 リソースエラー
```python
# ディスク容量不足（警告）
available_space = check_disk_space(output_path)
if available_space < estimated_size * 1.2:
    warnings.append(f"ディスク容量が不足している可能性があります（残り: {available_space}）")

# メモリ不足対策
try:
    process_large_export(episodes)
except MemoryError:
    # チャンク処理にフォールバック
    process_in_chunks(episodes, chunk_size=10)
```

## 8. 使用例

### 8.1 基本的なエクスポート
```python
# ユースケース初期化
project_repository = YamlProjectRepository(base_path)
episode_repository = YamlEpisodeRepository(project_path)
export_service = ExportService()
quality_checker = QualityChecker()

use_case = ProjectExportUseCase(
    project_repository=project_repository,
    episode_repository=episode_repository,
    export_service=export_service,
    quality_checker=quality_checker
)

# なろう形式で全話エクスポート
input_data = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.NAROU,
    output_path="/exports/narou/"
)

result = use_case.execute(input_data)

if result.success:
    print(f"✅ エクスポート成功")
    print(f"出力ファイル数: {len(result.output_files)}")
    print(f"合計サイズ: {result.total_size / 1024 / 1024:.1f} MB")

    if result.warnings:
        print("\n⚠️ 警告:")
        for warning in result.warnings:
            print(f"  • {warning}")
```

### 8.2 選択的エクスポートと品質チェック
```python
# カスタムオプションで第1章のみEPUB化
options = ExportOptions(
    include_metadata=True,
    include_illustrations=True,
    include_author_notes=True,
    quality_check=True,
    compress_output=False,
    split_by_chapter=False,
    custom_styling={
        "css": """
        body { font-family: 'Noto Serif JP', serif; }
        h1 { color: #333; border-bottom: 2px solid #333; }
        """
    }
)

chapter_input = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.EPUB,
    output_path="/exports/epub/",
    chapters=[1]
)

# プレビュー確認
preview = use_case.preview_export(chapter_input)
print(f"📊 エクスポートプレビュー:")
print(f"  含まれるエピソード: {len(preview['included_content']['episodes'])}話")
print(f"  推定サイズ: {preview['export_summary']['estimated_size'] / 1024:.1f} KB")
print(f"  推定ページ数: {preview['export_summary']['estimated_pages']}ページ")

# エクスポート実行
use_case.options = options
result = use_case.execute(chapter_input)

if result.quality_report:
    print(f"\n📈 品質レポート:")
    print(f"  平均品質スコア: {result.quality_report['average_quality_score']:.1f}")
    print(f"  品質問題: {result.quality_report['quality_issues']}件")
```

### 8.3 一括エクスポートとアーカイブ
```python
# 複数形式で同時エクスポート
formats = [
    ExportFormat.NAROU,
    ExportFormat.EPUB,
    ExportFormat.PDF,
    ExportFormat.ARCHIVE
]

results = {}
for format in formats:
    input_data = ProjectExportInput(
        project_name="転生したら最強の魔法使いだった件",
        export_format=format,
        output_path=f"/exports/{format.value}/"
    )

    print(f"\n📤 {format.value}形式でエクスポート中...")
    result = use_case.execute(input_data)
    results[format] = result

    if result.success:
        print(f"  ✅ 成功: {len(result.output_files)}ファイル")
    else:
        print(f"  ❌ 失敗: {result.message}")

# エクスポート履歴の保存
export_history = {
    "timestamp": datetime.now().isoformat(),
    "project": "転生したら最強の魔法使いだった件",
    "formats": [f.value for f in formats],
    "results": {
        format.value: {
            "success": result.success,
            "files": len(result.output_files),
            "size": result.total_size
        }
        for format, result in results.items()
    }
}

save_export_history(export_history)
```

### 8.4 試し読み版の作成
```python
# 試し読み版（1-3話）のPDF作成
sample_options = ExportOptions(
    include_metadata=True,
    include_illustrations=False,  # イラストは除外
    include_author_notes=False,   # 作者ノートは除外
    quality_check=True,
    compress_output=True,         # ファイルサイズ削減
    custom_styling={
        "watermark": "試し読み版",
        "footer_text": "続きは本編でお楽しみください"
    }
)

sample_input = ProjectExportInput(
    project_name="転生したら最強の魔法使いだった件",
    export_format=ExportFormat.PDF,
    output_path="/exports/samples/",
    episode_range=(1, 3)  # 1-3話のみ
)

use_case.options = sample_options
result = use_case.execute(sample_input)

if result.success:
    print(f"✅ 試し読み版を作成しました")
    print(f"ファイル: {result.output_files[0]}")
    print(f"サイズ: {result.total_size / 1024:.1f} KB")

    # 配布用URLの生成
    distribution_url = generate_distribution_url(
        result.output_files[0],
        expiry_days=30
    )
    print(f"配布URL: {distribution_url}")
```

## 9. テスト仕様

### 9.1 単体テスト
```python
class TestProjectExportUseCase:
    def test_narou_export_success(self):
        """なろう形式エクスポート成功テスト"""

    def test_epub_export_success(self):
        """EPUB形式エクスポート成功テスト"""

    def test_pdf_export_success(self):
        """PDF形式エクスポート成功テスト"""

    def test_selective_export(self):
        """選択的エクスポートテスト"""

    def test_quality_check_integration(self):
        """品質チェック統合テスト"""

    def test_metadata_conversion(self):
        """メタデータ変換テスト"""

    def test_invalid_range_error(self):
        """無効な範囲指定エラーテスト"""

    def test_output_path_error(self):
        """出力先エラーテスト"""
```

### 9.2 統合テスト
```python
class TestProjectExportIntegration:
    def test_full_export_workflow(self):
        """完全エクスポートワークフローテスト"""

    def test_multi_format_export(self):
        """複数形式同時エクスポートテスト"""

    def test_large_project_export(self):
        """大規模プロジェクトエクスポートテスト"""

    def test_concurrent_export(self):
        """並行エクスポートテスト"""
```

### 9.3 形式別テスト
```python
class TestFormatSpecificExport:
    def test_narou_formatting(self):
        """なろう形式変換テスト"""

    def test_epub_structure(self):
        """EPUB構造検証テスト"""

    def test_pdf_layout(self):
        """PDFレイアウトテスト"""

    def test_archive_completeness(self):
        """アーカイブ完全性テスト"""
```

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/project_export_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_project_export_use_case.py`
- **統合テスト**: `tests/integration/test_project_export_workflow.py`

### 10.2 設計方針
- **DDD原則の厳格遵守**: アプリケーション層でのビジネスロジック集約
- **形式独立性**: 新しいエクスポート形式の追加が容易
- **品質保証**: エクスポート前の自動品質チェック
- **エラー耐性**: 部分的な失敗でも可能な限り処理継続

### 10.3 今後の改善点
- [ ] クラウドストレージへの直接エクスポート
- [ ] 増分エクスポート機能（更新分のみ）
- [ ] エクスポートテンプレートのカスタマイズ機能
- [ ] 多言語対応（翻訳版エクスポート）
- [ ] エクスポート後の自動配信機能
- [ ] プレビュー画面でのリアルタイム確認
