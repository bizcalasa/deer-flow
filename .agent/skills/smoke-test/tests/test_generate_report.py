"""Tests for generate_report.py."""

import json
import os
import tempfile

import pytest

from scripts.generate_report import (
    build_check_result,
    build_report,
    write_report,
    main,
    REPORT_VERSION,
)


# ---------------------------------------------------------------------------
# build_check_result
# ---------------------------------------------------------------------------

def test_build_check_result_minimal():
    result = build_check_result("my_check", "pass", 42)
    assert result["name"] == "my_check"
    assert result["status"] == "pass"
    assert result["duration_ms"] == 42
    assert "message" not in result
    assert "details" not in result


def test_build_check_result_with_message_and_details():
    result = build_check_result("net_check", "fail", 100,
                                message="timeout", details=["step1", "step2"])
    assert result["message"] == "timeout"
    assert result["details"] == ["step1", "step2"]


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_all_pass():
    checks = [
        build_check_result("a", "pass", 10),
        build_check_result("b", "pass", 20),
    ]
    report = build_report(checks, environment="ci")
    assert report["overall"] == "pass"
    assert report["summary"]["passed"] == 2
    assert report["summary"]["failed"] == 0
    assert report["summary"]["total_duration_ms"] == 30
    assert report["version"] == REPORT_VERSION
    assert report["environment"] == "ci"


def test_build_report_with_failure():
    checks = [
        build_check_result("a", "pass", 5),
        build_check_result("b", "fail", 15),
        build_check_result("c", "skip", 0),
    ]
    report = build_report(checks)
    assert report["overall"] == "fail"
    assert report["summary"]["failed"] == 1
    assert report["summary"]["skipped"] == 1
    assert report["summary"]["total"] == 3


def test_build_report_triggered_by():
    report = build_report([], triggered_by="github-actions")
    assert report["triggered_by"] == "github-actions"


def test_build_report_no_triggered_by():
    report = build_report([])
    assert "triggered_by" not in report


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------

def test_write_report_creates_file():
    report = build_report([], environment="test")
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "sub", "report.json")
        write_report(report, out)
        assert os.path.isfile(out)
        with open(out) as fh:
            loaded = json.load(fh)
        assert loaded["environment"] == "test"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_returns_zero_on_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "report.json")
        rc = main(["--env", "unit-test", "--output", out])
    assert rc == 0


def test_main_writes_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "report.json")
        main(["--output", out, "--triggered-by", "pytest"])
        with open(out) as fh:
            data = json.load(fh)
        assert data["triggered_by"] == "pytest"
        assert "timestamp" in data
