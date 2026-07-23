#!/usr/bin/env python3
"""
Analysis Script - Detailed Trade Analysis
Analyzes winning and losing trades in detail
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_v6.core.collector import download_daily
from engine_v6.core.volume_bars import DynamicVolumeBarBuilder
from engine_v6.core.real_cvd import RealCVDAnalyzer
from engine_v6.core.microstructure import MicrostructureAnalyzer
from engine_v6.core.energy import EnergyField
from engine_v6.core.sniper_strategy import SniperStrategy

def analyze_trades(year=2026, month=6, day=15, balance=109.0):
    """Analyze trades in detail"""
    print('='*80)
    print(f'🔍 DETAILED TRADE ANALYSIS - {year}-{month:02d}-{day:02d}')
    print('='*80)
    
    # Download data
    trades = download_daily('BTCUSDT', year, month, day)
    if trades.empty:
        print('❌ No data available')
        return
    
    # Build Volume Bars
    builder = DynamicVolumeBarBuilder(min_volume=2.0, max_volume=100.0, percentile=50.0)
    bars = builder.process_ticks(trades, progress_every=-1)
    vbars = builder.to_dataframe(bars)
    
    # Analysis
    cvd = RealCVDAnalyzer(vbars)
    micro = MicrostructureAnalyzer(trades, vbars)
    ef = EnergyField(vbars, cvd, micro)
    
    # Strategy
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
    
    # Statistics
    print(f'\n📊 Statistics:')
    print(f'  Total Trades: {len(strategy.closed_trades)}')
    print(f'  Wins: {sum(1 for t in strategy.closed_trades if t.realized_pnl > 0)}')
    print(f'  Losses: {sum(1 for t in strategy.closed_trades if t.realized_pnl < 0)}')
    print(f'  Win Rate: {sum(1 for t in strategy.closed_trades if t.realized_pnl > 0) / max(len(strategy.closed_trades), 1) * 100:.1f}%')
    
    # Winning trades
    print(f'\n🏆 WINNING TRADES:')
    winning_trades = [t for t in strategy.closed_trades if t.realized_pnl > 0]
    for idx, t in enumerate(winning_trades, 1):
        print(f'\n  WIN #{idx} (Plan {t.plan_id}):')
        print(f'    Entry: ${t.entry_price:.2f} @ Bar {t.entry_bar}')
        print(f'    Exit: ${t.exit_price:.2f} @ Bar {t.exit_bar}')
        print(f'    Reason: {t.exit_reason}')
        print(f'    Bars Held: {t.bars_held}')
        print(f'    MFE: ${t.mfe:.2f} (Max Favorable)')
        print(f'    MAE: ${t.mae:.2f} (Max Adverse)')
        print(f'    PnL: ${t.realized_pnl:+.4f}')
        print(f'    RR: {t.risk_reward:.1f}')
    
    # Losing trades
    print(f'\n💀 LOSING TRADES:')
    losing_trades = [t for t in strategy.closed_trades if t.realized_pnl < 0]
    for idx, t in enumerate(losing_trades, 1):
        print(f'\n  LOSS #{idx} (Plan {t.plan_id}):')
        print(f'    Entry: ${t.entry_price:.2f} @ Bar {t.entry_bar}')
        print(f'    Exit: ${t.exit_price:.2f} @ Bar {t.exit_bar}')
        print(f'    Reason: {t.exit_reason}')
        print(f'    Bars Held: {t.bars_held}')
        print(f'    MFE: ${t.mfe:.2f} (Max Favorable)')
        print(f'    MAE: ${t.mae:.2f} (Max Adverse)')
        print(f'    PnL: ${t.realized_pnl:+.4f}')
        
        # Problem analysis
        if t.exit_reason == 'STOP':
            if t.mfe < t.initial_risk:
                print(f'    ❌ PROBLEM: Never reached profit target!')
            else:
                print(f'    ⚠️  PROBLEM: Hit profit but gave back!')
        elif t.exit_reason == 'TIMEOUT':
            print(f'    ❌ PROBLEM: Timed out before reaching target!')
    
    # Exit reasons
    print(f'\n📋 EXIT REASONS:')
    exit_reasons = {}
    for t in strategy.closed_trades:
        reason = t.exit_reason
        if reason not in exit_reasons:
            exit_reasons[reason] = {'count': 0, 'pnl': 0}
        exit_reasons[reason]['count'] += 1
        exit_reasons[reason]['pnl'] += t.realized_pnl
    
    for reason, data in exit_reasons.items():
        print(f'  {reason}: {data["count"]} trades | PnL ${data["pnl"]:+.2f}')
    
    # Fraud check
    violations = strategy.verify_all_trades()
    print(f'\n🔒 Fraud Verification:')
    print(f'  Violations: {violations["total"]}')
    if violations["total"] == 0:
        print(f'  ✅ NO FRAUD DETECTED - All trades are legitimate!')
    else:
        print(f'  ❌ FRAUD DETECTED - {violations["total"]} violations found')
        for v in strategy.fraud_violations:
            print(f'    ❌ {v["type"]}: {v}')
    
    print(f'\n✅ Analysis complete')

if __name__ == '__main__':
    analyze_trades()
