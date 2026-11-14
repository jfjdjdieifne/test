#!/usr/bin/env python3
"""
Full Month Test - 30 Days Backtest
Tests the Sniper Strategy V9.1 on a full month
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

def test_full_month(year=2026, month=6, start_balance=109.0):
    """Test strategy on a full month (30 days)"""
    print('='*80)
    print(f'🎯 SNIPER V9.1 - Full Month Test ({year}-{month:02d})')
    print('='*80)
    
    results = []
    balance = start_balance
    
    for day in range(1, 31):
        print(f'\n--- Day {day}/30 ---')
        
        # Download data
        trades = download_daily('BTCUSDT', year, month, day)
        if trades.empty:
            print(f'  ❌ No data for day {day}')
            continue
        
        # Build Volume Bars
        builder = DynamicVolumeBarBuilder(min_volume=2.0, max_volume=100.0, percentile=50.0)
        bars = builder.process_ticks(trades, progress_every=-1)
        vbars = builder.to_dataframe(bars)
        
        if len(bars) < 100:
            print(f'  ❌ Insufficient bars for day {day}')
            continue
        
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
        
        balance = strategy.balance
        wins = sum(1 for t in strategy.closed_trades if t.realized_pnl > 0)
        losses = sum(1 for t in strategy.closed_trades if t.realized_pnl < 0)
        total_pnl = sum(t.realized_pnl for t in strategy.closed_trades)
        violations = strategy.verify_all_trades()
        
        results.append({
            'day': day,
            'trades': len(strategy.closed_trades),
            'wins': wins,
            'losses': losses,
            'pnl': total_pnl,
            'balance': balance,
            'violations': violations['total'],
        })
        
        if len(strategy.closed_trades) > 0:
            win_rate = wins / len(strategy.closed_trades) * 100
            print(f'  ✅ {len(strategy.closed_trades):2d} trades | {wins:2d}W {losses:2d}L ({win_rate:5.1f}%) | PnL ${total_pnl:+7.2f} | Bal ${balance:.2f}')
        else:
            print(f'  ⚠️  No trades on day {day}')
    
    # Final results
    print()
    print('='*80)
    print('📊 FINAL RESULTS')
    print('='*80)
    
    total_trades = sum(r['trades'] for r in results)
    total_wins = sum(r['wins'] for r in results)
    total_losses = sum(r['losses'] for r in results)
    total_pnl = sum(r['pnl'] for r in results)
    total_violations = sum(r['violations'] for r in results)
    
    win_rate = total_wins / max(total_trades, 1) * 100
    
    print(f'\n📈 Performance:')
    print(f'  Starting Balance: ${start_balance:.2f}')
    print(f'  Final Balance: ${balance:.2f}')
    print(f'  Total PnL: ${total_pnl:+.2f}')
    print(f'  Return: {(balance/start_balance-1)*100:+.2f}%')
    print()
    print(f'📊 Trades:')
    print(f'  Total: {total_trades}')
    print(f'  Wins: {total_wins} ({win_rate:.1f}%)')
    print(f'  Losses: {total_losses} ({100-win_rate:.1f}%)')
    print()
    print(f'🔒 Fraud Detection:')
    print(f'  Total Violations: {total_violations}')
    if total_violations == 0:
        print(f'  ✅ NO FRAUD DETECTED - All trades are legitimate!')
    else:
        print(f'  ❌ FRAUD DETECTED - {total_violations} violations found')
    
    return results

if __name__ == '__main__':
    test_full_month()
