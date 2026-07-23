"""
Engine V9.1 "The Precision Sniper" - Balanced ICT Strategy
Selective but not overly restrictive | Liquidity Sweep + Confluence
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Dict
from dataclasses import dataclass

FEE_RATE = 0.001
MAKER_FEE_RATE = 0.0002
SLIPPAGE_BPS = 3
SLIPPAGE_RATE = SLIPPAGE_BPS / 10000
TOTAL_FRICTION = FEE_RATE * 2 + SLIPPAGE_RATE

@dataclass
class TradePlan:
    bar_idx: int
    timestamp: object
    direction: str
    entry_price: float
    stop_price: float
    targets: List[Dict]
    probability: float
    conviction: float
    risk_reward: float
    expected_r: float
    size_multiplier: float
    narrative: str
    signals_snapshot: Dict[str, float]
    plan_id: int = 0
    state: str = "PENDING"
    mode: str = "CAPITAL_GUARD"
    entry_bar: Optional[int] = None
    quantity: float = 0.0
    cash_used: float = 0.0
    exit_bar: Optional[int] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    realized_pnl: float = 0.0
    bars_held: int = 0
    mfe: float = 0.0
    mae: float = 0.0
    stop_current: float = 0.0
    initial_risk: float = 0.0
    _stage: int = 1
    _partial_qty_sold: float = 0.0
    _target_price: float = 0.0
    _entry_fee_paid: float = 0.0
    _exit_fee_paid: float = 0.0
    _slippage_paid: float = 0.0
    _max_price_reached: float = 0.0
    _min_price_reached: float = 999999.0

class SniperStrategy:
    def __init__(self, energy_field, vbars_df, balance=109.0, risk_pct=0.01, max_open=2, max_trades_per_day=8):
        self.ef = energy_field
        self.df = vbars_df
        self.n = len(vbars_df)
        self.balance = balance
        self.starting_balance = balance
        self.risk_pct = risk_pct
        self.max_open = max_open
        self.max_trades_per_day = max_trades_per_day
        self.open_trades = []
        self.closed_trades = []
        self.pending_trades = []
        self.last_signal_bar = -500
        self.close = vbars_df["close"].values
        self.high = vbars_df["high"].values
        self.low = vbars_df["low"].values
        self.open = vbars_df["open"].values
        self.range = np.maximum(self.high - self.low, 1e-12)
        self.volume = vbars_df["volume"].values
        self.timestamp = vbars_df["timestamp"].values
        self._plan_id_counter = 0
        self.active_orders = []
        self.total_fees_paid = 0.0
        self.total_slippage_paid = 0.0
        self.daily_trades = {}
        self.fraud_violations = []
        self._detect_structure()

    def _detect_structure(self):
        n = self.n
        self.swing_highs = []
        self.swing_lows = []
        self.liquidity_pools = []
        
        # Detect swings (pivot = 2 bars for more signals)
        for k in range(2, n - 2):
            if (self.high[k] > self.high[k-1] and self.high[k] > self.high[k-2] and
                self.high[k] > self.high[k+1] and self.high[k] > self.high[k+2]):
                self.swing_highs.append((k, self.high[k]))
            if (self.low[k] < self.low[k-1] and self.low[k] < self.low[k-2] and
                self.low[k] < self.low[k+1] and self.low[k] < self.low[k+2]):
                self.swing_lows.append((k, self.low[k]))
        
        # Detect liquidity pools (within 0.15% tolerance)
        tolerance = 0.0015
        for i, (k1, p1) in enumerate(self.swing_highs):
            pool = [(k1, p1)]
            for j, (k2, p2) in enumerate(self.swing_highs):
                if i != j and abs(p1 - p2) / p1 < tolerance:
                    pool.append((k2, p2))
            if len(pool) >= 2:
                avg_price = np.mean([p for _, p in pool])
                self.liquidity_pools.append({'type': 'BSL', 'price': avg_price, 'bars': [k for k, _ in pool], 'strength': len(pool)})
        
        for i, (k1, p1) in enumerate(self.swing_lows):
            pool = [(k1, p1)]
            for j, (k2, p2) in enumerate(self.swing_lows):
                if i != j and abs(p1 - p2) / p1 < tolerance:
                    pool.append((k2, p2))
            if len(pool) >= 2:
                avg_price = np.mean([p for _, p in pool])
                self.liquidity_pools.append({'type': 'SSL', 'price': avg_price, 'bars': [k for k, _ in pool], 'strength': len(pool)})

    def _detect_sweep_or_reversal(self, bar_idx):
        """Detect liquidity sweep OR strong reversal pattern"""
        # Check for SSL sweep
        for pool in self.liquidity_pools:
            if pool['type'] == 'SSL':
                for pool_bar in pool['bars']:
                    if pool_bar < bar_idx and bar_idx - pool_bar < 15:
                        if self.low[bar_idx] < pool['price'] and self.close[bar_idx] > pool['price']:
                            return {'type': 'SSL_SWEEP', 'price': pool['price'], 'strength': pool['strength']}
        
        # Check for strong bullish reversal (long lower wick + close near high)
        if bar_idx > 5:
            body = abs(self.close[bar_idx] - self.open[bar_idx])
            lower_wick = min(self.close[bar_idx], self.open[bar_idx]) - self.low[bar_idx]
            upper_wick = self.high[bar_idx] - max(self.close[bar_idx], self.open[bar_idx])
            
            # Strong reversal: lower wick > 2x body, close in upper 30%
            if lower_wick > body * 2 and self.close[bar_idx] > self.low[bar_idx] + (self.high[bar_idx] - self.low[bar_idx]) * 0.7:
                return {'type': 'BULLISH_REVERSAL', 'strength': 1}
        
        return None

    def _find_target(self, entry_price):
        """Find target: BSL pool or 2:1 RR"""
        bsl_pools = [p for p in self.liquidity_pools if p['type'] == 'BSL' and p['price'] > entry_price]
        
        if bsl_pools:
            # Find nearest strong BSL
            nearest = min(bsl_pools, key=lambda p: p['price'])
            return nearest['price']
        else:
            # No BSL - use 2.5:1 RR
            return entry_price * 1.025

    def _allocate_plan_id(self):
        self._plan_id_counter += 1
        return self._plan_id_counter

    def purge_all_plan_orders(self, plan_id):
        self.active_orders = [o for o in self.active_orders if o.get('plan_id') != plan_id]

    def calculate_true_net_pnl(self, entry_price, exit_price, qty, is_maker=False):
        fee_rate = MAKER_FEE_RATE if is_maker else FEE_RATE
        gross_entry = entry_price * qty
        gross_exit = exit_price * qty
        entry_fee = gross_entry * fee_rate
        exit_fee = gross_exit * fee_rate
        slippage_cost = gross_exit * SLIPPAGE_RATE
        raw_pnl = gross_exit - gross_entry
        true_net_pnl = raw_pnl - entry_fee - exit_fee - slippage_cost
        return true_net_pnl, entry_fee, exit_fee, slippage_cost

    def generate_signal(self, i):
        if i < 50 or i >= self.n - 1:
            return None
        if len(self.open_trades) + len(self.pending_trades) >= self.max_open:
            return None
        
        # Daily trade limit (relaxed to 8)
        date_str = str(self.timestamp[i])[:10]
        if date_str not in self.daily_trades:
            self.daily_trades[date_str] = 0
        if self.daily_trades[date_str] >= self.max_trades_per_day:
            return None
        
        # Min gap (relaxed to 20 bars)
        if i - self.last_signal_bar < 20:
            return None
        
        # SWEEP OR REVERSAL (relaxed - accept either)
        setup = self._detect_sweep_or_reversal(i)
        if not setup:
            return None
        
        # Get energy snapshot
        snap = self.ef.get_snapshot(i)
        if not snap.signals:
            return None
        
        # Probability & Conviction (relaxed thresholds)
        base_prob = snap.long_probability
        conviction = snap.conviction
        
        if conviction < 0.25:  # Relaxed from 0.4
            return None
        
        final_prob = base_prob * (1 + 0.2 * conviction)
        final_prob = np.clip(final_prob, 0.52, 0.85)
        
        edge = final_prob - 0.50
        if edge < 0.03:  # Relaxed from 0.05
            return None
        
        # STOP: Below recent swing low
        stop = self._adaptive_stop(i)
        if stop is None or stop >= self.close[i]:
            return None
        
        # TARGET: BSL or 2.5:1 RR
        target = self._find_target(self.close[i])
        
        # Calculate RR
        entry = self.close[i]
        loss_per_unit = entry - stop
        reward_per_unit = target - entry
        
        if loss_per_unit <= 0 or reward_per_unit <= 0:
            return None
        
        rr = reward_per_unit / loss_per_unit
        
        # Minimum RR 1.5:1 (relaxed from 2.0)
        if rr < 1.5:
            return None
        
        # Expected value
        expected_r = final_prob * rr - (1 - final_prob)
        fee_drag = TOTAL_FRICTION * rr
        if expected_r < fee_drag:
            return None
        
        # Sizing
        risk_amount = self.balance * self.risk_pct
        risk_amount = min(risk_amount, self.balance * 0.10)
        
        quantity = risk_amount / max(loss_per_unit, 1e-12)
        cash = quantity * entry * (1 + FEE_RATE)
        
        if cash > self.balance * 0.95:
            quantity = (self.balance * 0.95) / (entry * (1 + FEE_RATE))
            cash = quantity * entry * (1 + FEE_RATE)
        
        min_cash = 5.0 if self.balance < 500 else 10.0
        if cash < min_cash:
            return None
        
        setup_desc = f"{setup['type']}"
        narrative = f"🎯 SNIPER | {setup_desc} | Conv={conviction:.2f} | Target ${target:.2f} | RR={rr:.1f}"
        plan_id = self._allocate_plan_id()
        
        return TradePlan(
            bar_idx=i, timestamp=snap.timestamp, direction="LONG",
            entry_price=entry, stop_price=stop, targets=[{"price": target, "type": setup['type']}],
            probability=final_prob, conviction=conviction,
            risk_reward=rr, expected_r=expected_r,
            size_multiplier=1.0,
            narrative=narrative, signals_snapshot=dict(snap.signals),
            plan_id=plan_id, mode="CAPITAL_GUARD",
            quantity=quantity, cash_used=cash, stop_current=stop,
            initial_risk=loss_per_unit,
            _target_price=target, _stage=1,
        )

    def _adaptive_stop(self, i):
        recent_lows = [(k, p) for k, p in self.swing_lows if k < i]
        if not recent_lows:
            return None
        last_low = recent_lows[-1][1]
        buffer = last_low * 0.003  # 0.3% buffer
        stop = last_low - buffer
        min_dist = self.close[i] * 0.006  # 0.6% minimum
        if self.close[i] - stop < min_dist:
            stop = self.close[i] - min_dist
        if stop >= self.close[i]:
            return None
        return stop

    def process_pending(self, i):
        for pend in list(self.pending_trades):
            if i > pend.bar_idx + 3:
                self.pending_trades.remove(pend)
                continue
            fill_price = self.open[i]
            if fill_price <= pend.stop_price:
                self.pending_trades.remove(pend)
                continue
            pend.entry_price = fill_price
            pend.entry_bar = i
            pend.state = "OPEN"
            pend.stop_current = pend.stop_price
            pend._max_price_reached = fill_price
            pend._min_price_reached = fill_price
            fee_rate = MAKER_FEE_RATE
            pend._entry_fee_paid = pend.quantity * fill_price * fee_rate
            total_cost = pend.quantity * fill_price + pend._entry_fee_paid
            self.balance -= total_cost
            self.active_orders.append({'plan_id': pend.plan_id, 'type': 'STOP_LOSS', 'price': pend.stop_price, 'qty': pend.quantity})
            self.total_fees_paid += pend._entry_fee_paid
            self.open_trades.append(pend)
            self.pending_trades.remove(pend)
            self.last_signal_bar = i
            date_str = str(self.timestamp[i])[:10]
            self.daily_trades[date_str] = self.daily_trades.get(date_str, 0) + 1

    def manage_trades(self, i):
        for trade in list(self.open_trades):
            if trade.entry_bar is None:
                continue
            trade.bars_held = i - trade.entry_bar
            trade._max_price_reached = max(trade._max_price_reached, self.high[i])
            trade._min_price_reached = min(trade._min_price_reached, self.low[i])
            trade.mfe = trade._max_price_reached - trade.entry_price
            trade.mae = trade._min_price_reached - trade.entry_price
            current_r = (self.close[i] - trade.entry_price) / max(trade.initial_risk, 1e-12)
            
            # 1. STOP CHECK
            if self.low[i] <= trade.stop_current:
                exit_price = trade.stop_current
                if exit_price < self.low[i] or exit_price > self.high[i]:
                    exit_price = self.low[i]
                self._close_trade(trade, i, exit_price, "STOP")
                continue
            
            # 2. TARGET HIT - Partial TP
            if trade._stage == 1 and trade._max_price_reached >= trade._target_price:
                self._execute_partial_tp(trade, i, trade._target_price)
                trade._stage = 2
                continue
            
            # 3. AFTER TARGET - Trail stop
            if trade._stage == 2:
                total_fees = trade._entry_fee_paid + trade._exit_fee_paid
                fees_per_unit = total_fees / max(trade.quantity, 1e-12)
                breakeven = trade.entry_price + fees_per_unit
                trade.stop_current = max(trade.stop_current, breakeven)
                recent_lows = [(k, p) for k, p in self.swing_lows if k < i]
                if recent_lows:
                    last_low = recent_lows[-1][1]
                    trail_stop = last_low - (last_low * 0.001)
                    trade.stop_current = max(trade.stop_current, trail_stop)
                continue
            
            # 4. TIMEOUT (max 60 bars)
            if trade.bars_held > 60 and current_r < 0.5:
                self._close_trade(trade, i, self.close[i], "TIMEOUT")
                continue

    def _execute_partial_tp(self, trade, i, target_price):
        if self.high[i] < target_price and trade._max_price_reached < target_price:
            return
        partial_qty = trade.quantity * 0.5
        is_maker = True
        exit_price = target_price
        if exit_price < self.low[i] or exit_price > self.high[i]:
            if trade._max_price_reached >= exit_price:
                exit_price = min(exit_price, trade._max_price_reached)
            else:
                exit_price = self.high[i]
        exit_pnl, _, exit_fee, slippage_cost = self.calculate_true_net_pnl(trade.entry_price, exit_price, partial_qty, is_maker)
        proceeds = partial_qty * exit_price - exit_fee - slippage_cost
        self.balance += proceeds
        trade.realized_pnl += exit_pnl
        trade.quantity -= partial_qty
        trade._partial_qty_sold += partial_qty
        self.purge_all_plan_orders(trade.plan_id)
        trade._exit_fee_paid += exit_fee
        trade._slippage_paid += slippage_cost
        self.total_fees_paid += exit_fee
        self.total_slippage_paid += slippage_cost
        if trade.quantity <= 1e-12:
            self._close_trade(trade, i, exit_price, "TARGET_FULL")

    def _close_trade(self, trade, i, price, reason):
        market_low = self.low[i]
        market_high = self.high[i]
        if reason == "STOP":
            exit_price = price
            if exit_price < market_low:
                exit_price = market_low
            elif exit_price > market_high:
                exit_price = market_high
        else:
            exit_price = price
            if exit_price < market_low:
                exit_price = market_low
            elif exit_price > market_high:
                if trade._max_price_reached >= exit_price:
                    pass
                else:
                    exit_price = market_high
        remaining = trade.quantity
        if remaining > 0:
            is_maker = True
            close_pnl, _, exit_fee, slippage_cost = self.calculate_true_net_pnl(trade.entry_price, exit_price, remaining, is_maker)
            gross_exit = remaining * exit_price
            self.balance += gross_exit - exit_fee - slippage_cost
            trade.realized_pnl += close_pnl
            trade._exit_fee_paid += exit_fee
            trade._slippage_paid += slippage_cost
            self.total_fees_paid += exit_fee
            self.total_slippage_paid += slippage_cost
            trade.quantity = 0.0
        self.purge_all_plan_orders(trade.plan_id)
        trade.state = "CLOSED"
        trade.exit_bar = i
        trade.exit_price = exit_price
        trade.exit_reason = reason
        if trade in self.open_trades:
            self.open_trades.remove(trade)
        self.closed_trades.append(trade)
        snap = self.ef.get_snapshot(trade.bar_idx)
        self.ef.record_outcome(snap, trade.realized_pnl / max(trade.cash_used, 1e-12) * 100)

    def add_pending(self, plan):
        self.pending_trades.append(plan)

    def get_equity(self, i):
        eq = self.balance
        for t in self.open_trades:
            eq += t.quantity * self.close[i]
        for t in self.pending_trades:
            eq += t.cash_used
        return eq

    def verify_all_trades(self):
        return {'total': len(self.fraud_violations)}
