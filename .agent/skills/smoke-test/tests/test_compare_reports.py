"""Tests for compare_reports.py."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from compare_reports import load_report, index_checks, compare


SAMPLE_REPORT_A = {
    "report": {
        "summary": {
            "total": 3,
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "duration_ms": 1200,
        },
        "checks": [
            {"name": "api_health", "status": "pass", "duration_ms": 300},
            {"name": "db_connection", "status": "fail", "duration_ms": 500, "message": "timeout"},
            {"name": "frontend_load", "status": "pass", "duration_ms": 400},
        ],
    }
}

SAMPLE_REPORT_B = {
    "report": {
        "summary": {
            "total": 3,
            "passed": 3,
            "failed": 0,
            "skipped": 0,
            "duration_ms": 1100,
        },
        "checks": [
            {"name": "api_health", "status": "pass", "duration_ms": 280},
            {"name": "db_connection", "status": "pass", "duration_ms": 420},
            {"name": "frontend_load", "status": "pass", "duration_ms": 400},
        ],
    }
}


def write_temp_report(data):
    """Write a report dict to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(data, f)
    f.close()
    return f.name


def test_load_report_returns_dict():
    path = write_temp_report(SAMPLE_REPORT_A)
    try:
        result = load_report(path)
        assert isinstance(result, dict)
        assert "report" in result
    finally:
        os.unlink(path)


def test_load_report_missing_file_raises():
    with pytest.raises((FileNotFoundError, OSError)):
        load_report("/nonexistent/path/report.json")


def test_index_checks_by_name():
    checks = SAMPLE_REPORT_A["report"]["checks"]
    indexed = index_checks(checks)
    assert "api_health" in indexed
    assert "db_connection" in indexed
    assert "frontend_load" in indexed
    assert indexed["api_health"]["status"] == "pass"


def test_index_checks_empty_list():
    indexed = index_checks([])
    assert indexed == {}


def test_compare_detects_fixed_check():
    """A check that was failing in A but passing in B should appear as fixed."""
    result = compare(SAMPLE_REPORT_A, SAMPLE_REPORT_B)
    fixed = [c for c in result.get("fixed", []) if c["name"] == "db_connection"]
    assert len(fixed) == 1


def test_compare_detects_no_regressions_when_all_improve():
    result = compare(SAMPLE_REPORT_A, SAMPLE_REPORT_B)
    assert result.get("regressed", []) == []


def test_compare_detects_regression():
    """A check passing in A but failing in B should appear as regressed."""
    result = compare(SAMPLE_REPORT_B, SAMPLE_REPORT_A)
    regressed = [c for c in result.get("regressed", []) if c["name"] == "db_connection"]
    assert len(regressed) == 1


def test_compare_stable_checks():
    """Checks with the same status in both reports should be in stable."""
    result = compare(SAMPLE_REPORT_A, SAMPLE_REPORT_B)
    stable_names = [c["name"] for c in result.get("stable", [])]
    assert "api_health" in stable_names
    assert "frontend_load" in stable_names


def test_compare_new_check_in_b():
    """A check present only in B should appear in new_checks."""
    report_b_extra = json.loads(json.dumps(SAMPLE_REPORT_B))
    report_b_extra["report"]["checks"].append(
        {"name": "cache_health", "status": "pass", "duration_ms": 50}
    )
    result = compare(SAMPLE_REPORT_A, report_b_extra)
    new_names = [c["name"] for c in result.get("new_checks", [])]
    assert "cache_health" in new_names


def test_compare_removed_check():
    """A check present only in A should appear in removed_checks."""
    result = compare(SAMPLE_REPORT_B, SAMPLE_REPORT_A)
    # db_connection exists in both, nothing removed in this pair
    # Use a modified report where a check is absent
    report_a_extra = json.loads(json.dumps(SAMPLE_REPORT_A))
    report_a_extra["report"]["checks"].append(
        {"name": "legacy_check", "status": "pass", "duration_ms": 10}
    )
    result2 = compare(report_a_extra, SAMPLE_REPORT_B)
    removed_names = [c["name"] for c in result2.get("removed_checks", [])]
    assert "legacy_check" in removed_names
