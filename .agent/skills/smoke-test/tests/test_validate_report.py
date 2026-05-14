"""Tests for validate_report.py"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate_report import validate_report, validate_summary, validate_check  # noqa: E402


MINIMAL_VALID_REPORT = {
    "version": "1.0",
    "generated_at": "2024-01-01T00:00:00Z",
    "triggered_by": "ci",
    "duration_ms": 1234,
    "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
    "checks": [{"name": "health", "status": "pass", "duration_ms": 100}],
}


def test_valid_report_has_no_errors():
    assert validate_report(MINIMAL_VALID_REPORT) == []


def test_missing_top_level_key():
    data = {k: v for k, v in MINIMAL_VALID_REPORT.items() if k != "version"}
    errors = validate_report(data)
    assert any("version" in e for e in errors)


def test_report_root_not_dict():
    errors = validate_report(["not", "a", "dict"])
    assert errors == ["Report root must be a JSON object"]


def test_summary_missing_key():
    errors = validate_summary({"total": 1, "passed": 1, "failed": 0})
    assert any("skipped" in e for e in errors)


def test_summary_non_integer_value():
    errors = validate_summary({"total": "one", "passed": 1, "failed": 0, "skipped": 0})
    assert any("total" in e for e in errors)


def test_summary_not_dict():
    errors = validate_summary("bad")
    assert errors == ["'summary' must be a dict"]


def test_check_missing_key():
    errors = validate_check({"name": "x", "duration_ms": 10}, index=0)
    assert any("status" in e for e in errors)


def test_check_invalid_status():
    errors = validate_check({"name": "x", "status": "unknown", "duration_ms": 10}, index=0)
    assert any("unknown" in e for e in errors)


def test_check_valid_statuses():
    for status in ("pass", "fail", "skip"):
        errors = validate_check({"name": "x", "status": status, "duration_ms": 10}, index=0)
        assert errors == [], f"Expected no errors for status '{status}'"


def test_check_non_numeric_duration():
    errors = validate_check({"name": "x", "status": "pass", "duration_ms": "fast"}, index=2)
    assert any("duration_ms" in e for e in errors)


def test_checks_not_list():
    data = {**MINIMAL_VALID_REPORT, "checks": "not-a-list"}
    errors = validate_report(data)
    assert any("list" in e for e in errors)


def test_main_valid_report(tmp_path: Path):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(MINIMAL_VALID_REPORT), encoding="utf-8")
    sys.argv = ["validate_report.py", str(report_file)]
    from validate_report import main  # noqa: PLC0415
    assert main() == 0


def test_main_invalid_report(tmp_path: Path):
    bad = {k: v for k, v in MINIMAL_VALID_REPORT.items() if k != "version"}
    report_file = tmp_path / "bad_report.json"
    report_file.write_text(json.dumps(bad), encoding="utf-8")
    sys.argv = ["validate_report.py", str(report_file)]
    from validate_report import main  # noqa: PLC0415
    assert main() == 1
