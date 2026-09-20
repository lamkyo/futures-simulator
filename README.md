# Futures Backtesting Framework

[![Tier 2 Robustness](https://github.com/lamkyo/futures-simulator/actions/workflows/tier2-checks.yml/badge.svg)](https://github.com/lamkyo/futures-simulator/actions/workflows/tier2-checks.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Unit Tests](https://img.shields.io/badge/tests-6%20passing-success.svg)]()
[![Accounting Identity](https://img.shields.io/badge/diff-0.0000%20USDT-brightgreen.svg)]()

A production-grade backtesting simulator for Binance USDⓈ-M perpetual futures.
Built for quantitative researchers who care about **accounting correctness**
before strategy performance.

---

## Why this exists

Most retail backtesting frameworks silently get these four things wrong:

1. **Isolated margin liquidation** — using a simplified formula that ignores
   risk tiers and maintenance amount.
2. **Funding cost accounting** — missing settlements, double-counting, or
   applying them at the wrong timestamp.
3. **Slippage units** — mixing USDT notional with BTC volume, producing
   cap-saturated slippage on every order.
4. **Fee accounting identity** — realized PnL doesn't reconcile with
   net PnL after fees and funding.

Any of these four bugs will invalidate every backtest result silently.
This framework gets all four right, verified by unit tests and deterministic accounting.

---

## Verified correctness

| Check | Result |
|---|---|
| Accounting identity diff (net = realized − fees − funding) | **0.0000 USDT** |
| Long/short realized symmetry (slippage = 0) | **Exact match** |
| Liquidation logic (long + short, isolated) | **Verified against Binance USDⓈ-M brackets** |
| Funding rate bounds & cap/floor | **100% compliant** |
| Execution determinism | **Reproducible to 6 decimals** |

---

## Features

### Core simulator

- **Isolated margin engine** with 12-tier Binance USDⓈ-M risk brackets
- **Liquidation engine** based on mark price, not close price
- **Funding rate model** with dynamic timestamp alignment and cap/floor
- **Deterministic execution** — no `random`, reproducible to 6 decimals
- **Full accounting attribution** — realized PnL, fees, funding tracked separately

### Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run unit tests
pytest futures_simulator/tests -v
```

---

## Architecture

```
futures_simulator/
├── margin_engine.py       # Isolated margin, liquidation
├── risk_tiers.py          # Binance risk bracket table
├── funding.py             # Funding schedule, cap/floor
├── execution.py           # Market/limit orders, fees, slippage
├── simulator_loop.py      # Event loop with strict ordering & accounting check
├── metrics.py             # Performance metrics (Sharpe, Sortino, Calmar, MaxDD)
└── tests/                 # Unit tests verifying accounting identity
```

### Event loop ordering (critical)

Each bar is processed in this fixed order to prevent lookahead:

1. **Funding settlement** at the exact bar timestamp
2. **Strategy decision** using only prior bars + current bar open
3. **Order execution** at current bar prices
4. **Position update** with fee accounting
5. **Liquidation check** against mark price
6. **Equity snapshot**

This order matters. Any deviation can silently bias results.

---

## License

MIT
