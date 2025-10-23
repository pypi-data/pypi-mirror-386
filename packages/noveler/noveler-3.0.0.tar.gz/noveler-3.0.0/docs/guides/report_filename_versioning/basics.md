# Report Filename Versioning — 基本

## 概要

統一レポートファイル名生成サービスは、同一エピソードに複数バージョンのレポートを共存させるためのバージョン管理機能を提供します。基本フォーマットは次の通りです。

```
episode_{episode:03d}_{report_type}[_{timestamp}][_{version}].{ext}
```

## Version パラメータの使い方

```python
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

ps = create_path_service()

# バージョンなし（デフォルト）
filename = ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md"
)
# → episode_001_A41.md

# バージョン指定
filename = ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md",
    version="v2"
)
# → episode_001_A41_v2.md
```

### タイムスタンプ併用

```python
filename = ps.generate_report_filename(
    episode_number=42,
    report_type="quality",
    extension="json",
    include_timestamp=True,
    version="v3"
)
# → episode_042_quality_20251013_124325_v3.json
```

## バージョン情報の解析

```python
from noveler.domain.services.report_file_naming_service import ReportFileNamingService

parsed = ReportFileNamingService.parse_filename("episode_042_quality_v2.json")

assert parsed["episode_number"] == 42
assert parsed["report_type"] == "quality"
assert parsed["extension"] == "json"
assert parsed["version"] == "v2"
assert parsed["timestamp"] is None

parsed = ReportFileNamingService.parse_filename(
    "episode_042_quality_20251013_124325_v3.json"
)

assert parsed["timestamp"] == "20251013_124325"
assert parsed["version"] == "v3"
```

## 並び順と自然ソート

```python
filenames = [
    "episode_001_A41.md",
    "episode_001_A41_v1.md",
    "episode_001_A41_v2.md",
    "episode_002_A41.md",
    "episode_010_A41.md",
    "episode_010_A41_v1.md",
]

sorted_filenames = sorted(filenames)
# → エピソード番号とバージョンの順序が自然に維持される
```

**ポイント**

- エピソード番号は 3 桁ゼロ埋め（001, 002, 010）
- バージョンなしファイルは同一エピソードのバージョン付きより前に並ぶ
- アルファベット順となるため、バージョン接尾辞の命名を揃えることが重要
