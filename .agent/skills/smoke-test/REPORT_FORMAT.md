# Smoke Test Report Format

All smoke-test runs produce a JSON report saved under `reports/`.

## File naming

```
reports/smoke_test_<YYYYMMDD_HHMMSS>.json
```

## Schema

```json
{
  "suite": "deer-flow-smoke-test",
  "mode": "local | docker",
  "timestamp": "<ISO-8601 UTC>",
  "summary": {
    "total": 4,
    "pass": 3,
    "fail": 1
  },
  "results": [
    {
      "name": "<check_name>",
      "status": "pass | fail | skip",
      "duration_ms": 120,
      "output": "<truncated stdout/stderr>"
    }
  ]
}
```

## Fields

| Field | Type | Description |
|---|---|---|
| `suite` | string | Always `deer-flow-smoke-test` |
| `mode` | string | Deployment mode used (`local` or `docker`) |
| `timestamp` | string | UTC ISO-8601 start time |
| `summary.total` | int | Total checks executed |
| `summary.pass` | int | Checks that exited 0 |
| `summary.fail` | int | Checks that exited non-zero |
| `results[].name` | string | Script identifier (no extension) |
| `results[].status` | string | `pass`, `fail`, or `skip` |
| `results[].duration_ms` | int | Wall-clock time in milliseconds |
| `results[].output` | string | Combined stdout+stderr, single-line |

## Viewing a report

```bash
# Latest report
python3 .agent/skills/smoke-test/scripts/parse_report.py

# Specific report
python3 .agent/skills/smoke-test/scripts/parse_report.py \
  .agent/skills/smoke-test/reports/smoke_test_20240115_120000.json
```

## CI integration

`run_all_checks.sh` exits with code `1` when any check fails, making it
suitable as a CI gate step.
