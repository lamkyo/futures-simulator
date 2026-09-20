"""
Funding Rate Schedule, Cap/Floor, and Settlement Accounting.
"""

DEFAULT_FUNDING_CAP = 0.0075    # +0.75%
DEFAULT_FUNDING_FLOOR = -0.0075  # -0.75%

def clamp_funding_rate(rate: float, cap: float = DEFAULT_FUNDING_CAP, floor: float = DEFAULT_FUNDING_FLOOR) -> float:
    """Clamps funding rate within exchange bounds."""
    return max(floor, min(cap, rate))

def calculate_funding_payment(position_size: float, mark_price: float, funding_rate: float) -> float:
    """
    Computes funding payment in USDT.
    Positive result means position pays funding (deducted from balance).
    Negative result means position receives funding (added to balance).

    Formula:
    Payment = PositionSize * MarkPrice * ClampedFundingRate
    Long (size > 0) with rate > 0 => pays (+)
    Short (size < 0) with rate > 0 => receives (-)
    """
    clamped_rate = clamp_funding_rate(funding_rate)
    return position_size * mark_price * clamped_rate
