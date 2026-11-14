#!/usr/bin/env python3
"""
Test Script - Single Day Backtest
Tests the Sniper Strategy V9.1 on a single day
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine_v6.core.collector import download_daily
from engine_v6.core.volume_bars import DynamicVolumeBarBuilder
from engine_v6.core.real_cvd import RealCVDAnalyzer
from engine_v6.core.microstructure import MicrostructureAnalyzer
from engine_v6.core.energy import EnergyField
from engine_v6.core.sniper_strategy import SniperStrategy

def test_single_day(year=2026, month=6, day=15, balance=109.0):
    """Test strategy on a single day"""
    print('='*80)
    print(f'🎯 Testing Sniper Strategy V9.1 - {year}-{month:02d}-{day:02d}')
    print('='*80)
    
    # Download data
    print(f'\n📥 Downloading BTCUSDT data...')
    trades = download_daily('BTCUSDT', year, month, day)
    if trades.empty:
        print('❌ No data available')
        return None
    
    print(f'✅ Loaded {len(trades):,} trades')
    
    # Build Volume Bars
    print(f'\n📊 Building Volume Bars...')
    builder = DynamicVolumeBarBuilder(min_volume=2.0, max_volume=100.0, percentile=50.0)
    bars = builder.process_ticks(trades, progress_every=-1)
    vbars = builder.to_dataframe(bars)
    print(f'✅ Built {len(bars)} volume bars')
    
    # Analysis
    print(f'\n🔬 Analyzing market structure...')
    cvd = RealCVDAnalyzer(vbars)
    micro = MicrostructureAnalyzer(trades, vbars)
    ef = EnergyField(vbars, cvd, micro)
    print(f'✅ Analysis complete')
    
    # Strategy
    print(f'\n🎯 Running Sniper Strategy V9.1...')
    strategy = SniperStrategy(ef, vbars, balance=balance, risk_pct=0.01, max_open=2, max_trades_per_day=8)
    
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
    print(f'\n📊 Results:')
    print(f'  Trades: {len(strategy.closed_trades)}')
    print(f'  Wins: {sum(1 for t in strategy.closed_trades if t.realized_pnl > 0)}')
    print(f'  Losses: {sum(1 for t in strategy.closed_trades if t.realized_pnl < 0)}')
    print(f'  PnL: ${sum(t.realized_pnl for t in strategy.closed_trades):+.2f}')
    print(f'  Balance: ${strategy.balance:.2f}')
    
    # Trade details
    if strategy.closed_trades:
        print(f'\n🔍 Trade Details:')
        for t in strategy.closed_trades:
            win_loss = "WIN" if t.realized_pnl > 0 else "LOSS"
            print(f'  [{win_loss}] Entry ${t.entry_price:.2f} → Exit ${t.exit_price:.2f} ({t.exit_reason}) | PnL ${t.realized_pnl:+.4f}')
    
    # Fraud check
    violations = strategy.verify_all_trades()
    print(f'\n🔒 Fraud Verification:')
    print(f'  Violations: {violations["total"]}')
    if violations["total"] == 0:
        print(f'  ✅ NO FRAUD DETECTED - All trades are legitimate!')
    else:
        print(f'  ❌ FRAUD DETECTED - {violations["total"]} violations found')
    
    print(f'\n✅ Test complete')
    
    return strategy

if __name__ == '__main__':
    test_single_day()
