#!/usr/bin/env python3
"""Generate a structured JSON smoke-test report from shell check outputs."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


REPORT_VERSION = "1.0"


def build_check_result(
    name: str,
    status: str,
    duration_ms: int,
    message: Optional[str] = None,
    details: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a single check result entry."""
    result: Dict[str, Any] = {
        "name": name,
        "status": status,  # "pass" | "fail" | "skip"
        "duration_ms": duration_ms,
    }
    if message:
        result["message"] = message
    if details:
        result["details"] = details
    return result


def build_report(
    checks: List[Dict[str, Any]],
    environment: str = "local",
    triggered_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble the full report structure."""
    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    skipped = sum(1 for c in checks if c["status"] == "skip")
    total_ms = sum(c.get("duration_ms", 0) for c in checks)
    overall = "pass" if failed == 0 else "fail"

    report: Dict[str, Any] = {
        "version": REPORT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "overall": overall,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total_duration_ms": total_ms,
        },
        "checks": checks,
    }
    if triggered_by:
        report["triggered_by"] = triggered_by
    return report


def write_report(report: Dict[str, Any], output_path: str) -> None:
    """Write the report to a JSON file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"Report written to: {output_path}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a smoke-test JSON report.")
    parser.add_argument("--env", default="local", help="Environment name (default: local)")
    parser.add_argument("--output", default=".agent/skills/smoke-test/reports/report.json",
                        help="Output file path")
    parser.add_argument("--triggered-by", default=None, help="Who/what triggered the run")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    # Minimal self-contained demo: one synthetic passing check
    checks = [
        build_check_result("report_generator_self_check", "pass", 1,
                           message="generate_report.py loaded successfully")
    ]
    report = build_report(checks, environment=args.env, triggered_by=args.triggered_by)
    write_report(report, args.output)
    return 0 if report["overall"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
