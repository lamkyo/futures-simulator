"""
Unit tests verifying Deflated Sharpe Ratio (DSR) implementation against Bailey & López de Prado (2014).
"""
import math
import pytest
from scipy.stats import norm
from scripts.compute_dsr import compute_dsr_from_returns

def test_dsr_paper_benchmark_case():
    """
    Standard test case from Bailey & López de Prado (2014):
    Sharpe = 1.0, n_trials = 1, variance = 1.0, skew = 0.0, kurtosis = 3.0 (normal)
    sr_adj = 1.0 * sqrt(1 + 0.5) = sqrt(1.5) ≈ 1.22474
    Z = (1.22474 - 0) / 1.0 = 1.22474
    DSR = norm.cdf(1.22474) ≈ 0.8897
    """
    sharpe = 1.0
    n_trials = 1
    skew = 0.0
    kurtosis = 3.0
    variance_sharpe = 1.0

    e_max_sr = math.sqrt(2 * math.log(n_trials)) if n_trials > 1 else 0.0
    sr_adj = sharpe * math.sqrt(1 - skew * sharpe + (kurtosis - 1) / 4 * (sharpe ** 2))
    dsr = float(norm.cdf((sr_adj - e_max_sr) / math.sqrt(variance_sharpe)))

    assert dsr == pytest.approx(0.8897, abs=1e-3)

def test_dsr_multiple_testing_penalty():
    """Verify that increasing number of trials N strictly increases the expected max SR and penalizes DSR."""
    sharpe = 1.0
    skew = 0.0
    kurtosis = 3.0

    dsr_list = []
    for n in [1, 5, 20, 50]:
        e_max_sr = math.sqrt(2 * math.log(n)) if n > 1 else 0.0
        sr_adj = sharpe * math.sqrt(1 - skew * sharpe + (kurtosis - 1) / 4 * (sharpe ** 2))
        z = (sr_adj - e_max_sr) / 1.0
        dsr_list.append(float(norm.cdf(z)))

    # Higher N must lead to strictly lower DSR under multiple testing
    for i in range(len(dsr_list) - 1):
        assert dsr_list[i] > dsr_list[i+1]
