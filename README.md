# Engine V6 COMPLETE - Final Version

## Project Structure
```
Engine_V6_COMPLETE/
├── engine_v6/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── collector.py              # Binance aggTrades downloader
│       ├── volume_bars.py            # Dynamic Volume Bars
│       ├── real_cvd.py               # True CVD from tick data
│       ├── microstructure.py         # Tick velocity + OFI analysis
│       ├── energy.py                 # Energy Field (probability model)
│       ├── strategy.py               # Original strategy (for reference)
│       └── sniper_strategy.py        # V9.1 Final Strategy (LATEST)
├── data/                             # Data storage
├── reports/                          # Test reports
├── tests/                            # Test scripts
└── requirements.txt
```

## Installation
```bash
pip install -r requirements.txt
```

## Quick Start
```python
from engine_v6.core.collector import download_daily
from engine_v6.core.volume_bars import DynamicVolumeBarBuilder
from engine_v6.core.real_cvd import RealCVDAnalyzer
from engine_v6.core.microstructure import MicrostructureAnalyzer
from engine_v6.core.energy import EnergyField
from engine_v6.core.sniper_strategy import SniperStrategy

# Download data
trades = download_daily('BTCUSDT', 2026, 6, 15)

# Build Volume Bars
builder = DynamicVolumeBarBuilder(min_volume=2.0, max_volume=100.0, percentile=50.0)
bars = builder.process_ticks(trades, progress_every=-1)
vbars = builder.to_dataframe(bars)

# Analysis
cvd = RealCVDAnalyzer(vbars)
micro = MicrostructureAnalyzer(trades, vbars)
ef = EnergyField(vbars, cvd, micro)

# Strategy V9.1
strategy = SniperStrategy(ef, vbars, balance=109.0, risk_pct=0.01, max_open=2, max_trades_per_day=8)

# Backtest
n = len(vbars)
for i in range(50, n - 1):
    strategy.process_pending(i)
    strategy.manage_trades(i)
    if len(strategy.open_trades) + len(strategy.pending_trades) < 2:
        plan = strategy.generate_signal(i)
        if plan:
            strategy.add_pending(plan)

# Close open trades
for t in list(strategy.open_trades):
    strategy._close_trade(t, n-1, vbars['close'].iloc[n-1], 'END')

# Results
print(f'Trades: {len(strategy.closed_trades)}')
print(f'Wins: {sum(1 for t in strategy.closed_trades if t.realized_pnl > 0)}')
print(f'PnL: ${sum(t.realized_pnl for t in strategy.closed_trades):+.2f}')
```

## Strategy V9.1 Features
- ✅ Liquidity Sweep Detection
- ✅ Bullish Reversal Patterns
- ✅ BSL Targets (Liquidity Pools)
- ✅ Risk:Reward minimum 1.5:1
- ✅ Max 8 trades/day
- ✅ No Fraud - 0 violations
- ✅ Perfect Accounting

## Test Results (June 2026)
- 7 trades in 30 days
- -$3.18 PnL (-2.92%)
- 0% Win Rate
- 0 Fraud ✅

## Anti-Fraud Verification
All trades verified:
- Exit Price ≤ Max Market Price ✅
- Stop ≤ Current Low ✅
- No Lookahead Bias ✅
- Discrepancy = $0 ✅
