"""
Unit tests verifying accounting identity, liquidation formulas, and deterministic execution.
"""
import pytest
from futures_simulator.simulator_loop import Simulator, Bar
from futures_simulator.execution import Order, OrderSide
from futures_simulator.margin_engine import calculate_liquidation_price, check_liquidation
from futures_simulator.funding import calculate_funding_payment, clamp_funding_rate

def test_accounting_identity_roundtrip():
    """Verify net_pnl = realized_pnl - total_fees - total_funding diff is exactly 0.0000 USDT."""
    sim = Simulator(initial_balance=10_000.0, leverage=5.0)

    # 1. Open Long position
    bar1 = Bar(
        timestamp=1609459200000,
        open=50_000.0, high=51_000.0, low=49_500.0, close=50_500.0,
        volume=1000.0, mark_price=50_500.0
    )
    # Buy 0.2 BTC = $10,000 notional at $50k (Margin = $2000)
    order = Order(side=OrderSide.BUY, size=0.2)
    sim.step(bar1, desired_order=order)

    # 2. Funding bar settlement
    bar2 = Bar(
        timestamp=1609488000000,
        open=50_500.0, high=51_000.0, low=50_000.0, close=50_800.0,
        volume=500.0, mark_price=50_800.0,
        funding_rate=0.0001,  # 0.01%
        is_funding_bar=True
    )
    sim.step(bar2)

    # 3. Close position at $52,000
    bar3 = Bar(
        timestamp=1609516800000,
        open=52_000.0, high=52_500.0, low=51_800.0, close=52_000.0,
        volume=500.0, mark_price=52_000.0
    )
    order_close = Order(side=OrderSide.SELL, size=0.0)
    sim.step(bar3, desired_order=order_close)

    # Core check: Identity holds to 0.000000 USDT
    diff = sim.verify_accounting_identity()
    assert diff == pytest.approx(0.0, abs=1e-6), f"Accounting identity violation: diff={diff}"
    assert sim.account.total_fees > 0
    assert sim.account.total_funding > 0
    assert sim.account.realized_pnl > 390.0

def test_long_short_symmetry():
    """Verify long and short produce exact mirrored realized PnL when slippage=0."""
    entry = 50_000.0
    delta = 2_000.0
    size = 0.2  # $10,000 notional

    # Long: 50k -> 52k (+2k)
    long_sim = Simulator(initial_balance=10_000.0, leverage=5.0)
    long_sim.open_position(OrderSide.BUY, notional_usd=size * entry, entry_price=entry)
    long_pnl = long_sim.close_position(exit_price=entry + delta)

    # Short: 50k -> 48k (+2k)
    short_sim = Simulator(initial_balance=10_000.0, leverage=5.0)
    short_sim.open_position(OrderSide.SELL, notional_usd=size * entry, entry_price=entry)
    short_pnl = short_sim.close_position(exit_price=entry - delta)

    assert long_pnl == pytest.approx(short_pnl, abs=1e-6)
    assert long_pnl == pytest.approx(400.0, abs=1e-6)

def test_isolated_margin_liquidation_formulas():
    """Verify exact liquidation price for Binance USDⓈ-M risk tier 1."""
    entry = 50_000.0
    size = 0.5  # 0.5 BTC = 25,000 notional (Tier 1: MMR = 0.40% = 0.004, CumMaint = 0)
    margin = 2_500.0  # 10x leverage

    # Long Liq Price = (50000 - 2500 / 0.5) / (1 - 0.004) = (50000 - 5000) / 0.996 = 45180.72289
    long_liq = calculate_liquidation_price(entry, size, margin)
    assert long_liq == pytest.approx(45180.72289, abs=1e-3)
    assert check_liquidation(mark_price=45180.0, position_size=size, liquidation_price=long_liq) is True
    assert check_liquidation(mark_price=45200.0, position_size=size, liquidation_price=long_liq) is False

    # Short Liq Price = (50000 + 2500 / 0.5) / (1 + 0.004) = 55000 / 1.004 = 54780.87649
    short_liq = calculate_liquidation_price(entry, -size, margin)
    assert short_liq == pytest.approx(54780.87649, abs=1e-3)
    assert check_liquidation(mark_price=54800.0, position_size=-size, liquidation_price=short_liq) is True
    assert check_liquidation(mark_price=54700.0, position_size=-size, liquidation_price=short_liq) is False

def test_funding_cap_and_settlement():
    """Verify funding rate bounds and payment calculation."""
    assert clamp_funding_rate(0.015) == 0.0075
    assert clamp_funding_rate(-0.02) == -0.0075
    assert clamp_funding_rate(0.0003) == 0.0003

    # Long pays when funding is positive
    pay_long = calculate_funding_payment(position_size=1.0, mark_price=60_000.0, funding_rate=0.0001)
    assert pay_long == 6.0  # 1.0 * 60000 * 0.0001

    # Short receives (negative payment) when funding is positive
    pay_short = calculate_funding_payment(position_size=-1.0, mark_price=60_000.0, funding_rate=0.0001)
    assert pay_short == -6.0
