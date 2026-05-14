#!/usr/bin/env python3
"""parse_report.py — Parse and pretty-print a smoke-test JSON report."""

import json
import sys
from pathlib import Path
from datetime import datetime


STATUS_ICONS = {"pass": "✅", "fail": "❌", "skip": "⏭️"}


def load_report(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def format_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.2f}s"


def print_report(report: dict) -> None:
    suite = report.get("suite", "unknown")
    mode = report.get("mode", "unknown")
    ts = report.get("timestamp", "")
    summary = report.get("summary", {})
    results = report.get("results", [])

    print(f"\n{'='*50}")
    print(f"  Smoke Test Report — {suite}")
    print(f"  Mode: {mode}  |  Time: {ts}")
    print(f"{'='*50}")

    for r in results:
        icon = STATUS_ICONS.get(r["status"], "?")
        dur = format_duration(r.get("duration_ms", 0))
        print(f"  {icon}  {r['name']:<25} {dur}")
        if r["status"] == "fail" and r.get("output"):
            snippet = r["output"][:120].strip()
            print(f"       └─ {snippet}")

    total = summary.get("total", 0)
    passed = summary.get("pass", 0)
    failed = summary.get("fail", 0)
    print(f"\n  Result: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  — ALL CLEAR")
    print(f"{'='*50}\n")


def main() -> int:
    if len(sys.argv) < 2:
        reports_dir = Path(__file__).parent.parent / "reports"
        candidates = sorted(reports_dir.glob("smoke_test_*.json"), reverse=True)
        if not candidates:
            print("No report files found.", file=sys.stderr)
            return 1
        path = str(candidates[0])
        print(f"Using latest report: {path}")
    else:
        path = sys.argv[1]

    report = load_report(path)
    print_report(report)
    return 0 if report.get("summary", {}).get("fail", 1) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
