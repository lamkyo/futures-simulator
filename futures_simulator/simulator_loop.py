"""
Core Simulation Loop with Strict Event Ordering and Accounting Identity Verification.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .margin_engine import calculate_liquidation_price, check_liquidation
from .funding import calculate_funding_payment
from .execution import calculate_slippage, calculate_fee, Order, OrderSide
from .risk_tiers import get_risk_tier

@dataclass
class Bar:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    mark_price: float
    funding_rate: float = 0.0
    is_funding_bar: bool = False

@dataclass
class Position:
    size: float = 0.0              # Base asset units (positive=long, negative=short)
    entry_price: float = 0.0
    allocated_margin: float = 0.0
    leverage: float = 1.0

    @property
    def is_open(self) -> bool:
        return abs(self.size) > 1e-8

@dataclass
class Account:
    initial_balance: float
    cash_balance: float
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    total_funding: float = 0.0
    liquidation_count: int = 0

    def equity(self, mark_price: float, position: Position) -> float:
        unrealized = position.size * (mark_price - position.entry_price) if position.is_open else 0.0
        return self.cash_balance + position.allocated_margin + unrealized

class Simulator:
    def __init__(self, initial_balance: float, leverage: float = 2.0):
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.account = Account(
            initial_balance=initial_balance,
            cash_balance=initial_balance
        )
        self.position = Position(leverage=leverage)
        self.equity_curve: List[float] = [initial_balance]
        self.returns: List[float] = []
        self.trades: List[Dict[str, Any]] = []

    def verify_accounting_identity(self) -> float:
        """
        Accounting Identity Check:
        net_pnl = realized_pnl - total_fees - total_funding
        Reconciles exactly with (current_cash + allocated_margin - initial_balance) when no open position.
        Returns the absolute difference.
        """
        net_pnl = self.account.realized_pnl - self.account.total_fees - self.account.total_funding
        balance_delta = (self.account.cash_balance + self.position.allocated_margin) - self.account.initial_balance
        return abs(net_pnl - balance_delta)

    def close_position(self, exit_price: float, fee_rate: float = 0.0005) -> float:
        """Closes the currently active position."""
        if not self.position.is_open:
            return 0.0

        pnl = self.position.size * (exit_price - self.position.entry_price)
        exit_notional = abs(self.position.size * exit_price)
        exit_fee = calculate_fee(exit_notional, taker_fee=fee_rate)

        # Update account
        self.account.realized_pnl += pnl
        self.account.total_fees += exit_fee
        self.account.cash_balance += (self.position.allocated_margin + pnl - exit_fee)

        self.trades.append({
            "entry_price": self.position.entry_price,
            "exit_price": exit_price,
            "size": self.position.size,
            "pnl": pnl,
            "fee": exit_fee
        })

        # Reset position
        self.position.size = 0.0
        self.position.entry_price = 0.0
        self.position.allocated_margin = 0.0
        return pnl

    def open_position(self, side: OrderSide, notional_usd: float, entry_price: float, fee_rate: float = 0.0005):
        """Opens a new isolated margin position."""
        if self.position.is_open:
            return

        margin_needed = notional_usd / self.leverage
        entry_fee = calculate_fee(notional_usd, taker_fee=fee_rate)

        if self.account.cash_balance < (margin_needed + entry_fee):
            return  # Insufficient funds

        self.account.cash_balance -= (margin_needed + entry_fee)
        self.account.total_fees += entry_fee

        size = (notional_usd / entry_price) * (1.0 if side == OrderSide.BUY else -1.0)
        self.position.size = size
        self.position.entry_price = entry_price
        self.position.allocated_margin = margin_needed

    def step(self, bar: Bar, desired_order: Optional[Order] = None):
        """
        Executes a single bar in the strict deterministic order:
        1. Funding settlement at bar timestamp
        2. Strategy decision / Order execution
        3. Position update with fee accounting
        4. Liquidation check against mark price
        5. Equity snapshot
        """
        # Step 1: Funding settlement
        if bar.is_funding_bar and self.position.is_open:
            funding_pmt = calculate_funding_payment(self.position.size, bar.mark_price, bar.funding_rate)
            self.account.total_funding += funding_pmt
            self.account.cash_balance -= funding_pmt

        # Step 2 & 3: Order execution
        if desired_order is not None:
            exec_price = calculate_slippage(bar.open, desired_order.size, bar.volume)
            if desired_order.side == OrderSide.BUY:
                if self.position.size < 0:
                    self.close_position(exec_price)
                if desired_order.size > 0:
                    notional = desired_order.size * exec_price
                    self.open_position(OrderSide.BUY, notional, exec_price)
            elif desired_order.side == OrderSide.SELL:
                if self.position.size > 0:
                    self.close_position(exec_price)
                if desired_order.size > 0:
                    notional = desired_order.size * exec_price
                    self.open_position(OrderSide.SELL, notional, exec_price)

        # Step 4 & 5: Liquidation check against mark price
        if self.position.is_open:
            liq_price = calculate_liquidation_price(
                self.position.entry_price,
                self.position.size,
                self.position.allocated_margin
            )
            if check_liquidation(bar.mark_price, self.position.size, liq_price):
                # Liquidated: margin is lost to insurance fund
                self.account.liquidation_count += 1
                self.account.realized_pnl -= self.position.allocated_margin
                self.trades.append({
                    "entry_price": self.position.entry_price,
                    "exit_price": liq_price,
                    "size": self.position.size,
                    "pnl": -self.position.allocated_margin,
                    "liquidated": True
                })
                self.position.size = 0.0
                self.position.allocated_margin = 0.0

        # Step 6: Equity snapshot & Returns calculation
        current_eq = self.account.equity(bar.close, self.position)
        prev_eq = self.equity_curve[-1]
        ret = (current_eq - prev_eq) / prev_eq if prev_eq > 0 else 0.0

        self.equity_curve.append(current_eq)
        self.returns.append(ret)
