# Archive Disabled Configs Workflow

## Summary
This note explains how to run `scripts/tools/archive_disabled_configs.py` to collect
`*.disabled.json` and `*.backup` files into `archive/disabled_configs/YYYYMMDD/`.
The script is intentionally kept out of the pre-commit hooks; the canonical
invocation is manual or via a scheduled CI job (weekly) so that developers retain
control over when configuration snapshots are moved.

## Manual Usage
```
python scripts/tools/archive_disabled_configs.py \
  --project-root . \
  --dest archive/disabled_configs \
  --patterns "*.disabled.json,*.backup" \
  --dry-run
```
- Always begin with `--dry-run` to inspect the candidates.
- Remove `--dry-run` once the output looks correct.
- The command preserves the relative path of each file beneath the chosen
  destination.

## CI Scheduling (proposal)
- Add a weekly job (e.g., Sunday 03:00 UTC) that runs the script without
  `--dry-run` in production branches.
- Gate the job behind a `DISABLED_CONFIG_ARCHIVE=1` environment check so that it
  can be toggled if the pipeline needs to be paused.
- Publish the list of moved files as a workflow artifact to aid auditing.

## Notes
- The script skips heavy/temporary directories (`.git`, `dist`, `.mcp`, etc.).
- If additional patterns need to be added, extend the comma-separated value in
  the `--patterns` flag; the script already accepts arbitrary glob patterns.
- For large migrations, consider running the script locally first and committing
  the resulting archive to ensure reproducibility.
