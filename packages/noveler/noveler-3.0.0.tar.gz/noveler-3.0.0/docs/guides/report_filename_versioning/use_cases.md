# Report Filename Versioning — ユースケース集

## 1. Draft Revisions（推敲版管理）

```python
filename_v1 = ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md",
    version="v1"
)
# episode_001_A41_v1.md

filename_v2 = ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md",
    version="v2"
)
# episode_001_A41_v2.md

filename_final = ps.generate_report_filename(
    episode_number=1,
    report_type="A41",
    extension="md"
)
# episode_001_A41.md
```

```
reports/quality/
├── episode_001_A41.md        # 最新版（バージョンなし）
├── episode_001_A41_v1.md     # 初回推敲
├── episode_001_A41_v2.md     # 2回目推敲
└── episode_001_A41_v3.md     # 3回目推敲
```

## 2. Quality Check Iterations（品質チェック反復）

```python
filename_initial = ps.generate_report_filename(
    episode_number=5,
    report_type="quality",
    extension="json",
    include_timestamp=True,
    version="initial"
)
# episode_005_quality_20251013_100000_initial.json

filename_revised = ps.generate_report_filename(
    episode_number=5,
    report_type="quality",
    extension="json",
    include_timestamp=True,
    version="revised"
)
# episode_005_quality_20251013_131500_revised.json
```

**おすすめの保管構造**
```
reports/quality/
└── episode_005/
    ├── episode_005_quality_20251013_100000_initial.json
    └── episode_005_quality_20251013_131500_revised.json
```

## 3. A/B Testing（比較検証）

```python
filename_approach_a = ps.generate_report_filename(
    episode_number=10,
    report_type="A41",
    extension="md",
    version="approach-a"
)
# episode_010_A41_approach-a.md

filename_approach_b = ps.generate_report_filename(
    episode_number=10,
    report_type="A41",
    extension="md",
    version="approach-b"
)
# episode_010_A41_approach-b.md
```

## 4. Backup Versions（バックアップ運用）

```python
filename_daily = ps.generate_report_filename(
    episode_number=20,
    report_type="backup",
    extension="yaml",
    include_timestamp=True,
    version="daily"
)
# episode_020_backup_20251013_020000_daily.yaml

filename_weekly = ps.generate_report_filename(
    episode_number=20,
    report_type="backup",
    extension="yaml",
    include_timestamp=True,
    version="weekly"
)
# episode_020_backup_20251013_020000_weekly.yaml
```

```
backups/
├── daily/
│   └── episode_020_backup_20251013_020000_daily.yaml
└── weekly/
    └── episode_020_backup_20251013_020000_weekly.yaml
```
