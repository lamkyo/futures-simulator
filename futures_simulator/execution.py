"""
Execution Simulation, Fee Attribution, and Slippage Modeling.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

@dataclass
class Order:
    side: OrderSide
    size: float         # Base asset quantity (e.g., BTC)
    order_type: OrderType = OrderType.MARKET
    limit_price: float = 0.0

DEFAULT_TAKER_FEE = 0.0005  # 0.05%
DEFAULT_MAKER_FEE = 0.0002  # 0.02%

def calculate_slippage(
    price: float,
    size: float,
    bar_volume: float,
    slippage_factor: float = 0.1,
    max_slippage_bps: float = 20.0
) -> float:
    """
    Computes executed price after slippage.
    Crucial fix: Avoids unit mismatch between USDT notional and Base Asset Volume.
    Both are evaluated in Base units (BTC).
    """
    if bar_volume <= 0 or slippage_factor <= 0:
        return price

    # Participation rate in base asset units
    participation = min(1.0, abs(size) / bar_volume)
    slippage_bps = min(max_slippage_bps, participation * slippage_factor * 10_000)
    slippage_fraction = slippage_bps / 10_000

    if size > 0:  # Buying pushes price up
        return price * (1.0 + slippage_fraction)
    else:         # Selling pushes price down
        return price * (1.0 - slippage_fraction)

def calculate_fee(notional: float, is_maker: bool = False, taker_fee: float = DEFAULT_TAKER_FEE, maker_fee: float = DEFAULT_MAKER_FEE) -> float:
    """Trading fee in USDT: Notional * FeeRate"""
    rate = maker_fee if is_maker else taker_fee
    return abs(notional) * rate
