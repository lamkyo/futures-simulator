"""
Isolated Margin & Liquidation Engine for Binance USDⓈ-M Futures.
Implements exact maintenance margin rate (MMR) and cumulated maintenance amount logic.
"""
from typing import Optional
from .risk_tiers import get_risk_tier, RiskTier

def calculate_maintenance_margin(notional: float, tier: Optional[RiskTier] = None) -> float:
    """Maintenance margin = Notional * MMR - Maintenance Amount"""
    abs_notional = abs(notional)
    if tier is None:
        tier = get_risk_tier(abs_notional)
    return max(0.0, abs_notional * tier.maint_margin_rate - tier.maint_amount)

def calculate_liquidation_price(
    entry_price: float,
    position_size: float,
    allocated_margin: float,
    tier: Optional[RiskTier] = None
) -> float:
    """
    Exact Binance USDⓈ-M Isolated Margin liquidation price.
    Formula:
    Long:  Liq = (EntryPrice - (Margin - CumMaint) / Size) / (1 - MMR)
    Short: Liq = (EntryPrice + (Margin - CumMaint) / Size) / (1 + MMR)
    """
    if position_size == 0:
        return 0.0

    notional = abs(position_size * entry_price)
    if tier is None:
        tier = get_risk_tier(notional)

    mmr = tier.maint_margin_rate
    cum_maint = tier.maint_amount
    abs_size = abs(position_size)

    if position_size > 0:  # Long
        numerator = entry_price - (allocated_margin - cum_maint) / abs_size
        denominator = 1.0 - mmr
        liq_price = numerator / denominator
        return max(0.0, liq_price)
    else:  # Short
        numerator = entry_price + (allocated_margin - cum_maint) / abs_size
        denominator = 1.0 + mmr
        liq_price = numerator / denominator
        return max(0.0, liq_price)

def check_liquidation(
    mark_price: float,
    position_size: float,
    liquidation_price: float
) -> bool:
    """Check if mark price triggers liquidation."""
    if position_size > 0:  # Long: liquidates when mark_price <= liq_price
        return mark_price <= liquidation_price
    elif position_size < 0:  # Short: liquidates when mark_price >= liq_price
        return mark_price >= liquidation_price
    return False
