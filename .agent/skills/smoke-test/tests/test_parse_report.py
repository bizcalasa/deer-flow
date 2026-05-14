"""Unit tests for parse_report.py helpers."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import parse_report as pr


SAMPLE_REPORT = {
    "suite": "deer-flow-smoke-test",
    "mode": "local",
    "timestamp": "2024-01-15T10:00:00Z",
    "summary": {"total": 3, "pass": 2, "fail": 1},
    "results": [
        {"name": "env_check", "status": "pass", "duration_ms": 120, "output": ""},
        {"name": "docker_check", "status": "pass", "duration_ms": 340, "output": ""},
        {"name": "frontend_check", "status": "fail", "duration_ms": 890, "output": "npm not found"},
    ],
}


def test_format_duration_ms():
    assert pr.format_duration(500) == "500ms"


def test_format_duration_seconds():
    assert pr.format_duration(1500) == "1.50s"


def test_load_report(tmp_path):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(SAMPLE_REPORT))
    loaded = pr.load_report(str(report_file))
    assert loaded["suite"] == "deer-flow-smoke-test"
    assert loaded["summary"]["total"] == 3


def test_print_report_no_exception(capsys):
    pr.print_report(SAMPLE_REPORT)
    captured = capsys.readouterr()
    assert "deer-flow-smoke-test" in captured.out
    assert "env_check" in captured.out
    assert "FAILED" in captured.out


def test_main_returns_nonzero_on_failure(tmp_path, monkeypatch):
    report_file = tmp_path / "smoke_test_20240115_100000.json"
    report_file.write_text(json.dumps(SAMPLE_REPORT))
    monkeypatch.setattr(sys, "argv", ["parse_report.py", str(report_file)])
    result = pr.main()
    assert result == 1


def test_main_returns_zero_on_all_pass(tmp_path, monkeypatch):
    passing = dict(SAMPLE_REPORT)
    passing["summary"] = {"total": 2, "pass": 2, "fail": 0}
    passing["results"] = [
        {"name": "env_check", "status": "pass", "duration_ms": 100, "output": ""},
        {"name": "docker_check", "status": "pass", "duration_ms": 200, "output": ""},
    ]
    report_file = tmp_path / "smoke_test_pass.json"
    report_file.write_text(json.dumps(passing))
    monkeypatch.setattr(sys, "argv", ["parse_report.py", str(report_file)])
    result = pr.main()
    assert result == 0
