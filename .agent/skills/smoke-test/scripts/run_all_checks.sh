#!/usr/bin/env bash
# run_all_checks.sh — Orchestrates all smoke-test checks and aggregates results

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/../reports"
REPORT_FILE="${REPORT_DIR}/smoke_test_$(date +%Y%m%d_%H%M%S).json"
MODE="${1:-local}"  # local | docker

mkdir -p "${REPORT_DIR}"

PASS=0
FAIL=0
RESULTS=[]

run_check() {
  local name="$1"
  local script="$2"
  local start end duration status
  start=$(date +%s%N)
  if bash "${script}" > /tmp/smoke_out.txt 2>&1; then
    status="pass"
    ((PASS++)) || true
  else
    status="fail"
    ((FAIL++)) || true
  fi
  end=$(date +%s%N)
  duration=$(( (end - start) / 1000000 ))
  local output
  output=$(cat /tmp/smoke_out.txt | sed 's/"/\"/g' | tr '\n' ' ')
  echo "  [${status^^}] ${name} (${duration}ms)"
  RESULTS+="{\"name\":\"${name}\",\"status\":\"${status}\",\"duration_ms\":${duration},\"output\":\"${output}\"},"
}

echo "=== DeerFlow Smoke Test Suite ==="
echo "Mode: ${MODE}"
echo "Started: $(date)"
echo ""

run_check "env_check"       "${SCRIPT_DIR}/check_local_env.sh"
run_check "docker_check"    "${SCRIPT_DIR}/check_docker.sh"
run_check "frontend_check"  "${SCRIPT_DIR}/frontend_check.sh"

if [[ "${MODE}" == "docker" ]]; then
  run_check "deploy_docker" "${SCRIPT_DIR}/deploy_docker.sh"
else
  run_check "deploy_local"  "${SCRIPT_DIR}/deploy_local.sh"
fi

RESULTS="[${RESULTS%,}]"
TOTAL=$((PASS + FAIL))

cat > "${REPORT_FILE}" <<EOF
{
  "suite": "deer-flow-smoke-test",
  "mode": "${MODE}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "summary": {"total": ${TOTAL}, "pass": ${PASS}, "fail": ${FAIL}},
  "results": ${RESULTS}
}
EOF

echo ""
echo "=== Summary: ${PASS}/${TOTAL} passed ==="
echo "Report saved: ${REPORT_FILE}"

[[ "${FAIL}" -eq 0 ]] || exit 1
