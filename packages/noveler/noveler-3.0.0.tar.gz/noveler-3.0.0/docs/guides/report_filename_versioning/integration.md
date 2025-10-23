# Report Filename Versioning — 統合と検証

## 推敲ツールとの連携例

```python
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

ps = create_path_service()
reports_dir = ps.get_reports_dir() / "quality"

# 初回推敲
path_v1 = reports_dir / ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md",
    version="v1"
)

# 修正後の再推敲
path_v2 = reports_dir / ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md",
    version="v2"
)

# 最終版（バージョンなし）
path_final = reports_dir / ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md"
)
```

## 品質レポートツールとの統合
- `export_quality_report_tool` は現状 version パラメータを直接受け付けませんが、PathService を通じて拡張可能です。
- 既存ツールがサポートしていない場合でも、生成後にファイル名を差し替える運用で段階的に導入できます。

## レガシーフォーマットからの移行

| Before | After |
| --- | --- |
| `A41_ep001.md` | `episode_001_A41.md` |
| `quality_ep001_20251013_124325.json` | `episode_001_quality_20251013_124325.json` |
| `quality_ep001_final.json` | `episode_001_quality_20251013_124325_final.json` |

## テスト

```python
def test_filename_with_version(service):
    config = ReportFileNameConfig(
        episode_number=1, report_type="A41", extension="md", version="v2"
    )
    assert service.generate_filename(config) == "episode_001_A41_v2.md"

def test_filename_with_timestamp_and_version(service, freezer):
    freezer.move_to("2025-01-15 10:30:45")
    config = ReportFileNameConfig(
        episode_number=42,
        report_type="quality",
        extension="json",
        include_timestamp=True,
        version="v3",
    )
    assert service.generate_filename(config) == "episode_042_quality_20250115_103045_v3.json"
```

**Coverage**: `tests/unit/domain/services/test_report_file_naming_service.py` にバージョン関連 25 ケースが含まれ、100% パス済み。

## API リファレンス

```python
@dataclass(frozen=True)
class ReportFileNameConfig:
    episode_number: int
    report_type: str
    extension: str
    include_timestamp: bool = False
    timestamp_format: str = "%Y%m%d_%H%M%S"
    version: str | None = None
```

```python
def generate_report_filename(
    self,
    episode_number: int,
    report_type: str,
    extension: str = "md",
    include_timestamp: bool = False,
    version: str | None = None,
) -> str:
    """Format: episode_{episode:03d}_{report_type}[_{timestamp}][_{version}].{ext}"""
```
