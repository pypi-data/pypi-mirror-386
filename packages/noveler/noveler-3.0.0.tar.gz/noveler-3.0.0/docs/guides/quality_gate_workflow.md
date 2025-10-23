# Quality Gate Workflow Guide

## Overview

The quality gate workflow implements a two-gate system to ensure manuscript quality:
- **Gate B**: Core quality checks (rhythm, readability, grammar)
- **Gate C**: Editorial 12-step checklist verification

## Gate B: Core Quality Checks

Gate B evaluates three primary aspects of manuscript quality:

### Configuration

Gate B thresholds are defined in `config/quality/gate_defaults.yaml`:

```yaml
gate_defaults:
  thresholds:
    gate_b:
      rhythm: 80      # Minimum score for rhythm check
      readability: 80 # Minimum score for readability
      grammar: 90     # Minimum score for grammar
```

### Execution

```bash
# Run core quality checks
bin/check-core --out reports/quality.ndjson

# Or via CI wrapper with Gate B evaluation
python scripts/ci/run_quality_checks_ndjson.py \
  --file-path manuscript/EP001.txt \
  --fail-on-score-below 80
```

### Metadata

The tool generates metadata for Gate B evaluation:

```json
{
  "gate_b_pass": true,
  "gate_b_should_fail": false,
  "gate_b_thresholds": {
    "rhythm": 80,
    "readability": 80,
    "grammar": 90
  },
  "gate_b_evaluation": {
    "rhythm": {"required": 80, "actual": 85, "pass": true},
    "readability": {"required": 80, "actual": 92, "pass": true},
    "grammar": {"required": 90, "actual": 95, "pass": true}
  }
}
```

### MCP Integration

Gate B metadata is automatically included when using the MCP tool:

```bash
# Via MCP CLI
noveler mcp call run_quality_checks '{
  "episode_number": 1,
  "file_path": "manuscript/EP001.txt",
  "gate_thresholds": {
    "rhythm": 80,
    "readability": 80,
    "grammar": 90
  }
}'
```

The response includes `gate_b_*` metadata fields for programmatic gate evaluation.

## Gate C: Editorial Checklist

Gate C validates the editorial 12-step checklist for comprehensive quality assurance:

### Configuration

```yaml
gate_defaults:
  editorial_checklist:
    require_all_pass: true  # All items must be PASS (no TODO/NOTE)
```

### Execution

```bash
# Generate editorial checklist
bin/check-editorial-checklist --out reports/editorial_checklist.md

# Evaluate Gate C
python scripts/tools/editorial_checklist_evaluator.py \
  --file reports/editorial_checklist.md \
  --format json
```

### Metadata

Gate C evaluation generates the following metadata:

```json
{
  "gate_c_pass": true,
  "gate_c_should_fail": false,
  "gate_c_counts": {
    "total": 12,
    "pass": 12,
    "note": 0,
    "todo": 0,
    "unknown": 0,
    "checked": 12,
    "unchecked": 0
  },
  "gate_c_counts_by_status": {
    "PASS": 12,
    "NOTE": 0,
    "TODO": 0,
    "UNKNOWN": 0
  },
  "gate_c_require_all_pass": true
}
```

If evaluation fails or encounters errors:

```json
{
  "gate_c_pass": false,
  "gate_c_should_fail": true,
  "gate_c_counts": {
    "total": 12,
    "pass": 8,
    "note": 2,
    "todo": 2,
    "unknown": 0,
    "checked": 12,
    "unchecked": 0
  },
  "gate_c_counts_by_status": {
    "PASS": 8,
    "NOTE": 2,
    "TODO": 2,
    "UNKNOWN": 0
  },
  "gate_c_error": "Optional error message"
}
```

`gate_c_counts` summarises the totals in lowercase keys while `gate_c_counts_by_status`
preserves the raw uppercase categories reported by the evaluator. `checked` equals
`total - unknown`, so documented PASS/NOTE/TODO items are easy to track.

### MCP Integration

Gate C can be enabled via the MCP tool:

```bash
# Via MCP CLI with Gate C
noveler mcp call run_quality_checks '{
  "episode_number": 1,
  "file_path": "manuscript/EP001.txt",
  "enable_gate_c": true,
  "editorial_report": "reports/editorial_checklist.md"
}'
```

The response includes `gate_c_*` metadata fields for checklist status evaluation.

### Integration with CI

```bash
# Enable Gate C in CI wrapper
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root . \
  --file-path manuscript/EP001.txt \
  --enable-gate-c \
  --editorial-report reports/editorial_checklist.md
```

## Combined Workflow

The `bin/check-all` script runs both gates:

```bash
# Run complete quality gate workflow
bin/check-all --episode 1 --work サンプル作品 -- --project-root .

# Output:
# - Gate B: reports/quality.ndjson
# - Gate C: reports/editorial_checklist.md
# - Exit code: 0 if both pass, 2 if either fails
```

