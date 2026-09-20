"""
Performance & Risk Metrics Calculation for Futures Strategies.
"""
from typing import List, Dict, Any
import numpy as np

def calculate_drawdowns(equity_curve: List[float]) -> np.ndarray:
    """Calculates drawdown array from equity curve."""
    equities = np.array(equity_curve)
    peak = np.maximum.accumulate(equities)
    drawdowns = (equities - peak) / np.where(peak > 0, peak, 1.0)
    return drawdowns

def calculate_metrics(
    equity_curve: List[float],
    returns: List[float],
    trades: List[Dict[str, Any]],
    annualization_factor: float = 365 * 24  # hourly bars
) -> Dict[str, Any]:
    """Calculates quant metrics for evaluation."""
    if len(equity_curve) < 2 or len(returns) == 0:
        return {
            "sharpe": 0.0, "sortino": 0.0, "calmar": 0.0,
            "max_drawdown": 0.0, "win_rate": 0.0, "profit_factor": 0.0,
            "total_trades": len(trades)
        }

    rets = np.array(returns)
    drawdowns = calculate_drawdowns(equity_curve)
    max_dd = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

    mean_ret = float(np.mean(rets))
    std_ret = float(np.std(rets))

    # Sharpe Ratio
    sharpe = (mean_ret / std_ret * np.sqrt(annualization_factor)) if std_ret > 1e-9 else 0.0

    # Sortino Ratio (downside deviation only)
    downside_rets = rets[rets < 0]
    downside_std = float(np.std(downside_rets)) if len(downside_rets) > 0 else 0.0
    sortino = (mean_ret / downside_std * np.sqrt(annualization_factor)) if downside_std > 1e-9 else 0.0

    # Calmar Ratio
    total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
    calmar = (total_return / abs(max_dd)) if abs(max_dd) > 1e-6 else 0.0

    # Win rate & Profit factor
    wins = [t["pnl"] for t in trades if t.get("pnl", 0) > 0]
    losses = [abs(t["pnl"]) for t in trades if t.get("pnl", 0) < 0]
    win_rate = (len(wins) / len(trades)) if len(trades) > 0 else 0.0
    profit_factor = (sum(wins) / sum(losses)) if sum(losses) > 0 else (float("inf") if sum(wins) > 0 else 0.0)

    return {
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "calmar": round(calmar, 4),
        "max_drawdown": round(abs(max_dd) * 100, 2),  # in percent
        "win_rate": round(win_rate * 100, 2),        # in percent
        "profit_factor": round(profit_factor, 4),
        "total_trades": len(trades),
        "initial_equity": equity_curve[0],
        "final_equity": equity_curve[-1],
        "net_profit": round(equity_curve[-1] - equity_curve[0], 4)
    }
