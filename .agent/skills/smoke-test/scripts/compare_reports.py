#!/usr/bin/env python3
"""Compare two smoke-test reports and highlight regressions or improvements.

Usage:
    python compare_reports.py <baseline_report.json> <current_report.json>

Exit codes:
    0 - no regressions detected
    1 - one or more regressions detected (previously passing check now fails)
    2 - usage / file error
"""

import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_report(path: str) -> dict[str, Any]:
    """Load and return a report JSON file."""
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(2)
    with p.open() as fh:
        return json.load(fh)


def index_checks(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a dict keyed by check name for quick look-up."""
    return {c["name"]: c for c in report.get("checks", [])}


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def compare(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare baseline vs current report.

    Returns a result dict with keys:
        regressions  – checks that went from 'pass' to 'fail'
        improvements – checks that went from 'fail' to 'pass'
        new_failures – checks that are new and failing
        new_passes   – checks that are new and passing
        unchanged    – checks whose status did not change
    """
    base_idx = index_checks(baseline)
    curr_idx = index_checks(current)

    all_names = set(base_idx) | set(curr_idx)

    result: dict[str, list] = {
        "regressions": [],
        "improvements": [],
        "new_failures": [],
        "new_passes": [],
        "unchanged": [],
    }

    for name in sorted(all_names):
        in_base = name in base_idx
        in_curr = name in curr_idx

        if in_base and in_curr:
            base_status = base_idx[name].get("status")
            curr_status = curr_idx[name].get("status")
            if base_status == "pass" and curr_status == "fail":
                result["regressions"].append(name)
            elif base_status == "fail" and curr_status == "pass":
                result["improvements"].append(name)
            else:
                result["unchanged"].append(name)
        elif in_curr and not in_base:
            curr_status = curr_idx[name].get("status")
            if curr_status == "fail":
                result["new_failures"].append(name)
            else:
                result["new_passes"].append(name)
        # checks only in baseline are silently ignored (removed checks)

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_comparison(diff: dict[str, list]) -> None:
    """Print a human-readable summary of the comparison."""
    sections = [
        ("regressions",  "🔴 Regressions (pass → fail)"),
        ("improvements", "🟢 Improvements (fail → pass)"),
        ("new_failures", "🟠 New failures"),
        ("new_passes",   "🔵 New passes"),
        ("unchanged",    "⚪ Unchanged"),
    ]

    print("=" * 60)
    print("Smoke-test report comparison")
    print("=" * 60)

    for key, label in sections:
        items = diff.get(key, [])
        print(f"\n{label} ({len(items)}):")
        if items:
            for name in items:
                print(f"  - {name}")
        else:
            print("  (none)")

    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> tuple[str, str]:
    """Parse positional CLI arguments."""
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <baseline_report.json> <current_report.json>",
            file=sys.stderr,
        )
        sys.exit(2)
    return sys.argv[1], sys.argv[2]


def main() -> int:
    baseline_path, current_path = parse_args()

    baseline = load_report(baseline_path)
    current = load_report(current_path)

    diff = compare(baseline, current)
    print_comparison(diff)

    if diff["regressions"] or diff["new_failures"]:
        print("Result: REGRESSIONS DETECTED", file=sys.stderr)
        return 1

    print("Result: no regressions detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
