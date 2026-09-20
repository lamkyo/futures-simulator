#!/usr/bin/env python3
"""
Aggregate Tier 2 robustness results and produce summary report.
"""
import argparse
import json
from pathlib import Path

def aggregate(input_dir: str, output_file: str):
    in_path = Path(input_dir)
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": str(Path(input_dir).stat().st_mtime),
        "checks": {},
        "overall_verdict": "FAIL",
        "failed_gates": []
    }

    # 1. Check DSR
    dsr_file = in_path / "dsr.json"
    if dsr_file.exists():
        try:
            with open(dsr_file, "r") as f:
                dsr_data = json.load(f)
            passed = dsr_data.get("pass_criteria", False)
            summary["checks"]["dsr"] = {
                "metric": "Deflated Sharpe Ratio",
                "value": dsr_data.get("dsr"),
                "threshold": ">= 0.95",
                "passed": passed
            }
            if not passed:
                summary["failed_gates"].append(f"DSR failed: {dsr_data.get('dsr')} < 0.95")
        except Exception as e:
            summary["failed_gates"].append(f"DSR parse error: {e}")
    else:
        summary["failed_gates"].append("DSR check missing")

    # 2. Check Cost Stress
    stress_file = in_path / "stress_2025.json"
    if stress_file.exists():
        try:
            with open(stress_file, "r") as f:
                stress_data = json.load(f)
            passed = stress_data.get("passed_cost_stress", False)
            summary["checks"]["cost_stress"] = {
                "metric": "Cost Stress 2x & 3x",
                "passed": passed
            }
            if not passed:
                summary["failed_gates"].append("Cost stress multipliers failed to stay positive")
        except Exception:
            pass

    # 3. Check SMA variants
    sma_files = list(in_path.glob("sma_*.json"))
    if sma_files:
        sma_passed = True
        for sf in sma_files:
            try:
                with open(sf, "r") as f:
                    sdata = json.load(f)
                if sdata.get("net_profit", 0) <= 0:
                    sma_passed = False
            except Exception:
                sma_passed = False
        summary["checks"]["sma_variants"] = {
            "variants_tested": len(sma_files),
            "passed": sma_passed
        }
        if not sma_passed:
            summary["failed_gates"].append("Not all SMA parameter variants produced positive returns")

    # Final decision
    if len(summary["failed_gates"]) == 0 and len(summary["checks"]) > 0:
        summary["overall_verdict"] = "PASS"
    else:
        summary["overall_verdict"] = "FAIL"

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary generated: {out_path} => VERDICT: {summary['overall_verdict']}")
    if summary["failed_gates"]:
        print("Failed gates:")
        for gate in summary["failed_gates"]:
            print(f"  - {gate}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="reports/tier2")
    parser.add_argument("--output", default="reports/tier2/summary.json")
    args = parser.parse_args()
    aggregate(args.input_dir, args.output)
