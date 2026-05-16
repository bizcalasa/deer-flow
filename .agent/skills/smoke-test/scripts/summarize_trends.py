#!/usr/bin/env python3
"""Summarize trends across multiple smoke-test reports.

Reads a directory of JSON reports (or an explicit list) and prints a
table showing how each check has changed over time: pass-rate, last
status, and whether the check is newly failing or newly passing.

Usage:
    python summarize_trends.py --reports-dir reports/
    python summarize_trends.py report1.json report2.json report3.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_report(path: str) -> Optional[dict]:
    """Load a single JSON report; return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[warn] Could not load {path}: {exc}", file=sys.stderr)
        return None


def collect_report_paths(reports_dir: str) -> List[str]:
    """Return all *.json files inside *reports_dir*, sorted by name."""
    base = Path(reports_dir)
    if not base.is_dir():
        raise FileNotFoundError(f"Reports directory not found: {reports_dir}")
    paths = sorted(str(p) for p in base.glob("*.json"))
    return paths


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------

def build_trends(reports: List[dict]) -> Dict[str, dict]:
    """Build a per-check trend summary from an ordered list of reports.

    Returns a dict keyed by check name::

        {
            "check_name": {
                "history": ["pass", "fail", "pass"],  # oldest → newest
                "pass_count": 2,
                "fail_count": 1,
                "last_status": "pass",
                "trend": "stable" | "improving" | "degrading" | "flaky",
            },
            ...
        }
    """
    trends: Dict[str, dict] = {}

    for report in reports:
        checks = report.get("checks", [])
        for check in checks:
            name = check.get("name", "<unknown>")
            status = check.get("status", "unknown").lower()
            if name not in trends:
                trends[name] = {"history": [], "pass_count": 0, "fail_count": 0}
            trends[name]["history"].append(status)
            if status == "pass":
                trends[name]["pass_count"] += 1
            elif status == "fail":
                trends[name]["fail_count"] += 1

    for name, data in trends.items():
        history = data["history"]
        data["last_status"] = history[-1] if history else "unknown"
        data["trend"] = _classify_trend(history)

    return trends


def _classify_trend(history: List[str]) -> str:
    """Classify a check's trend based on its status history."""
    if len(history) < 2:
        return "stable"

    passes = [s == "pass" for s in history]
    # All same
    if all(passes):
        return "stable"
    if not any(passes):
        return "stable"

    # Last half better than first half?
    mid = len(passes) // 2
    first_rate = sum(passes[:mid]) / max(mid, 1)
    second_rate = sum(passes[mid:]) / max(len(passes) - mid, 1)

    if second_rate > first_rate + 0.2:
        return "improving"
    if second_rate < first_rate - 0.2:
        return "degrading"
    return "flaky"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

TREND_ICONS = {
    "stable": "─",
    "improving": "↑",
    "degrading": "↓",
    "flaky": "~",
}


def print_trends(trends: Dict[str, dict], total_reports: int) -> int:
    """Print a formatted trends table.  Returns 1 if any check is failing."""
    if not trends:
        print("No check data found in the provided reports.")
        return 0

    name_w = max(len(n) for n in trends) + 2
    header = f"{'Check':<{name_w}}  {'Last':<6}  {'Pass':>5}  {'Fail':>5}  Trend"
    print(header)
    print("-" * len(header))

    any_failing = False
    for name, data in sorted(trends.items()):
        last = data["last_status"]
        icon = TREND_ICONS.get(data["trend"], "?")
        pass_rate = data["pass_count"] / total_reports * 100 if total_reports else 0
        marker = "  ← FAILING" if last == "fail" else ""
        print(
            f"{name:<{name_w}}  {last:<6}  {pass_rate:>4.0f}%  "
            f"{data['fail_count']:>5}  {icon} {data['trend']}{marker}"
        )
        if last == "fail":
            any_failing = True

    print()
    print(f"Reports analysed: {total_reports}")
    return 1 if any_failing else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Summarize smoke-test trends across multiple reports."
    )
    parser.add_argument(
        "report_files",
        nargs="*",
        metavar="REPORT",
        help="Explicit report JSON files to analyse.",
    )
    parser.add_argument(
        "--reports-dir",
        metavar="DIR",
        help="Directory to scan for *.json report files.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    paths: List[str] = list(args.report_files or [])

    if args.reports_dir:
        try:
            paths += collect_report_paths(args.reports_dir)
        except FileNotFoundError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2

    if not paths:
        print("[error] No report files specified. Use --reports-dir or pass files directly.", file=sys.stderr)
        return 2

    reports = [r for p in paths if (r := load_report(p)) is not None]
    if not reports:
        print("[error] No valid reports could be loaded.", file=sys.stderr)
        return 2

    trends = build_trends(reports)
    return print_trends(trends, total_reports=len(reports))


if __name__ == "__main__":
    sys.exit(main())
