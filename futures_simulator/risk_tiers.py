"""
Binance USDⓈ-M Risk Bracket / Maintenance Margin Tiers for BTCUSDT Perpetual.
"""
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class RiskTier:
    tier: int
    notional_floor: float
    notional_cap: float
    max_leverage: int
    maint_margin_rate: float
    maint_amount: float  # Cumulated maintenance amount

# 12-tier Binance USDⓈ-M risk brackets for BTCUSDT
BTC_RISK_TIERS: List[RiskTier] = [
    RiskTier(1, 0.0, 50_000.0, 125, 0.0040, 0.0),
    RiskTier(2, 50_000.0, 250_000.0, 100, 0.0050, 50.0),
    RiskTier(3, 250_000.0, 1_000_000.0, 50, 0.0100, 1_300.0),
    RiskTier(4, 1_000_000.0, 5_000_000.0, 20, 0.0250, 16_300.0),
    RiskTier(5, 5_000_000.0, 10_000_000.0, 10, 0.0500, 141_300.0),
    RiskTier(6, 10_000_000.0, 20_000_000.0, 5, 0.1000, 641_300.0),
    RiskTier(7, 20_000_000.0, 50_000_000.0, 4, 0.1250, 1_141_300.0),
    RiskTier(8, 50_000_000.0, 100_000_000.0, 3, 0.1500, 2_391_300.0),
    RiskTier(9, 100_000_000.0, 200_000_000.0, 2, 0.2500, 12_391_300.0),
    RiskTier(10, 200_000_000.0, 300_000_000.0, 1, 0.5000, 62_391_300.0),
]

def get_risk_tier(notional: float, tiers: List[RiskTier] = BTC_RISK_TIERS) -> RiskTier:
    """Find the applicable risk tier for a given position notional."""
    abs_notional = abs(notional)
    for tier in tiers:
        if tier.notional_floor <= abs_notional <= tier.notional_cap:
            return tier
    return tiers[-1]
