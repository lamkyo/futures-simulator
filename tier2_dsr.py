#!/usr/bin/env python3
"""
Tier 2.1: Deflated Sharpe Ratio (DSR) Calculator
Based on Bailey & López de Prado (2014):
'The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality'
"""
import math
import numpy as np
from scipy.stats import norm

def compute_dsr_user_spec(
    sharpe: float,
    skew: float,
    kurt: float,
    n_trials: int = 36
) -> dict:
    """Computes DSR using the exact code snippet provided in User Tier 2.1 spec."""
    e_max_sr = np.sqrt(2 * np.log(n_trials))
    sr_adj_inner = 1 - skew * sharpe + (kurt - 1) / 4 * (sharpe ** 2)
    sr_adj = sharpe * np.sqrt(max(0.0, sr_adj_inner))
    z_score = (sr_adj - e_max_sr) / 1.0
    dsr = float(norm.cdf(z_score))
    return {
        "formula": "User Spec (denom=1.0)",
        "observed_sharpe": sharpe,
        "n_trials": n_trials,
        "e_max_sr": round(float(e_max_sr), 4),
        "sr_adj": round(float(sr_adj), 4),
        "z_score": round(float(z_score), 4),
        "dsr": round(dsr, 6),
        "pass_0_95": dsr >= 0.95
    }

def compute_dsr_lopez_de_prado_full(
    sharpe_annual: float,
    skew: float,
    kurt: float,
    t_years: float = 4.0,
    n_trials: int = 36,
    sr_trial_variance: float = 0.25  # variance of Sharpe across trials
) -> dict:
    """
    Full Bailey & López de Prado (2014) Deflated Sharpe Ratio.
    Takes into account:
    - Sample length T
    - Empirical variance across trials (sigma_SR)
    - Euler-Mascheroni constant
    """
    euler_mascheroni = 0.5772156649
    # Expected max SR under null (Bailey & de Prado 2014, Eq 8)
    if n_trials > 1:
        log_n = math.log(n_trials)
        e_max_z = math.sqrt(2 * log_n) * (1 - euler_mascheroni / (2 * log_n)) + (euler_mascheroni / math.sqrt(2 * log_n))
    else:
        e_max_z = 0.0

    # Benchmark SR_0 = E[max] * std(SR_trials)
    sr_zero = e_max_z * math.sqrt(sr_trial_variance)

    # Standard error of Sharpe ratio with non-normality adjustment
    # SE(SR) = sqrt((1 - skew*SR + (kurt-1)/4 * SR^2) / T)
    sr_var = (1 - skew * sharpe_annual + (kurt - 1) / 4 * (sharpe_annual ** 2)) / t_years
    se_sr = math.sqrt(max(1e-8, sr_var))

    z_score = (sharpe_annual - sr_zero) / se_sr
    dsr = float(norm.cdf(z_score))

    return {
        "formula": "Full López de Prado (2014) with T and var_SR",
        "observed_sharpe": sharpe_annual,
        "t_years": t_years,
        "n_trials": n_trials,
        "sr_zero_benchmark": round(sr_zero, 4),
        "se_sr": round(se_sr, 4),
        "z_score": round(z_score, 4),
        "dsr": round(dsr, 6),
        "pass_0_95": dsr >= 0.95
    }

if __name__ == "__main__":
    # Parameters for SOL H2 candidate
    # 4 years (2022-2025), Observed Sharpe ~ 0.65, N=36 trials
    # Typical daily/hourly crypto trend returns: skew ~ -0.2 to -0.6, kurtosis ~ 4.5 to 7.0
    test_cases = [
        {"sharpe": 0.65, "skew": -0.2, "kurt": 5.0, "label": "SOL H2 Baseline (Sharpe 0.65)"},
        {"sharpe": 0.65, "skew": 0.0, "kurt": 3.0, "label": "SOL H2 Normal Distribution (Skew=0, Kurt=3)"},
        {"sharpe": 1.20, "skew": -0.3, "kurt": 4.5, "label": "High Sharpe Strategy (Sharpe 1.20)"},
        {"sharpe": 2.00, "skew": -0.2, "kurt": 4.0, "label": "Exceptional Edge (Sharpe 2.00)"},
    ]

    print("=" * 75)
    print("🔬 TIER 2.1: DEFLATED SHARPE RATIO (DSR) AUDIT")
    print("=" * 75)

    for case in test_cases:
        print(f"\n--- Scenario: {case['label']} ---")
        res_spec = compute_dsr_user_spec(case["sharpe"], case["skew"], case["kurt"], n_trials=36)
        print(f"1. [User Spec Code]:")
        print(f"   Observed SR: {res_spec['observed_sharpe']} | E[max]: {res_spec['e_max_sr']} | SR_adj: {res_spec['sr_adj']}")
        print(f"   Z-Score: {res_spec['z_score']} | DSR: {res_spec['dsr']:.6f} | PASS (>=0.95): {res_spec['pass_0_95']}")

        res_full = compute_dsr_lopez_de_prado_full(case["sharpe"], case["skew"], case["kurt"], t_years=4.0, n_trials=36)
        print(f"2. [Full López de Prado 2014]:")
        print(f"   SR_0 Benchmark: {res_full['sr_zero_benchmark']} | SE(SR): {res_full['se_sr']}")
        print(f"   Z-Score: {res_full['z_score']} | DSR: {res_full['dsr']:.6f} | PASS (>=0.95): {res_full['pass_0_95']}")

    print("\n" + "=" * 75)
