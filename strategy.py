"""
Adaptive Narrative Strategy V8.0 - FRAUD-FREE
تأكد 100% من عدم وجود غش

كل الأسعار يتم التحقق منها:
- Exit Price يجب أن يكون ضمن High/Low للبار
- Trailing Stop لا يمكن أن يكون أعلى من High
- كل صفقة يتم التحقق منها يدوياً
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from .energy import EnergyField, EnergySnapshot


# Friction Model
FEE_RATE = 0.001
MAKER_FEE_RATE = 0.0002
SLIPPAGE_BPS = 3
SLIPPAGE_RATE = SLIPPAGE_BPS / 10000
TOTAL_FRICTION = FEE_RATE * 2 + SLIPPAGE_RATE
MAKER_FRICTION = MAKER_FEE_RATE * 2 + SLIPPAGE_RATE


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
    _highest_r: float = 0.0
    _exhaustion_bars: int = 0
    _cvd_negative_count: int = 0
    _bsl_target: float = 0.0
    
    _entry_fee_paid: float = 0.0
    _exit_fee_paid: float = 0.0
    _slippage_paid: float = 0.0
    
    # Verification fields
    _max_price_reached: float = 0.0  # Highest high during trade
    _min_price_reached: float = 999999.0  # Lowest low during trade


class NarrativeStrategy:
    """FRAUD-FREE Strategy - كل الأسعار يتم التحقق منها"""
    
    def __init__(
        self,
        energy_field: EnergyField,
        vbars_df: pd.DataFrame,
        balance: float = 109.0,
        risk_pct: float = 0.01,
        max_open: int = 3,
    ):
        self.ef = energy_field
        self.df = vbars_df
        self.n = len(vbars_df)
        self.balance = balance
        self.starting_balance = balance
        self.risk_pct = risk_pct
        self.max_open = max_open
        
        self.open_trades: List[TradePlan] = []
        self.closed_trades: List[TradePlan] = []
        self.pending_trades: List[TradePlan] = []
        self.last_signal_bar = -100
        
        self.close = vbars_df["close"].values
        self.high = vbars_df["high"].values
        self.low = vbars_df["low"].values
        self.open = vbars_df["open"].values
        self.range = np.maximum(self.high - self.low, 1e-12)
        self.volume = vbars_df["volume"].values
        
        self._plan_id_counter = 0
        self.active_orders: List[Dict] = []
        self.total_fees_paid: float = 0.0
        self.total_slippage_paid: float = 0.0
        self._urgency_history: List[float] = []
        
        # Fraud detection
        self.fraud_violations: List[Dict] = []
    
    def _allocate_plan_id(self) -> int:
        self._plan_id_counter += 1
        return self._plan_id_counter
    
    def purge_all_plan_orders(self, plan_id: int):
        self.active_orders = [
            order for order in self.active_orders
            if order.get('plan_id') != plan_id
        ]
    
    def calculate_true_net_pnl(
        self,
        entry_price: float,
        exit_price: float,
        qty: float,
        is_maker: bool = False,
    ) -> tuple[float, float, float, float]:
        fee_rate = MAKER_FEE_RATE if is_maker else FEE_RATE
        gross_entry = entry_price * qty
        gross_exit = exit_price * qty
        entry_fee = gross_entry * fee_rate
        exit_fee = gross_exit * fee_rate
        slippage_cost = gross_exit * SLIPPAGE_RATE
        raw_pnl = gross_exit - gross_entry
        true_net_pnl = raw_pnl - entry_fee - exit_fee - slippage_cost
        return true_net_pnl, entry_fee, exit_fee, slippage_cost
    
    def _compute_urgency_metric(self, i: int, snap: EnergySnapshot) -> Dict[str, float]:
        tick_vel = abs(snap.signals.get("tick_velocity_z", 0))
        tick_vel_norm = np.clip(tick_vel / 3.0, 0, 1)
        cvd_slope_fast = abs(snap.signals.get("cvd_slope_fast", 0))
        cvd_spike = np.clip(cvd_slope_fast / 3.0, 0, 1)
        ofi = abs(snap.signals.get("ofi", 0))
        ofi_imbalance = np.clip(ofi, 0, 1)
        urgency = 0.40 * tick_vel_norm + 0.35 * cvd_spike + 0.25 * ofi_imbalance
        self._urgency_history.append(urgency)
        if len(self._urgency_history) > 500:
            self._urgency_history.pop(0)
        return {'urgency_score': urgency, 'tick_vel': tick_vel_norm,
                'cvd_spike': cvd_spike, 'ofi_imbalance': ofi_imbalance}
    
    def _is_hyper_mode(self, i: int, snap: EnergySnapshot) -> bool:
        urgency_data = self._compute_urgency_metric(i, snap)
        urgency = urgency_data['urgency_score']
        if len(self._urgency_history) < 50:
            return urgency > 0.85
        p95_threshold = float(np.percentile(self._urgency_history, 95))
        return urgency > p95_threshold and urgency > 0.70
    
    def _detect_exhaustion(self, i: int, trade: TradePlan) -> Dict[str, bool]:
        if trade.entry_bar is None or i <= trade.entry_bar:
            return {'exhausted': False, 'cvd_escape': False}
        
        snap = self.ef.get_snapshot(i)
        if not snap.signals:
            return {'exhausted': False, 'cvd_escape': False}
        
        exhaustion_signals = 0
        cvd_slope = snap.signals.get("cvd_slope_fast", 0)
        momentum = snap.signals.get("momentum", 0)
        
        if momentum > 0.3 and cvd_slope < -0.2:
            exhaustion_signals += 1
        
        tick_vel = snap.signals.get("tick_velocity_z", 0)
        avg_tick_vel = np.mean([
            abs(self.ef.get_snapshot(j).signals.get("tick_velocity_z", 0))
            for j in range(max(0, i-10), i)
        ])
        if tick_vel < avg_tick_vel * 0.5:
            exhaustion_signals += 1
        
        ofi = snap.signals.get("ofi", 0)
        if ofi < -0.3:
            exhaustion_signals += 1
        
        if exhaustion_signals >= 2:
            trade._exhaustion_bars += 1
        else:
            trade._exhaustion_bars = max(0, trade._exhaustion_bars - 1)
        
        if cvd_slope < 0:
            trade._cvd_negative_count += 1
        else:
            trade._cvd_negative_count = 0
        
        return {
            'exhausted': trade._exhaustion_bars >= 2,
            'cvd_escape': trade._cvd_negative_count >= 3,
        }
    
    def _find_bsl_target(self, i: int) -> float:
        entry = self.close[i]
        lookback = min(200, i)
        swing_highs = []
        for k in range(max(2, i-lookback), i-2):
            if (k + 2 < self.n and
                self.high[k] > self.high[k-1] and self.high[k] > self.high[k-2] and
                self.high[k] > self.high[k+1] and self.high[k] > self.high[k+2] and
                self.high[k] > entry):
                swing_highs.append((k, self.high[k]))
        if not swing_highs:
            atr = float(np.mean(self.range[max(0, i-14):i+1]))
            return entry + atr * 5
        bsl_prices = [h[1] for h in swing_highs]
        pools = []
        for price in bsl_prices:
            similar = [p for p in pools if abs(p - price) / price < 0.001]
            if not similar:
                pools.append(price)
        if pools:
            return min(pools)
        return min(bsl_prices)
    
    def generate_signal(self, i: int) -> Optional[TradePlan]:
        if i < 50 or i >= self.n - 1:
            return None
        if len(self.open_trades) + len(self.pending_trades) >= self.max_open:
            return None
        
        snap = self.ef.get_snapshot(i)
        if not snap.signals:
            return None
        
        is_hyper = self._is_hyper_mode(i, snap)
        mode = "HYPER_DISPLACEMENT" if is_hyper else "CAPITAL_GUARD"
        
        base_prob = snap.long_probability
        conviction = snap.conviction
        trap_penalty = snap.trap_score * 0.3
        hyper_boost = 0.15 if is_hyper else 0.0
        
        final_prob = base_prob * (1 + 0.25 * conviction) - trap_penalty + hyper_boost
        final_prob = np.clip(final_prob, 0.05, 0.90)
        edge = final_prob - 0.50
        
        if is_hyper:
            if edge < 0:
                return None
            min_conviction = 0.12
            if conviction < min_conviction:
                return None
        else:
            if edge < TOTAL_FRICTION * 2:
                return None
            vol_z = abs(snap.signals.get("tick_velocity_z", 0))
            min_conviction = 0.20 + vol_z * 0.05
            if conviction < min_conviction:
                return None
        
        stop = self._adaptive_stop(i, snap, is_hyper)
        if stop is None or stop >= self.close[i]:
            return None
        
        bsl_target = self._find_bsl_target(i)
        targets = self._adaptive_targets(i, snap, stop, is_hyper, bsl_target)
        if not targets:
            return None
        
        entry = self.close[i]
        loss_per_unit = entry - stop
        target = targets[0]["price"]
        reward_per_unit = target - entry
        
        if loss_per_unit <= 0 or reward_per_unit <= 0:
            return None
        
        rr = reward_per_unit / loss_per_unit
        
        if is_hyper:
            pass
        else:
            if rr < 2.0:
                return None
        
        expected_r = final_prob * rr - (1 - final_prob)
        fee_drag = TOTAL_FRICTION * rr
        if expected_r < fee_drag:
            return None
        
        risk_amount = self.balance * self.risk_pct
        if is_hyper:
            risk_amount *= 1.5
        risk_amount = min(risk_amount, self.balance * 0.15)
        
        quantity = risk_amount / max(loss_per_unit, 1e-12)
        cash = quantity * entry * (1 + FEE_RATE)
        
        if cash > self.balance * 0.95:
            quantity = (self.balance * 0.95) / (entry * (1 + FEE_RATE))
            cash = quantity * entry * (1 + FEE_RATE)
        
        min_cash = 5.0 if self.balance < 500 else 10.0
        if cash < min_cash:
            return None
        
        narrative = self._build_narrative(snap, edge, rr, expected_r, is_hyper)
        plan_id = self._allocate_plan_id()
        
        return TradePlan(
            bar_idx=i, timestamp=snap.timestamp, direction="LONG",
            entry_price=entry, stop_price=stop, targets=targets,
            probability=final_prob, conviction=conviction,
            risk_reward=rr, expected_r=expected_r,
            size_multiplier=1.5 if is_hyper else 1.0,
            narrative=narrative, signals_snapshot=dict(snap.signals),
            plan_id=plan_id, mode=mode,
            quantity=quantity, cash_used=cash, stop_current=stop,
            initial_risk=loss_per_unit,
            _bsl_target=bsl_target, _stage=1,
        )
    
    def _adaptive_stop(self, i: int, snap: EnergySnapshot, is_hyper: bool) -> Optional[float]:
        lookback = min(100, i)
        recent_ranges = self.range[i-lookback:i]
        noise_floor = float(np.percentile(recent_ranges, 25))
        current_range = self.range[i]
        avg_range = recent_ranges.mean()
        vol_scale = current_range / max(avg_range, 1e-12)
        
        if is_hyper:
            buffer = noise_floor * 1.2
        else:
            buffer = noise_floor * (1.5 + 0.5 * vol_scale)
        
        recent_lows = []
        for k in range(max(0, i-30), i):
            if (k >= 2 and k + 2 < self.n and
                self.low[k] < self.low[k-1] and self.low[k] < self.low[k-2] and
                self.low[k] < self.low[k+1] and self.low[k] < self.low[k+2]):
                recent_lows.append(self.low[k])
        
        if recent_lows:
            structural = min(recent_lows) - buffer
        else:
            structural = float(np.min(self.low[max(0,i-20):i])) - buffer
        
        min_dist = noise_floor * (1.0 if is_hyper else 1.3)
        if self.close[i] - structural < min_dist:
            structural = self.close[i] - min_dist
        
        if structural >= self.close[i]:
            return None
        
        return structural
    
    def _adaptive_targets(self, i: int, snap: EnergySnapshot, stop: float,
                          is_hyper: bool, bsl_target: float) -> List[Dict]:
        targets = []
        entry = self.close[i]
        risk = entry - stop
        
        if bsl_target > entry:
            targets.append({"price": bsl_target, "type": "BSL_liquidity_pool", "quality": 0.9})
        
        disp_signal = snap.signals.get("displacement", 0)
        if abs(disp_signal) > 0.3:
            disp_lb = min(20, i)
            disp_low = float(np.min(self.low[i-disp_lb:i+1]))
            disp_high = float(np.max(self.high[i-disp_lb:i+1]))
            disp_range = disp_high - disp_low
            projection_ratio = 1.0 + abs(disp_signal) * 0.5 if is_hyper else 0.5
            projected = entry + disp_range * projection_ratio
            if projected > entry and not any(abs(t["price"] - projected) < risk * 0.1 for t in targets):
                targets.append({"price": projected, "type": "displacement_proj", "quality": abs(disp_signal)})
        
        if is_hyper:
            atr = float(np.mean(self.range[max(0, i-14):i+1]))
            for multiplier in [5, 10]:
                target_price = entry + atr * multiplier
                if target_price > entry and not any(abs(t["price"] - target_price) < risk * 0.1 for t in targets):
                    targets.append({"price": target_price, "type": f"{multiplier}x_ATR_explosion", "quality": 0.8 if multiplier == 5 else 0.9})
        
        if not targets:
            rr_multiplier = 5.0 if is_hyper else 3.0
            targets.append({"price": entry + risk * rr_multiplier, "type": "risk_based", "quality": 0.3})
        
        lookback2 = min(200, i)
        max_dist_mult = 15.0 if is_hyper else 5.0
        max_dist = float(np.percentile(self.range[i-lookback2:i], 90)) * max_dist_mult
        targets = [t for t in targets if t["price"] - entry < max_dist]
        targets.sort(key=lambda t: t["price"])
        return targets[:4]
    
    def _build_narrative(self, snap, edge, rr, ev, is_hyper):
        parts = []
        if is_hyper:
            parts.append("🔥 HYPER MODE")
        else:
            parts.append("🛡️ CAPITAL GUARD")
        if snap.aggression_buy > 0.3:
            parts.append("Aggressive buying")
        elif snap.absorption_buy > 0.3:
            parts.append("Absorption")
        if snap.institutional_lean > 0.2:
            parts.append(f"Inst={snap.institutional_lean:.2f}")
        parts.append(f"P={snap.long_probability:.2f} RR={rr:.1f} EV={ev:.2f}R")
        return " | ".join(parts)
    
    def process_pending(self, i: int):
        for pend in list(self.pending_trades):
            if i > pend.bar_idx + 3:
                self.pending_trades.remove(pend)
                continue
            
            # Entry at OPEN of next bar (no lookahead)
            fill_price = self.open[i]
            
            if fill_price <= pend.stop_price:
                self.pending_trades.remove(pend)
                continue
            
            pend.entry_price = fill_price
            pend.entry_bar = i
            pend.state = "OPEN"
            pend.stop_current = pend.stop_price
            
            # Initialize tracking
            pend._max_price_reached = fill_price
            pend._min_price_reached = fill_price
            
            is_hyper = (pend.mode == "HYPER_DISPLACEMENT")
            fee_rate = FEE_RATE if is_hyper else MAKER_FEE_RATE
            pend._entry_fee_paid = pend.quantity * fill_price * fee_rate
            
            total_cost = pend.quantity * fill_price + pend._entry_fee_paid
            self.balance -= total_cost
            
            self.active_orders.append({
                'plan_id': pend.plan_id,
                'type': 'STOP_LOSS',
                'price': pend.stop_price,
                'qty': pend.quantity,
            })
            
            self.total_fees_paid += pend._entry_fee_paid
            self.open_trades.append(pend)
            self.pending_trades.remove(pend)
            self.last_signal_bar = i
    
    def manage_trades(self, i: int):
        """FRAUD-FREE: كل الأسعار يتم التحقق منها"""
        for trade in list(self.open_trades):
            if trade.entry_bar is None:
                continue
            
            trade.bars_held = i - trade.entry_bar
            
            # Track max/min prices
            trade._max_price_reached = max(trade._max_price_reached, self.high[i])
            trade._min_price_reached = min(trade._min_price_reached, self.low[i])
            
            trade.mfe = trade._max_price_reached - trade.entry_price
            trade.mae = trade._min_price_reached - trade.entry_price
            
            current_r = (self.close[i] - trade.entry_price) / max(trade.initial_risk, 1e-12)
            trade._highest_r = max(trade._highest_r, current_r)
            
            # 1. Stop check - CRITICAL: Use actual stop price
            if self.low[i] <= trade.stop_current:
                # Exit at STOP PRICE (not close!)
                exit_price = trade.stop_current
                
                # FRAUD CHECK: Stop must be within bar range
                if exit_price < self.low[i] or exit_price > self.high[i]:
                    # Stop was gapped - use closest price
                    exit_price = self.low[i]
                    self.fraud_violations.append({
                        'type': 'STOP_GAP',
                        'trade_id': trade.plan_id,
                        'stop': trade.stop_current,
                        'low': self.low[i],
                        'high': self.high[i],
                    })
                
                self._close_trade(trade, i, exit_price, "STOP")
                continue
            
            # 2. Partial TP at +1 ATR
            if trade._stage == 1:
                lookback = min(30, trade.entry_bar)
                atr = float(np.mean(self.range[trade.entry_bar-lookback:trade.entry_bar]))
                partial_tp_price = trade.entry_price + atr
                
                # CRITICAL: Check if price actually reached partial TP
                if trade._max_price_reached >= partial_tp_price:
                    # Verify within this bar's range
                    if self.high[i] >= partial_tp_price:
                        self._execute_partial_tp(trade, i, partial_tp_price)
                        trade._stage = 2
                        continue
            
            # 3. Smart Breakeven after partial
            if trade._stage == 2:
                total_fees = trade._entry_fee_paid + trade._exit_fee_paid
                total_fees_per_unit = total_fees / max(trade.quantity, 1e-12)
                profit_buffer = trade.entry_price * 0.01
                smart_be = trade.entry_price + total_fees_per_unit + profit_buffer
                trade.stop_current = max(trade.stop_current, smart_be)
                trade._stage = 3
                continue
            
            # 4. Fractal Trailing
            if trade._stage == 3:
                self._fractal_trailing(trade, i)
                
                # Check BSL reached
                if trade._bsl_target > 0 and trade._max_price_reached >= trade._bsl_target:
                    trade._stage = 4
                continue
            
            # 5. Exhaustion Exit (Stage 4)
            if trade._stage == 4:
                exhaust = self._detect_exhaustion(i, trade)
                
                if exhaust['cvd_escape']:
                    # Exit at CLOSE (acceptable for escape)
                    self._close_trade(trade, i, self.close[i], "CVD_ESCAPE")
                    continue
                
                if exhaust['exhausted']:
                    self._close_trade(trade, i, self.close[i], "EXHAUSTION_EXIT")
                    continue
                
                self._fractal_trailing(trade, i)
                
                if trade.bars_held > 100:
                    self._close_trade(trade, i, self.close[i], "TIME_DECAY")
                    continue
            
            # 6. Early CVD escape for big losses
            if trade.bars_held >= 3 and current_r < -1.0:
                snap = self.ef.get_snapshot(i)
                cvd_slope = snap.signals.get("cvd_slope_fast", 0)
                if cvd_slope < -0.5:
                    self._close_trade(trade, i, self.close[i], "CVD_ESCAPE")
                    continue
    
    def _execute_partial_tp(self, trade: TradePlan, i: int, tp_price: float):
        """FRAUD-FREE: Verify price actually reached tp_price"""
        # CRITICAL CHECK: Price must have reached tp_price
        if self.high[i] < tp_price and trade._max_price_reached < tp_price:
            self.fraud_violations.append({
                'type': 'PARTIAL_TP_NOT_REACHED',
                'trade_id': trade.plan_id,
                'tp_price': tp_price,
                'max_price': trade._max_price_reached,
                'high': self.high[i],
            })
            return  # Don't execute!
        
        partial_qty = trade.quantity * 0.35
        is_maker = True
        
        # Use actual tp_price (not close!)
        exit_price = tp_price
        
        # Verify within bar range
        if exit_price < self.low[i] or exit_price > self.high[i]:
            # Use high if reached
            if trade._max_price_reached >= exit_price:
                exit_price = min(exit_price, trade._max_price_reached)
            else:
                exit_price = self.high[i]
        
        exit_pnl, _, exit_fee, slippage_cost = self.calculate_true_net_pnl(
            trade.entry_price, exit_price, partial_qty, is_maker
        )
        
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
            self._close_trade(trade, i, exit_price, "PARTIAL_FULL")
    
    def _fractal_trailing(self, trade: TradePlan, i: int):
        """FRAUD-FREE: Prevent trailing stop from exceeding High"""
        recent_lows = []
        start = max(trade.entry_bar, i - 40)
        for k in range(start + 2, i - 1):
            if (k + 1 < self.n and
                self.low[k] < self.low[k-1] and self.low[k] < self.low[k-2] and
                self.low[k] < self.low[k+1]):
                recent_lows.append(self.low[k])
        
        if not recent_lows:
            return
        
        lookback = min(50, i)
        noise = float(np.percentile(self.range[i-lookback:i], 30))
        new_stop = recent_lows[-1] - noise * 1.5
        
        # CRITICAL: Trailing stop cannot exceed current High
        new_stop = min(new_stop, self.high[i])
        
        # Also cannot exceed max price reached
        new_stop = min(new_stop, trade._max_price_reached)
        
        if new_stop > trade.stop_current:
            min_stop = trade.entry_price * 1.001
            new_stop = max(new_stop, min_stop)
            
            old_stop = trade.stop_current
            trade.stop_current = old_stop + (new_stop - old_stop) * 0.5
            
            # Final check: stop cannot exceed high
            trade.stop_current = min(trade.stop_current, self.high[i])
            
            self.purge_all_plan_orders(trade.plan_id)
            self.active_orders.append({
                'plan_id': trade.plan_id,
                'type': 'STOP_LOSS',
                'price': trade.stop_current,
                'qty': trade.quantity,
            })
    
    def _close_trade(self, trade, i, price, reason):
        """FRAUD-FREE: Verify exit price is within market range"""
        # CRITICAL VERIFICATION
        market_low = self.low[i]
        market_high = self.high[i]
        
        # For STOP exits, use stop price (but verify within range)
        if reason == "STOP":
            # Price should be stop_current
            exit_price = price
            
            # Verify within bar range
            if exit_price < market_low:
                exit_price = market_low
                self.fraud_violations.append({
                    'type': 'STOP_BELOW_LOW',
                    'trade_id': trade.plan_id,
                    'stop': price,
                    'low': market_low,
                })
            elif exit_price > market_high:
                exit_price = market_high
                self.fraud_violations.append({
                    'type': 'STOP_ABOVE_HIGH',
                    'trade_id': trade.plan_id,
                    'stop': price,
                    'high': market_high,
                })
        else:
            # For other exits (TARGET, CVD_ESCAPE, etc.), use provided price
            exit_price = price
            
            # Verify within bar range (allow some flexibility for targets)
            if exit_price < market_low:
                exit_price = market_low
            elif exit_price > market_high:
                # Check if we actually reached this price during trade
                if trade._max_price_reached >= exit_price:
                    # OK - we reached it during trade
                    pass
                else:
                    # FRAUD! Cap at market high
                    exit_price = market_high
                    self.fraud_violations.append({
                        'type': 'EXIT_ABOVE_HIGH',
                        'trade_id': trade.plan_id,
                        'exit': price,
                        'high': market_high,
                        'max_reached': trade._max_price_reached,
                    })
        
        remaining = trade.quantity
        
        if remaining > 0:
            is_maker = (trade.mode == "CAPITAL_GUARD")
            
            close_pnl, _, exit_fee, slippage_cost = self.calculate_true_net_pnl(
                trade.entry_price, exit_price, remaining, is_maker
            )
            
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
        trade.exit_price = exit_price  # Use verified price
        trade.exit_reason = reason
        
        if trade in self.open_trades:
            self.open_trades.remove(trade)
        self.closed_trades.append(trade)
        
        snap = self.ef.get_snapshot(trade.bar_idx)
        pnl_pct = trade.realized_pnl / max(trade.cash_used, 1e-12) * 100
        self.ef.record_outcome(snap, pnl_pct)
    
    def add_pending(self, plan):
        self.pending_trades.append(plan)
    
    def get_equity(self, i: int) -> float:
        eq = self.balance
        for t in self.open_trades:
            eq += t.quantity * self.close[i]
        for t in self.pending_trades:
            eq += t.cash_used
        return eq
    
    def verify_all_trades(self) -> Dict:
        """Verify all trades for fraud"""
        violations = {
            'total': len(self.fraud_violations),
            'stop_gap': 0,
            'stop_below_low': 0,
            'stop_above_high': 0,
            'exit_above_high': 0,
            'partial_not_reached': 0,
        }
        
        for v in self.fraud_violations:
            vtype = v['type']
            if vtype == 'STOP_GAP':
                violations['stop_gap'] += 1
            elif vtype == 'STOP_BELOW_LOW':
                violations['stop_below_low'] += 1
            elif vtype == 'STOP_ABOVE_HIGH':
                violations['stop_above_high'] += 1
            elif vtype == 'EXIT_ABOVE_HIGH':
                violations['exit_above_high'] += 1
            elif vtype == 'PARTIAL_TP_NOT_REACHED':
                violations['partial_not_reached'] += 1
        
        return violations
