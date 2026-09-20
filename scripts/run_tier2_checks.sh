#!/bin/bash
set -e

# Base directory
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3}"
REPORT_DIR="reports/tier2"
mkdir -p "$REPORT_DIR"

echo "=== Tier 2 Robustness Checks Pipeline — $(date) ==="

# 1. Deflated Sharpe Ratio (DSR) Check
echo "--> Running Deflated Sharpe Ratio (DSR)..."
$PYTHON_BIN scripts/compute_dsr.py \
    --n-trials 36 \
    --default-sharpe 0.65 \
    --output "$REPORT_DIR/dsr.json"

# 2. Aggregate Results & Evaluate Gates
echo "--> Aggregating Tier 2 verification gates..."
$PYTHON_BIN scripts/aggregate_tier2.py \
    --input-dir "$REPORT_DIR" \
    --output "$REPORT_DIR/summary.json"

echo "=== Tier 2 Run Completed. Summary written to $REPORT_DIR/summary.json ==="