> Note: When running inside the 00_ガイド repository, the extra `-- --project-root .`
> flag keeps path resolution anchored to the current workspace instead of switching
> to a neighbouring sample project.

### Combined Metadata

When both gates are enabled, the response includes a unified `should_fail` flag:

```json
{
  "gate_b_pass": true,
  "gate_b_should_fail": false,
  "gate_c_pass": false,
  "gate_c_should_fail": true,
  "gate_c_counts": {
    "total": 12,
    "pass": 6,
    "note": 3,
    "todo": 3,
    "unknown": 0,
    "checked": 12,
    "unchecked": 0
  },
  "gate_c_counts_by_status": {
    "PASS": 6,
    "NOTE": 3,
    "TODO": 3,
    "UNKNOWN": 0
  },
  "should_fail": true
}
```

The `should_fail` flag is `true` if either Gate B or Gate C fails, allowing for simple CI/CD integration.

### Sample `bin/check-all` run

```bash
bin/check-all \
  --core-out temp/sample_quality.ndjson \
  --editorial-out temp/sample_editorial.md \
  --work サンプル作品 \
  --episode 1 \
  -- --project-root . \
  --file-path temp/EP001.txt
```

This produces NDJSON containing both summary metrics and individual findings:

```json
{"type": "summary_metrics", "details": {"aspect_scores": {"rhythm": 93.0, "readability": 100.0, "grammar": 100.0, "style": 100.0}}, "gate_b_pass": true, "gate_c_pass": true}
{"type": "dialogue_ratio_out_of_range", "severity": "medium", "reason_code": "DIALOGUE_RATIO_OUT_OF_RANGE", "gate_c_counts": {"total": 12, "pass": 12, "note": 0, "todo": 0, "unknown": 0, "checked": 12, "unchecked": 0}}
```

The accompanying checklist (`temp/sample_editorial.md`) shows every item marked as `Status: PASS`, so Gate C also passes and `should_fail` remains `false`.

### MCP Combined Example

```bash
# Run both gates via MCP
noveler mcp call run_quality_checks '{
  "episode_number": 1,
  "file_path": "manuscript/EP001.txt",
  "gate_thresholds": {
    "rhythm": 80,
    "readability": 80,
    "grammar": 90
  },
  "enable_gate_c": true,
  "editorial_report": "reports/editorial_checklist.md"
}'
```

### Exit Codes

- `0`: All gates passed
- `2`: One or more gates failed
- `3`: Execution error

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Quality Gates (CLI)
  run: |
    bin/check-all --episode ${{ env.EPISODE }} -- --project-root .
  continue-on-error: false  # Fail build on gate failure

- name: Run Quality Gates (MCP)
  run: |
    RESULT=$(noveler mcp call run_quality_checks '{
      "episode_number": ${{ env.EPISODE }},
      "file_path": "manuscript/EP${{ env.EPISODE }}.txt",
      "gate_thresholds": {"rhythm": 80, "readability": 80, "grammar": 90},
      "enable_gate_c": true
    }')

    # Check should_fail metadata
    SHOULD_FAIL=$(echo "$RESULT" | jq -r '.metadata.should_fail // false')
    if [ "$SHOULD_FAIL" = "true" ]; then
      echo "Quality gates failed"
      exit 2
    fi
```

### Local Development

```bash
# Dry run to see commands
bin/check-all --dry-run

# Run with custom outputs
bin/check-all \
  --core-out temp/gate_b.ndjson \
  --editorial-out temp/gate_c.md \
  -- --project-root .
```

## Troubleshooting

### Gate B Failures

Check specific aspect scores:
```bash
jq '.gate_b_evaluation' reports/quality.ndjson
```

Common issues:
- Rhythm: Long/short sentence runs
- Readability: Complex sentences, difficult vocabulary
- Grammar: Punctuation errors, typos

### Gate C Failures

Review checklist status:
```bash
grep "Status:" reports/editorial_checklist.md | sort | uniq -c
```

Address TODO/NOTE items before gate passes.

## Customization

### Adjusting Thresholds

1. Edit `config/quality/gate_defaults.yaml`
2. Test with sample manuscripts
3. Document rationale for threshold changes

### Selective Gate Execution

```bash
# Gate B only
bin/check-core

# Gate C only
bin/check-editorial-checklist

# Both with Gate C optional
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root . \
  --file-path manuscript/EP001.txt \
  $([ "$ENABLE_GATE_C" = "true" ] && echo "--enable-gate-c")
```

## Best Practices

1. **Run gates early and often** during development
2. **Fix Gate B issues first** (automated checks)
3. **Review Gate C manually** for context-specific items
4. **Document exemptions** when overriding gate failures
5. **Monitor trends** to adjust thresholds appropriately

## Related Documentation

- [Quality Check Tools](../tools/quality_checks.md)
- [Editorial 12-step Checklist](../tools/editorial_checklist.md)
- [CI/CD Configuration](../ci/configuration.md)
