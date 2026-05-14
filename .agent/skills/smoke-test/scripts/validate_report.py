#!/usr/bin/env python3
"""Validate a smoke-test report JSON against the expected schema."""

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_KEYS = {"version", "generated_at", "triggered_by", "duration_ms", "summary", "checks"}
REQUIRED_SUMMARY_KEYS = {"total", "passed", "failed", "skipped"}
REQUIRED_CHECK_KEYS = {"name", "status", "duration_ms"}
VALID_STATUSES = {"pass", "fail", "skip"}


def validate_summary(summary: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return ["'summary' must be a dict"]
    for key in REQUIRED_SUMMARY_KEYS:
        if key not in summary:
            errors.append(f"'summary' is missing key: '{key}'")
        elif not isinstance(summary[key], int):
            errors.append(f"'summary.{key}' must be an integer")
    return errors


def validate_check(check: Any, index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(check, dict):
        return [f"checks[{index}] must be a dict"]
    for key in REQUIRED_CHECK_KEYS:
        if key not in check:
            errors.append(f"checks[{index}] is missing key: '{key}'")
    status = check.get("status")
    if status is not None and status not in VALID_STATUSES:
        errors.append(f"checks[{index}].status '{status}' is not one of {sorted(VALID_STATUSES)}")
    duration = check.get("duration_ms")
    if duration is not None and not isinstance(duration, (int, float)):
        errors.append(f"checks[{index}].duration_ms must be numeric")
    return errors


def validate_report(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Report root must be a JSON object"]
    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    for key in sorted(missing):
        errors.append(f"Missing top-level key: '{key}'")
    if "summary" in data:
        errors.extend(validate_summary(data["summary"]))
    if "checks" in data:
        if not isinstance(data["checks"], list):
            errors.append("'checks' must be a list")
        else:
            for i, check in enumerate(data["checks"]):
                errors.extend(validate_check(check, i))
    return errors


def parse_args() -> Path:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <report.json>", file=sys.stderr)
        sys.exit(2)
    return Path(sys.argv[1])


def main() -> int:
    report_path = parse_args()
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: File not found: {report_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON — {exc}", file=sys.stderr)
        return 2

    errors = validate_report(data)
    if errors:
        print(f"Report validation FAILED ({len(errors)} error(s)):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Report validation PASSED: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
